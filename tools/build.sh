#!/bin/bash
# Full pipeline: upstream base/new + translated tree -> compiled Russian build.
# usage: work/build.sh [OUTDIR]      (default /home/user/work/out)
set -e
cd /home/user
OUT=${1:-/home/user/work/out}

rm -rf "$OUT"
python3 work/assemble.py work/base/source work/new/source work/tr2 "$OUT" \
        --report work/report_assemble.json
python3 work/post_game_over.py "$OUT/scenes/game_over.scene.dry" \
        work/tr2/scenes/game_over.scene.dry work/report_achievements.txt
cp -r work/tr2/scenes/tutorial "$OUT/scenes/"
python3 work/carry_code.py work/base/source work/tr2 "$OUT"
python3 work/carry_tr_scenes.py work/tr2 "$OUT"
python3 work/apply_values.py "$OUT" work/value_map.json work/extra_map.json
python3 work/apply_party_names.py "$OUT"
python3 work/js_localize.py work/base/source work/tr2 "$OUT" --report work/js_strings.json
python3 work/fix_candkeys.py work/new/source "$OUT" "" work/value_map.json work/extra_map.json
python3 work/patch_fragments.py "$OUT" work/tr2 --report work/fragment_patches.json
python3 work/fix_titles.py work/base/source work/tr2 "$OUT" --report work/title_fixes.json
python3 work/fix_mojibake.py "$OUT" work/mojibake_fixes.json
python3 work/fix_spaces.py "$OUT" work/space_fixes.json
echo "build ready in $OUT"
