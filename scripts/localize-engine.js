#!/usr/bin/env node
/*
 * Localises the few strings that come from the dendrynexus engine itself
 * (they are not part of the game sources):
 *   - the "Continue..." button shown when a scene has no choices
 *   - the "Game Over" heading
 *
 * The script is idempotent and is run both from postinstall and before a build.
 */
const fs = require('fs');
const path = require('path');

const REPLACEMENTS = [
  ["title: 'Continue...'", "title: 'Продолжить'"],
  ["title: 'Continue…'", "title: 'Продолжить'"],
  ["simpleContent('Game Over')", "simpleContent('Игра окончена')"],
];

const targets = [
  path.join(__dirname, '..', 'node_modules', 'dendrynexus', 'lib', 'engine.js'),
  path.join(__dirname, '..', 'node_modules', 'dendrynexus', 'lib', 'ui', 'cli.js'),
];

let changed = 0;
for (const file of targets) {
  if (!fs.existsSync(file)) continue;
  let src = fs.readFileSync(file, 'utf8');
  const before = src;
  for (const [from, to] of REPLACEMENTS) {
    src = src.split(from).join(to);
  }
  if (src !== before) {
    fs.writeFileSync(file, src);
    changed++;
    console.log('localized engine strings in', path.relative(process.cwd(), file));
  }
}
if (!changed) console.log('engine strings already localized');
