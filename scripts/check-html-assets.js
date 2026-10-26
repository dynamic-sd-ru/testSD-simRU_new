#!/usr/bin/env node
/*
 * Проверка HTML-обвязки после сборки.
 *
 * `dendrynexus make-html` копирует из шаблона только те файлы, которых нет в
 * out/html (в шаблоне они названы с префиксом «+»), поэтому переведённый
 * index.html сохраняется. Но если кто-то запустит сборку с `--overwrite`,
 * шаблон затрёт перевод — этот скрипт ловит такую ситуацию и падает с
 * понятным сообщением, вместо того чтобы молча задеплоить английский UI.
 *
 * Проверяется:
 *   1. index.html на месте и содержит русские подписи (значит, он переведённый);
 *   2. файлы, на которые он ссылается (game.css, game.js, d3, favicon), существуют;
 *   3. папка img на месте и в ней есть портреты и достижения.
 */
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..');
const html = path.join(root, 'out', 'html');
const problems = [];

function fail(msg) {
  problems.push(msg);
}

const indexPath = path.join(html, 'index.html');
if (!fs.existsSync(indexPath)) {
  fail('нет out/html/index.html — соберите проект: npm run make-html');
} else {
  const index = fs.readFileSync(indexPath, 'utf8');
  const markers = ['Настройки', 'Фоновые изображения', 'Загрузка/Сохранение'];
  const missing = markers.filter((m) => !index.includes(m));
  if (missing.length) {
    fail(
      'out/html/index.html не переведён (нет подписей: ' + missing.join(', ') + ').\n' +
        '    Скорее всего сборка шла с --overwrite. Верните файл: git checkout -- out/html/index.html'
    );
  }
}

for (const name of ['game.css', 'game.js', 'd3.v7.min.js', 'd3-parliament.js', 'd3-linegraph.js', 'favicon.ico']) {
  const p = path.join(html, name);
  if (!fs.existsSync(p)) {
    fail('нет out/html/' + name + (name === 'favicon.ico' ? '' : ' — файл из шаблона/репозитория не скопирован'));
  }
}

const img = path.join(html, 'img');
if (!fs.existsSync(img)) {
  fail('нет папки out/html/img — картинки игры не восстановлены');
} else {
  const count = (dir) => (fs.existsSync(dir) ? fs.readdirSync(dir).length : 0);
  const portraits = count(path.join(img, 'portraits'));
  const achievements = count(path.join(img, 'achievement'));
  if (portraits < 50) fail('в out/html/img/portraits всего ' + portraits + ' файлов — картинки потеряны');
  if (achievements < 50) fail('в out/html/img/achievement всего ' + achievements + ' файлов — картинки потеряны');
}

// Файлы, на которые ссылаются сцены, но которых нет и в оригинальной игре
// (баг upstream: автор не выложил картинки). Не считаем это ошибкой сборки,
// но пишем предупреждение, чтобы не искать их заново.
const KNOWN_MISSING = [
  'img/achievement/grosse_weimarer_koalition.png',
  'img/achievement/volkspartei_fur_das_volk.png',
  'img/achievement/blockparteien_parade.png',
  'img/redsaxony.png',
  'img/lol.mp4',
];
const missingKnown = KNOWN_MISSING.filter((rel) => !fs.existsSync(path.join(html, rel)));
if (missingKnown.length) {
  console.warn(
    'предупреждение: ' + missingKnown.length + ' файлов нет и в оригинале ' +
      '(upstream): ' + missingKnown.join(', ')
  );
}

if (problems.length) {
  console.error('\nПроверка HTML-обвязки не прошла:');
  for (const p of problems) console.error('  - ' + p);
  process.exit(1);
}

const index = fs.readFileSync(indexPath, 'utf8');
console.log(
  'html ok: index.html переведён (' + index.length + ' байт), ассеты и ' +
    fs.readdirSync(path.join(img, 'portraits')).length + ' портретов на месте'
);
