"""Аудит переноса: кириллические фрагменты TR ищутся в OUT как
непрерывная последовательность кириллических букв (маркап/пунктуация
игнорируются). Запуск: python3 work/audit_cov.py [TR] [OUT]"""
import re, sys, glob, os, json

TR = sys.argv[1] if len(sys.argv) > 1 else 'work/tr'
OUT = sys.argv[2] if len(sys.argv) > 2 else 'work/out'
RUN = re.compile(r'[А-Яа-яЁё][А-Яа-яЁё]*(?:[^А-Яа-яЁё\n]{1,3}[А-Яа-яЁё][А-Яа-яЁё]*)*')
CYR = re.compile(r'[А-Яа-яЁё]')
MOJI = [('ÃŸ', 'ß'), ('Ã¤', 'ä'), ('Ã¼', 'ü'), ('Ã¶', 'ö'),
        ('Ã§', 'ç'), ('Ã©', 'é'), ('Ã„', 'Ä'), ('Ã–', 'Ö'), ('Ãœ', 'Ü')]


def cyr_merge(text):
    """оставить только кириллицу, схлопнув разрывы до 2 символов"""
    text = text
    for a, b in MOJI:
        text = text.replace(a, b)
    return ''.join(CYR.findall(text))


def runs(text):
    text = text
    for a, b in MOJI:
        text = text.replace(a, b)
    out = []
    for m in RUN.finditer(text):
        frag = m.group(0)
        if len(CYR.findall(frag)) >= 6:
            out.append(frag)
    return out


def main():
    total = miss_total = 0
    files = []
    details = []
    for p in glob.glob(os.path.join(TR, '**', '*.dry'), recursive=True):
        rel = os.path.relpath(p, TR)
        src = open(p, encoding='utf-8', errors='replace').read()
        tr_runs = [' '.join(CYR.findall(r)) for r in runs(src)]
        tr_runs = [r.replace(' ', '') for r in tr_runs if len(r.replace(' ', '')) >= 6]
        if not tr_runs:
            continue
        total += len(tr_runs)
        q = os.path.join(OUT, rel)
        if not os.path.exists(q):
            miss_total += len(tr_runs)
            files.append((rel, len(tr_runs)))
            details.append({'file': rel, 'missing': ['<файл отсутствует>']})
            continue
        hay = cyr_merge(open(q, encoding='utf-8', errors='replace').read())
        miss = [r for r in tr_runs if r not in hay]
        miss_total += len(miss)
        if miss:
            files.append((rel, len(miss)))
            details.append({'file': rel, 'missing': miss[:60]})
    files.sort(key=lambda x: -x[1])
    print('фрагментов: %d, найдено: %d, потеряно: %d (%.2f%%)'
          % (total, total - miss_total, miss_total,
             100.0 * (total - miss_total) / total if total else 100.0))
    for rel, n in files[:15]:
        print('  %4d  %s' % (n, rel))
    with open('work/audit_cov.json', 'w', encoding='utf-8') as f:
        json.dump({'total': total, 'missing': miss_total, 'details': details},
                  f, ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
