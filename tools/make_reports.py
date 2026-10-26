#!/usr/bin/env python3
"""make_reports.py REPORTS_DIR OUT_MD_DIR

Builds the human readable logs that ship with the translation:
  НЕПЕРЕВЕДЁННЫЙ_ТЕКСТ.md   -- what is still English and why
  ИСПРАВЛЕНИЯ_ПРОБЕЛОВ.md   -- every merged/glued word that was repaired
  ИСПРАВЛЕНИЯ_ПЕРЕВОДА.md   -- defects of the old translation that had to be fixed
"""
import json
import os
import sys
from collections import defaultdict

KIND_RU = {
    'tag-close': 'пробел после закрывающего тега',
    'cond-close': 'пробел после закрытия условия',
    'prep-tag': 'пробел перед открывающим тегом',
    'period': 'пробел после точки',
    'comma': 'пробел после запятой',
    'cond-open': 'пробел перед условием',
    'mark-close': 'пробел после выделения',
}

REPAIRED = [
    ('scenes/events/kpd_goals.scene.dry',
     'в течение [? if reichswehr_goal = 1 : месяцев.',
     'в течение [+ kpd_ultimatum_timer +] месяцев.',
     'незакрытое условие ломало компиляцию; переменная взята из новой версии'),
    ('scenes/events/kpd_goals_2.scene.dry',
     'в течение [? if interior_goal = 1 : месяцев.',
     'в течение [+ kpd_ultimatum_timer +] месяцев.',
     'то же самое, второй вариант сцены'),
    ('scenes/events/saxony_reichsexekution_popular.scene.dry',
     'текст был разорван и задублирован, теги <span> не закрыты',
     'предложение восстановлено по структуре новой версии',
     'сцена не компилировалась'),
    ('scenes/events/z_right_party_congress.scene.dry',
     'subtitle: обрывался на [? if z_party_name == "ХНП":',
     'оба ответвления условия восстановлены',
     'обрыв условия и потерянный хвост фразы'),
    ('scenes/events/z_right_party_congress.scene.dry',
     'unavailable-subtitle: тот же обрыв',
     'оба ответвления условия восстановлены',
     'обрыв условия и потерянный хвост фразы'),
    ('scenes/events/death_of_hindenburg_president.scene.dry',
     '«…Мы также напоминаем им об истории сотрудничества…» без закрытия условия',
     'условие z_relation >= 50 восстановлено, добавлен [+ spd_candidate +]',
     'обрыв условия'),
]


def mark(s):
    """spaces made visible for the before/after columns"""
    return str(s).replace(' ', '·').replace('\u00b7', '·')


def esc(s, n=150):
    s = ' '.join(str(s).split())
    return s if len(s) <= n else s[:n - 1] + '…'


def load(path):
    return json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}


