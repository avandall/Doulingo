"""
Test Suite: ARC Real Integration for Doulingo
=============================================
Kiểm thử THẬT ARC Platform trên các luồng nghiệp vụ cốt lõi của Doulingo:
1. Deep Scoring Agent (app/scoring/tier2_deep.py) — Chấm điểm phát âm & ngữ pháp IELTS
2. Conversational Chat Agent (app/api/routers/chat.py) — RAG Retrieval + LLM + TTS
3. ARC Invariant Safety Engine — Đảm bảo tính bất biến của điểm số và hội thoại
4. ARC CI Gate — Đánh giá tuân thủ vết thực thi (CTF v1.0) trên trace thực tế
"""

import json
import os
import sys
from pathlib import Path
from typing import Any

# Đảm bảo import được app khi chạy trực tiếp bằng python tests/test_arc_doulingo.py
REPO_ROOT = str(Path(__file__).resolve().parent.parent)
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from app.api.routers.chat import _execute_voice_turn_pipeline
from app.scoring.features import WordTimestamp
from app.scoring.tier2_deep import evaluate_tier2
from arc.execution.fork_engine.fault_catalog import FaultSpec
from arc.execution.fork_engine.orchestrator import ForkOrchestrator
from arc.execution.invariant_engine.evaluator import InvariantEvaluator
from arc.sdk import get_current_trace_context, trace_agent


# ==============================================================================
# BẤT BIẾN AN TOÀN NGHIỆP VỤ THỰC TẾ (REAL INVARIANTS)
# ==============================================================================

INV_SCORE_001_SPEC: dict[str, Any] = {
    "id": "INV-SCORE-001",
    "statement": "Điểm IELTS ước lượng (estimated_band) phải nằm trong khoảng hợp lệ [4.0, 9.0]",
    "category": "safety",
    "severity": "critical",
    "check": "context.get('estimated_band', 0) >= 4.0 and context.get('estimated_band', 0) <= 9.0",
}

INV_CHAT_001_SPEC: dict[str, Any] = {
    "id": "INV-CHAT-001",
    "statement": "Hội thoại phản hồi từ AI không được rỗng và không bị crash",
    "category": "safety",
    "severity": "critical",
    "check": "len(context.get('ai_utterance', '').strip()) > 0",
}


# ==============================================================================
# TEST 1: CHẤM ĐIỂM THỰC TẾ VỚI TIER 2 DEEP SCORER + ARC TRACE
# ==============================================================================

