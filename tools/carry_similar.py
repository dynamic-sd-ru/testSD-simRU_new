#!/usr/bin/env python3
"""carry_similar.py NEW_DIR TR_DIR OUT_DIR DONORS_JSON [--report JSON]

Some upstream files are near copies of files that are already translated
(the "SAPD collapse" scene is the "Weimar collapse" scene with another party,
the new no-confidence scene is the old one, ...).  For every line of such a file
that is still English in the build, this step looks the same line up in one or
more donor files - translated originals - and takes the donor's Russian text.

Nothing is retranslated here: only finished translation is moved over.
"""
import sys, os, json, re, tempfile
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dry
import assemble as asm

CYR = re.compile(r'[\u0400-\u04FF]')


def payload(c):
    if c[0] in ('prose', 'heading'):
        return c[1]
    return c[2] if len(c) > 2 else ''


def main(new_dir, tr_dir, out_dir, donors_path, report_path=None):
    donors = json.load(open(donors_path, encoding='utf-8'))
    filled = []
    for target, sources in donors.items():
        out_path = os.path.join(out_dir, target)
        new_path = os.path.join(new_dir, target)
        if not (os.path.exists(out_path) and os.path.exists(new_path)):
            continue
        text = open(out_path, encoding='utf-8').read()
        lines = text.split('\n')
        need = {}
        for sc in dry.parse(text):
            for c in sc['chunks']:
                if c[0] not in ('prose', 'heading', 'option', 'directive'):
                    continue
                t = payload(c)
                if not t or CYR.search(t) or not re.search(r'[A-Za-z]{3}', t):
                    continue
                if not dry.translatable_text(t) and c[0] != 'directive':
                    continue
                need[c[-1]] = c[0]
        if not need:
            continue
        for src in sources:
            base = os.path.join(new_dir, src)
            tr = os.path.join(tr_dir, src)
            if not (os.path.exists(base) and os.path.exists(tr)):
                continue
            rep = {'untranslated': [], 'stale': [], 'merged_lines': [],
                   'reflowed': [], 'reflow_skipped': [],
                   'scene_matched_by_options': [], 'new_scene_text': [],
                   'files_new': [], 'file': target}
            tmp = tempfile.mktemp(suffix='.dry')
            asm.merge_file(base, new_path, tr, tmp, rep)
            cand = open(tmp, encoding='utf-8').read().split('\n')
            os.unlink(tmp)
            got = {}
            for sc in dry.parse('\n'.join(cand)):
                for c in sc['chunks']:
                    if c[0] in ('prose', 'heading', 'option', 'directive') \
                            and CYR.search(payload(c)):
                        got[c[-1]] = payload(c)
            for ln, kind in need.items():
                if ln in got and ln not in [f[1] for f in filled if f[0] == target]:
                    old = payload([c for s in dry.parse(text) for c in s['chunks']
                                   if c[-1] == ln][0])
                    if kind in ('prose', 'heading'):
                        lines[ln] = got[ln]
                    elif kind == 'option':
                        oid = [c for s in dry.parse(text) for c in s['chunks']
                               if c[-1] == ln][0][1]
                        lines[ln] = '- @%s: %s' % (oid, got[ln])
                    elif kind == 'directive':
                        key = [c for s in dry.parse(text) for c in s['chunks']
                               if c[-1] == ln][0][1]
                        lines[ln] = '%s: %s' % (key, got[ln])
                    filled.append([target, ln, src, old[:60]])
        open(out_path, 'w', encoding='utf-8').write('\n'.join(lines))
    print('carried from similar translated files: %d lines' % len(filled))
    if report_path:
        json.dump(filled, open(report_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)


if __name__ == '__main__':
    argv = sys.argv[1:]
    rp = None
    if '--report' in argv:
        i = argv.index('--report')
        rp = argv[i + 1]
        del argv[i:i + 2]
    main(argv[0], argv[1], argv[2], argv[3], rp)
