#!/usr/bin/env python3
"""Ищет непереведённый текст внутри «магических» блоков {! ... !} (сырой HTML).

Такие блоки компилятор не переводит: в них остаётся исходный английский текст,
и он виден в интерфейсе. Скрипт обходит out/game.json, вытаскивает видимый
текст magic-узлов (без тегов и атрибутов) и печатает всё, где остались
латинские слова.

Запуск: python3 tools/audit_magic.py [out/game.json]
"""
import json
import re
import sys
from html.parser import HTMLParser

PATH = sys.argv[1] if len(sys.argv) > 1 else "out/game.json"


class TextExtractor(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in ("style", "script"):
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in ("style", "script") and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.parts.append(data)


def visible_text(html):
    p = TextExtractor()
    try:
        p.feed(html)
    except Exception:
        return html
    return re.sub(r"\s+", " ", "".join(p.parts)).strip()


CJK_LATIN = re.compile(r"[A-Za-z][A-Za-z'’.-]*")
# служебные строки, которые не нужно переводить
ALLOWED = re.compile(
    r"^(?:"
    r"http\S*|"
    r"[A-Za-z0-9_.-]+\.(?:jpg|jpeg|png|gif|svg|mp3|ogg|mp4|css|js)|"
    r"[a-z-]+:\s*[^;]*;?|"  # css
    r"rgba?\([^)]*\)"
    r")$"
)


def walk(node, out):
    if isinstance(node, dict):
        if node.get("type") == "magic":
            content = node.get("content")
            if isinstance(content, str):
                out.append(content)
        for v in node.values():
            walk(v, out)
    elif isinstance(node, list):
        for v in node:
            walk(v, out)


def main():
    data = json.load(open(PATH, encoding="utf-8"))
    scenes = data["scenes"]
    findings = {}
    for sid, scene in scenes.items():
        magics = []
        walk(scene, magics)
        for m in magics:
            text = visible_text(m)
            if not text:
                continue
            hits = [h for h in CJK_LATIN.findall(text) if not ALLOWED.match(h.strip())]
            if hits:
                findings.setdefault(sid, []).append(sorted(set(hits)))

    total = sum(len(v) for v in findings.values())
    print(f"сцен с непереведённым HTML: {len(findings)}, фрагментов: {total}")
    for sid, items in sorted(findings.items()):
        frag = sorted({h for group in items for h in group})
        print(f"\n{sid}:")
        for f in frag[:15]:
            print("   ", f)


if __name__ == "__main__":
    main()
