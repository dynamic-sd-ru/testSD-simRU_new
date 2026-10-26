// Полное автопрохождение игры в jsdom: от главного меню до концовки.
//
// Запуск:  node tools/smoke_play.js [url] [макс_шагов] [seed]
// Печатает каждый шаг (сцена, год/месяц, что нажали) и итоговый отчёт.
// Код возврата 1, если игра не дошла до концовки или были ошибки JS.
const { JSDOM, VirtualConsole } = require('jsdom');

const URL = process.argv[2] || 'http://127.0.0.1:8099/index.html';
const MAX_STEPS = Number(process.argv[3] || 4000);
const SEED = Number(process.argv[4] || 1);

const errors = [];
// jsdom не умеет проигрывать видео/звук и ходить в интернет — это не ошибки игры
const EXPECTED = [/Not implemented: HTMLMediaElement/, /Could not load iframe/, /Could not load img/];
const vc = new VirtualConsole();
vc.on('jsdomError', (e) => {
  const msg = String((e && e.message) || e);
  if (EXPECTED.some((re) => re.test(msg))) return;
  errors.push(msg);
});
const wait = (ms) => new Promise((r) => setTimeout(r, ms));

// детерминированный ГПСЧ, чтобы прохождение повторялось
let seed = SEED >>> 0;
function rnd() {
  seed = (seed * 1664525 + 1013904223) >>> 0;
  return seed / 4294967296;
}
const pickRandom = (arr) => arr[Math.floor(rnd() * arr.length)];

const clean = (s) => String(s || '').replace(/\s+/g, ' ').trim();

