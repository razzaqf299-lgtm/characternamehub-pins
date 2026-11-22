#!/usr/bin/env node
// Run a characternamehub.com generator page in jsdom and collect the names it produces.
// Usage: node extract.js page.html [iterations]
// Prints JSON: {count, hasGender, genderEffective, male:[], female:[], any:[]}
const fs = require('fs');
const { JSDOM, VirtualConsole } = require('jsdom');

const file = process.argv[2];
const ITER = parseInt(process.argv[3] || '250', 10);
let html = fs.readFileSync(file, 'utf8');
// drop external scripts; the generators are inline
html = html.replace(/<script[^>]*\bsrc=[^>]*>\s*<\/script>/gi, '');

const vc = new VirtualConsole(); // swallow page console noise
const dom = new JSDOM(html, {
  runScripts: 'dangerously',
  pretendToBeVisual: true,
  url: 'https://characternamehub.com/',
  virtualConsole: vc,
  beforeParse(w) {
    w.alert = () => {};
    w.speechSynthesis = { speak() {}, cancel() {}, getVoices: () => [] };
    w.SpeechSynthesisUtterance = function () {};
    w.scrollTo = () => {};
    w.Element.prototype.scrollIntoView = function () {};
    w.matchMedia = () => ({ matches: false, addListener() {}, removeListener() {}, addEventListener() {}, removeEventListener() {} });
    Object.defineProperty(w.navigator, 'clipboard', { value: { writeText: () => Promise.resolve() } });
  },
});
const w = dom.window;
const d = w.document;

function run() {
  const selects = [...d.querySelectorAll('select')];
  const idOf = (s) => ((s.id || '') + ' ' + (s.name || '')).toLowerCase();
  const genderSel = selects.find((s) => /gender|sex/.test(idOf(s)));
  const qtySel = selects.find((s) => /quant|count|number|amount|howmany/.test(idOf(s)));
  const others = selects.filter((s) => s !== genderSel && s !== qtySel);

  let btn = [...d.querySelectorAll('button, input[type=button], a')].find((b) => /generatebtn/i.test(b.id || ''));
  if (!btn) btn = [...d.querySelectorAll('button, input[type=button]')].find((b) => /generate/i.test(b.textContent || b.value || '') && !/regenerate/i.test(b.textContent || ''));
  if (!btn) throw new Error('No generate button found');

  const setVal = (s, v) => {
    s.value = v;
    s.dispatchEvent(new w.Event('change', { bubbles: true }));
    s.dispatchEvent(new w.Event('input', { bubbles: true }));
  };
  if (qtySel) {
    const vals = [...qtySel.options].map((o) => o.value).filter((v) => /^\d+$/.test(v));
    if (vals.length) setVal(qtySel, String(Math.max(...vals.map(Number))));
  }

  const nameNodes = () => {
    let nodes = [...d.querySelectorAll('[class*="name-text"]')];
    if (!nodes.length) nodes = [...d.querySelectorAll('[class*="name-card"] [class*="name"]:not([class*="meaning"])')];
    return nodes.map((n) => n.textContent.trim()).filter((t) => t && t.length < 40);
  };

  const buckets = {};
  const genders = genderSel ? ['male', 'female'].filter((g) => [...genderSel.options].some((o) => o.value === g)) : [];
  const groups = genders.length ? genders : ['any'];
  for (const g of groups) {
    const set = new Set();
    for (let i = 0; i < ITER; i++) {
      if (genderSel) setVal(genderSel, g);
      for (const s of others) {
        const opts = [...s.options].map((o) => o.value).filter((v) => v !== '');
        if (opts.length) setVal(s, opts[Math.floor(Math.random() * opts.length)]);
      }
      btn.click();
      nameNodes().forEach((n) => set.add(n));
    }
    buckets[g] = [...set];
  }
  // also count with gender = any/neutral for the total
  const all = new Set(Object.values(buckets).flat());
  if (genderSel) {
    for (const g of ['any', 'neutral', 'all', 'unisex']) {
      if (![...genderSel.options].some((o) => o.value === g)) continue;
      for (let i = 0; i < ITER / 2; i++) {
        setVal(genderSel, g);
        for (const s of others) {
          const opts = [...s.options].map((o) => o.value).filter((v) => v !== '');
          if (opts.length) setVal(s, opts[Math.floor(Math.random() * opts.length)]);
        }
        btn.click();
        nameNodes().forEach((n) => all.add(n));
      }
    }
  }
  let genderEffective = false;
  if (buckets.male && buckets.female) {
    const f = new Set(buckets.female);
    const overlap = buckets.male.filter((n) => f.has(n)).length;
    genderEffective = overlap / Math.max(1, Math.min(buckets.male.length, buckets.female.length)) < 0.3;
  }
  return {
    count: all.size,
    hasGender: !!genders.length,
    genderEffective,
    male: buckets.male || [],
    female: buckets.female || [],
    any: buckets.any || [],
  };
}

w.addEventListener('load', () => {
  setTimeout(() => {
    let out;
    try {
      out = JSON.stringify(run());
    } catch (e) {
      out = JSON.stringify({ error: String(e) });
    }
    // write fully before exiting: process.exit() right after console.log truncates piped output at 64KB
    process.stdout.write(out + '\n', () => process.exit(0));
  }, 200);
});
setTimeout(() => { console.log(JSON.stringify({ error: 'timeout' })); process.exit(0); }, 120000);