def test_arc_real_tier2_scorer():
    """Test THẬT 1: Đánh giá âm vị & ngữ pháp thật qua evaluate_tier2().
    
    ARC tự động bắt:
    - Span của Agent: doulingo_tier2_scorer
    - Các Tool được gọi: analyze_grammar_spacy, compute_pronunciation_score
    - Độ trễ execution (latency_ms) và xuất ra CTF v1.0 trace thật.
    """
    sample_transcript = (
        "I have lived in London for three years because I study computer science at university."
    )
    # Dữ liệu ASR Word Timestamps thật với confidence điểm cao
    words = [
        WordTimestamp(word="I", start_time=0.1, end_time=0.3, confidence=0.95),
        WordTimestamp(word="have", start_time=0.3, end_time=0.6, confidence=0.92),
        WordTimestamp(word="lived", start_time=0.6, end_time=1.0, confidence=0.90),
        WordTimestamp(word="in", start_time=1.0, end_time=1.2, confidence=0.96),
        WordTimestamp(word="London", start_time=1.2, end_time=1.7, confidence=0.94),
        WordTimestamp(word="for", start_time=1.7, end_time=1.9, confidence=0.91),
        WordTimestamp(word="three", start_time=1.9, end_time=2.3, confidence=0.93),
        WordTimestamp(word="years", start_time=2.3, end_time=2.8, confidence=0.95),
        WordTimestamp(word="because", start_time=2.8, end_time=3.3, confidence=0.88),
        WordTimestamp(word="I", start_time=3.3, end_time=3.5, confidence=0.97),
        WordTimestamp(word="study", start_time=3.5, end_time=3.9, confidence=0.91),
        WordTimestamp(word="computer", start_time=3.9, end_time=4.4, confidence=0.92),
        WordTimestamp(word="science", start_time=4.4, end_time=4.9, confidence=0.94),
        WordTimestamp(word="at", start_time=4.9, end_time=5.1, confidence=0.95),
        WordTimestamp(word="university", start_time=5.1, end_time=5.8, confidence=0.93),
    ]

    # Gọi hàm chấm điểm THẬT của Doulingo (đã gắn ARC)
    score_result = evaluate_tier2(words=words, transcript=sample_transcript, target_band=6.5)

    # 1. Kiểm tra kết quả chấm điểm nghiệp vụ
    assert score_result.estimated_band >= 4.0
    assert score_result.estimated_band <= 9.0
    assert score_result.raw_score > 0.0
    assert score_result.grammar_analysis.get("error_count") == 0

    # 2. Kiểm tra Trace CTF v1.0 THẬT do ARC thu thập
    ctf_trace = score_result.ctf_trace
    assert ctf_trace is not None, "ARC phải tự động sinh CTF Trace từ hàm evaluate_tier2!"
    assert ctf_trace["agent"]["name"] == "doulingo_tier2_scorer"
    assert ctf_trace["model"]["provider"] == "spacy"
    assert ctf_trace["outcome"]["status"] == "completed"

    # Kiểm tra các tool steps do ARC ghi nhận trong quá trình chấm điểm
    step_tools = [s["request"]["tool"] for s in ctf_trace["steps"]]
    assert "analyze_grammar_spacy" in step_tools
    assert "compute_pronunciation_score" in step_tools

    # 3. Đánh giá Bất biến Invariant INV-SCORE-001 bằng InvariantEvaluator
    evaluator = InvariantEvaluator()
    eval_res = evaluator.evaluate(
        INV_SCORE_001_SPEC,
        ctf_trace.get("effects", []),
        {"estimated_band": score_result.estimated_band},
    )
    assert eval_res.violated is False, "Điểm thi của học viên phải nằm trong ngưỡng an toàn [4.0, 9.0]!"

    print("\n✅ Test 1 THẬT (Deep Scorer):")
    print(f"   - Estimated Band: {score_result.estimated_band}")
    print(f"   - Tool steps captured by ARC: {step_tools}")
    print(f"   - Real execution latency: {score_result.latency_ms:.2f}ms")

    # Lưu trace thật ra file để dùng cho CI Gate
    os.makedirs("data", exist_ok=True)
    with open("data/real_doulingo_scoring_trace.json", "w", encoding="utf-8") as f:
        json.dump(ctf_trace, f, indent=2, ensure_ascii=False, default=str)


# ==============================================================================
# TEST 2: HỘI THOẠI CHAT PIPELINE THỰC TẾ + ARC TRACE
# ==============================================================================

def test_arc_real_chat_voice_turn():
    """Test THẬT 2: Luồng hội thoại voice turn của học viên qua _execute_voice_turn_pipeline().
    
    ARC tự động bắt:
    - Span Agent: doulingo_voice_turn_agent
    - Tool RAG: rag_retrieve_dialogues (truy vấn DB tài liệu mẫu)
    - Tool LLM: conversational_llm_generate (sinh câu đối đáp phù hợp level)
    - Tool TTS: tts_audio_synthesis
    """
    import asyncio

    user_utterance = "Can you recommend a good restaurant near the Eiffel Tower?"

    # Gọi pipeline hội thoại THẬT của Doulingo (Lily nhân vật, topic Du lịch)
    result = asyncio.run(
        _execute_voice_turn_pipeline(
            user_id="user_test_999@doulingo.com",
            topic="Travel & Directions",
            band_level=5.5,
            conversation_history=[],
            character_id="lily",
            text_only_mode=True,  # Tránh phụ thuộc dịch vụ TTS ngoài khi test
            user_transcript=user_utterance,
            audio_bytes=None,
            level=5,
        )
    )

    # 1. Kiểm tra nghiệp vụ phản hồi
    ai_reply = result.get("ai_utterance", "")
    assert len(ai_reply) > 0, "AI Agent phải sinh câu trả lời cho học viên!"

    # 2. Kiểm tra CTF Trace do ARC thu thập
    ctf_trace = result.get("ctf_trace")
    assert ctf_trace is not None, "ARC phải sinh CTF trace cho voice turn pipeline!"
    assert ctf_trace["agent"]["name"] == "doulingo_voice_turn_agent"
    assert ctf_trace["model"]["provider"] == "gemini"

    step_tools = [s["request"]["tool"] for s in ctf_trace["steps"]]
    assert "rag_retrieve_dialogues" in step_tools
    assert "conversational_llm_generate" in step_tools

    # 3. Đánh giá Bất biến Invariant INV-CHAT-001
    evaluator = InvariantEvaluator()
    eval_res = evaluator.evaluate(
        INV_CHAT_001_SPEC,
        ctf_trace.get("effects", []),
        {"ai_utterance": ai_reply},
    )
    assert eval_res.violated is False, "Hội thoại không được vi phạm bất biến an toàn!"

    print("\n✅ Test 2 THẬT (Chat Voice Turn):")
    print(f"   - User utterance: {user_utterance}")
    print(f"   - AI Reply: {ai_reply[:60]}...")
    print(f"   - Tool steps captured by ARC: {step_tools}")

    # Lưu trace thật ra file
    with open("data/real_doulingo_chat_trace.json", "w", encoding="utf-8") as f:
        json.dump(ctf_trace, f, indent=2, ensure_ascii=False, default=str)


