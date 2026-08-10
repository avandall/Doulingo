"""
Material Bank Data Models & Markdown Parser for Duolingo Speak
Parses academic IELTS material files (DB1_*.md to DB5_*.md) into Pydantic models.
Provides fast in-memory indexing (< 5ms retrieval) for the Prompt Factory.
"""

import glob
import os
import re
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class Persona(BaseModel):
    """AI Persona candidate for dynamic roleplay sampling."""
    id: str = Field(..., description="Persona ID, e.g. P1, P2, P3")
    title: str = Field(..., description="Persona title, e.g. Local Resident")
    description: str = Field(..., description="Behavioral description of persona")


class Question(BaseModel):
    """Question seed categorized by IELTS Band level."""
    id: str = Field(..., description="Question ID, e.g. Q_5_01")
    text: str = Field(..., description="Question prompt text")
    band: str = Field(default="5.0-6.0", description="Band level, e.g. 5.0-6.0 or 6.5+")


class VocabularyItem(BaseModel):
    """Academic collocations and vocabulary items with definitions."""
    phrase: str = Field(..., description="Vocabulary phrase or collocation")
    meaning: str = Field(..., description="Definition / Vietnamese context")
    band: str = Field(default="5.0-6.0", description="Band level, e.g. 5.0-6.0 or 6.5+")


class GrammarPattern(BaseModel):
    """High-scoring grammar response pattern."""
    pattern_id: str = Field(..., description="Pattern ID, e.g. Pattern_1")
    pattern: str = Field(..., description="Sentence pattern structure template")


class TopicBank(BaseModel):
    """Nuclear material bank for a specific topic."""
    topic_id: str = Field(..., description="Normalized topic ID")
    topic_name: str = Field(..., description="Human-readable topic title")
    target_levels: List[str] = Field(
        default_factory=lambda: ["5.0-6.0", "6.5+"],
        description="Target IELTS bands supported"
    )
    personas: List[Persona] = Field(default_factory=list)
    questions: List[Question] = Field(default_factory=list)
    vocabulary: List[VocabularyItem] = Field(default_factory=list)
    grammar_patterns: List[GrammarPattern] = Field(default_factory=list)


