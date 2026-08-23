# TIER 1 VERIFICATION REPORT
Generated: 2026-08-22 13:09
Active Preset: python_backend
Status: FAIL

## Summary
- **Python: Ruff (Lint)**: ❌ FAIL
- **Python: Mypy (Type Check)**: ✅ PASS
- **Python: Bandit (Security)**: ✅ PASS
- **Python: Pytest (Runtime)**: ❌ FAIL

## Details & Error Truncated Logs

### ❌ Python: Ruff (Lint) Failures:
```text
   |

F401 [*] `pytest` imported but unused
  --> tests/test_e2e_conversational_system.py:14:8
   |
12 | from typing import Any
13 | from unittest.mock import patch
14 | import pytest
   |        ^^^^^^
15 | from fastapi.testclient import TestClient
   |
help: Remove unused import: `pytest`
   |
13 | from unittest.mock import patch
   - import pytest
14 | from fastapi.testclient import TestClient
   |

Found 3 errors.
[*] 3 fixable with the `--fix` option.
```

### ❌ Python: Pytest (Runtime) Failures:
```text
........................................................................ [ 30%]
.........................F.............................................. [ 61%]
........................................................................ [ 92%]
.................                                                        [100%]
=================================== FAILURES ===================================
________________ test_confused_fallback_for_unclear_transcript _________________
tests/test_fallback_engine.py:121: in test_confused_fallback_for_unclear_transcript
    assert any(kw in ai_resp_lower for kw in ["confusing", "uncertain", "doubt", "puzzling", "clarity", "wonder"])
E   assert False
E    +  where False = any(<generator object test_confused_fallback_for_unclear_transcript.<locals>.<genexpr> at 0x760c504b5560>)
=============================== warnings summary ===============================
../../.local/lib/python3.12/site-packages/fastapi/testclient.py:1
  /home/avandall/.local/lib/python3.12/site-packages/fastapi/testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
=========================== short test summary info ============================
FAILED tests/test_fallback_engine.py::test_confused_fallback_for_unclear_transcript
1 failed, 232 passed, 1 warning in 178.43s (0:02:58)
```
