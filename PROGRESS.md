# Перенос перевода на upstream 307d5473 — рабочее состояние

## Что сделано
- Взяты исходники: эталон `base` = 60d02d0e (версия, с которой сделан перевод),
  `new` = 307d5473 (текущий upstream), `tr` = перевод из этого репозитория (`source/`).
- Написан сборщик `tools/assemble.py`: структура/код из NEW, текст — из перевода.
  Сцены сопоставляются по id (плюс алиасы переименованных), проза — по маркерам
  условий (`cond_key`), заголовки — по порядку, строки достижений — по имени ачивки.
- Шаги постобработки: `tools/post_game_over.py` (таблицы достижений),
  `carry_code.py` (правки JS, сделанные в переводе), `apply_values.py` (имена
  партий/персон/идеологий), `js_localize.py`, `patch_fragments.py`,
  `fix_titles.py`, `fix_mojibake.py`, `fix_spaces.py`.
- Проверка переноса: `tools/audit_cov.py` сравнивает кириллические фрагменты
  перевода с итоговой сборкой. Текущий результат: **99.91 %** (33290 из 33319).

## Партии (из перевода, не выдумано)
DNEF = ФНЕГ, DNF = НФГ, DSU = НСС, NVF = ННФ, SAPD = СРПГ, VNR = ННОР,
CVD = ХНС, CSVD = ХСНС, CNBLP = ХНПКЗ, KPD = КПГ, SPD = СДПГ, DVP = ННП,
DNVP = НННП, KVP = КНП, CVP = ХНП, LVP = ЛНП, NSDAP = НСДАП, WP = ЭП,
BVP = БНП, Z = Центр, DDP = НДП, DStP = НГП, Others = Прочие, I = б/п.

## Осталось
1. Добить 29 потерянных фрагментов (cvp_coalition_joever 12, library 5,
   status_right 5, panzerkreuzer 2, schleicher_cabinet_12 2, root 1,
   dvp_party_congress_0 1, schleicher_cabinet_12_alt 1).
2. Компиляция `dendrynexus compile` + смок-тест выборов 1934.
3. Логи `.md`: непереведённые строки, правки слипшихся слов.
4. Перенос результата в `source/`, `make-html -- --pretty`, коммит.

## Как пересобрать
```
bash tools/build.sh /tmp/out        # полный пайплайн
python3 tools/audit_cov.py          # отчёт о переносе
```
(пути внутри `build.sh` предполагают раскладку `/home/user/work/{base,new,tr2}`).
