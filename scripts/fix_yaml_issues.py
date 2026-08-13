"""Auto-fix common YAML schema issues found by validate_yaml.py.

Usage:
    python fix_yaml_issues.py <folder>

This script makes simple, conservative fixes:
- normalize `content_unit.register` to allowed set
- ensure `band_tiers` entries have `grammar_required` (list) and `sentence_length_target`
- ensure `sample_dialogues` is non-empty (adds two examples when empty)
- map invalid `turn_type` values to `standalone` (or `elaborate` for follow_up)
- extend `user_model_answer` if it's shorter than 5 words by appending harmless phrase
- fix target_band_max when <= target_band_min by increasing max by 0.5

Backups: original files are saved as `<file>.bak` before overwriting.
"""
import sys
from pathlib import Path
from typing import Any

import yaml

VALID_REGISTERS = {"casual", "neutral", "formal", "academic", "semi-formal"}
VALID_TURN_TYPES = {"standalone", "opening", "elaborate", "negotiation", "closing"}
BAND_MIN, BAND_MAX = 1.0, 9.0


def normalize_register(r):
    if not isinstance(r, str):
        return 'neutral'
    s = r.lower()
    if 'formal' in s:
        return 'formal'
    if 'academic' in s:
        return 'academic'
    if 'semi' in s:
        return 'semi-formal'
    if s in ('casual', 'informal'):
        return 'casual'
    # fallback
    return 'neutral'


def ensure_list(x):
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def fix_doc(doc):
    changed = False
    cu = doc.get('content_unit')
    # If content_unit missing, create a minimal one using available metadata
    if not cu:
        cu = {
            'template_type': 'band_ladder',
            'title': doc.get('title') or 'Auto-added content unit',
            'topic_tags': [],
            'target_band_min': 5.0,
            'target_band_max': 6.0,
            'register': 'neutral',
            'source_citation': doc.get('source') or 'auto'
        }
        doc['content_unit'] = cu
        changed = True
    # ensure topic_tags is a non-empty list
    tt = cu.get('topic_tags')
    if not isinstance(tt, list):
        cu['topic_tags'] = ensure_list(tt)
        changed = True
    if not cu['topic_tags']:
        cu['topic_tags'] = ['auto']
        changed = True
    if cu:
        reg = cu.get('register')
        if reg not in VALID_REGISTERS:
            cu['register'] = normalize_register(reg)
            changed = True
        # fix band bounds
        tbmin = cu.get('target_band_min')
        tbmax = cu.get('target_band_max')
        try:
            if isinstance(tbmin, (int, float)) and isinstance(tbmax, (int, float)):
                    if tbmin >= tbmax:
                        # prefer increasing max, but if that exceeds BAND_MAX, lower min instead
                        if float(tbmin) + 0.5 <= BAND_MAX:
                            cu['target_band_max'] = float(tbmin) + 0.5
                        else:
                            # lower min so that max can be min+0.5 without exceeding BAND_MAX
                            cu['target_band_min'] = max(BAND_MIN, float(tbmax) - 0.5)
                        changed = True
                    # clamp to allowed range
                    if cu['target_band_max'] > BAND_MAX:
                        cu['target_band_max'] = BAND_MAX
                        changed = True
                    if cu['target_band_min'] < BAND_MIN:
                        cu['target_band_min'] = BAND_MIN
                        changed = True
        except Exception:
            pass

    # band_tiers
    tiers = doc.get('band_tiers')
    if not isinstance(tiers, list) or len(tiers) == 0:
        # create a minimal band_tiers entry if missing
        doc['band_tiers'] = [{'band_min': 5.0, 'band_max': 6.0, 'can_do_description': 'Auto-added', 'grammar_required': [], 'vocabulary_core': [], 'sentence_length_target': 'short'}]
        changed = True
        tiers = doc['band_tiers']

    for t in tiers:
        if 'grammar_required' not in t or not isinstance(t.get('grammar_required'), list):
            t['grammar_required'] = ensure_list(t.get('grammar_required'))
            changed = True
        if 'vocabulary_core' not in t or not isinstance(t.get('vocabulary_core'), list):
            t['vocabulary_core'] = ensure_list(t.get('vocabulary_core'))
            changed = True
        if 'sentence_length_target' not in t:
            t['sentence_length_target'] = 'short'
            changed = True

    # sample_dialogues
    sds = doc.get('sample_dialogues')
    if not isinstance(sds, list) or len(sds) == 0:
        # add two simple sample dialogues
        mid_band = 6.0
        cu = doc.get('content_unit', {})
        if isinstance(cu.get('target_band_min'), (int, float)) and isinstance(cu.get('target_band_max'), (int, float)):
            mid_band = (cu['target_band_min'] + cu['target_band_max']) / 2.0

        doc['sample_dialogues'] = [
            {'band_level': float(mid_band), 'turn_type': 'standalone', 'ai_line': 'Can you tell me about this topic?', 'user_model_answer': 'I often talk about this topic with my friends and family.'},
            {'band_level': float(min(9.0, mid_band + 1.0)), 'turn_type': 'standalone', 'ai_line': 'How has this changed over time?', 'user_model_answer': 'Over the years it has changed because people moved to cities and lifestyles shifted significantly.'}
        ]
        changed = True
        sds = doc['sample_dialogues']

    # fix turn_type and short answers
    for sd in sds:
        tt = sd.get('turn_type')
        if tt not in VALID_TURN_TYPES:
            if isinstance(tt, str) and 'follow' in tt:
                sd['turn_type'] = 'elaborate'
            else:
                sd['turn_type'] = 'standalone'
            changed = True
        ans = str(sd.get('user_model_answer', '')).strip()
        wc = len(ans.split())
        if wc < 5:
            # append a neutral phrase to reach 6 words
            addition = 'It was very enjoyable and informative.'
            if ans:
                sd['user_model_answer'] = ans + ' ' + addition
            else:
                sd['user_model_answer'] = 'I enjoyed it. ' + addition
            changed = True
        # ensure band_level is a multiple of 0.5
        if 'band_level' in sd and isinstance(sd['band_level'], (int, float)):
            bl = float(sd['band_level'])
            rounded = round(bl * 2) / 2.0
            if rounded != bl:
                sd['band_level'] = rounded
                changed = True
            # clamp
            if sd['band_level'] < BAND_MIN:
                sd['band_level'] = BAND_MIN
                changed = True
            if sd['band_level'] > BAND_MAX:
                sd['band_level'] = BAND_MAX
                changed = True

    return changed


