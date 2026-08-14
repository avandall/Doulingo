# TIER 1 VERIFICATION REPORT
Generated: 2026-08-14 14:36
Status: FAIL

## Summary
- **Ruff (Lint)**: ❌ FAIL
- **Mypy (Type Check)**: ✅ PASS
- **Bandit (Security)**: ✅ PASS
- **Pytest (Runtime)**: ✅ PASS

## Details & Error Truncated Logs

### ❌ Ruff (Lint) Failures:
```text
F821 Undefined name `embed_openai`
   --> scripts/generate_embeddings.py:314:20
    |
312 |     if args.backend == "openai":
313 |         def embed_fn(t: list[str]) -> list[list[float]]:
314 |             return embed_openai(t, model=model_name)
    |                    ^^^^^^^^^^^^
315 |     elif args.backend == "gemini":
316 |         gemini_pool = GeminiKeyPool()
    |

Found 1 error.
```
