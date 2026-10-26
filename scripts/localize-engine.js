#!/usr/bin/env node
/*
 * Локализует строки, которые приходят из самого движка dendrynexus
 * (в исходниках игры их нет):
 *   - кнопку «Продолжить…», которая показывается, когда вариантов ответа нет
 *   - заголовок «Игра окончена»
 *   - подпись недоступной колоды «В колоде нет доступных карточек.»
 *   - сообщение о конце игры в HTML-интерфейсе
 *
 * Скрипт идемпотентен и запускается из postinstall, а также перед сборкой.
 */
const fs = require('fs');
const path = require('path');

// Важно: многоточие сохраняется. Сцены игры проверяют, что единственный
// вариант ответа — это «Продолжить…» (post_event.scene.dry, has_event), и
// сверяются именно со строкой с многоточием; без него игра уходила в пустую
// сцену events_choice и кнопка «Продолжить» ничего не делала.
const REPLACEMENTS = [
  ["title: 'Continue...'", "title: 'Продолжить…'"],
  ["title: 'Continue…'", "title: 'Продолжить…'"],
  // повторный запуск не должен оставлять прошлый вариант без многоточия
  ["title: 'Продолжить'", "title: 'Продолжить…'"],
  ["simpleContent('Game Over')", "simpleContent('Игра окончена')"],
  ['"No cards available from deck."', '"В колоде нет доступных карточек."'],
  ["'No cards available from deck.'", "'В колоде нет доступных карточек.'"],
  ["'Game Over (reload to read again)'", "'Игра окончена (перезагрузите страницу, чтобы прочитать снова)'"],
  // меню сохранений/загрузки и системные сообщения браузерного интерфейса
  ['save_button.textContent = "Load"', 'save_button.textContent = "Загрузить"'],
  ['save_button.textContent = "Save"', 'save_button.textContent = "Сохранить"'],
  ['save_element.textContent = "Empty"', 'save_element.textContent = "Пусто"'],
  ["window.alert('Saved.')", "window.alert('Сохранено.')"],
  ["window.alert('Loaded.')", "window.alert('Загружено.')"],
  ["window.alert('No save available.')", "window.alert('Сохранение не найдено.')"],
  [
    "window.alert('Saving and loading is currently disabled.')",
    "window.alert('Сохранение и загрузка сейчас отключены.')",
  ],
];

const targets = [
  path.join(__dirname, '..', 'node_modules', 'dendrynexus', 'lib', 'engine.js'),
  path.join(__dirname, '..', 'node_modules', 'dendrynexus', 'lib', 'ui', 'cli.js'),
  path.join(__dirname, '..', 'node_modules', 'dendrynexus', 'lib', 'ui', 'browser.js'),
  path.join(__dirname, '..', 'node_modules', 'dendrynexus', 'lib', 'ui', 'random_or_file_choice.js'),
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
