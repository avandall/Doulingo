import json
import os
import uuid
from pathlib import Path
from typing import Any

from arc.sdk import trace_agent, trace_tool, get_current_trace_context
from arc.execution.fork_engine.fault_catalog import FaultSpec
from arc.execution.fork_engine.orchestrator import ForkOrchestrator
from arc.execution.invariant_engine.evaluator import InvariantEvaluator
from arc.execution.fork_engine.reproducer_export import export_minimal_reproducer_yaml

# ==============================================================================
# 1. ĐỊNH NGHĨA INVARIANT (BẤT BIẾN NGHIỆP VỤ DOULINGO)
# ==============================================================================
# Quy tắc: Mỗi bài học hoàn thành chỉ được cộng tối đa 20 EXP.
# Nghiêm cấm lỗi cộng 2 lần (Double Reward) khi mạng chập chờn / retry.
INV_EXP_001_SPEC: dict[str, Any] = {
    "id": "INV-EXP-001",
    "statement": "Tổng điểm EXP thưởng cho 1 bài học không được vượt quá 20 EXP",
    "category": "conservation",
    "severity": "critical",
    "check": "sum([e.delta.amount for e in effects if e.type == 'learning.exp_reward']) <= 20",
}

# ==============================================================================
# 2. ĐỊNH NGHĨA TOOLS CỦA DOULINGO AGENT
# ==============================================================================
@trace_tool(name="dictionary_lookup")
def lookup_vocab(word: str) -> dict[str, Any]:
    """Tool tra từ điển vựng."""
    return {
        "word": word,
        "definition": "A greeting or expression of goodwill.",
        "difficulty": "A1"
    }

