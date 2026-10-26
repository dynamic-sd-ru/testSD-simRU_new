const { JSDOM, VirtualConsole } = require('/home/user/testSD-simRU_new/node_modules/jsdom');
const wait = ms => new Promise(r => setTimeout(r, ms));
(async () => {
  const dom = await JSDOM.fromURL('http://127.0.0.1:8099/index.html',
    { runScripts: 'dangerously', resources: 'usable', pretendToBeVisual: true, virtualConsole: new VirtualConsole() });
  const w = dom.window;
  await wait(2500);
  const keys = Object.keys(w.dendryUI || {});
  console.log('ui keys:', keys.join(', '));
  const eng = w.dendryUI.dendryEngine;
  console.log('candidates:', Object.keys(w).filter(k => /eng|dendry|game/i.test(k)).slice(0, 15));
  if (eng) {
    const game = eng.game;
    let target = null;
    for (const id of Object.keys(game.scenes)) {
      const sc = game.scenes[id];
      if (id === game.rootSceneId) continue;
      if (!sc.options || !sc.options.length) { target = id; break; }
    }
    eng.state.sceneId = target;
    const ch = eng._compileChoices(game.scenes[target]);
    console.log(JSON.stringify({ scene: target, titles: ch && ch.map(c => c.title).slice(0, 3) }));
  }
  process.exit(0);
})();
