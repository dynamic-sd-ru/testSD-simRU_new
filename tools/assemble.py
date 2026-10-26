#!/usr/bin/env python3
"""assemble.py BASE NEW TR DEST [--report out.json]

Builds a Russian tree out of three versions of the same game files:

  BASE -- upstream revision the translation was made from
  NEW  -- current upstream revision (structure/code authority)
  TR   -- translated tree of BASE (text authority)

For every text slot of NEW we look up the corresponding text of TR through
BASE: NEW -> BASE -> TR.  Slots that have no counterpart in the translation
(brand new upstream text) keep the English original and are reported.
The exact line layout of NEW is preserved - only payloads are substituted.
"""
import os
import re
import sys
import json
import glob
import difflib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dry import (parse, signature, length_bucket, translatable_text,
                 cond_key, TRANSLATABLE_KEYS)

# scenes whose achievement rows are restored by a dedicated post-processing step:
# the rows are skipped here (they are re-flowed in the translation), everything
# else in the scene is merged as usual.
ROW_SCENES = {'scenes/game_over.scene.dry': {'achievements'}}
SKIP_SCENES = {}

ACH_ROW = re.compile(
    r'\[\?\s*if\s+(?:not\s+)?(?:game_)?achievement_[A-Za-z0-9_]+\s*:')


def ach_row_lines(text):
    """Line numbers covered by achievement rows (depth counted [? ... ?])."""
    out = set()
    line = 0
    depth = 0
    in_row = False
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '\n':
            if in_row:
                out.add(line)
            line += 1
            i += 1
            continue
        if text.startswith('[?', i):
            if depth == 0 and ACH_ROW.match(text, i):
                in_row = True
            depth += 1
            i += 2
            continue
        if text.startswith('?]', i):
            depth -= 1
            if in_row and depth == 0:
                out.add(line)
                in_row = False
            i += 2
            continue
        i += 1
    if in_row:
        out.add(line)
    return out


def without_rows(scene, skip):
    if scene is None or not skip:
        return scene
    return {'id': scene['id'],
            'chunks': [c for c in scene['chunks'] if c[-1] not in skip]}

# files renamed between the translation and current upstream (BASE path)
FILE_ALIASES = {
    'scenes/events/cvp_coalition_joever.scene.dry':
        'scenes/events/vote_of_no_confidence_joever.scene.dry',
    'scenes/government_affairs/blank_4_alt.scene.dry':
        'scenes/government_affairs/blank_4.scene_alt.dry',
}

# scene ids renamed between the translation and current upstream
SCENE_ALIASES = {
    ('scenes/events/death_of_hindenburg_president.scene.dry',
     'lettow_vorbeck_victory'): 'Lettow_Forbeck_victory',
}

VALUE_CANON = {}


def load_value_maps(paths):
    """ru value -> english source value, for comparing conditions across versions."""
    for path in paths:
        if not os.path.exists(path):
            continue
        d = json.load(open(path, encoding='utf-8'))
        for table in (d.get('global', {}),):
            for en, ru in table.items():
                VALUE_CANON.setdefault(ru, en)


def canon_cond(key):
    if not key:
        return key
    out = []
    for part in key:
        if part.startswith('refs'):
            out.append(part)
            continue
        out.append(re.sub(r'"([^"]*)"',
                          lambda m: '"%s"' % VALUE_CANON.get(m.group(1), m.group(1)),
                          part))
    return tuple(out)


# ---------------------------------------------------------------- alignment --
def anchor_token(ch):
    """Token used to align a non-prose chunk between two versions."""
    if ch[0] == 'option':
        return 'O:' + ch[1]
    if ch[0] == 'directive':
        return 'D:' + ch[1]
    if ch[0] == 'heading':
        return 'H'
    # code: keep the directive keyword only, values are translated/edited
    body = ch[1]
    m = re.match(r'^([a-z][a-z0-9-]*):', body)
    if m:
        return 'C:' + m.group(1)
    return 'C:' + body[:30]


