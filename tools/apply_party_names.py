#!/usr/bin/env python3
"""apply_party_names.py ROOT

Upstream re-flowed some tables (the library one among them), so whole fragments
of the translation could not be matched line by line and the party labels fell
back to the English abbreviations.  The abbreviations below are the ones used
by the translation (and confirmed by the maintainer); this step restores them
in the visible labels (**SPD** -> **СДПГ**).

Only bold labels are touched, and never inside HTML attributes.
"""
import glob
import re
import sys

PARTY = {
    'DNEF': 'ФНЕГ', 'DNF': 'НФГ', 'DSU': 'НСС', 'NVF': 'ННФ',
    'SAPD': 'СРПГ', 'VNR': 'ННОР', 'CVD': 'ХНС', 'CSVD': 'ХСНС',
    'CNBLP': 'ХНПКЗ', 'KPD': 'КПГ', 'SPD': 'СДПГ', 'DVP': 'ННП',
    'DNVP': 'НННП', 'KVP': 'КНП', 'CVP': 'ХНП', 'LVP': 'ЛНП',
    'NSDAP': 'НСДАП', 'WP': 'ЭП', 'BVP': 'БНП',
}

ATTR = re.compile(r'\b(?:title|alt|src)="[^"]*"')
CODE = re.compile(r'\*\*(' + '|'.join(sorted(PARTY, key=len, reverse=True)) + r')\*\*')


def main(root):
    changed = files = 0
    for p in sorted(glob.glob(root + '/**/*.dry', recursive=True)):
        text = open(p, encoding='utf-8').read()
        masked = ATTR.sub(lambda m: '\0' * len(m.group(0)), text)
        out, pos, hits = [], 0, 0
        for m in CODE.finditer(masked):
            out.append(text[pos:m.start()])
            out.append('**%s**' % PARTY[m.group(1)])
            pos = m.end()
            hits += 1
        if not hits:
            continue
        out.append(text[pos:])
        open(p, 'w', encoding='utf-8').write(''.join(out))
        changed += hits
        files += 1
    print('party labels restored: %d in %d files' % (changed, files))


if __name__ == '__main__':
    main(*sys.argv[1:2])
