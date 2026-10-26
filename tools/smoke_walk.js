// Smoke walk: repeatedly click the first available choice and report each scene.
const { JSDOM, VirtualConsole } = require('/home/user/testSD-simRU_new/node_modules/jsdom');
const url = process.argv[2] || 'http://127.0.0.1:8099/index.html';
const steps = Number(process.argv[3] || 8);
const errors = [];
const vc = new VirtualConsole();
vc.on('jsdomError', e => errors.push(String((e && e.message) || e)));
const wait = ms => new Promise(r => setTimeout(r, ms));
const text = d => ((d.querySelector('#content') || d.body).textContent || '').replace(/\s+/g, ' ').trim();

(async () => {
  const dom = await JSDOM.fromURL(url, { runScripts: 'dangerously', resources: 'usable',
    pretendToBeVisual: true, virtualConsole: vc });
  const w = dom.window, d = w.document;
  await wait(2500);
  const log = [];
  for (let i = 0; i < steps; i++) {
    const links = [...d.querySelectorAll('#content ul.choices a')];
    log.push({ step: i, text: text(d).slice(0, 160), choices: links.map(a => a.textContent.trim()).slice(0, 6) });
    if (!links.length) break;
    // prefer a real game start, otherwise take the first choice
    const pick = links.find(a => /Начать \(|Начать игру|Продолжить/.test(a.textContent)) || links[0];
    pick.dispatchEvent(new w.MouseEvent('click', { bubbles: true, cancelable: true, view: w }));
    await wait(900);
  }
  console.log(JSON.stringify({ log, errors: errors.slice(0, 5) }, null, 1));
  process.exit(0);
})();