def text_score(a, b):
    """Similarity of two English chunks (new vs base)."""
    if a == b:
        return 3.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def lang_score(a, b):
    """Similarity of an English chunk and its Russian translation (shape only)."""
    sa, sb = signature(a), signature(b)
    score = 0.0
    if sa == sb:
        score += 1.5
    else:
        score += difflib.SequenceMatcher(None, sa, sb, autojunk=False).ratio()
    la, lb = len(a), len(b)
    if la and lb:
        r = min(la, lb) / max(la, lb)
        score += r
    pa = [a.count(c) for c in ',.!?:']
    pb = [b.count(c) for c in ',.!?:']
    denom = max(sum(pa), sum(pb), 1)
    score += 1.0 - sum(abs(x - y) for x, y in zip(pa, pb)) / denom
    return score


def dp_align(n, m, score, gap=-0.35):
    """Needleman-Wunsch -> dict i->j (0-based)."""
    NEG = -1e9
    dp = [[NEG] * (m + 1) for _ in range(n + 1)]
    bt = [[0] * (m + 1) for _ in range(n + 1)]
    dp[0][0] = 0.0
    for i in range(1, n + 1):
        dp[i][0] = dp[i - 1][0] + gap
        bt[i][0] = 1
    for j in range(1, m + 1):
        dp[0][j] = dp[0][j - 1] + gap
        bt[0][j] = 2
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            s = score(i - 1, j - 1)
            cand = [(dp[i - 1][j - 1] + s, 0), (dp[i - 1][j] + gap, 1), (dp[i][j - 1] + gap, 2)]
            best = max(cand, key=lambda x: x[0])
            dp[i][j] = best[0]
            bt[i][j] = best[1]
    out = {}
    i, j = n, m
    while i > 0 or j > 0:
        d = bt[i][j]
        if d == 0:
            out[i - 1] = j - 1
            i, j = i - 1, j - 1
        elif d == 1:
            i -= 1
        else:
            j -= 1
    return out


def pair_prose_big(list_a, list_b):
    """Cheap alignment for very long lists: block matching on shape tokens."""
    def tok(t):
        return 'SIG%s|%d' % (signature(t), length_bucket(len(t)))
    ta = [tok(t) for t in list_a]
    tb = [tok(t) for t in list_b]
    sm = difflib.SequenceMatcher(None, ta, tb, autojunk=False)
    out = {}
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            out[i + k] = j + k
    return out


def pair_prose(list_a, list_b, scorer, threshold, keyer=None):
    if not list_a or not list_b:
        return {}
    if keyer is not None:
        ka = [keyer(x) for x in list_a]
        kb = [keyer(x) for x in list_b]
        cnt_a, cnt_b = {}, {}
        for k in ka:
            cnt_a[k] = cnt_a.get(k, 0) + 1
        for k in kb:
            cnt_b[k] = cnt_b.get(k, 0) + 1
        fixed = {}
        used_b = set()
        for i, k in enumerate(ka):
            if not k or cnt_a.get(k) != 1 or cnt_b.get(k) != 1:
                continue
            j = kb.index(k)
            fixed[i] = j
            used_b.add(j)
        if fixed:
            rest_a = [x for i, x in enumerate(list_a) if i not in fixed]
            rest_b = [x for j, x in enumerate(list_b) if j not in used_b]
            idx_a = [i for i in range(len(list_a)) if i not in fixed]
            idx_b = [j for j in range(len(list_b)) if j not in used_b]
            sub = pair_prose(rest_a, rest_b, scorer, threshold)
            for i, j in sub.items():
                fixed[idx_a[i]] = idx_b[j]
            return fixed
    if len(list_a) * len(list_b) > 40000:
        return pair_prose_big(list_a, list_b)
    if len(list_a) == len(list_b) and all(
            scorer(a, b) >= threshold for a, b in zip(list_a, list_b)):
        return {i: i for i in range(len(list_a))}
    def sc(i, j):
        v = scorer(list_a[i], list_b[j])
        return v if v >= threshold else -0.5
    return dp_align(len(list_a), len(list_b), sc)


