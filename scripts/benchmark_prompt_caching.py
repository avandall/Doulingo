#!/usr/bin/env python3
"""
benchmark_prompt_caching.py — Manual Offline Benchmark for Prompt Caching & TTFT.

Executes 2 multi-turn requests against Groq/Gemini to measure:
1. Turn 1 (Cold Start Prefill): Measures baseline latency.
2. Turn 2 (Cached Request): Measures TTFT reduction from KV-cache hit.
"""

import sys
import time

from dotenv import load_dotenv

load_dotenv()

from app.core.ai_engine import AIEngine


def run_benchmark(scenario_id: str = "hotel_stay", level: int = 5) -> None:
    engine = AIEngine()
    engine.reload_keys()

    print("=" * 60)
    print("PROMPT CACHING & TTFT BENCHMARK")
    print("=" * 60)

    # 1. Warm up / Start Greeting
    t0 = time.perf_counter()
    greeting = engine.start_roleplay_greeting(scenario_id=scenario_id, character_id="lily", level=level)
    t_greeting = (time.perf_counter() - t0) * 1000.0
    print(f"[Greeting] Latency: {t_greeting:.1f}ms | Angle: {engine._session_angles.get(scenario_id)}")
    print(f"[Greeting AI]: {greeting.get('final_response', '')}")

    # 2. Turn 1 (Cold Prefill)
    t1_start = time.perf_counter()
    resp1 = engine.process_turn(
        scenario_id=scenario_id,
        character_id="lily",
        user_transcript="Hi, I would like to check in please.",
        conversation_history=[],
        level=level,
    )
    t_turn1 = (time.perf_counter() - t1_start) * 1000.0
    print(f"[Turn 1 - Cold Prefill] Latency: {t_turn1:.1f}ms")

    # 3. Turn 2 (Cached Prefill)
    history = [
        {"role": "user", "content": "Hi, I would like to check in please."},
        {"role": "assistant", "content": resp1.get("final_response", "")},
    ]
    t2_start = time.perf_counter()
    resp2 = engine.process_turn(
        scenario_id=scenario_id,
        character_id="lily",
        user_transcript="Yes, I have a reservation under John Smith.",
        conversation_history=history,
        level=level,
    )
    t_turn2 = (time.perf_counter() - t2_start) * 1000.0
    print(f"[Turn 2 - Potential Cache Hit] Latency: {t_turn2:.1f}ms")
    print(f"[Turn 2 AI]: {resp2.get('final_response', '')}")

    if t_turn1 > 0:
        speedup = ((t_turn1 - t_turn2) / t_turn1) * 100.0
        print(f"[Speedup] Turn 2 delta: {speedup:+.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    sid = sys.argv[1] if len(sys.argv) > 1 else "hotel_stay"
    run_benchmark(sid)
