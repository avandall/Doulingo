from pathlib import Path
import yaml

p = Path("output/extracted")
if not p.exists():
    print("output/extracted not found")
    raise SystemExit(1)

files = sorted(list(p.glob("*.yaml")) + list(p.glob("*.yml")))
removed = []
for f in files:
    try:
        text = f.read_text(encoding="utf-8")
    except Exception as e:
        print(f"skip read error {f}: {e}")
        continue
    try:
        docs = [d for d in yaml.safe_load_all(text) if d is not None]
    except Exception:
        # if not parseable, keep the file
        continue
    if not docs:
        continue
    # if every non-None doc is the string "SKIP", remove
    if all(isinstance(d, str) and d.strip() == "SKIP" for d in docs):
        try:
            f.unlink()
            removed.append(str(f))
        except Exception as e:
            print(f"failed to remove {f}: {e}")

print(len(removed))
for r in removed:
    print(r)