def segments(scene):
    """[(anchor_chunk|None, [prose chunks])] - anchor starts a segment."""
    segs = []
    cur = [None, []]
    for ch in scene['chunks']:
        if ch[0] == 'prose':
            cur[1].append(ch)
        else:
            if cur[1] or cur[0] is not None:
                segs.append(cur)
            cur = [ch, []]
    if cur[1] or cur[0] is not None:
        segs.append(cur)
    return segs


def align_scenes(scene_a, scene_b, scorer, threshold, keyer=None):
    """Map chunk indices of scene_a -> chunk indices of scene_b."""
    sa = segments(scene_a)
    sb = segments(scene_b)
    tokens_a = [anchor_token(s[0]) if s[0] else 'START' for s in sa]
    tokens_b = [anchor_token(s[0]) if s[0] else 'START' for s in sb]
    sm = difflib.SequenceMatcher(None, tokens_a, tokens_b, autojunk=False)
    mapping = {}
    for i, j, n in sm.get_matching_blocks():
        for k in range(n):
            ga, gb = sa[i + k], sb[j + k]
            if ga[0] is not None and gb[0] is not None:
                mapping[ga[0][-1]] = gb[0][-1]
            pm = pair_prose([c[1] for c in ga[1]], [c[1] for c in gb[1]],
                            scorer, threshold, keyer)
            for x, y in pm.items():
                mapping[ga[1][x][-1]] = gb[1][y][-1]
    return mapping


def second_chance(new_scene, tr_scene, mapped, threshold=1.75):
    """Match leftover new chunks against unused translated chunks of the scene."""
    used = set(mapped.values())
    pool = [ch for ch in tr_scene['chunks']
            if ch[-1] not in used and ch[0] in ('prose', 'heading')]
    extra = {}
    for ch in new_scene['chunks']:
        if ch[0] not in ('prose', 'heading') or ch[-1] in mapped:
            continue
        best, best_score = None, threshold
        for cand in pool:
            if cand[0] != ch[0]:
                continue
            sc = lang_score(ch[1], cand[1])
            if sc > best_score:
                best, best_score = cand, sc
        if best is not None:
            extra[ch[-1]] = best[-1]
            pool.remove(best)
    return extra


def index_by_line(scene):
    return {ch[-1]: ch for ch in scene['chunks']}


