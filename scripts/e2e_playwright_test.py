"""
scripts/e2e_playwright_test.py
==============================
Playwright Real-User E2E Diagnostic Test Suite:
- Launches local test server.
- Emulates mobile browser (iPhone 14 / Mobile Safari).
- Tests full user journey:
  1. Opening app & selecting Lily / everyday_chat scenario.
  2. Waiting for initial opening greeting and measuring opening latency.
  3. Simulating user clicking mic to start speaking, speaking, and clicking mic to stop.
  4. Diagnosing why on mobile clicking mic to stop results in "nothing happens" (empty transcript bug).
  5. Testing latency of /api/process_turn vs /api/process_turn_fast.
  6. Testing latency of /api/tts vs /api/tts/stream.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

from playwright.async_api import async_playwright

SERVER_PORT = 8765
SERVER_URL = f"http://127.0.0.1:{SERVER_PORT}"


def wait_for_server(url: str, timeout: float = 10.0) -> bool:
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(f"{url}/api/topics", timeout=1.0) as res:
                if res.status == 200:
                    return True
        except Exception:
            time.sleep(0.3)
    return False


async def run_playwright_tests():
    print("=" * 70)
    print("STARTING PLAYWRIGHT REAL-USER DIAGNOSTIC TEST")
    print("=" * 70)

    # 1. Start Server
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--port", str(SERVER_PORT), "--host", "127.0.0.1"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=str(Path(__file__).resolve().parent.parent)
    )

    try:
        print(f"Waiting for server on {SERVER_URL}...")
        if not wait_for_server(SERVER_URL):
            print("ERROR: Server failed to start in time!")
            return False

        print("Server is UP and HEALTHY!")

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--use-fake-ui-for-media-stream",
                    "--use-fake-device-for-media-stream",
                    "--disable-web-security"
                ]
            )
            context = await browser.new_context(
                viewport={"width": 390, "height": 844},
                user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1",
                permissions=["microphone"]
            )
            page = await context.new_page()

            console_logs = []
            page.on("console", lambda msg: console_logs.append(f"[{msg.type.upper()}] {msg.text}"))
            network_requests = []
            page.on("request", lambda req: network_requests.append(f"REQ: {req.method} {req.url}"))
            network_responses = []
            page.on("response", lambda res: network_responses.append(f"RES: {res.status} {res.url}"))

            print("\n1. Navigating to Duolingo Speak app...")
            t0 = time.time()
            await page.goto(SERVER_URL, wait_until="networkidle")
            print(f"Page loaded in {(time.time() - t0)*1000:.1f}ms")

            # 2. Select Character & Scenario
            print("\n2. Starting Scenario 'everyday_chat'...")
            t_start_sc = time.time()
            await page.evaluate("""() => {
                window.app.startScenario('everyday_chat');
            }""")

            # Wait for practice screen and AI speech text
            greeting_el = page.locator("#ai-speech-text")
            await page.wait_for_selector("#practice-screen.active", timeout=5000)
            await page.wait_for_function("""() => {
                const el = document.getElementById('ai-speech-text');
                return el && el.textContent.trim().length > 0 && !el.textContent.includes('Generating');
            }""", timeout=15000)
            
            greeting_text = await greeting_el.inner_text()
            print(f"Initial AI Greeting received in {(time.time() - t_start_sc)*1000:.1f}ms: '{greeting_text[:80]}...'")

            # 3. TEST ROOT CAUSE: Mobile Mic Recording & Stop Event
            print("\n3. Testing Mic Recording & Stop Behavior...")
            mic_btn = page.locator("#btn-mic-toggle")
            
            # Click Mic to start
            await mic_btn.click()
            await page.wait_for_timeout(500)
            
            state_after_start = await page.evaluate("""() => ({
                isListening: window.app.speechHandler ? window.app.speechHandler.isListening : null,
                finalTranscript: window.app.speechHandler ? window.app.speechHandler.finalTranscript : null,
                lastRecognizedText: window.app.speechHandler ? window.app.speechHandler.lastRecognizedText : null
            })""")
            print(f"State while listening: {state_after_start}")

            # Click Mic to stop WITHOUT browser having fired Web Speech onresult (Standard Mobile condition!)
            print("Simulating User clicking Mic to STOP (when Web Speech has produced 0 text)...")
            req_count_before = len(network_requests)
            await mic_btn.click()
            await page.wait_for_timeout(1500)
            
            new_requests = network_requests[req_count_before:]
            print(f"Network requests triggered after Mic Stop: {new_requests}")

            ai_text_after_mic_stop = await greeting_el.inner_text()
            print(f"AI text after stop: '{ai_text_after_mic_stop[:80]}...'")
            print(f"DID AI RESPOND? {'NO (NOTHING HAPPENED!)' if ai_text_after_mic_stop == greeting_text else 'YES'}")

            # 4. MEASURE SERVER LATENCIES (Direct Benchmarking)
            print("\n4. Benchmarking Latencies across Endpoints...")
            bench_results = await page.evaluate("""async () => {
                const results = {};
                
                // Test A: Current /api/process_turn (Synchronous heavy CoT)
                const t0 = performance.now();
                const resA = await fetch('/api/process_turn', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        scenario_id: 'everyday_chat',
                        character_id: 'lily',
                        user_transcript: 'I went to a coffee shop and read a good book.',
                        conversation_history: [],
                        level: 1
                    })
                });
                results.process_turn_ms = Math.round(performance.now() - t0);
                const dataA = await resA.json();
                results.process_turn_response = (dataA.ai_response || dataA.final_response || '').slice(0, 60);

                // Test B: /api/process_turn_fast (Decoupled Fast Voice)
                const t1 = performance.now();
                const resB = await fetch('/api/process_turn_fast', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        scenario_id: 'everyday_chat',
                        character_id: 'lily',
                        user_transcript: 'I went to a coffee shop and read a good book.',
                        conversation_history: [],
                        level: 1
                    })
                });
                results.process_turn_fast_ms = Math.round(performance.now() - t1);
                const dataB = await resB.json();
                results.process_turn_fast_response = (dataB.ai_response || '').slice(0, 60);

                // Test C: /api/tts (Full MP3 Blob)
                const t2 = performance.now();
                const resC = await fetch('/api/tts?text=' + encodeURIComponent(dataA.ai_response || 'Hello world') + '&character_id=lily');
                const blobC = await resC.blob();
                results.tts_full_blob_ms = Math.round(performance.now() - t2);
                results.tts_blob_bytes = blobC.size;

                // Test D: /api/tts/stream (Sentence-Level Streaming TTFA)
                const t3 = performance.now();
                const resD = await fetch('/api/tts/stream?text=' + encodeURIComponent(dataA.ai_response || 'Hello world') + '&character_id=lily');
                const reader = resD.body.getReader();
                const firstChunk = await reader.read();
                results.tts_stream_first_chunk_ms = Math.round(performance.now() - t3);
                results.tts_first_chunk_bytes = firstChunk.value ? firstChunk.value.length : 0;
                reader.cancel();

                return results;
            }""")

            print("\n=== LATENCY BENCHMARK RESULTS ===")
            print(json.dumps(bench_results, indent=2))

            print("\n--- Console Logs during Real User Session ---")
            for log in console_logs[-15:]:
                print(" ", log)

            await browser.close()
            return True

    finally:
        server_process.terminate()
        server_process.wait()
        print("\nTest server stopped.")


if __name__ == "__main__":
    asyncio.run(run_playwright_tests())