class MaterialBank:
    """In-memory indexer & loader for IELTS Material Banks."""

    def __init__(self, docs_dir: str = "docs") -> None:
        self.docs_dir = docs_dir
        self.topics: Dict[str, TopicBank] = {}

    @staticmethod
    def normalize_id(tid: str) -> str:
        """Normalize a topic ID string for robust case-insensitive lookups."""
        clean = tid.strip().lower()
        clean = re.sub(r'[\s_]+', '-', clean)
        clean = re.sub(r'[^\w-]', '', clean)
        return clean.strip('-')

    def load_all(self, docs_dir: Optional[str] = None) -> int:
        """Parse all DB*.md files in docs_dir and build in-memory TopicBank index."""
        target_dir = docs_dir or self.docs_dir
        files = sorted(glob.glob(os.path.join(target_dir, "DB*.md")))
        
        for filepath in files:
            self._parse_file(filepath)
            
        return len(self.topics)

    def _parse_file(self, filepath: str) -> None:
        """Parse a single markdown database file."""
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()

        split_pattern = r'\n(?=#\s*TOPIC:|\b##\s*Topic\s+\d+:|\b##\s*TOPIC:)'
        raw_blocks = re.split(split_pattern, content, flags=re.IGNORECASE)

        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            
            self._parse_topic_block(block)

    def _parse_topic_block(self, block: str) -> None:
        """Parse an individual topic block into a TopicBank instance."""
        top_match = re.search(r'#+\s*(?:TOPIC|Topic\s*\d*):\s*([^\n]+)', block, re.IGNORECASE)
        tid_match = re.search(r'`?topic_id:\s*[\"\']?([a-zA-Z0-9_-]+)[\"\']?`?', block)
        tname_match = re.search(r'`?topic_name:\s*[\"\']?([^\n\"\'`]+)[\"\']?`?', block)
        levels_match = re.search(r'`?target_levels:\s*\[([^\]]+)\]`?', block)

        if not top_match and not tid_match:
            return

        raw_title = top_match.group(1).strip() if top_match else (tname_match.group(1).strip() if tname_match else "")
        if raw_title.startswith("DB") or raw_title.upper().startswith("MASTER DATABASE"):
            return

        topic_name = tname_match.group(1).strip() if tname_match else raw_title
        raw_tid = tid_match.group(1).strip() if tid_match else raw_title
        topic_id = self.normalize_id(raw_tid)

        if not topic_id:
            return

        target_levels = []
        if levels_match:
            target_levels = [lvl.strip(' "\'').strip() for lvl in levels_match.group(1).split(',')]
        if not target_levels:
            target_levels = ["5.0-6.0", "6.5+"]

        personas = self._parse_personas(block)
        questions = self._parse_questions(block)
        vocabulary = self._parse_vocabulary(block)
        grammar_patterns = self._parse_grammar(block)

        if topic_id not in self.topics:
            self.topics[topic_id] = TopicBank(
                topic_id=topic_id,
                topic_name=topic_name,
                target_levels=target_levels,
                personas=personas,
                questions=questions,
                vocabulary=vocabulary,
                grammar_patterns=grammar_patterns
            )
        else:
            self._merge_topic(self.topics[topic_id], personas, questions, vocabulary, grammar_patterns)

    def _parse_personas(self, block: str) -> List[Persona]:
        """Extract persona pool from topic block."""
        personas: List[Persona] = []
        sec_match = re.search(r'1\.\s*PERSONA POOL(.*?)(?=2\.\s*QUESTION POOL|3\.\s*VOCABULARY|\Z)', block, re.DOTALL | re.IGNORECASE)
        if not sec_match:
            return personas

        for line in sec_match.group(1).split('\n'):
            line = line.strip()
            m1 = re.match(r'^(?:-\s*)?\[(P\d+)\]\s*\*\*([^\*]+)\*\*:\s*(.*)', line)
            if m1:
                personas.append(Persona(id=m1.group(1), title=m1.group(2).strip(), description=m1.group(3).strip()))
                continue
            m2 = re.match(r'^(?:-\s*)?\[(P\d+)\]\s*([^:]+):\s*(.*)', line)
            if m2:
                personas.append(Persona(id=m2.group(1), title=m2.group(2).strip(), description=m2.group(3).strip()))

        return personas

    def _parse_questions(self, block: str) -> List[Question]:
        """Extract question pool categorized by Band level."""
        questions: List[Question] = []
        sec_match = re.search(r'2\.\s*QUESTION POOL(.*?)(?=3\.\s*VOCABULARY|4\.\s*GRAMMAR|\Z)', block, re.DOTALL | re.IGNORECASE)
        if not sec_match:
            return questions

        current_band = "5.0-6.0"
        for line in sec_match.group(1).split('\n'):
            line = line.strip()
            if "Band 6.5+" in line or "Band 7" in line:
                current_band = "6.5+"
            elif "Band 5" in line or "Band 4" in line:
                current_band = "5.0-6.0"
            elif line.startswith('-'):
                if "None available" in line or "N/A" in line:
                    continue
                m = re.match(r'^\-\s*(?:(Q[_\d\w]+):\s*)?(.*)', line)
                if m:
                    qid = m.group(1) if m.group(1) else f"Q_{len(questions)+1}"
                    qval = m.group(2).strip()
                    if qval:
                        questions.append(Question(id=qid, text=qval, band=current_band))

        return questions

    def _parse_vocabulary(self, block: str) -> List[VocabularyItem]:
        """Extract vocabulary pool categorized by Band level."""
        vocab: List[VocabularyItem] = []
        sec_match = re.search(r'3\.\s*VOCABULARY.*?(.*?)(?=4\.\s*GRAMMAR|\Z)', block, re.DOTALL | re.IGNORECASE)
        if not sec_match:
            return vocab

        current_band = "5.0-6.0"
        for line in sec_match.group(1).split('\n'):
            line = line.strip()
            if "Band 6.5+" in line or "Band 7" in line:
                current_band = "6.5+"
            elif "Band 5" in line or "Band 4" in line:
                current_band = "5.0-6.0"
            elif line.startswith('-'):
                if "None available" in line or "N/A" in line:
                    continue
                m1 = re.match(r'^\-\s*[`\*]{1,2}([^`\*]+)[`\*]{1,2}:\s*(.*)', line)
                if m1:
                    phrase = m1.group(1).strip()
                    meaning = m1.group(2).strip()
                    vocab.append(VocabularyItem(phrase=phrase, meaning=meaning, band=current_band))
                    continue
                m2 = re.match(r'^\-\s*([^:]+):\s*(.*)', line)
                if m2:
                    phrase = m2.group(1).strip(' `*')
                    meaning = m2.group(2).strip()
                    vocab.append(VocabularyItem(phrase=phrase, meaning=meaning, band=current_band))

        return vocab

    def _parse_grammar(self, block: str) -> List[GrammarPattern]:
        """Extract grammar patterns from topic block."""
        grammar: List[GrammarPattern] = []
        sec_match = re.search(r'4\.\s*GRAMMAR.*?(.*?)(?=#|\Z)', block, re.DOTALL | re.IGNORECASE)
        if not sec_match:
            return grammar

        for line in sec_match.group(1).split('\n'):
            line = line.strip()
            if line.startswith('-'):
                m = re.match(r'^\-\s*(?:(Pattern[_\d\w]+):\s*)?\"?(.*?)\"?$', line)
                if m:
                    pid = m.group(1) if m.group(1) else f"Pattern_{len(grammar)+1}"
                    pat = m.group(2).strip()
                    if pat:
                        grammar.append(GrammarPattern(pattern_id=pid, pattern=pat))

        return grammar

    def _merge_topic(
        self,
        target: TopicBank,
        personas: List[Persona],
        questions: List[Question],
        vocabulary: List[VocabularyItem],
        grammar_patterns: List[GrammarPattern]
    ) -> None:
        """Merge additional pool items into existing TopicBank instance without duplication."""
        existing_titles = {p.title.lower() for p in target.personas}
        for p in personas:
            if p.title.lower() not in existing_titles:
                target.personas.append(p)
                existing_titles.add(p.title.lower())

        existing_qtexts = {q.text.lower() for q in target.questions}
        for q in questions:
            if q.text.lower() not in existing_qtexts:
                target.questions.append(q)
                existing_qtexts.add(q.text.lower())

        existing_phrases = {v.phrase.lower() for v in target.vocabulary}
        for v in vocabulary:
            if v.phrase.lower() not in existing_phrases:
                target.vocabulary.append(v)
                existing_phrases.add(v.phrase.lower())

        existing_pats = {g.pattern.lower() for g in target.grammar_patterns}
        for g in grammar_patterns:
            if g.pattern.lower() not in existing_pats:
                target.grammar_patterns.append(g)
                existing_pats.add(g.pattern.lower())

    PRESET_MAPPINGS: Dict[str, List[str]] = {
        "everyday-chat": ["friends", "family-and-friends-bonds", "ielts-speaking-friends", "hobbies"],
        "cafe-dining": ["food", "ielts-speaking-food", "food-health", "ielts-speaking-healthy-eating"],
        "travel-culture": ["travel", "holidays-and-travel", "travel-and-transport", "ielts-speaking-travelling", "culture"],
        "work-study-space": ["work", "jobs-and-work", "study", "education-and-study", "ielts-speaking-what-you-do-your-job"],
        "digital-lifestyle": ["technology", "science-and-technology", "mobile-phones", "arts-and-media", "movies"],
        "det-childhood-memory": ["youth-and-childhood", "ielts-speaking-childhood", "ielts-speaking-memories-of-the-past"],
        "det-best-friend": ["friends", "family-and-friends-bonds", "ielts-speaking-friends"],
        "det-career-ambition": ["jobs-and-work", "work", "ielts-speaking-what-you-do-your-job"],
        "det-school-life": ["education-and-study", "study", "studying"],
        "det-book-movie": ["arts-and-media", "movies", "reading"],
        "det-sports-health": ["health-and-fitness", "diet-and-health", "food-health"],
        "det-hometown-city": ["hometown", "home-and-places", "culture"],
        "det-dream-travel": ["travel", "holidays-and-travel", "travel-and-transport"],
        "det-social-media": ["technology", "mobile-phones", "science-and-technology"],
        "det-ai-future": ["science-and-technology", "technology", "machines-cycles-and-processes"],
    }

    def get_topic(self, topic_id: str) -> Optional[TopicBank]:
        """Lookup a topic by topic_id, preset mapping, or keyword search with robust fallback."""
        if not self.topics:
            return None

        norm = self.normalize_id(topic_id)
        # Tier 1: Exact key or normalized title match
        if norm in self.topics:
            return self.topics[norm]

        for topic in self.topics.values():
            if self.normalize_id(topic.topic_name) == norm:
                return topic

        # Tier 2: Explicit scenario mapping
        if norm in self.PRESET_MAPPINGS:
            for candidate in self.PRESET_MAPPINGS[norm]:
                cand_norm = self.normalize_id(candidate)
                if cand_norm in self.topics:
                    return self.topics[cand_norm]

        # Tier 3: Keyword & Token Substring Matching
        tokens = [t for t in re.split(r'[-_\s]+', norm) if len(t) > 2]
        for token in tokens:
            for tid, topic in self.topics.items():
                if token in tid or token in self.normalize_id(topic.topic_name):
                    return topic

        # Tier 4: Fallback to any loaded topic bank so sampling never fails
        return list(self.topics.values())[0]

    def list_topics(self) -> List[Dict[str, Any]]:
        """Return a list of summary dictionaries for all loaded topics."""
        return [
            {
                "topic_id": t.topic_id,
                "topic_name": t.topic_name,
                "target_levels": t.target_levels,
                "persona_count": len(t.personas),
                "question_count": len(t.questions),
                "vocab_count": len(t.vocabulary),
                "grammar_count": len(t.grammar_patterns),
            }
            for t in self.topics.values()
        ]


_global_material_bank: Optional[MaterialBank] = None


def get_material_bank(docs_dir: str = "docs") -> MaterialBank:
    """Singleton getter for MaterialBank instance."""
    global _global_material_bank
    if _global_material_bank is None:
        _global_material_bank = MaterialBank(docs_dir=docs_dir)
        _global_material_bank.load_all()
    return _global_material_bank
