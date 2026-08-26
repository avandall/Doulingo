"""
app/core/exemplar_rag.py
========================
Dialogue Exemplar Bank & Hybrid RAG Engine (TASK-003).

Provides:
- Metadata filtering (level, persona, topic, dialogue_act) with progressive relaxation.
- Semantic similarity search using TF-IDF / Cosine distance against state_summary.
- Maximal Marginal Relevance (MMR) ranking for response diversity.
- Automatic fallback mechanisms to guarantee returning 2-3 top exemplars.
"""

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


class DialogueExemplar(dict):
    """
    Dict subclass representing a dialogue exemplar.
    Supports both dict key access (ex['text']) and property access (ex.text).
    """

    def __getattr__(self, key: str) -> Any:
        try:
            return self[key]
        except KeyError:
            raise AttributeError(f"'DialogueExemplar' object has no attribute '{key}'")

    def __setattr__(self, key: str, value: Any) -> None:
        self[key] = value


class ExemplarRAG:
    """
    Hybrid RAG Engine for natural dialogue exemplars.
    Combines Metadata Filtering, TF-IDF Cosine Similarity Search, and MMR Diversity.
    """

    def __init__(
        self,
        data_path: str = "app/data/sample_dialogue_bank.json",
        exemplars: list[dict[str, Any]] | None = None,
    ) -> None:
        self.data_path = data_path
        self.exemplars: list[DialogueExemplar] = []
        self.vectorizer: TfidfVectorizer | None = None
        self.tfidf_matrix: np.ndarray | None = None

        if exemplars is not None:
            self._load_from_list(exemplars)
        else:
            self.load_bank(data_path)

    def _load_from_list(self, raw_list: list[dict[str, Any]]) -> None:
        """Internal helper to populate and index exemplars from a list of dicts."""
        self.exemplars = []
        for idx, item in enumerate(raw_list):
            ex = DialogueExemplar({
                "id": str(item.get("id", f"ex_{idx+1:03d}")),
                "level": str(item.get("level", "A1")).upper(),
                "persona": str(item.get("persona", "Default")),
                "topic": str(item.get("topic", "general")),
                "dialogue_act": str(item.get("dialogue_act", "statement")),
                "text": str(item.get("text", "")).strip(),
                "quality_score": float(item.get("quality_score", 4.0)),
                "score": 0.0,
            })
            if ex["text"]:
                self.exemplars.append(ex)

        self._build_vector_index()

    def load_bank(self, data_path: str | None = None) -> int:
        """Loads dialogue bank from JSON file."""
        target_path = data_path or self.data_path
        p = Path(target_path)
        if not p.exists() and not p.is_absolute():
            # Try resolving relative to workspace root
            p = Path(os.getcwd()) / target_path

        if p.exists():
            with open(p, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
                if isinstance(raw_data, list):
                    self._load_from_list(raw_data)
                    return len(self.exemplars)

        # Fallback to empty if file not found
        self._load_from_list([])
        return 0

    def _build_vector_index(self) -> None:
        """Fits TF-IDF vectorizer over all exemplar texts for fast vector search."""
        if not self.exemplars:
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        texts = [ex["text"] for ex in self.exemplars]
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            token_pattern=r"(?u)\b\w+\b",
            ngram_range=(1, 2),
            min_df=1,
        )
        try:
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)
        except ValueError:
            # Handle edge cases (e.g. empty or stop-words only texts)
            self.vectorizer = TfidfVectorizer(token_pattern=r"\S+")
            self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def get_total_count(self) -> int:
        """Returns total number of loaded exemplars."""
        return len(self.exemplars)

    def _match_field(self, item_val: str, target_val: str | None) -> bool:
        """Helper for case-insensitive metadata matching."""
        if not target_val or target_val == "*":
            return True
        return item_val.strip().lower() == target_val.strip().lower()

    def _filter_candidates(
        self,
        level: str | None = None,
        persona: str | None = None,
        topic: str | None = None,
        dialogue_act: str | None = None,
        min_candidates: int = 3,
    ) -> list[DialogueExemplar]:
        """
        Progressive metadata filtering with multi-stage relaxation
        to guarantee finding at least `min_candidates` matching exemplars.
        """
        if not self.exemplars:
            return []

        # Tiered filtering passes
        stages = [
            # 1. Exact match all provided criteria
            lambda ex: (
                self._match_field(ex["level"], level)
                and self._match_field(ex["persona"], persona)
                and self._match_field(ex["topic"], topic)
                and self._match_field(ex["dialogue_act"], dialogue_act)
            ),
            # 2. Match level + topic + dialogue_act (relax persona)
            lambda ex: (
                self._match_field(ex["level"], level)
                and self._match_field(ex["topic"], topic)
                and self._match_field(ex["dialogue_act"], dialogue_act)
            ),
            # 3. Match level + dialogue_act (relax topic & persona)
            lambda ex: (
                self._match_field(ex["level"], level)
                and self._match_field(ex["dialogue_act"], dialogue_act)
            ),
            # 4. Match level + topic
            lambda ex: (
                self._match_field(ex["level"], level)
                and self._match_field(ex["topic"], topic)
            ),
            # 5. Match level only
            lambda ex: self._match_field(ex["level"], level),
            # 6. Match dialogue_act only
            lambda ex: self._match_field(ex["dialogue_act"], dialogue_act),
            # 7. Match topic only
            lambda ex: self._match_field(ex["topic"], topic),
            # 8. All exemplars fallback
            lambda ex: True,
        ]

        seen_ids = set()
        candidates: list[DialogueExemplar] = []

        for stage_filter in stages:
            stage_matches = [ex for ex in self.exemplars if stage_filter(ex)]
            for ex in stage_matches:
                if ex["id"] not in seen_ids:
                    seen_ids.add(ex["id"])
                    candidates.append(ex)
            if len(candidates) >= min_candidates:
                break

        return candidates

    def _compute_semantic_scores(
        self, candidates: list[DialogueExemplar], state_summary: str | None
    ) -> list[float]:
        """Calculates semantic similarity scores between state_summary and candidates."""
        if not state_summary or not state_summary.strip() or self.vectorizer is None or self.tfidf_matrix is None:
            return [1.0 for _ in candidates]

        try:
            query_vec = self.vectorizer.transform([state_summary.strip()])
            cand_indices = [self.exemplars.index(c) for c in candidates if c in self.exemplars]

            if not cand_indices:
                return [1.0 for _ in candidates]

            cand_matrix = self.tfidf_matrix[cand_indices]
            sims = cosine_similarity(query_vec, cand_matrix)[0]
            return [float(s) for s in sims]
        except Exception:
            return [1.0 for _ in candidates]

    def retrieve(
        self,
        level: str | None = None,
        persona: str | None = None,
        topic: str | None = None,
        dialogue_act: str | None = None,
        state_summary: str | None = None,
        top_k: int = 3,
        use_mmr: bool = True,
        lambda_mult: float = 0.6,
    ) -> list[DialogueExemplar]:
        """
        Retrieves top_k exemplar sentences based on Metadata filter, Semantic similarity, and MMR.

        Args:
            level: CEFR level ("A1", "A2", "B1", "B2", "C1")
            persona: AI persona name ("Alex", "Lily", "Oscar", etc.)
            topic: Conversation topic ("daily_life", "work", "hobbies", etc.)
            dialogue_act: Dialogue act ("greeting", "question", "opinion", etc.)
            state_summary: Natural language context / user conversation summary
            top_k: Number of exemplars to return (default 3, typically 2-3)
            use_mmr: Whether to apply Maximal Marginal Relevance for diversity
            lambda_mult: MMR trade-off parameter between relevance (1.0) and diversity (0.0)

        Returns:
            List of 2-3 top exemplar items sorted by relevance & quality score.
        """
        if not self.exemplars:
            return []

        candidates = self._filter_candidates(
            level=level,
            persona=persona,
            topic=topic,
            dialogue_act=dialogue_act,
            min_candidates=top_k,
        )

        if not candidates:
            return []

        # Compute semantic similarity scores against state_summary
        sim_scores = self._compute_semantic_scores(candidates, state_summary)

        # Combine similarity score (70%) with quality_score (30%)
        scored_candidates: list[DialogueExemplar] = []
        for cand, sim in zip(candidates, sim_scores):
            q_norm = min(max(cand["quality_score"] / 5.0, 0.0), 1.0)
            combined_score = 0.7 * sim + 0.3 * q_norm
            cand_copy = DialogueExemplar(cand.copy())
            cand_copy["score"] = round(combined_score, 4)
            scored_candidates.append(cand_copy)

        # If MMR diversity disabled or state_summary empty, sort by combined score
        if not use_mmr or not state_summary or len(scored_candidates) <= top_k:
            scored_candidates.sort(key=lambda x: x["score"], reverse=True)
            return scored_candidates[:top_k]

        # Maximal Marginal Relevance (MMR) Diversity Selection
        return self._apply_mmr(
            candidates=scored_candidates,
            top_k=top_k,
            lambda_mult=lambda_mult,
        )

    def _apply_mmr(
        self,
        candidates: list[DialogueExemplar],
        top_k: int,
        lambda_mult: float,
    ) -> list[DialogueExemplar]:
        """Applies Maximal Marginal Relevance to select top_k diverse & relevant candidates."""
        if not candidates:
            return []

        # Vectorize candidate texts for inter-candidate similarity
        cand_texts = [c["text"] for c in candidates]
        try:
            temp_vectorizer = TfidfVectorizer(token_pattern=r"\S+")
            cand_matrix = temp_vectorizer.fit_transform(cand_texts)
            pairwise_sim = cosine_similarity(cand_matrix)
        except Exception:
            pairwise_sim = np.zeros((len(candidates), len(candidates)))

        selected_indices: list[int] = []
        unselected_indices = list(range(len(candidates)))

        # Pick candidate with highest combined score first
        best_idx = int(np.argmax([c["score"] for c in candidates]))
        selected_indices.append(best_idx)
        unselected_indices.remove(best_idx)

        while len(selected_indices) < top_k and unselected_indices:
            best_mmr = -float("inf")
            best_cand_idx = -1

            for idx in unselected_indices:
                rel = candidates[idx]["score"]
                max_sim_to_selected = max(pairwise_sim[idx, sel] for sel in selected_indices)
                mmr_score = lambda_mult * rel - (1.0 - lambda_mult) * max_sim_to_selected

                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best_cand_idx = idx

            if best_cand_idx != -1:
                selected_indices.append(best_cand_idx)
                unselected_indices.remove(best_cand_idx)
            else:
                break

        return [candidates[i] for i in selected_indices]


def format_exemplars_for_prompt(exemplars: list[dict[str, Any]]) -> str:
    """
    Formats a list of retrieved exemplar dicts into a prompt-friendly string.

    Example Output:
    - [greeting]: "Hello there! How are you doing today?"
    - [question]: "What is your favorite dish to eat for breakfast?"
    """
    if not exemplars:
        return "No specific dialogue exemplars retrieved."

    formatted_lines = []
    for ex in exemplars:
        act = ex.get("dialogue_act", "example")
        text = ex.get("text", "").strip()
        formatted_lines.append(f'- [{act}]: "{text}"')

    return "\n".join(formatted_lines)