# -------------------------------------------------------------------- merge --
def merge_file(base_path, new_path, tr_path, out_path, report):
    new_text = open(new_path, encoding='utf-8').read()
    new_scenes = parse(new_text)
    base_scenes = parse(open(base_path, encoding='utf-8').read()) if base_path else []
    tr_scenes = parse(open(tr_path, encoding='utf-8').read()) if tr_path else []
    new_lines = new_text.split('\n')

    def put(line_no, payload):
        """Replace the payload, preserving the original indentation."""
        old = new_lines[line_no]
        indent = old[:len(old) - len(old.lstrip())]
        new_lines[line_no] = indent + payload

    base_map, tr_map = {}, {}
    for sc in base_scenes:
        base_map.setdefault(sc['id'], sc)
    for sc in tr_scenes:
        tr_map.setdefault(sc['id'], sc)

    anon = lambda ss: [s for s in ss if not s['id']]
    anon_new, anon_base, anon_tr = anon(new_scenes), anon(base_scenes), anon(tr_scenes)
    pos_of = {}
    for i, sc in enumerate(new_scenes):
        pos_of[id(sc)] = i

    for idx, sc in enumerate(new_scenes):
        if sc['id']:
            base_sc = base_map.get(sc['id'])
            tr_sc = tr_map.get(sc['id'])
            if tr_sc is None:
                alias = SCENE_ALIASES.get((report['file'], sc['id']))
                if alias:
                    tr_sc = tr_map.get(alias)
                    if tr_sc is not None:
                        report['scene_matched_by_options'].append(
                            [report['file'], sc['id'], alias])
            if tr_sc is None and base_sc is not None:
                # renamed scene: match by option ids
                new_opts = {c[1] for c in sc['chunks'] if c[0] == 'option'}
                best, score = None, 0
                for cand in tr_scenes:
                    o = {c[1] for c in cand['chunks'] if c[0] == 'option'}
                    s = len(new_opts & o)
                    if s > score:
                        best, score = cand, s
                if score >= 2:
                    tr_sc = best
                    report['scene_matched_by_options'].append(
                        [report['file'], sc['id'], best['id']])
        else:
            i = anon_new.index(sc)
            base_sc = anon_base[i] if i < len(anon_base) else None
            tr_sc = anon_tr[i] if i < len(anon_tr) else None

        if sc['id'] in ROW_SCENES.get(report['file'], ()):
            skip = ach_row_lines(new_text)
            sc = without_rows(sc, skip)
            base_sc = without_rows(base_sc, ach_row_lines(
                open(base_path, encoding='utf-8').read())) if base_sc else None
            tr_sc = without_rows(tr_sc, ach_row_lines(
                open(tr_path, encoding='utf-8').read())) if tr_sc else None
        if sc['id'] in SKIP_SCENES.get(report['file'], ()):
            continue
        if not tr_sc:
            for ch in sc['chunks']:
                if ch[0] in ('prose', 'heading') and translatable_text(ch[1]):
                    report['new_scene_text'].append([report['file'], ch[-1], ch[1]])
                elif ch[0] in ('directive', 'option') and translatable_text(ch[2]):
                    report['new_scene_text'].append([report['file'], ch[-1], ch[2]])
            continue

        base_to_tr = align_scenes(
            base_sc, tr_sc, lang_score, 0.9,
            keyer=lambda t: canon_cond(cond_key(t))) if base_sc else {}
        base_by_line = index_by_line(base_sc) if base_sc else {}
        new_to_base = align_scenes(sc, base_sc, text_score, 0.45,
                                   keyer=cond_key) if base_sc else {}
        tr_by_line = index_by_line(tr_sc)
        # headings are matched by order when base alignment fails (re-flowed tables)
        tr_headings = [c for _, c in sorted(tr_by_line.items()) if c[0] == 'heading']
        new_headings = [c for c in sc['chunks'] if c[0] == 'heading']
        heading_by_order = {}
        if tr_headings and len(tr_headings) == len(new_headings):
            heading_by_order = {nc[-1]: tc[-1]
                                for nc, tc in zip(new_headings, tr_headings)}
        # second chance: structural match of leftovers straight new -> tr
        base_to_tr_chunks = {}
        for bl, bl_ch in (base_by_line.items() if base_by_line else []):
            if bl in base_to_tr:
                base_to_tr_chunks[bl] = base_to_tr[bl]
        direct = {}
        for ch in sc['chunks']:
            if ch[0] not in ('prose', 'heading'):
                continue
            bi = new_to_base.get(ch[-1])
            if bi is not None and bi in base_to_tr:
                direct[ch[-1]] = base_to_tr[bi]
        direct.update(second_chance(sc, tr_sc, direct))

        dir_counter = {}
        used_tr_text = []          # translated prose already placed in this scene
        translated_lines = set()   # new-file prose lines that got a translation
        for ch in sc['chunks']:
            line = ch[-1]
            if ch[0] == 'code':
                continue
            bi = new_to_base.get(line)
            b_ch = base_by_line.get(bi) if bi is not None else None
            t_ch = None
            if line in direct:
                t_ch = tr_by_line.get(direct[line])
            elif b_ch is not None and bi in base_to_tr:
                t_ch = tr_by_line.get(base_to_tr[bi])

            if ch[0] == 'directive':
                key = ch[1]
                k = dir_counter.get(key, 0)
                dir_counter[key] = k + 1
                # directives are matched by key: take the k-th translation
                cand = [t for bl, t in sorted(tr_by_line.items())
                        if t[0] == 'directive' and t[1] == key]
                if t_ch is not None and t_ch[0] == 'directive' and t_ch[1] == key:
                    val = t_ch[2]
                elif k < len(cand):
                    val = cand[k][2]
                else:
                    val = None
                if val is None:
                    if translatable_text(ch[2]):
                        report['untranslated'].append([report['file'], line, key, ch[2]])
                else:
                    put(line, '%s: %s' % (key, val))
                    if b_ch is not None and b_ch[0] == 'directive' and b_ch[2] != ch[2]:
                        report['stale'].append([report['file'], line, 'directive ' + key])
            elif ch[0] == 'option':
                if t_ch is not None and t_ch[0] == 'option':
                    text = t_ch[2]
                    put(line, ('- @%s: %s' % (ch[1], text)).rstrip()
                        if text else '- @%s' % ch[1])
                elif translatable_text(ch[2]):
                    report['untranslated'].append([report['file'], line, 'option @' + ch[1], ch[2]])
            elif ch[0] == 'heading':
                if t_ch is None and line in heading_by_order:
                    t_ch = tr_by_line.get(heading_by_order[line])
                if t_ch is not None and t_ch[0] == 'heading':
                    put(line, '= ' + t_ch[1])
                elif translatable_text(ch[1]):
                    report['untranslated'].append([report['file'], line, 'heading', ch[1]])
            else:  # prose
                if t_ch is not None and t_ch[0] == 'prose':
                    put(line, t_ch[1])
                    used_tr_text.append(re.sub(r'\s+', '', t_ch[1]))
                    translated_lines.add(line)
                    if b_ch is not None and b_ch[0] == 'prose' and b_ch[1] != ch[1]:
                        r = text_score(b_ch[1], ch[1])
                        if r < 0.5:
                            report['stale'].append([report['file'], line, 'prose %.2f' % r])
                elif translatable_text(ch[1]):
                    # upstream split a sentence the translation keeps on one line:
                    # the words are already there, drop the leftover fragment
                    flat = re.sub(r'\s+', '', ch[1])
                    if len(flat) > 12 and any(flat in t for t in used_tr_text):
                        put(line, '')
                        continue
                    # the sentence continues on the previous line, which the
                    # translation already covers as a whole
                    if (line - 1) in translated_lines:
                        put(line, '')
                        report['merged_lines'].append(
                            [report['file'], line, 'prose', ch[1]])
                        continue
                    report['untranslated'].append([report['file'], line, 'prose', ch[1]])

    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    open(out_path, 'w', encoding='utf-8').write('\n'.join(new_lines))


