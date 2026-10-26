#!/usr/bin/env python3
"""fix_mojibake.py ROOT [LOG.json]

Repairs UTF-8 text that was decoded as Latin-1 somewhere in the translation
chain ("PreuÃŸen" -> "Preußen", "WÃ¤hlt" -> "Wählt").  Only the pairs that
actually occur in the game files are handled.
"""
import sys
import os
import re
import glob
import json

TABLE = [
    ('ÃŸ', 'ß'), ('Ã¤', 'ä'), ('Ã¼', 'ü'), ('Ã¶', 'ö'), ('Ã„', 'Ä'),
    ('Ã–', 'Ö'), ('Ãœ', 'Ü'), ('Ã©', 'é'), ('Ã¨', 'è'), ('Ã¡', 'á'),
    ('â€ž', '„'), ('â€œ', '“'), ('â€\x9d', '”'), ('â€™', '’'),
    ('â€“', '–'), ('â€”', '—'), ('Â»', '»'), ('Â«', '«'), ('Â ', ' '),
]
RX = re.compile('|'.join(re.escape(a) for a, _ in TABLE))
MAP = dict(TABLE)


def main(root, log_path=None):
    hits = []
    for p in sorted(glob.glob(root + '/**/*', recursive=True)):
        if os.path.isdir(p):
            continue
        text = open(p, encoding='utf-8').read()
        if not RX.search(text):
            continue
        for m in RX.finditer(text):
            hits.append({'file': os.path.relpath(p, root), 'before': m.group(0),
                         'after': MAP[m.group(0)]})
        open(p, 'w', encoding='utf-8').write(RX.sub(lambda m: MAP[m.group(0)], text))
    print('mojibake fixes: %d in %d files'
          % (len(hits), len({h['file'] for h in hits})))
    if log_path:
        json.dump(hits, open(log_path, 'w', encoding='utf-8'),
                  ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main(*sys.argv[1:])