@trace_tool(name="award_exp_reward")
def award_exp_reward(
    student_id: str,
    lesson_id: str,
    exp: int = 20,
    fault_spec: dict[str, Any] | None = None,
    effects_ledger: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Tool cộng điểm thưởng EXP cho học viên khi làm bài đúng.
    
    Có thể bị tiêm lỗi Chaos 'timeout_after_commit':
    Database đã cộng EXP xong, nhưng kết nối mạng bị đứt lúc trả về client.
    """
    # 1. Ghi nhận tác động (Side Effect) vào sổ cái Ledger
    effect_entry: dict[str, Any] = {
        "effect_id": f"eff_{uuid.uuid4().hex[:8]}",
        "step_id": 2,
        "type": "learning.exp_reward",
        "resource": f"student:{student_id}:lesson:{lesson_id}",
        "delta": {"amount": exp},
        "reversible": False,
        "observed_at_step": 2,
    }
    if effects_ledger is not None:
        effects_ledger.append(effect_entry)

    ctx = get_current_trace_context()
    if ctx is not None:
        ctx.effects.append(effect_entry)

    # 2. Xử lý tiêm lỗi Chaos Fault Injection
    if fault_spec:
        fault_type = fault_spec.get("type") or fault_spec.get("fault_type")
        if fault_type == "timeout_after_commit":
            # Hệ thống đã cộng điểm, nhưng phản hồi mạng bị Timeout 504
            return {
                "status_code": 504,
                "status": "error",
                "error": "504 Gateway Timeout (timeout_after_commit injected by ARC)",
            }

    return {
        "status": "ok",
        "student_id": student_id,
        "lesson_id": lesson_id,
        "exp_awarded": exp,
    }

# ==============================================================================
# 3. AI AGENT DOULINGO WORKFLOW
# ==============================================================================
@trace_agent(name="doulingo_tutor_agent", model_provider="gemini", model_id="gemini-1.5-flash")
def run_doulingo_lesson_agent(
    student_id: str = "student_99",
    lesson_id: str = "lesson_french_01",
    user_answer: str = "bonjour",
    inject_fault: bool = False,
) -> dict[str, Any]:
    """Workflow chính:
    1. Tra từ vựng để chấm điểm
    2. Nếu đúng, cộng điểm EXP qua tool award_exp_reward
    3. Nếu gặp lỗi timeout, agent ngây thơ retry gọi lại mà không có idempotency key!
    """
    ctx = get_current_trace_context()
    effects: list[dict[str, Any]] = []

    # Step 1: Tra cứu từ
    vocab = lookup_vocab(user_answer)

    # Step 2: Cộng điểm thưởng (kèm kịch bản lỗi nếu inject_fault=True)
    active_fault = {"type": "timeout_after_commit", "step": 2, "tool": "award_exp_reward"} if inject_fault else None

    reward_res = award_exp_reward(
        student_id=student_id,
        lesson_id=lesson_id,
        exp=20,
        fault_spec=active_fault,
        effects_ledger=effects,
    )

    # LỖ HỔNG BẢO MẬT & ĐỘ TIN CẬY CỦA AGENT:
    # Khi thấy lỗi 504 Timeout, Agent tự động retry mà KHÔNG check idempotency key
    # Dẫn đến việc học viên bị cộng điểm 2 lần (Double Reward defect)!
    if reward_res.get("status_code") == 504 or reward_res.get("status") == "error":
        # Retry lần 2 -> Database lại cộng tiếp 20 EXP nữa!
        reward_res = award_exp_reward(
            student_id=student_id,
            lesson_id=lesson_id,
            exp=20,
            fault_spec=None,  # Lần 2 thành công
            effects_ledger=effects,
        )

    ctf_trace = ctx.to_ctf_dict() if ctx is not None else {}
    if ctx is not None and effects and not ctf_trace.get("effects"):
        ctf_trace["effects"] = effects

    return {
        "status": "completed",
        "vocab": vocab,
        "reward": reward_res,
        "effects": ctf_trace.get("effects", effects),
        "ctf_trace": ctf_trace,
    }

# ==============================================================================
# 4. CÁC TEST CASES THỂ HIỆN TOÀN BỘ GIÁ TRỊ CỦA ARC
# ==============================================================================

def test_1_nominal_execution():
    """TÍNH NĂNG 1: Chạy chuẩn (Nominal) - Đảm bảo Invariant luôn PASS."""
    res = run_doulingo_lesson_agent(inject_fault=False)
    assert res["status"] == "completed"
    assert len(res["effects"]) == 1
    assert res["effects"][0]["delta"]["amount"] == 20

    # Đánh giá Invariant bằng InvariantEvaluator của ARC
    evaluator = InvariantEvaluator()
    eval_res = evaluator.evaluate(INV_EXP_001_SPEC, res["effects"], {})
    assert eval_res.violated is False, "Nominal execution không được vi phạm Invariant!"
    print("\n✅ Test 1 (Nominal): Invariant INV-EXP-001 PASS (Cộng đúng 20 EXP)")

    # Lưu trace chuẩn
    os.makedirs("data", exist_ok=True)
    with open("data/sample_doulingo_trace.json", "w", encoding="utf-8") as f:
        json.dump(res["ctf_trace"], f, indent=2, ensure_ascii=False)


def test_2_chaos_fault_injection_double_reward():
    """TÍNH NĂNG 2: Tiêm lỗi Chaos (Fault Injection) 'timeout_after_commit'.
    
    Phát hiện lỗi nghiêm trọng: Agent retry sai cách làm học viên được x2 điểm (40 EXP).
    ARC Invariant Engine bắt ngay lập tức vi phạm này!
    """
    res = run_doulingo_lesson_agent(inject_fault=True)
    assert res["status"] == "completed"
    # Agent đã gọi tool 2 lần do retry
    assert len(res["effects"]) == 2
    total_exp = sum(e["delta"]["amount"] for e in res["effects"])
    assert total_exp == 40, "Đã phát hiện Double Reward: 40 EXP thay vì 20 EXP!"

    # Invariant Evaluator bắt vi phạm
    evaluator = InvariantEvaluator()
    eval_res = evaluator.evaluate(INV_EXP_001_SPEC, res["effects"], {})
    assert eval_res.violated is True, "ARC phải phát hiện lỗi vi phạm INV-EXP-001!"
    print(f"\n⚠️ Test 2 (Chaos): Phát hiện vi phạm {eval_res.invariant_id}! Tổng EXP nhận: {total_exp} > 20")


def test_3_fork_engine_parallel_branches():
    """TÍNH NĂNG 3: Rẽ nhánh song song (Fork Engine) & Đánh giá thống kê Wilson Score.
    
    ARC ForkOrchestrator phân nhánh ra K=20 luồng độc lập, mô phỏng mạng chập chờn
    (35% số luồng bị dính timeout_after_commit = 7/20 luồng).
    """
    orchestrator = ForkOrchestrator(k=20)
    fault_spec = FaultSpec(at_step=2, fault_type="timeout_after_commit", target_tool="award_exp_reward")
    evaluator = InvariantEvaluator()

    def custom_branch_worker(branch_id: int, spec: FaultSpec) -> dict[str, Any]:
        # Giả lập mạng chập chờn: 7 trên 20 nhánh (branch 0..6) bị lỗi mạng
        inject = branch_id < 7
        agent_res = run_doulingo_lesson_agent(inject_fault=inject)

        eval_res = evaluator.evaluate(INV_EXP_001_SPEC, agent_res["effects"], {})
        violations = ["INV-EXP-001"] if eval_res.violated else []

        return {
            "branch_id": branch_id,
            "status": "success",
            "fault_applied": spec.to_dict(),
            "violations": violations,
            "cost_usd": 0.0015,
            "tokens": 85,
            "duration_ms": 25,
        }

    # Khởi chạy rẽ nhánh song song 20 branches
    fork_result = orchestrator.run_fork(fault_spec=fault_spec, branch_executor=custom_branch_worker)

    assert fork_result.status == "completed"
    assert fork_result.k == 20
    assert fork_result.n_valid == 20
    assert "INV-EXP-001" in fork_result.violations

    v_stat = fork_result.violations["INV-EXP-001"]
    assert v_stat["hits"] == 7
    reproduce_rate = v_stat["violation_rate"]  # 7 / 20 = 0.35 (35%)
    ci = v_stat["wilson_ci"]                   # 95% Wilson Score Confidence Interval

    print(f"\n🔀 Test 3 (Fork Engine): Rẽ {fork_result.k} nhánh song song thành công!")
    print(f"   - Số lần vi phạm bug (hits): {v_stat['hits']}/{fork_result.k}")
    print(f"   - Tỉ lệ tái hiện lỗi (violation_rate): {reproduce_rate * 100:.1f}%")
    print(f"   - Khoảng tin cậy 95% Wilson Score CI: [{ci[0]:.3f}, {ci[1]:.3f}]")
    print(f"   - Tổng chi phí đo kiểm: ${fork_result.total_cost_usd:.4f}")

    # TÍNH NĂNG 4: Tự động xuất file Minimal Reproducer YAML
    repro_file = export_minimal_reproducer_yaml(
        trace="trace_doulingo_double_reward_001",
        faults=[fault_spec.to_dict()],
        violated="INV-EXP-001",
        determinism_level="L1",
        reproduce_rate=reproduce_rate,
        confidence_interval=ci,
        cost_usd=fork_result.total_cost_usd,
        output_path="arc-repro-doulingo.yaml",
    )
    print(f"📁 Test 4 (Export Reproducer): Đã xuất file bug reproducer tại '{repro_file}'")
    assert Path("arc-repro-doulingo.yaml").exists()


if __name__ == "__main__":
    print("=== CHẠY TEST TỔNG HỢP ARC TRÊN DOULINGO ===")
    test_1_nominal_execution()
    test_2_chaos_fault_injection_double_reward()
    test_3_fork_engine_parallel_branches()
    print("\n🎉 Hoàn thành toàn bộ kịch bản kiểm thử ARC!")