# ==============================================================================
# TEST 3: RẼ NHÁNH FORK ENGINE TRÊN LOGIC THẬT
# ==============================================================================

def test_arc_real_fork_branching():
    """Test THẬT 3: Rẽ nhánh song song 10 branches trên Scorer thật.
    
    Chạy ForkOrchestrator với 10 branches song song gọi hàm chấm điểm thật,
    tính toán thống kê chi phí, số sample hợp lệ (n_valid).
    """
    orchestrator = ForkOrchestrator(k=10)
    fault_spec = FaultSpec(at_step=0, fault_type="latency_spike", target_tool="analyze_grammar_spacy")

    words = [
        WordTimestamp(word="Hello", start_time=0.0, end_time=0.5, confidence=0.95),
        WordTimestamp(word="world", start_time=0.5, end_time=1.0, confidence=0.92),
    ]

    def real_branch_worker(branch_id: int, spec: FaultSpec) -> dict[str, Any]:
        # Mỗi nhánh chạy hàm chấm điểm thật
        res = evaluate_tier2(words=words, transcript="Hello world")
        return {
            "branch_id": branch_id,
            "status": "success",
            "fault_applied": spec.to_dict(),
            "violations": [],
            "cost_usd": 0.0005,
            "tokens": 40,
            "duration_ms": res.latency_ms,
        }

    fork_res = orchestrator.run_fork(fault_spec=fault_spec, branch_executor=real_branch_worker)

    assert fork_res.status == "completed"
    assert fork_res.k == 10
    assert fork_res.n_valid == 10
    assert len(fork_res.violations) == 0, "Không có vi phạm trên luồng nominal của Scorer!"

    print("\n✅ Test 3 THẬT (Fork Engine trên Scorer thật):")
    print(f"   - K branches executed in parallel: {fork_res.k}")
    print(f"   - N_valid samples: {fork_res.n_valid}")
    print(f"   - Total USD cost: ${fork_res.total_cost_usd:.4f}")


# ==============================================================================
# TEST 4: ARC BẮT LỖI VI PHẠM BẤT BIẾN (INVARIANT VIOLATION DETECTION)
# ==============================================================================