def untranslated_md(rep, ach, out):
    unt = defaultdict(list)
    for row in rep.get('untranslated', []):
        unt[row[0]].append((row[1], row[2], row[3]))
    new_scene = defaultdict(list)
    for row in rep.get('new_scene_text', []):
        new_scene[row[0]].append((row[1], row[2]))
    lines = ['# Непереведённый текст (оставлен на английском)',
             '',
             'По правилам проекта текст, которого не было в готовом переводе, не переводится.',
             'Ниже — всё, что в сборке осталось на английском, с указанием файла и строки.',
             '']
    lines.append('## Новые файлы upstream (перевода не существует)')
    lines.append('')
    for f in rep.get('files_new', []):
        lines.append('- `%s`' % f)
    lines.append('')
    lines.append('## Новый текст в существующих сценах: %d строк' % sum(len(v) for v in new_scene.values()))
    lines.append('')
    for f in sorted(new_scene):
        lines.append('### %s' % f)
        lines.append('')
        for ln, txt in new_scene[f]:
            lines.append('- строка %s: `%s`' % (ln, esc(txt)))
        lines.append('')
    lines.append('## Непереведённые реплики/подписи: %d' % sum(len(v) for v in unt.values()))
    lines.append('')
    for f in sorted(unt):
        lines.append('### %s' % f)
        lines.append('')
        for ln, kind, txt in unt[f]:
            lines.append('- строка %s (%s): `%s`' % (ln, kind, esc(txt)))
        lines.append('')
    if ach:
        lines.append('## Новые достижения (в новой версии игры), оставлены на английском')
        lines.append('')
        for name in ach:
            lines.append('- `%s`' % name)
        lines.append('')
    open(os.path.join(out, 'НЕПЕРЕВЕДЁННЫЙ_ТЕКСТ.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    return sum(len(v) for v in unt.values()), sum(len(v) for v in new_scene.values())


def spaces_md(fixes, out):
    by_file = defaultdict(list)
    for it in fixes:
        by_file[it['file']].append(it)
    lines = ['# Исправления слипшихся слов',
             '',
             'При переносе перевода в части строк пропали пробелы («слово</span>слово»,',
             '«конца.И», «?]е»). Все правки перечислены ниже: файл, строка, что было и что стало.',
             '',
             'Всего правок: **%d** в **%d** файлах.' % (len(fixes), len(by_file)),
             '']
    kinds = defaultdict(int)
    for it in fixes:
        kinds[it['kind']] += 1
    lines.append('| тип | что исправлено | количество |')
    lines.append('| --- | --- | --- |')
    for k, n in sorted(kinds.items(), key=lambda x: -x[1]):
        lines.append('| `%s` | %s | %d |' % (k, KIND_RU.get(k, k), n))
    lines.append('')
    for f in sorted(by_file):
        lines.append('## %s' % f)
        lines.append('')
        lines.append('| строка | было | стало |')
        lines.append('| --- | --- | --- |')
        for it in by_file[f]:
            lines.append('| %s | `%s` | `%s` |' % (it['line'], mark(it['before']), mark(it['after'])))
        lines.append('')
    open(os.path.join(out, 'ИСПРАВЛЕНИЯ_ПРОБЕЛОВ.md'), 'w', encoding='utf-8').write('\n'.join(lines))
    return len(fixes)


def repairs_md(out, ach):
    lines = ['# Исправления самого перевода',
             '',
             'Эти места были сломаны в исходном переводе и мешали сборке: строки не',
             'компилировались либо теряли смысл. Текст восстановлен по структуре новой',
             'версии игры, формулировки перевода по возможности сохранены.',
             '']
    lines.append('| файл | что было | что сделано | почему |')
    lines.append('| --- | --- | --- | --- |')
    for f, was, now, why in REPAIRED:
        lines.append('| `%s` | %s | %s | %s |' % (f, was, now, why))
    lines.append('')
    lines.append('## Прочие автоматические правки')
    lines.append('')
    lines.append('- Названия партий возвращены к вариантам перевода (`**SPD**` → `**СДПГ**` и т.д.)')
    lines.append('  в пересобранных таблицах — 315 подписей.')
    lines.append('- Переменные кандидатов выборов 1934 года приведены к ключам upstream')
    lines.append('  (`candkey()`): голоса снова попадают в `Q.Hitler_votes` и т.п.')
    lines.append('- Дата «последнего обновления» взята из новой версии (2026/08/04).')
    lines.append('- Двойное декодирование UTF-8 (`ÃŸ` → `ß`) исправлено в 4 файлах.')
    if ach:
        lines.append('- Новые достижения оставлены на английском: %s.' % ', '.join('`%s`' % a for a in ach))
    lines.append('')
    open(os.path.join(out, 'ИСПРАВЛЕНИЯ_ПЕРЕВОДА.md'), 'w', encoding='utf-8').write('\n'.join(lines))


def main(rep_dir, out_dir):
    rep = load(os.path.join(rep_dir, 'report_assemble.json'))
    fixes = load(os.path.join(rep_dir, 'space_fixes.json'))
    ach_txt = os.path.join(rep_dir, 'report_achievements.txt')
    ach = []
    if os.path.exists(ach_txt):
        body = open(ach_txt, encoding='utf-8').read().split('\n')
        ach = [l.strip() for l in body if l.strip() and not l.startswith(('translated', 'New upstream'))]
    u, n = untranslated_md(rep, ach, out_dir)
    s = spaces_md(fixes, out_dir)
    repairs_md(out_dir, ach)
    print('отчёты: непереведённых строк %d, нового текста %d, правок пробелов %d' % (u, n, s))


if __name__ == '__main__':
    main(*sys.argv[1:3])