def main():
    base_dir, new_dir, tr_dir, dest = sys.argv[1:5]
    report_path = None
    only = None
    for i, a in enumerate(sys.argv):
        if a == '--report':
            report_path = sys.argv[i + 1]
        if a == '--only':
            only = sys.argv[i + 1]
    load_value_maps(['work/value_map.json', 'work/extra_map.json'])
    report = {'untranslated': [], 'stale': [], 'merged_lines': [],
              'scene_matched_by_options': [],
              'new_scene_text': [], 'files_new': [], 'file': ''}
    n = 0
    for p in sorted(glob.glob(new_dir + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        rel = os.path.relpath(p, new_dir)
        if only and only not in rel:
            continue
        base_p = os.path.join(base_dir, rel)
        if not os.path.exists(base_p) and rel in FILE_ALIASES:
            base_p = os.path.join(base_dir, FILE_ALIASES[rel])
        tr_p = os.path.join(tr_dir, rel)
        out_p = os.path.join(dest, rel)
        report['file'] = rel
        if not os.path.exists(tr_p):
            report['files_new'].append(rel)
            os.makedirs(os.path.dirname(out_p), exist_ok=True)
            open(out_p, 'w', encoding='utf-8').write(open(p, encoding='utf-8').read())
            continue
        merge_file(base_p if os.path.exists(base_p) else None, p, tr_p, out_p, report)
        n += 1
    print('merged %d files' % n)
    if report_path:
        json.dump(report, open(report_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)
        print('untranslated: %d  stale: %d  new-scene text: %d'
              % (len(report['untranslated']), len(report['stale']),
                 len(report['new_scene_text'])))
        print('new files: %s' % report['files_new'])


if __name__ == '__main__':
    main()