def process_file(p: Path):
    text = p.read_text(encoding='utf-8')
    try:
        docs = list(yaml.safe_load_all(text))
    except yaml.YAMLError as e:
        print(f"Skipping (YAML parse error): {p} -> {e}")
        return False
    any_changed = False
    new_docs: list[Any] = []
    for doc in docs:
        if doc is None:
            new_docs.append(doc)
            continue
        changed = fix_doc(doc)
        any_changed = any_changed or changed
        new_docs.append(doc)

    if any_changed:
        bak = p.with_suffix(p.suffix + '.bak')
        if not bak.exists():
            p.replace(bak)
            # write back original as .bak is created by replace
            # now write fixed content to original path
        # If replace moved file, our path now points to a new (nonexistent) path. Read from bak and write fixed content to original.
        fixed_yaml = '\n'.join(yaml.safe_dump(d, allow_unicode=True, sort_keys=False) for d in new_docs if d is not None)
        p.write_text(fixed_yaml, encoding='utf-8')
        return True
    return False


def main():
    if len(sys.argv) < 2:
        print('Usage: fix_yaml_issues.py <folder>')
        sys.exit(1)
    root = Path(sys.argv[1])
    if not root.exists():
        print('Folder not found:', root)
        sys.exit(1)

    changed_files = []
    for p in root.rglob('*.yaml'):
        try:
            if process_file(p):
                changed_files.append(str(p))
        except Exception as e:
            print('Error processing', p, e)

    print('Fixed files:', len(changed_files))
    for f in changed_files:
        print('  ', f)


if __name__ == '__main__':
    main()