(async () => {
  const dom = await JSDOM.fromURL(URL, {
    runScripts: 'dangerously',
    resources: 'usable',
    pretendToBeVisual: true,
    virtualConsole: vc,
  });
  const w = dom.window;
  const d = w.document;
  await wait(2500);

  const engine = () => w.dendryUI && w.dendryUI.dendryEngine;
  const sceneId = () => {
    const e = engine();
    return e && e.state ? e.state.sceneId : '?';
  };
  const q = () => {
    const e = engine();
    return (e && e.state && e.state.qualities) || {};
  };
  const date = () => {
    const Q = q();
    return `${Q.year}-${String(Q.month).padStart(2, '0')}${Q.rubicon ? ' (rubicon, нед. ' + Q.week + ')' : ''}`;
  };

  const fire = async (el) => {
    el.dispatchEvent(new w.MouseEvent('click', { bubbles: true, cancelable: true, view: w }));
    await wait(40);
  };

  // -------- выбор действия на текущем экране --------
  // Возвращает { el, text } либо null.
  function nextAction() {
    const content = d.querySelector('#content');
    if (!content) return null;

    const choices = [...content.querySelectorAll('ul.choices a')].filter((a) => clean(a.textContent));
    if (choices.length) {
      const cont = choices.find((a) => /^(Продолжить…?|Продолжить\.\.\.)$/.test(clean(a.textContent)));
      if (cont) return { el: cont, text: clean(cont.textContent), kind: 'продолжить' };
      // старт игры из главного меню
      const start = choices.find((a) => /^Начать игру$/.test(clean(a.textContent)));
      if (start) return { el: start, text: clean(start.textContent), kind: 'меню' };
      const skipTutorial = choices.find((a) => /без обучения|Пропустить обучение/i.test(clean(a.textContent)));
      if (skipTutorial) return { el: skipTutorial, text: clean(skipTutorial.textContent), kind: 'меню' };
      const back = choices.find((a) => /^Назад$/.test(clean(a.textContent)));
      if (back) return { el: back, text: clean(back.textContent), kind: 'меню' };
      const pick = pickRandom(choices);
      return { el: pick, text: clean(pick.textContent), kind: 'выбор' };
    }

    // рука: сначала разыгрываем карточку
    const hand = [...content.querySelectorAll('ul.hand li.card-in-hand a, ul.hand li.card-in-hand .card, ul.hand li.card-in-hand')]
      .filter((el) => clean(el.textContent) || el.querySelector('img'));
    if (hand.length) {
      const card = hand[0].querySelector('a, .card') || hand[0];
      return { el: card, text: 'карточка из руки', kind: 'карта' };
    }

    // иначе тянем карту из колоды (колоды чередуем, чтобы обойти все ветки)
    const decks = [...content.querySelectorAll('ul.decks li.deck a, ul.decks li.deck')];
    if (decks.length) {
      const deck = decks[deckCursor++ % decks.length].querySelector('a') || decks[deckCursor % decks.length];
      return { el: deck, text: 'колода: ' + clean(deck.getAttribute('title') || deck.textContent), kind: 'колода' };
    }

    // модальные окна / прочие кнопки
    const buttons = [...d.querySelectorAll('#content button, .modal button, #modal button')].filter(
      (b) => clean(b.textContent)
    );
    if (buttons.length) {
      const b = buttons[0];
      return { el: b, text: clean(b.textContent), kind: 'кнопка' };
    }
    return null;
  }

  const log = [];
  // копим непереведённые фрагменты (3+ латинских слова подряд)
  const latinRuns = new Set();
  const scanLatin = (txt) => {
    const runs = txt.match(/(?:[A-Za-z][A-Za-z'’.-]*\s+){2,}[A-Za-z][A-Za-z'’.-]*/g);
    if (!runs) return;
    for (const r of runs) {
      if (latinRuns.size < 200) latinRuns.add(r.trim());
    }
  };
  let deckCursor = 0;
  let stuck = 0;
  let lastSignature = '';
  let gameOver = false;
  let endingSeen = false;
  let slidesSeen = false;
  let slidesRead = 0;
  let slidesDepth = 0;

  for (let step = 0; step < MAX_STEPS; step++) {
    const sid = sceneId();
    const fullText = clean(d.querySelector('#content') && d.querySelector('#content').textContent);
    scanLatin(fullText);
    const body = fullText.slice(0, 120);
    const signature = sid + '|' + body;
    if (signature === lastSignature) {
      stuck++;
      if (stuck > 40) {
        console.error(`ЗАСТРЯЛИ на сцене ${sid} (${date()}): ${body}`);
        console.error('варианты:', [...d.querySelectorAll('#content ul.choices a')].map((a) => clean(a.textContent)).join(' | '));
        log.push({ step, scene: sid, date: date(), stuck: true, text: body });
        break;
      }
    } else {
      stuck = 0;
      lastSignature = signature;
    }

    if (/^game_over/.test(sid) && process.env.DUMP_ENDING) {
      console.log(`   [экран] ${sid}: ${fullText.slice(0, 300)}`);
    }
    if (/^game_over/.test(sid)) {
      gameOver = true;
      if (/Конец|Игра окончена|Закончить игру/.test(clean(d.body.textContent))) endingSeen = true;
    }

    const action = nextAction();
    if (!action) {
      log.push({ step, scene: sid, date: date(), text: body, action: null });
      console.log(`[${step}] ${sid} ${date()} — нет доступных действий; текст: ${body}`);
      break;
    }

    if (step % 25 === 0 || /^game_over/.test(sid) || action.kind === 'колода') {
      log.push({ step, scene: sid, date: date(), action: `${action.kind}: ${action.text}`, text: body });
      console.log(`[${step}] ${sid} ${date()} → ${action.kind}: ${action.text.slice(0, 60)}`);
    }

    await fire(action.el);

    // концовка: меню концовки -> финальные слайды -> назад -> закончить игру
    if (gameOver) {
      const links = [...d.querySelectorAll('#content ul.choices a')];
      const find = (re) => links.find((a) => re.test(clean(a.textContent)));

      if (find(/Закончить игру/) && slidesSeen) {
        const end = find(/Закончить игру/);
        console.log('концовка прочитана, нажимаем «Закончить игру»');
        await fire(end);
        // экран @end_game помечен game-over: движок дописывает «Игра окончена…»
        const finalText = clean(d.querySelector('#content').textContent);
        endingSeen = /Игра окончена/.test(finalText);
        console.log('экран конца игры:', finalText.slice(0, 160));
        log.push({ step, scene: sceneId(), date: date(), action: 'конец игры' });
        break;
      }
      if (find(/Закончить игру/) && !slidesSeen) {
        const slides = find(/Посмотреть финальные слайды/);
        if (slides) {
          console.log('концовка достигнута, открываем финальные слайды');
          log.push({ step, scene: sid, date: date(), action: 'финальные слайды' });
          await fire(slides);
          continue;
        }
        console.log('финальных слайдов нет, сразу заканчиваем игру');
        slidesSeen = true;
        continue;
      }
      if (find(/^Назад/)) {
        slidesSeen = true;
        slidesRead++;
        console.log(`слайд прочитан (${slidesRead}), возвращаемся`);
        log.push({ step, scene: sid, date: date(), action: 'слайд: ' + body.slice(0, 60) });
        await fire(find(/^Назад/));
        continue;
      }
      // меню финальных слайдов: открываем по очереди все доступные концовки
      if (slidesDepth === 0) {
        slidesDepth = 1;
      }
      const slide = links.find((a) => !/Назад|Закончить игру|пройденные пути/.test(clean(a.textContent)));
      if (slide) {
        slidesSeen = true;
        console.log('открываем концовку: ' + clean(slide.textContent).slice(0, 60));
        log.push({ step, scene: sid, date: date(), action: 'концовка: ' + clean(slide.textContent).slice(0, 60) });
        await fire(slide);
        continue;
      }
      console.log('в меню концовки нет доступных пунктов');
      break;
    }
  }

  const Q = q();
  const report = {
    steps: log.length,
    lastScene: sceneId(),
    date: date(),
    gameOver,
    endingSeen,
    year: Q.year,
    month: Q.month,
    errors: errors.slice(0, 5),
    latinFragments: [...latinRuns].slice(0, 40),
  };
  if (process.env.LOG_JSON) {
    require('fs').writeFileSync(process.env.LOG_JSON, JSON.stringify(log, null, 1));
  }
  if (latinRuns.size) {
    console.log('\nлатинские фрагменты в интерфейсе (проверить, не забыт ли перевод):');
    for (const r of [...latinRuns].slice(0, 40)) console.log('  -', r);
  }
  console.log('\n=== ИТОГ ===');
  console.log(JSON.stringify(report, null, 1));
  process.exit(gameOver && errors.length === 0 ? 0 : 1);
})();