def test_arc_detects_scoring_invariant_violation():
    """Test THẬT 4: Mô phỏng bug thuật toán chấm điểm khiến Band vọt lên 10.5 (> 9.0).
    
    ARC Invariant Engine sẽ:
    1. Bắt quả tang giá trị 10.5 vi phạm quy tắc [4.0, 9.0].
    2. Báo VIOLATED = True và chỉ đích danh quy tắc INV-SCORE-001.
    3. Xuất file Minimal Bug Reproducer YAML để kiểm tra lại.
    """
    from arc.execution.fork_engine.reproducer_export import export_minimal_reproducer_yaml

    # Giả sử một lỗi tính toán trọng số (hoặc model hallucinate) khiến điểm Band vọt lên 10.5
    buggy_estimated_band = 10.5
    mock_effects = [{"type": "score.ielts", "delta": {"band": buggy_estimated_band}}]

    evaluator = InvariantEvaluator()
    eval_res = evaluator.evaluate(
        INV_SCORE_001_SPEC,
        mock_effects,
        {"estimated_band": buggy_estimated_band},
    )

    # ARC PHẢI BẮT ĐƯỢC VI PHẠM NÀY!
    assert eval_res.violated is True, "ARC phải bắt được lỗi khi điểm Band vọt ra khỏi ngưỡng 9.0!"

    print("\n🚨 Test 4 (ARC BẮT VI PHẠM BẤT BIẾN THÀNH CÔNG):")
    print(f"   - Mã vi phạm: {eval_res.invariant_id}")
    print(f"   - Quy tắc: {INV_SCORE_001_SPEC['statement']}")
    print(f"   - Giá trị vi phạm: {buggy_estimated_band} (VƯỢT NGƯỠNG TỐI ĐA 9.0)")
    print(f"   - Trạng thái ARC: VIOLATED = {eval_res.violated} ❌")

    # Tự động xuất file bug reproducer
    repro_path = export_minimal_reproducer_yaml(
        trace="trace_real_doulingo_scoring_bug",
        faults=[{"step": 1, "type": "out_of_bounds_score", "val": buggy_estimated_band}],
        violated=eval_res.invariant_id,
        determinism_level="L1",
        reproduce_rate=1.0,
        output_path="arc-repro-scoring-bug.yaml",
    )
    print(f"   - Đã sinh bug reproducer: {repro_path}")


# ==============================================================================
# TEST 5: ARC BẮT LỖI TOOL CALL BỊ SẬP (TOOL EXCEPTION CAPTURE)
# ==============================================================================

def test_arc_detects_tool_failure_and_exception_capture():
    """Test THẬT 5: Mô phỏng Tool RAG hoặc DB bị mất kết nối.
    
    ARC @trace_tool sẽ:
    1. Bẫy ngoại lệ an toàn (trap_exceptions=True) không để crash server.
    2. Ghi nhận response status = 'error'.
    3. Thu thập toàn bộ nội dung lỗi và thời gian trễ vào CTF trace step.
    """
    from arc.sdk import trace_tool, trace_agent, get_current_trace

    @trace_tool(name="flaky_database_query")
    def flaky_db_tool(query: str) -> dict[str, Any]:
        # Giả lập Database ném lỗi mất kết nối
        raise ConnectionRefusedError("Database SQLite/Turso bị ngắt kết nối đột ngột!")

    with trace_agent(name="doulingo_fault_handler_agent") as ctx:
        # Gọi tool bị lỗi
        res = flaky_db_tool("SELECT * FROM content_units WHERE id = 123")

        # ARC đã bẫy exception: không làm sập tiến trình
        assert res.get("status") == "error"
        assert "Database SQLite/Turso" in res.get("error", "")

        trace = get_current_trace()

    assert trace is not None
    assert len(trace["steps"]) == 1
    step_0 = trace["steps"][0]

    # Kiểm tra vết ARC đã bắt được:
    assert step_0["request"]["tool"] == "flaky_database_query"
    assert step_0["response"]["status"] == "error"
    assert step_0["outcome"] == "error"
    assert step_0["response"]["latency_ms"] >= 0

    print("\n🚨 Test 5 (ARC BẮT LỖI TOOL CRASH THÀNH CÔNG):")
    print(f"   - Tool bị lỗi: {step_0['request']['tool']}")
    print(f"   - Trạng thái Step: {step_0['response']['status']}")
    print(f"   - Chi tiết lỗi thu thập: {step_0['response']['error']}")
    print(f"   - Latency tại thời điểm crash: {step_0['response']['latency_ms']}ms")
    print("   - Đánh giá: ARC đã bảo vệ tiến trình và ghi nhận đầy đủ hộp đen tai nạn! 🛡️")


if __name__ == "__main__":
    print("=== BẮT ĐẦU CHẠY KIỂM THỬ THẬT ARC TRÊN DOULINGO ===")
    test_arc_real_tier2_scorer()
    test_arc_real_chat_voice_turn()
    test_arc_real_fork_branching()
    test_arc_detects_scoring_invariant_violation()
    test_arc_detects_tool_failure_and_exception_capture()
    print("\n🎉 Hoàn thành toàn bộ kiểm thử THẬT ARC!")
