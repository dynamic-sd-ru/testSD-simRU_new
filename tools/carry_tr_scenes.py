#!/usr/bin/env python3
"""carry_tr_scenes.py TR TARGET

The translation adds a small tutorial of its own (a menu entry plus a couple of
scenes).  Upstream does not have it, so the assembler cannot bring it over;
this step copies the scenes and menu entries from the translation verbatim.
"""
import os
import re
import sys

# file -> (scene ids, option ids) that only exist in the translation
EXTRAS = {
    'scenes/root.scene.dry': (['1928_tutorial'], ['1928_tutorial']),
    'scenes/post_event.scene.dry': (['tutorial_events_choice'], []),
}


def scene_block(lines, scene_id):
    start = None
    for i, ln in enumerate(lines):
        if ln.strip() == '@' + scene_id:
            start = i
            break
    if start is None:
        return None
    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith('@'):
            end = j
            break
    while end > start and not lines[end - 1].strip():
        end -= 1
    return lines[start:end]


def option_line(lines, opt_id):
    pat = re.compile(r'^\s*-\s+@' + re.escape(opt_id) + r'\b')
    for i, ln in enumerate(lines):
        if pat.match(ln):
            return ln, i
    return None, None


def main(tr_dir, target_dir):
    added = 0
    for rel, (scenes, options) in EXTRAS.items():
        tp = os.path.join(tr_dir, rel)
        op = os.path.join(target_dir, rel)
        if not (os.path.exists(tp) and os.path.exists(op)):
            continue
        tr_lines = open(tp, encoding='utf-8').read().split('\n')
        out_lines = open(op, encoding='utf-8').read().split('\n')
        out_text = '\n'.join(out_lines)
        for opt in options:
            if re.search(r'^\s*-\s+@' + re.escape(opt) + r'\b', out_text, re.M):
                continue
            line, idx = option_line(tr_lines, opt)
            if line is None:
                continue
            # insert before the next translated option that already exists
            anchor = None
            for nxt in tr_lines[idx + 1:]:
                m = re.match(r'^\s*-\s+@([A-Za-z0-9_.\-]+)', nxt)
                if not m:
                    continue
                for j, ln in enumerate(out_lines):
                    if re.match(r'^\s*-\s+@' + re.escape(m.group(1)) + r'\b', ln):
                        anchor = j
                        break
                if anchor is not None:
                    break
            out_lines.insert(anchor if anchor is not None else len(out_lines), line)
            added += 1
        for sid in scenes:
            if re.search(r'^@' + re.escape(sid) + r'\s*$', '\n'.join(out_lines), re.M):
                continue
            block = scene_block(tr_lines, sid)
            if not block:
                continue
            if out_lines and out_lines[-1].strip():
                out_lines.append('')
            out_lines.extend(block)
            out_lines.append('')
            added += 1
        open(op, 'w', encoding='utf-8').write('\n'.join(out_lines))
    print('translation-only scenes/options copied: %d' % added)


if __name__ == '__main__':
    main(*sys.argv[1:3])
