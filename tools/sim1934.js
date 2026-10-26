// Simulation of the 1934 presidential election JS block.
// usage: node work/sim1934.js <file.scene.dry> [cvp]
const fs = require('fs');

const file = process.argv[2];
const cvp = process.argv[3] === 'cvp';
const text = fs.readFileSync(file, 'utf8');

function blocks(src) {
  const lines = src.split('\n');
  const out = [];
  let i = 0;
  while (i < lines.length) {
    if (lines[i].includes('{!')) {
      const opened = (lines[i].match(/\{!/g) || []).length - (lines[i].match(/!\}/g) || []).length;
      if (opened <= 0) { i++; continue; }
      const start = i;
      let open = opened, j = i;
      while (open > 0 && j + 1 < lines.length) {
        j++;
        open += (lines[j].match(/\{!/g) || []).length - (lines[j].match(/!\}/g) || []).length;
      }
      out.push(lines.slice(start, j + 1).join('\n'));
      i = j + 1;
      continue;
    }
    i++;
  }
  return out;
}

const all = blocks(text);
const descBlock = all.find(b => b.includes('candidate_descs = {'));
const voteBlock = all.find(b => b.includes('candidate_votes = {}'));

function code(block) {
  return block
    .replace(/^on-arrival:\s*\{!/, '')
    .replace(/!}\s*$/, '');
}

const store = {};
const defaults = {
  parties: ['spd', 'kpd', 'z', 'ddp', 'dvp', 'dnvp', 'nsdap', 'other'],
  spd_normalized: 27.5, kpd_normalized: 14.2, z_normalized: 15.1,
  ddp_normalized: 4.4, dvp_normalized: 7.3, dnvp_normalized: 7.1,
  nsdap_normalized: 22.4, other_normalized: 2.0,
  spd_candidate: 'Эккенер', kpd_candidate: 'Тельман', nsdap_candidate: 'Гитлер',
  z_candidate: 'Аденауэр', ddp_candidate: 'Гесслер', dvp_candidate: 'Гесслер',
  dnvp_candidate: 'Зельдте', other_candidate: 'Зельдте',
  Center_bonus: 0, Liberal_bonus: 0, Reactionary_bonus: 0,
  lvp_formed: 0, z_party_name: 'Центр', dnf_votes: 0, dnvp_ideology: 'Правые',
  ddp_ideology: 'Левые', lvp_ideology: 'Умеренные', pro_republic: 60,
  lvp_votes: 8, cvp_formed: cvp ? 1 : 0, lauttenbach_adopted: 0,
  judicial_reform: 0, kpd_leader: 'Тельман', hitler_citizen: 1,
  hitler_deported: 0, hitler_dead: 0, last_round_candidates: [],
};
Object.assign(store, defaults);
if (cvp) {
  store.z_candidate = 'Леттов_Форбек';
  store.dnvp_candidate = 'Леттов_Форбек';
  store.other_candidate = 'Леттов_Форбек';
  store.dnf_candidate = 'Гугенберг';
}

const Q = new Proxy(store, {
  get(t, k) {
    if (k in t) return t[k];
    if (typeof k === 'string' && k.endsWith('_normalized')) return 1;
    return undefined;
  },
  set(t, k, v) { t[k] = v; return true; },
  has(t, k) { return k in t; },
});

const codeText = code(descBlock) + '\n' + code(voteBlock);
let result;
try {
  const fn = new Function('Q', 'dendryUI', codeText + '\nreturn {winner: Q.winner, ' +
    'winner_votes: Q.winner_votes, desc: Q.winner_desc, ' +
    'votes: Object.keys(Q).filter(k => k.endsWith("_votes") && !k.endsWith("_votes_disp")).reduce((a,k)=>{a[k]=Q[k];return a;}, {})};');
  result = fn(Q, {});
} catch (e) {
  console.log('ERROR', e.message);
  process.exit(1);
}
console.log(JSON.stringify(result, null, 1));
