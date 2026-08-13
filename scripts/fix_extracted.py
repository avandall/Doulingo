#!/usr/bin/env python3
"""
Post-process existing extracted YAML files to pull `response_text` from the
previous `response` field that contains a JSON stringified Interaction object.

Usage:
  python scripts/fix_extracted.py --dir output_claude/extracted

This will update each .yaml in-place adding `response_text` and `raw` keys.
"""

import argparse
import json
from pathlib import Path

import yaml


def extract_from_raw(raw_obj):
    # raw_obj may be a dict-like parsed from the JSON string in the original 'response'
    if isinstance(raw_obj, dict):
        if raw_obj.get("output_text"):
            return raw_obj.get("output_text")
        if isinstance(raw_obj.get("steps"), list):
            parts = []
            for step in raw_obj.get("steps", []):
                if step.get("type") == "model_output":
                    for content in step.get("content", []):
                        if content.get("type") == "text" and content.get("text"):
                            parts.append(content.get("text"))
            if parts:
                return "\n\n".join(parts)
        # maybe nested under 'response' or similar
        for k in ("response", "output", "text"):
            v = raw_obj.get(k)
            if isinstance(v, str) and v.strip():
                return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default="output_claude/extracted")
    args = ap.parse_args()

    p = Path(args.dir)
    for fn in p.glob("*.yaml"):
        try:
            data = yaml.safe_load(open(fn, encoding="utf-8")) or {}
        except Exception:
            print(f"Skipping unreadable: {fn}")
            continue

        # if response_text already present skip
        if data.get("response_text"):
            continue

        resp_field = data.get("response")
        parsed = None
        if isinstance(resp_field, str):
            # try to parse JSON string
            try:
                parsed = json.loads(resp_field)
            except Exception:
                parsed = None
        elif isinstance(resp_field, dict):
            parsed = resp_field

        response_text = None
        if parsed is not None:
            response_text = extract_from_raw(parsed)

        if response_text is None and isinstance(parsed, dict):
            # fallback: try to pull output_text key
            response_text = parsed.get("output_text")

        # write updated YAML
        new = {
            **data,
        }
        if response_text:
            new["response_text"] = response_text
        if parsed is not None:
            new["raw"] = parsed

        yaml.safe_dump(new, open(fn, "w", encoding="utf-8"), allow_unicode=True)
        print(f"Updated: {fn}")


if __name__ == "__main__":
    main()
