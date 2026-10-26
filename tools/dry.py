"""Parser/diff helpers for .scene.dry files (dendrynexus).

A file is split into scenes (lines starting with '@'), each scene into chunks.
A chunk is one of:
  ('directive', key, value)     -- 'title: foo'
  ('option', id, text)          -- '- @opt_id: text'
  ('heading', text)             -- '= Heading'
  ('prose', text)               -- free text paragraph
  ('code', text)                -- raw line kept verbatim (view-if:, on-arrival:, ...)
"""
import re

TRANSLATABLE_KEYS = {'title', 'subtitle', 'unavailable-subtitle'}

DIRECTIVE_RE = re.compile(r'^([a-z][a-z0-9-]*):[ \t]?(.*)$')
OPTION_RE = re.compile(r'^-[ \t]+@([A-Za-z0-9_.\-]+)(:[ \t]?.*)?$')


def parse(text):
    """Return list of scenes: {'id': str|None, 'chunks': [...]}"""
    scenes = []
    cur = {'id': None, 'chunks': []}
    in_code = False   # inside a multi-line {! ... !} block
    for ln_no, raw in enumerate(text.split('\n')):
        line = raw.rstrip()
        s = line.strip()
        if in_code:
            cur['chunks'].append(('code', s, ln_no))
            if '!}' in s:
                in_code = False
            continue
        if s.startswith('@'):
            # scene header (not an option, options start with '- @')
            if cur['id'] is not None or cur['chunks']:
                scenes.append(cur)
            cur = {'id': s[1:], 'chunks': []}
            continue
        if not s:
            continue
        m = OPTION_RE.match(s)
        if m:
            body = (m.group(2) or '')
            body = body[1:] if body.startswith(':') else body
            cur['chunks'].append(('option', m.group(1), body.strip(), ln_no))
            continue
        if s.startswith('='):
            cur['chunks'].append(('heading', s[1:].strip(), ln_no))
            continue
        m = DIRECTIVE_RE.match(s)
        if m and len(m.group(1)) < 40:
            key = m.group(1)
            if key in TRANSLATABLE_KEYS:
                cur['chunks'].append(('directive', key, m.group(2).strip(), ln_no))
            else:
                cur['chunks'].append(('code', s, ln_no))
                if '{!' in s and '!}' not in s[s.index('{!'):]:
                    in_code = True
            continue
        cur['chunks'].append(('prose', s, ln_no))
    if cur['id'] is not None or cur['chunks']:
        scenes.append(cur)
    return scenes


def scene_map(scenes):
    out = {}
    for sc in scenes:
        if sc['id']:
            out[sc['id']] = sc
    return out


def signature(text):
    """Marker-only signature of a prose chunk; used to align base vs translation."""
    marks = []
    for m in re.finditer(r'\[\?\s*if\s+([^\]:]*):|\[\+\s*([^+\]]*?)\s*\+\]|</?span[^>]*>|</?b>|\*\*|\?\]', text):
        if m.group(1) is not None:
            marks.append('IF')
        elif m.group(2) is not None:
            marks.append('VAR')
        else:
            marks.append('M')
    return ''.join(marks)


def length_bucket(n):
    if n == 0:
        return 0
    if n < 40:
        return 1
    if n < 90:
        return 2
    if n < 200:
        return 3
    if n < 450:
        return 4
    return 5


def prose_of(scenes):
    """All prose chunks of a scene list, in order (with scene index)."""
    out = []
    for i, sc in enumerate(scenes):
        for ch in sc['chunks']:
            if ch[0] == 'prose':
                out.append((i, ch[1]))
    return out


_WORD = re.compile(r'[A-Za-zА-Яа-яЁё]{2,}')


def translatable_text(text):
    """True if the chunk contains visible words worth translating."""
    s = text
    s = re.sub(r'\{!.*?!\}', ' ', s)
    s = re.sub(r'<[^>]*>', ' ', s)
    s = re.sub(r'\[\+\s*[^\]]*?\s*\+\]', ' ', s)
    s = re.sub(r'\[\?\s*if\s+[^:]*:', ' ', s)
    s = s.replace('?]', ' ').replace('**', ' ')
    words = _WORD.findall(s)
    return len(words) >= 2


_COND = re.compile(r'\[\?\s*if\s+([^:]*?)\s*:')
_VARREF = re.compile(r'\[\+\s*([^\]]*?)\s*\+\]')


def cond_key(text):
    """Language independent key of a prose chunk: its conditions and var refs."""
    conds = tuple(c.strip() for c in _COND.findall(text))
    refs = tuple(v.strip() for v in _VARREF.findall(text))
    if not conds and not refs:
        return None
    return conds + ('|refs|',) + refs
