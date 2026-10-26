#!/bin/bash
# Полный конвейер переноса перевода.
#   usage: tools/build.sh [OUTDIR]
#   BASE — версия игры, для которой сделан перевод (60d02d0e)
#   NEW  — актуальная версия игры (307d5473)
#   TR   — дерево перевода (обычно source/ этого репозитория)
# Пути можно переопределить переменными окружения BASE_DIR / NEW_DIR / TR_DIR.
set -e
ROOT=${ROOT:-/home/user}
BASE=${BASE_DIR:-$ROOT/work/base/source}
NEW=${NEW_DIR:-$ROOT/work/new/source}
TR=${TR_DIR:-$ROOT/work/tr2}
OUT=${1:-$ROOT/work/out}
TOOLS=$(cd "$(dirname "$0")" && pwd)

rm -rf "$OUT"
python3 "$TOOLS/assemble.py" "$BASE" "$NEW" "$TR" "$OUT" \
        --report "$ROOT/work/report_assemble.json"
python3 "$TOOLS/carry_similar.py" "$NEW" "$TR" "$OUT" "$TOOLS/maps/similar_donors.json" \
        --report "$ROOT/work/similar_carried.json"
python3 "$TOOLS/apply_neo.py" "$OUT" "$TOOLS/maps/neo_ru.json" \
        --report "$ROOT/work/neo_applied.json"
python3 "$TOOLS/post_game_over.py" "$OUT/scenes/game_over.scene.dry" \
        "$TR/scenes/game_over.scene.dry" "$ROOT/work/report_achievements.txt"
cp -r "$TR/scenes/tutorial" "$OUT/scenes/"
python3 "$TOOLS/carry_code.py" "$BASE" "$TR" "$OUT"
python3 "$TOOLS/carry_tr_scenes.py" "$TR" "$OUT"
python3 "$TOOLS/apply_values.py" "$OUT" "$TOOLS/maps/value_map.json" "$TOOLS/maps/extra_map.json" \
        "$TOOLS/maps/party_values.json"
python3 "$TOOLS/apply_party_names.py" "$OUT"
python3 "$TOOLS/js_localize.py" "$BASE" "$TR" "$OUT" --report "$ROOT/work/js_strings.json"
python3 "$TOOLS/fix_candkeys.py" "$NEW" "$OUT" "" "$TOOLS/maps/value_map.json" "$TOOLS/maps/extra_map.json"
python3 "$TOOLS/apply_display_names.py" "$OUT"
python3 "$TOOLS/patch_fragments.py" "$OUT" "$TR" --report "$ROOT/work/fragment_patches.json"
python3 "$TOOLS/fix_titles.py" "$BASE" "$TR" "$OUT" --report "$ROOT/work/title_fixes.json"
python3 "$TOOLS/fix_tr_breaks.py" "$OUT" "$TOOLS/maps/tr_fixes.json"
python3 "$TOOLS/fix_mojibake.py" "$OUT" "$ROOT/work/mojibake_fixes.json"
python3 "$TOOLS/fix_spaces.py" "$OUT" "$ROOT/work/space_fixes.json"
echo "build ready in $OUT"
