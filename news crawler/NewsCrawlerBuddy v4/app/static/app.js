'use strict';
/* NewsCrawler Buddy front-end (vanilla JS, no build step). All user-facing text comes from /static/i18n/*.json */

/* ---------- helpers ---------- */
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const load = (k, d) => { try { const v = JSON.parse(localStorage.getItem(k)); return v ?? d; } catch { return d; } };
const store = (k, v) => localStorage.setItem(k, JSON.stringify(v));
const clone = o => JSON.parse(JSON.stringify(o));
const get = (o, p) => p.split('.').reduce((a, k) => a?.[k], o);
const put = (o, p, v) => { const ks = p.split('.'), l = ks.pop(); ks.reduce((a, k) => a[k], o)[l] = v; };
const deepMerge = (a, b) => { for (const k in b) { if (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k]) && a[k] && typeof a[k] === 'object') deepMerge(a[k], b[k]); else a[k] = b[k]; } return a; };
const debounce = (fn, ms) => { let h; return (...a) => { clearTimeout(h); h = setTimeout(() => fn(...a), ms); }; };
const fmtN = n => Number.isInteger(+n) ? String(+n) : (+n).toFixed(1);

const FIELDS = ['title', 'text', 'description', 'author', 'published', 'category', 'language', 'source', 'url', 'canonical_url', 'word_count'];
const STEPS = ['method', 'source', 'delay', 'fields', 'review'];
const NAV = [['dashboard', '🏠', 'nav.home'], ['method', '🕷️', 'nav.new'], ['history', '📚', 'nav.history'], ['settings', '⚙️', 'nav.settings']];
const NAV_OF = { method: 'method', source: 'method', delay: 'method', fields: 'method', review: 'method', live: 'dashboard', results: 'history' };
const TERMINAL = ['completed', 'failed', 'stopped'];

function defaultCfg() {
  return {
    mode: 'domain',
    source: { url: 'bbc.com/news', start: 'section' },
    api: { provider: 'guardian', keyword: '', language: 'en', country: '', category: '', date_from: '', date_to: '' },
    index: { url: '', link_pattern: '', page_template: '', page_start: 2, page_end: 2, page_step: 1, stop_empty: 0, include_first: true, follow_next: false },
    limits: { max_articles: 50, date_from: '', date_to: '', keywords: '', depth: 1, max_per_hour: 300, max_per_day: 2000 },
    delay: { base: 10, variation: true, var_min: 1, var_max: 5, direction: 'both', floor: 1 },
    advanced: { concurrency: 1, retries: 2, user_agent: '', ua_list: '', headers: '', proxy: '', selectors: { title: '', content: '', date: '', author: '' } },
    fields: FIELDS.filter(f => f !== 'canonical_url'),
    cleaning: { strip_html: true, dedupe: true, min_words: 30, normalize_dates: true, detect_language: true, language_filter: '' },
    label: { source: 'category', manual: '' },
    split: { enabled: true, train: 80, val: 10, test: 10, stratify: true, seed: 42 }
  };
}

const S = {
  prefs: Object.assign({ lang: (navigator.language || '').toLowerCase().startsWith('zh') ? 'zh-TW' : 'en', theme: 'system', mode: 'simple', onboarded: false, agreed: false, notify: false }, load('ncb.prefs', {})),
  cfg: deepMerge(defaultCfg(), load('ncb.cfg.v1', {})),
  meta: null, es: null, opts: null, robots: null
};
const savePrefs = () => store('ncb.prefs', S.prefs);
const saveCfg = () => store('ncb.cfg.v1', S.cfg);

/* ---------- i18n ---------- */
let I18N = {};
const t = (k, v) => { let s = I18N[k] ?? k; if (v) for (const x in v) s = s.split(`{${x}}`).join(v[x]); return s; };
const tl = k => t(k).split('|');
async function loadLang() {
  I18N = await (await fetch(`/static/i18n/${S.prefs.lang}.json`)).json();
  document.documentElement.lang = S.prefs.lang === 'zh-TW' ? 'zh-Hant' : 'en';
  document.title = t('app.name');
}
const errMsg = e => I18N['msg.' + e.message] || e.message;

/* ---------- api / toast ---------- */
async function api(path, opts = {}) {
  const o = { headers: {}, ...opts };
  if (o.body && typeof o.body !== 'string') { o.body = JSON.stringify(o.body); o.headers['Content-Type'] = 'application/json'; }
  const r = await fetch('/api' + path, o);
  let data = null; try { data = await r.json(); } catch { /* empty */ }
  if (!r.ok) throw new Error((data && (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))) || r.statusText);
  return data;
}
let toastTimer;
function toast(msg) { const el = $('#toast'); el.textContent = msg; el.classList.add('show'); clearTimeout(toastTimer); toastTimer = setTimeout(() => el.classList.remove('show'), 3200); }

/* ---------- theme ---------- */
function applyTheme() {
  const th = S.prefs.theme === 'system' ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light') : S.prefs.theme;
  document.body.dataset.theme = th; document.body.dataset.mode = S.prefs.mode;
  [['#selTheme', S.prefs.theme], ['#selMode', S.prefs.mode], ['#selLang', S.prefs.lang]].forEach(([s, v]) => { const el = $(s); if (el) el.value = v; });
}
matchMedia('(prefers-color-scheme: dark)').addEventListener('change', applyTheme);
async function setPref(k, v) {
  S.prefs[k] = v; savePrefs();
  if (k === 'lang') { await loadLang(); renderShell(); route(); } else applyTheme();
}

/* ---------- mascot (spider-robot) ---------- */
function mascot(state = 'idle', size = 120) {
  const eyes = state === 'sleepy'
    ? '<path class="o" fill="none" d="M38 52q7 7 14 0M68 52q7 7 14 0"/>'
    : state === 'celebrate'
      ? '<path class="o" fill="none" d="M38 54q7-12 14 0M68 54q7-12 14 0"/>'
      : '<circle class="o m-eye" cx="45" cy="50" r="8"/><circle class="o m-eye" cx="75" cy="50" r="8"/><circle class="m-pupil" cx="46" cy="51" r="3.5"/><circle class="m-pupil" cx="76" cy="51" r="3.5"/>';
  const mouth = state === 'sleepy' ? '<path class="o" fill="none" d="M54 68h12"/>' : '<path class="o" fill="none" d="M50 66q10 10 20 0"/>';
  const extra = state === 'sleepy' ? '<text class="zz" x="92" y="24">Z z z</text>' : state === 'celebrate' ? '<text x="2" y="22" font-size="18">🎉</text><text x="96" y="24" font-size="18">✨</text>' : '';
  const L = (d) => `<path class="o" fill="none" d="${d}"/>`;
  return `<svg class="mascot ${state}" width="${size}" height="${size * 0.85}" viewBox="0 0 120 100" role="img" aria-label="${esc(t('mascot.' + state))}">
  <g class="legsA">${L('M28 44L10 30')}${L('M27 64L8 74')}${L('M92 44L110 30')}${L('M93 64L112 74')}</g>
  <g class="legsB">${L('M26 54L6 52')}${L('M30 72L14 90')}${L('M94 54L114 52')}${L('M90 72L106 90')}</g>
  <g class="m-body-g"><path class="o" fill="none" d="M60 28V14"/><circle class="o m-ant" cx="60" cy="11" r="5"/>
  <ellipse class="o m-body" cx="60" cy="55" rx="34" ry="28"/>${eyes}${mouth}
  <circle class="m-cheek" cx="36" cy="64" r="4"/><circle class="m-cheek" cx="84" cy="64" r="4"/></g>${extra}</svg>`;
}

/* ---------- small charts ---------- */
function bars(values, { floor = null } = {}) {
  if (!values.length) return '';
  const H = 100, max = Math.max(...values, floor || 0, 1) * 1.1, w = values.length * 10;
  const line = floor != null ? `<line x1="0" x2="${w}" y1="${H - floor / max * H}" y2="${H - floor / max * H}" stroke="var(--secondary)" stroke-width="1.5" stroke-dasharray="4 3"/>` : '';
  return `<svg class="chart" viewBox="0 0 ${w} ${H}" preserveAspectRatio="none" role="img" aria-label="${esc(t('delay.chart'))}">${line}${values.map((v, i) => `<rect x="${i * 10 + 1}" y="${H - v / max * H}" width="8" height="${v / max * H}" rx="2" fill="var(--primary)"/>`).join('')}</svg>`;
}
function hbars(obj, total) {
  const entries = Object.entries(obj); const max = total || Math.max(...entries.map(e => e[1]), 1);
  if (!entries.length) return `<p class="muted">–</p>`;
  return entries.map(([k, v]) => `<div class="hbar"><span title="${esc(k)}">${esc(k)}</span><div class="tr"><div class="fi" style="width:${Math.min(100, v / max * 100)}%"></div></div><b>${v}</b></div>`).join('');
}

/* ---------- forms ---------- */
function forms(obj) {
  const val = p => get(obj, p);
  const hint = o => o.hint ? `<small>${t(o.hint)}</small>` : '';
  return {
    inp(p, label, o = {}) {
      const v = val(p), type = o.type || 'text';
      if (type === 'checkbox') return `<label class="check ${o.cls || ''}"><input type="checkbox" data-bind="${p}" ${v ? 'checked' : ''}><span>${t(label)}</span></label>`;
      return `<label class="field ${o.cls || ''}"><span>${t(label)}</span><input type="${type}" data-bind="${p}" value="${esc(v)}" ${o.min != null ? `min="${o.min}"` : ''} ${o.max != null ? `max="${o.max}"` : ''} ${o.step ? `step="${o.step}"` : ''} ${o.ph ? `placeholder="${esc(o.ph)}"` : ''} ${o.auto ? `autocomplete="${o.auto}"` : ''}>${hint(o)}</label>`;
    },
    sel(p, label, opts, o = {}) {
      const v = val(p);
      return `<label class="field ${o.cls || ''}"><span>${t(label)}</span><select data-bind="${p}">${opts.map(([k, l, raw]) => `<option value="${esc(k)}" ${String(v) === String(k) ? 'selected' : ''}>${raw ? esc(l) : t(l)}</option>`).join('')}</select>${hint(o)}</label>`;
    },
    area(p, label, o = {}) {
      return `<label class="field ${o.cls || ''}"><span>${t(label)}</span><textarea data-bind="${p}" ${o.ph ? `placeholder="${esc(o.ph)}"` : ''}>${esc(val(p))}</textarea>${hint(o)}</label>`;
    }
  };
}
function bind(root, obj, cb) {
  $$('[data-bind]', root).forEach(el => {
    const ev = (el.type === 'checkbox' || el.tagName === 'SELECT') ? 'change' : 'input';
    el.addEventListener(ev, () => {
      const v = el.type === 'checkbox' ? el.checked : el.type === 'number' ? (el.value === '' ? '' : parseFloat(el.value)) : el.value;
      put(obj, el.dataset.bind, v); if (obj === S.cfg) saveCfg(); if (cb) cb(el);
    });
  });
}
function fieldChecks(obj) {
  return `<div class="cols">${FIELDS.map(f => `<label class="check"><input type="checkbox" data-field="${f}" ${obj.fields.includes(f) ? 'checked' : ''}><span>${t('field.' + f)}</span></label>`).join('')}</div>`;
}
function wireFields(root, obj) {
  $$('[data-field]', root).forEach(el => el.onchange = () => {
    const a = obj.fields, k = el.dataset.field, i = a.indexOf(k);
    if (el.checked && i < 0) a.push(k); if (!el.checked && i >= 0) a.splice(i, 1);
    if (obj === S.cfg) saveCfg();
  });
}
function cleaningForm(f) {
  const n = (p, l, o) => f.inp(p, l, { type: 'number', ...o });
  return `<div class="card"><h2>${t('clean.title')}</h2><div class="cols">
    ${f.inp('cleaning.strip_html', 'clean.strip', { type: 'checkbox' })}${f.inp('cleaning.dedupe', 'clean.dedupe', { type: 'checkbox' })}
    ${f.inp('cleaning.normalize_dates', 'clean.dates', { type: 'checkbox' })}${f.inp('cleaning.detect_language', 'clean.lang', { type: 'checkbox' })}
    ${n('cleaning.min_words', 'clean.minwords', { min: 0, hint: 'clean.minwords.hint' })}
    ${f.inp('cleaning.language_filter', 'clean.langfilter', { ph: 'en / zh', cls: 'adv-only' })}</div></div>
  <div class="card"><h2>${t('label.title')}</h2><div class="cols">
    ${f.sel('label.source', 'label.source', [['category', 'label.category'], ['manual', 'label.manual'], ['none', 'label.none']])}
    ${f.inp('label.manual', 'label.value')}</div></div>
  <div class="card"><h2>${t('split.title')}</h2>${f.inp('split.enabled', 'split.enable', { type: 'checkbox' })}
    <div class="cols">${n('split.train', 'split.train', { min: 0, max: 100 })}${n('split.val', 'split.val', { min: 0, max: 100 })}${n('split.test', 'split.test', { min: 0, max: 100 })}</div>
    ${f.inp('split.stratify', 'split.stratify', { type: 'checkbox' })}${n('split.seed', 'split.seed', { cls: 'adv-only' })}</div>`;
}

/* ---------- view helpers ---------- */
const STATE_ICON = { queued: '⏳', running: '🕷️', paused: '😴', completed: '🎉', failed: '❌', stopped: '⏹️' };
const stateBadge = s => `<span class="badge st-${s}"><span aria-hidden="true">${STATE_ICON[s] || ''}</span> ${t('state.' + s)}</span>`;
const fmtDate = ts => new Date(ts * 1000).toLocaleString(S.prefs.lang);
function fmtDur(sec) { sec = Math.round(sec); if (sec < 60) return t('dur.s', { n: sec }); if (sec < 3600) return t('dur.m', { n: Math.round(sec / 60) }); return t('dur.h', { n: (sec / 3600).toFixed(1) }); }
function fmtRanges(r) { return r.map(([a, b]) => a === b ? `${fmtN(a)}s` : `${fmtN(a)}–${fmtN(b)}s`).join(` ${t('or')} `); }
function robotsBadge(r) {
  const icon = { green: '🟢', yellow: '🟡', red: '🔴' }[r.status];
  return `<div class="light ${r.status}"><span class="dot" aria-hidden="true">${icon}</span><strong>${t('robots.' + r.status)}</strong><span>${t('robots.reason.' + r.reason)}</span>${r.crawl_delay ? `<span>${t('robots.cd', { s: r.crawl_delay })}</span>` : ''}</div>`;
}
function radio(name, opts, cur) {
  return `<div class="seg" role="radiogroup">${opts.map(([v, l, raw]) => `<label class="pill"><input type="radio" name="${name}" value="${esc(v)}" ${cur === v ? 'checked' : ''}><span>${raw ? esc(l) : t(l)}</span></label>`).join('')}</div>`;
}
const wizard = i => `<ol class="steps" aria-label="${t('wiz.progress')}">${STEPS.map((s, k) => `<li class="${k === i ? 'on' : k < i ? 'done' : ''}"><a href="#/${s}" ${k === i ? 'aria-current="step"' : ''}>${k + 1}. ${t('step.' + s)}</a></li>`).join('')}</ol>`;
const wizNav = i => `<div class="nav-row">${i > 0 ? `<a class="btn ghost" href="#/${STEPS[i - 1]}">← ${t('back')}</a>` : '<span></span>'}${i < STEPS.length - 1 ? `<a class="btn" href="#/${STEPS[i + 1]}">${t('next')} →</a>` : ''}</div>`;
function closeStream() { if (S.es) { S.es.close(); S.es = null; } }

/* ---------- shell ---------- */
function renderShell() {
  const items = NAV.map(([r, i, k]) => `<li><a href="#/${r}" data-nav="${r}"><span class="ic" aria-hidden="true">${i}</span><span class="lb">${t(k)}</span></a></li>`).join('');
  $('#sidebar').innerHTML = `<ul>${items}</ul>`;
  $('#bottomnav').innerHTML = `<ul>${items}</ul>`;
  $('#topbar').innerHTML = `<div class="top-brand">${mascot('idle', 44)}<span>${t('app.name')}</span></div>
  <div class="top-ctl">
   <label><span class="sr">${t('a11y.lang')}</span><select id="selLang"><option value="en">English</option><option value="zh-TW">繁體中文</option></select></label>
   <label><span class="sr">${t('a11y.theme')}</span><select id="selTheme"><option value="system">🖥️ ${t('theme.system')}</option><option value="light">☀️ ${t('theme.light')}</option><option value="dark">🌙 ${t('theme.dark')}</option></select></label>
   <label><span class="sr">${t('a11y.mode')}</span><select id="selMode"><option value="simple">🙂 ${t('mode.simple')}</option><option value="advanced">🛠️ ${t('mode.advanced')}</option></select></label></div>`;
  $('#selLang').onchange = e => setPref('lang', e.target.value);
  $('#selTheme').onchange = e => setPref('theme', e.target.value);
  $('#selMode').onchange = e => setPref('mode', e.target.value);
  $$('[data-i18n]').forEach(el => el.textContent = t(el.dataset.i18n));
  applyTheme();
}

/* ---------- router ---------- */
const routes = {};
async function route() {
  const [, name = 'dashboard', arg] = location.hash.split('/');
  if (!S.prefs.onboarded && name !== 'onboarding') { location.hash = '#/onboarding'; return; }
  closeStream();
  const main = $('#main');
  main.innerHTML = `<p class="muted">${t('loading')}</p>`;
  try { await (routes[name] || routes.dashboard)(main, arg); }
  catch (e) { main.innerHTML = `<div class="alert err" role="alert">${esc(errMsg(e))}</div>`; }
  const active = NAV_OF[name] || name;
  $$('[data-nav]').forEach(a => { a.classList.toggle('active', a.dataset.nav === active); a.toggleAttribute('aria-current', a.dataset.nav === active); });
  window.scrollTo(0, 0);
}

/* ---------- onboarding ---------- */
routes.onboarding = async main => {
  const p = S.prefs;
  main.innerHTML = `<section class="card hero">${mascot('idle', 150)}<h1>${t('onb.title')}</h1><p>${t('onb.sub')}</p>
  <fieldset><legend>${t('onb.lang')}</legend>${radio('lang', [['en', 'English', 1], ['zh-TW', '繁體中文', 1]], p.lang)}</fieldset>
  <fieldset><legend>${t('onb.theme')}</legend>${radio('theme', [['system', 'theme.system'], ['light', 'theme.light'], ['dark', 'theme.dark']], p.theme)}</fieldset>
  <fieldset><legend>${t('onb.mode')}</legend>${radio('mode', [['simple', 'mode.simple'], ['advanced', 'mode.advanced']], p.mode)}<small>${t('mode.simple.desc')}<br>${t('mode.advanced.desc')}</small></fieldset>
  <div class="card" style="text-align:left"><h2>⚖️ ${t('legal.title')}</h2><p>${t('legal.text')}</p>
   <label class="check"><input type="checkbox" id="agree" ${p.agreed ? 'checked' : ''}><span>${t('onb.agree')}</span></label></div>
  <button class="btn coral" id="go" ${p.agreed ? '' : 'disabled'}>${t('onb.go')} 🚀</button></section>`;
  $$('input[name=lang]').forEach(el => el.onchange = () => setPref('lang', el.value));
  $$('input[name=theme]').forEach(el => el.onchange = () => setPref('theme', el.value));
  $$('input[name=mode]').forEach(el => el.onchange = () => setPref('mode', el.value));
  $('#agree').onchange = e => { $('#go').disabled = !e.target.checked; };
  $('#go').onclick = () => { S.prefs.agreed = true; S.prefs.onboarded = true; savePrefs(); location.hash = '#/dashboard'; };
};

/* ---------- dashboard ---------- */
async function rerunJob(id) {
  const j = await api('/jobs/' + id);
  const r = await api('/jobs', { method: 'POST', body: { name: j.name, config: j.config } });
  location.hash = '#/live/' + r.id;
}
routes.dashboard = async main => {
  const jobs = await api('/jobs');
  const day = new Date().toDateString();
  const todays = jobs.filter(j => new Date(j.created * 1000).toDateString() === day);
  const todayCount = todays.reduce((a, j) => a + j.collected, 0);
  const running = jobs.filter(j => !TERMINAL.includes(j.state));
  const recent = jobs.filter(j => j.collected > 0).slice(0, 5);
  const codes = {}; let req = 0, err = 0;
  jobs.forEach(j => { const p = j.progress || {}; req += p.requests || 0; err += p.errors || 0; for (const [k, v] of Object.entries(p.status_codes || {})) codes[k] = (codes[k] || 0) + v; });
  const used = {};
  todays.filter(j => j.mode === 'api').forEach(j => { const id = j.config?.api?.provider; used[id] = (used[id] || 0) + (j.progress?.requests || 0); });
  const quota = Object.fromEntries(Object.entries(used).map(([id, n]) => { const p = S.meta.providers.find(x => x.id === id); return [`${p?.name || id}`, n]; }));
  const tips = tl('tips');
  main.innerHTML = `<h1>${t('dash.title')}</h1>
  <section class="card tip">${mascot(running.length ? 'walking' : 'idle', 100)}<div><h2>${t('dash.hello')}</h2><p>💡 ${esc(tips[Math.floor(Math.random() * tips.length)])}</p>
   <div class="btns"><a class="btn coral" href="#/method">🕷️ ${t('dash.new')}</a>${jobs[0] ? `<button class="btn ghost" id="rerun">🔁 ${t('dash.rerun')}</button>` : ''}</div></div></section>
  <div class="grid3"><div class="card center"><h2>${t('dash.today')}</h2><b style="font-size:2rem">${todayCount}</b></div>
   <div class="card center"><h2>${t('dash.running')}</h2><b style="font-size:2rem">${running.length}</b></div>
   <div class="card center"><h2>${t('dash.total')}</h2><b style="font-size:2rem">${jobs.length}</b></div></div>
  ${running.length ? `<section class="card"><h2>${t('dash.running')}</h2>${running.map(j => `<p>${stateBadge(j.state)} <a href="#/live/${j.id}">${esc(j.name)}</a> – ${j.collected}</p>`).join('')}</section>` : ''}
  <section class="card"><h2>${t('dash.recent')}</h2>${recent.length ? `<ul class="plain">${recent.map(j => `<li><a href="#/results/${j.id}">${esc(j.name)}</a> – ${j.collected} ${t('res.rows')} · ${fmtDate(j.created)}</li>`).join('')}</ul>` : `<div class="center">${mascot('sleepy', 90)}<p>${t('dash.empty')}</p></div>`}</section>
  <section class="card adv-only"><h2>${t('dash.stats')}</h2><div class="cols"><div><h3>${t('dash.codes')}</h3>${hbars(codes)}</div>
   <div><h3>${t('dash.success')}</h3><b style="font-size:1.6rem">${req ? Math.round((1 - err / req) * 100) : 100}%</b><h3>${t('dash.quota')}</h3>${hbars(quota)}</div></div></section>`;
  const b = $('#rerun'); if (b) b.onclick = () => rerunJob(jobs[0].id).catch(e => toast(errMsg(e)));
};

/* ---------- 3. method ---------- */
function wirePicks(root) {
  $$('[data-pick]', root).forEach(b => b.onclick = () => { S.cfg.mode = b.dataset.pick; saveCfg(); location.hash = '#/source'; });
}
routes.method = async main => {
  const list = (id, k) => tl(`method.${id}.${k}`).map(x => `<li>${esc(x)}</li>`).join('');
  const mcard = (id, icon, cls) => `<article class="card"><h2>${icon} ${t(`method.${id}.title`)}</h2><p>${t(`method.${id}.when`)}</p>
    <h3>${t('pros')}</h3><ul class="plain pros">${list(id, 'pros')}</ul><h3>${t('cons')}</h3><ul class="plain cons">${list(id, 'cons')}</ul>
    <button class="btn ${cls}" data-pick="${id}">${t('choose')}</button></article>`;
  main.innerHTML = `${wizard(0)}<h1>${t('method.title')}</h1><p>${t('method.intro')}</p>
  <div class="grid3">${mcard('domain', '🌐', '')}${mcard('index', '📑', 'ghost')}${mcard('api', '🔑', 'mint')}${mcard('demo', '🧪', 'coral')}</div>
  <section class="card"><h2>🧭 ${t('quiz.title')}</h2>
  ${[1, 2, 3].map(n => `<fieldset><legend>${t('quiz.q' + n)}</legend>${radio('q' + n, [['yes', 'yes'], ['no', 'no']], '')}</fieldset>`).join('')}
  <button class="btn" id="quizGo">${t('quiz.btn')}</button><div id="quizOut" role="status" aria-live="polite"></div></section>`;
  wirePicks(main);
  $('#quizGo').onclick = () => {
    const a = n => (document.querySelector(`input[name=q${n}]:checked`) || {}).value;
    if (!a(1) || !a(2) || !a(3)) { toast(t('quiz.answer')); return; }
    let d = 0, p = 0;
    if (a(1) === 'yes') d++; else p++;      // full text -> domain
    if (a(2) === 'yes') p++; else d++;      // has API key -> api
    if (a(3) === 'yes') d++; else p++;      // large volume -> domain (API quotas are limited)
    const rec = d > p ? 'domain' : 'api';
    $('#quizOut').innerHTML = `<div class="light green"><span class="dot" aria-hidden="true">👉</span><strong>${t('quiz.rec.' + rec)}</strong></div><button class="btn" data-pick="${rec}">${t('quiz.use')}</button>`;
    wirePicks($('#quizOut'));
  };
};

/* ---------- 4. source ---------- */
function robotsHtml(r) {
  return robotsBadge(r) + (r.status === 'red' ? `<div class="alert err" role="alert">${t('src.robots.blocked')}</div>` : '');
}
routes.source = async main => {
  const c = S.cfg, f = forms(c);
  const n = (p, l, o) => f.inp(p, l, { type: 'number', ...o });
  let keys = {};
  if (c.mode === 'api') keys = await api('/keys');
  const modeRadio = `<fieldset><legend>${t('src.mode')}</legend>${radio('mode', [['domain', 'mode.domain'], ['index', 'mode.index'], ['api', 'mode.api'], ['demo', 'mode.demo']], c.mode)}</fieldset>`;
  let body = '';
  if (c.mode === 'domain') {
    body = `<div class="card"><h2>🌐 ${t('mode.domain')}</h2>
      ${f.inp('source.url', 'src.url', { hint: 'src.url.hint', ph: 'bbc.com/news', auto: 'url' })}
      <p><strong>${t('src.start')}</strong></p>${radio('start', [['section', 'start.section'], ['rss', 'start.rss'], ['sitemap', 'start.sitemap']], c.source.start)}
      <button class="btn ghost" id="chk">🤖 ${t('src.robots.check')}</button><div id="robotsOut" aria-live="polite">${S.robots ? robotsHtml(S.robots) : ''}</div></div>`;
  } else if (c.mode === 'index') {
    body = indexBody(f, c);
  } else if (c.mode === 'api') {
    const pid = c.api.provider, prov = S.meta.providers.find(p => p.id === pid) || S.meta.providers[0];
    const k = keys[prov.id];
    body = `<div class="card"><h2>🔑 ${t('mode.api')}</h2>
      ${f.sel('api.provider', 'api.provider', S.meta.providers.map(p => [p.id, p.name, true]))}
      <p>${k ? `✅ ${t('api.key.status')}: <code>${esc(k.masked)}</code> (${esc(k.source)})` : `⚠️ ${t('api.key.none')} <a href="#/settings">${t('api.go.settings')}</a>`}</p>
      <p>${prov.full_text ? t('api.fulltext') : t('api.snippet')}</p>
      <button class="btn ghost" id="test" ${k ? '' : 'disabled'}>🔌 ${t('api.test')}</button> <span id="testOut" role="status"></span>
      <div class="cols" style="margin-top:1rem">${f.inp('api.keyword', 'api.keyword')}${f.inp('api.language', 'api.language', { ph: 'en' })}
      ${f.inp('api.country', 'api.country', { ph: 'us' })}${f.inp('api.category', 'api.category')}
      ${f.inp('api.date_from', 'lim.from', { type: 'date' })}${f.inp('api.date_to', 'lim.to', { type: 'date' })}</div>
      <p id="est" class="muted"></p></div>`;
  } else {
    body = `<div class="card tip">${mascot('walking', 100)}<p>${t('src.demo.note')}</p></div>`;
  }
  main.innerHTML = `${wizard(1)}<h1>${t('src.title')}</h1>${modeRadio}${body}
  <div class="card"><h2>${t('src.limits')}</h2><div class="cols">
   ${n('limits.max_articles', 'lim.max', { min: 1, max: 100000 })}
   ${c.mode === 'api' ? '' : f.inp('limits.date_from', 'lim.from', { type: 'date' }) + f.inp('limits.date_to', 'lim.to', { type: 'date' })}
   ${c.mode === 'api' ? '' : f.inp('limits.keywords', 'lim.keywords', { hint: 'lim.keywords.hint' })}
   ${c.mode === 'domain' ? n('limits.depth', 'lim.depth', { min: 1, max: 3 }) : ''}</div></div>${wizNav(1)}`;

  $$('input[name=mode]').forEach(el => el.onchange = () => { c.mode = el.value; saveCfg(); routes.source(main); });
  $$('input[name=start]').forEach(el => el.onchange = () => { c.source.start = el.value; saveCfg(); });
  const updEst = debounce(async () => {
    const el = $('#est'); if (!el) return;
    try {
      const e = await api('/jobs/estimate', { method: 'POST', body: { config: c } });
      const p = S.meta.providers.find(x => x.id === c.api.provider);
      el.textContent = t('api.estimate', { n: e.requests, q: p?.daily_quota ?? '?' });
    } catch { el.textContent = ''; }
  }, 300);
  bind(main, c, el => {
    if (el.dataset.bind === 'api.provider') routes.source(main);
    if (el.dataset.bind === 'source.url') { S.robots = null; const o = $('#robotsOut'); if (o) o.innerHTML = ''; }
    updEst();
  });
  updEst();
  if (c.mode === 'index') wireIndex(main);
  const chk = $('#chk');
  if (chk) chk.onclick = async () => {
    try {
      S.robots = await api('/robots', { method: 'POST', body: { url: c.source.url } });
      $('#robotsOut').innerHTML = robotsHtml(S.robots);
    } catch (e) { toast(errMsg(e)); }
  };
  const test = $('#test');
  if (test) test.onclick = async () => {
    try {
      const r = await api(`/providers/${c.api.provider}/test`, { method: 'POST' });
      $('#testOut').textContent = r.ok ? '✅ ' + t('api.test.ok') : '❌ ' + errMsg({ message: r.message });
    } catch (e) { $('#testOut').textContent = '❌ ' + errMsg(e); }
  };
};

/* ---------- 5. delay ---------- */
const LIGHT = { green: '🟢', yellow: '🟡', red: '🔴' };
routes.delay = async main => {
  const f = forms(S.cfg);
  const n = (p, l, o) => f.inp(p, l, { type: 'number', ...o });
  main.innerHTML = `${wizard(2)}<h1>${t('delay.title')}</h1>
  <div class="card tip">${mascot('sleepy', 90)}<p>💡 ${t('delay.intro')}</p></div>
  ${S.cfg.mode === 'demo' ? `<div class="alert">${t('delay.demo.note')}</div>` : ''}
  <div class="card"><div class="cols">
   ${n('delay.base', 'delay.base', { min: 0, step: '0.5' })}${f.inp('delay.variation', 'delay.variation', { type: 'checkbox' })}
   ${n('delay.var_min', 'delay.min', { min: 0, step: '0.5' })}${n('delay.var_max', 'delay.max', { min: 0, step: '0.5' })}
   ${f.sel('delay.direction', 'delay.direction', [['both', 'delay.both'], ['plus', 'delay.plus'], ['minus', 'delay.minus']])}</div>
   <p><small>${t('delay.formula')}</small></p>
   <div class="cols adv-only">${n('limits.max_per_hour', 'delay.maxhour', { min: 0 })}${n('limits.max_per_day', 'delay.maxday', { min: 0 })}</div></div>
  <div class="card" id="prev" aria-live="polite"></div>${wizNav(2)}`;
  const upd = async () => {
    try {
      const r = await api('/delay/preview', { method: 'POST', body: S.cfg.delay });
      $('#prev').innerHTML = `<h2>${t('delay.actual')}</h2><p style="font-size:1.4rem"><strong>${fmtRanges(r.ranges)}</strong></p>
        <div class="light ${r.level}"><span class="dot" aria-hidden="true">${LIGHT[r.level]}</span><strong>${t('delay.safety.' + r.level)}</strong>${r.warn ? `<span>${t('delay.warn')}</span>` : ''}</div>
        ${bars(r.samples, { floor: r.floor })}<small>${t('delay.chart')}</small>`;
    } catch (e) { $('#prev').innerHTML = `<div class="alert err">${esc(errMsg(e))}</div>`; }
  };
  bind(main, S.cfg, debounce(upd, 250));
  upd();
};

/* ---------- 6. fields & cleaning ---------- */
routes.fields = async main => {
  const f = forms(S.cfg);
  main.innerHTML = `${wizard(3)}<h1>${t('fields.title')}</h1>
  <div class="card"><h2>${t('fields.select')}</h2>${fieldChecks(S.cfg)}</div>${cleaningForm(f)}
  <div class="card adv-only"><h2>${t('adv.title')}</h2><div class="cols">
   ${f.inp('advanced.concurrency', 'adv.concurrency', { type: 'number', min: 1, max: 5 })}${f.inp('advanced.retries', 'adv.retries', { type: 'number', min: 0, max: 10 })}
   ${f.inp('advanced.user_agent', 'adv.ua')}${f.inp('advanced.proxy', 'adv.proxy', { ph: 'http://127.0.0.1:8080' })}</div>
   ${f.area('advanced.ua_list', 'adv.ualist')}${f.area('advanced.headers', 'adv.headers', { ph: 'Accept-Language: en' })}
   <h3>${t('adv.sel.hint')}</h3><div class="cols">${f.inp('advanced.selectors.title', 'adv.sel.title')}${f.inp('advanced.selectors.content', 'adv.sel.content')}
   ${f.inp('advanced.selectors.date', 'adv.sel.date')}${f.inp('advanced.selectors.author', 'adv.sel.author')}</div></div>${wizNav(3)}`;
  bind(main, S.cfg);
  wireFields(main, S.cfg);
};

/* ---------- 7. review & run ---------- */
routes.review = async main => {
  const c = S.cfg;
  const src = c.mode === 'api' ? (S.meta.providers.find(p => p.id === c.api.provider)?.name || c.api.provider) : c.mode === 'demo' ? t('mode.demo') : c.mode === 'index' ? c.index.url : c.source.url;
  let est = null;
  try { est = await api('/jobs/estimate', { method: 'POST', body: { config: c } }); } catch (e) { est = { error: errMsg(e) }; }
  main.innerHTML = `${wizard(4)}<h1>${t('rev.title')}</h1>
  <div class="card"><h2>${t('rev.summary')}</h2><ul class="plain">
   <li>${t('rev.mode')}: <strong>${t('mode.' + c.mode)}</strong></li><li>${t('rev.source')}: <strong>${esc(src)}</strong></li>
   <li>${t('rev.max')}: <strong>${c.limits.max_articles}</strong></li><li>${t('rev.delay')}: <strong id="dtxt">…</strong></li>
   <li>${t('rev.est')}: <strong>${est.error ? esc(est.error) : t('rev.est.val', { n: est.requests, d: fmtDur(est.seconds) })}</strong></li></ul>
   ${c.mode === 'domain' && S.robots?.status === 'red' ? `<div class="alert err" role="alert">${t('src.robots.blocked')}</div>` : ''}
   ${c.mode === 'domain' && !S.robots ? `<div class="alert">${t('rev.robots.warn')}</div>` : ''}
   <label class="field"><span>${t('rev.name')}</span><input type="text" id="jobname" value="${esc(c.mode + '-' + new Date().toISOString().slice(0, 10))}"></label>
   <div class="btns"><button class="btn coral" id="start">🚀 ${t('rev.start')}</button></div></div>
  <div class="card"><h2>💾 ${t('rev.preset')}</h2><div class="cols">
   <label class="field"><span>${t('rev.preset.name')}</span><input type="text" id="pname"></label>
   <label class="field adv-only"><span>${t('rev.schedule')}</span><select id="psched"><option value="">${t('sch.none')}</option><option value="daily">${t('sch.daily')}</option><option value="weekly">${t('sch.weekly')}</option></select></label></div>
   <button class="btn ghost" id="psave">${t('rev.preset.save')}</button></div>
  <div class="card adv-only"><h2>${t('cfg.title')}</h2><textarea id="cfgtext" aria-label="${t('cfg.title')}"></textarea>
   <div class="btns"><button class="btn ghost sm" id="cj">${t('cfg.json')}</button><button class="btn ghost sm" id="cy">${t('cfg.yaml')}</button><button class="btn sm" id="ci">${t('cfg.import')}</button></div></div>
  ${wizNav(4)}`;
  api('/delay/preview', { method: 'POST', body: c.delay }).then(r => { $('#dtxt').textContent = fmtRanges(r.ranges); }).catch(() => { });
  $('#start').onclick = async () => {
    try {
      const r = await api('/jobs', { method: 'POST', body: { name: $('#jobname').value, config: S.cfg } });
      location.hash = '#/live/' + r.id;
    } catch (e) { toast(errMsg(e)); }
  };
  $('#psave').onclick = async () => {
    try {
      await api('/presets', { method: 'POST', body: { name: $('#pname').value, config: S.cfg, schedule: $('#psched').value || null } });
      toast(t('rev.preset.saved'));
    } catch (e) { toast(errMsg(e)); }
  };
  const dump = fmt => async () => { try { $('#cfgtext').value = (await api('/config/dump', { method: 'POST', body: { config: S.cfg, format: fmt } })).text; } catch (e) { toast(errMsg(e)); } };
  $('#cj').onclick = dump('json'); $('#cy').onclick = dump('yaml');
  $('#ci').onclick = async () => {
    try {
      const d = await api('/config/parse', { method: 'POST', body: { text: $('#cfgtext').value } });
      S.cfg = deepMerge(defaultCfg(), d); saveCfg(); toast(t('cfg.imported')); routes.review(main);
    } catch (e) { toast(errMsg(e)); }
  };
};

/* ---------- 8. live progress ---------- */
const logText = l => t('log.' + l.code, l.args || {});
routes.live = async (main, id) => {
  id = +id;
  main.innerHTML = `<h1>${t('live.title')}</h1><div class="live-grid"><div class="card center" id="mbox"></div>
  <div class="card"><div id="stline"></div>
   <div class="progress" id="pbar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0" aria-label="${t('live.title')}"><div></div></div>
   <p class="cd" id="cd"></p><div id="alertBox" role="alert"></div><div class="stats" id="stats"></div><div class="btns" id="ctl"></div></div></div>
  <div class="card"><h2>${t('live.chart')}</h2><div id="chart"></div></div>
  <div class="card"><h2>${t('live.log')}</h2><div class="log" id="log" role="log" tabindex="0"></div></div>`;
  let lastState = null, lastMascot = null, notified = false;
  const act = async a => {
    try {
      await api(`/jobs/${id}/${a}`, { method: 'POST' });
      if (a === 'resume' && TERMINAL.includes(lastState)) setTimeout(() => routes.live(main, id), 400);
    } catch (e) { toast(errMsg(e)); }
  };
  const controls = st => {
    const b = (a, cls, ic, k) => `<button class="btn ${cls}" data-a="${a}">${ic} ${t(k)}</button>`;
    let h = '';
    if (st === 'running') h = b('pause', 'ghost', '⏸️', 'btn.pause') + b('stop', 'danger', '⏹️', 'btn.stop');
    else if (st === 'paused') h = b('resume', 'mint', '▶️', 'btn.resume') + b('stop', 'danger', '⏹️', 'btn.stop');
    else if (st === 'stopped' || st === 'failed') h = b('resume', 'mint', '▶️', 'btn.continue') + `<a class="btn" href="#/results/${id}">📊 ${t('btn.results')}</a>`;
    else if (st === 'completed') h = `<a class="btn coral" href="#/results/${id}">📊 ${t('btn.results')}</a>`;
    $('#ctl').innerHTML = h;
    $$('[data-a]', $('#ctl')).forEach(el => el.onclick = () => act(el.dataset.a));
  };
  const update = s => {
    const st = s.state;
    if (st !== lastState) { lastState = st; controls(st); }
    if (s.mascot !== lastMascot) { lastMascot = s.mascot; $('#mbox').innerHTML = mascot(s.mascot, 140); }
    $('#stline').innerHTML = stateBadge(st);
    const col = s.collected ?? 0, tg = s.target || 0;
    const pct = tg ? Math.min(100, col / tg * 100) : (st === 'completed' ? 100 : 0);
    $('#pbar').setAttribute('aria-valuenow', Math.round(pct)); $('#pbar > div').style.width = pct + '%';
    $('#cd').innerHTML = st === 'paused' ? t('live.paused') : s.countdown > 0 ? t('live.next', { s: `<strong>${(+s.countdown).toFixed(1)}</strong>` }) : '';
    const al = $('#alertBox');
    al.innerHTML = s.alert ? `<div class="alert">😴 ${t('alert.rate', { status: s.alert.status, backoff: s.alert.backoff })}</div>`
      : st === 'failed' && s.message ? `<div class="alert err">${esc(errMsg({ message: s.message }))}</div>` : '';
    const stat = (v, k) => `<div class="stat"><b>${v}</b><span>${t(k)}</span></div>`;
    $('#stats').innerHTML = stat(`${col}/${tg}`, 'live.collected') + stat(s.requests ?? 0, 'live.requests') + stat(s.errors ?? 0, 'live.errors') +
      stat(s.skipped ?? 0, 'live.skipped') + stat(s.duplicates ?? 0, 'live.dups') + stat((s.avg_ms ?? 0) + ' ms', 'live.avg') +
      stat(s.last_wait != null ? (+s.last_wait).toFixed(1) + 's' : '–', 'live.lastwait');
    $('#chart').innerHTML = bars(s.times || []);
    const log = $('#log'), stick = log.scrollTop + log.clientHeight >= log.scrollHeight - 30;
    (s.logs || []).forEach(l => { const d = document.createElement('div'); d.className = 'ln ' + l.level; d.innerHTML = `<time>${esc(l.t)}</time>${esc(logText(l))}`; log.appendChild(d); });
    while (log.childElementCount > 600) log.firstChild.remove();
    if (stick) log.scrollTop = log.scrollHeight;
    if (TERMINAL.includes(st)) {
      closeStream();
      if (!notified && S.prefs.notify && 'Notification' in window && Notification.permission === 'granted') { new Notification(t('app.name'), { body: t('state.' + st) }); }
      notified = true;
    }
  };
  closeStream();
  S.es = new EventSource(`/api/jobs/${id}/events`);
  S.es.onmessage = ev => update(JSON.parse(ev.data));
};

/* ---------- 9. results & export ---------- */
function reportHtml(rp) {
  const miss = Object.fromEntries(Object.entries(rp.missing).filter(([, v]) => v > 0));
  const wc = Object.fromEntries(rp.word_count.labels.map((l, i) => [l, rp.word_count.counts[i]]));
  const rem = Object.fromEntries(Object.entries(rp.removed).filter(([, v]) => v > 0).map(([k, v]) => [t('rm.' + k), v]));
  return `<div class="stats"><div class="stat"><b>${rp.raw}</b><span>${t('res.raw')}</span></div><div class="stat"><b>${rp.final}</b><span>${t('res.final')}</span></div>
   <div class="stat"><b>${(rp.duplicate_rate * 100).toFixed(1)}%</b><span>${t('res.duprate')}</span></div>
   <div class="stat"><b>${Math.round(rp.word_count.mean)}</b><span>${t('res.mean')}</span></div><div class="stat"><b>${Math.round(rp.word_count.median)}</b><span>${t('res.median')}</span></div></div>
   <div class="cols"><div><h3>${t('res.words')}</h3>${hbars(wc)}</div><div><h3>${t('res.cats')}</h3>${hbars(rp.categories)}</div>
   <div><h3>${t('res.missing')}</h3>${hbars(miss, rp.raw)}</div><div><h3>${t('res.removed')}</h3>${hbars(rem)}</div>
   <div><h3>${t('res.langs')}</h3>${hbars(rp.languages)}</div><div><h3>${t('res.splits')}</h3>${hbars(rp.split_counts)}</div></div>`;
}
routes.results = async (main, id) => {
  id = +id;
  const job = await api('/jobs/' + id);
  const base = defaultCfg(), jc = job.config || {};
  const o = { fields: clone(jc.fields || base.fields), cleaning: Object.assign(base.cleaning, jc.cleaning), label: Object.assign(base.label, jc.label), split: Object.assign(base.split, jc.split) };
  const f = forms(o);
  main.innerHTML = `<h1>${t('res.title')}: ${esc(job.name)}</h1><p>${stateBadge(job.state)} · ${job.collected} ${t('res.rows')}</p>
  <details class="card"><summary><strong>${t('res.options')}</strong></summary>${fieldChecks(o)}${cleaningForm(f)}<button class="btn" id="apply">${t('res.apply')}</button></details>
  <section class="card"><h2>${t('res.preview')}</h2><div id="tbl"><p class="muted">${t('loading')}</p></div></section>
  <section class="card"><h2>${t('res.report')}</h2><div id="rep"></div></section>
  <section class="card"><h2>⬇️ ${t('res.export')}</h2><div class="cols">
   <label class="field"><span>${t('res.format')}</span><select id="fmt"><option value="csv">CSV</option><option value="json">JSON</option><option value="jsonl">JSONL</option><option value="xlsx">Excel (.xlsx)</option><option value="parquet">Parquet</option></select></label></div>
   <button class="btn coral" id="exp">${t('res.export')}</button><div id="exps"></div></section>`;
  bind(main, o); wireFields(main, o);
  const process = async () => {
    try {
      const d = await api(`/jobs/${id}/process`, { method: 'POST', body: o });
      const long = ['text', 'description', 'title'];
      $('#tbl').innerHTML = d.rows.length ? `<div class="table-wrap"><table><thead><tr>${d.columns.map(c => `<th scope="col">${esc(c)}</th>`).join('')}</tr></thead><tbody>${d.rows.map(r => `<tr>${d.columns.map(c => `<td class="${long.includes(c) ? 'txt' : ''}" ${long.includes(c) ? `title="${esc(r[c])}"` : ''}>${esc(r[c])}</td>`).join('')}</tr>`).join('')}</tbody></table></div>` : `<div class="center">${mascot('sleepy', 90)}<p>${t('res.none')}</p></div>`;
      $('#rep').innerHTML = reportHtml(d.report);
    } catch (e) { $('#tbl').innerHTML = `<div class="alert err">${esc(errMsg(e))}</div>`; }
  };
  const exports = async () => {
    const list = await api(`/jobs/${id}/exports`);
    $('#exps').innerHTML = list.length ? `<h3>${t('res.versions')}</h3>` + list.map(v => `<p><strong>${esc(v.version)}</strong>: ${v.files.map(fn => `<a href="/api/exports/${id}/${encodeURIComponent(v.version)}/${encodeURIComponent(fn)}" download>${esc(fn)}</a>`).join(' · ')}</p>`).join('') : '';
  };
  $('#apply').onclick = process;
  $('#exp').onclick = async () => {
    try { await api(`/jobs/${id}/export`, { method: 'POST', body: { format: $('#fmt').value, opts: o } }); toast(t('res.exported')); await exports(); }
    catch (e) { toast(errMsg(e)); }
  };
  await process(); await exports();
};

/* ---------- 10. history & presets ---------- */
routes.history = async main => {
  const [jobs, presets] = await Promise.all([api('/jobs'), api('/presets')]);
  const hb = (a, id, ic, k) => `<button class="btn ghost sm" data-h="${a}" data-id="${id}">${ic} ${t(k)}</button>`;
  main.innerHTML = `<h1>${t('hist.title')}</h1>
  <section class="card"><h2>${t('hist.jobs')}</h2>${jobs.length ? `<div class="table-wrap"><table><thead><tr><th scope="col">${t('hist.name')}</th><th scope="col">${t('hist.mode')}</th><th scope="col">${t('hist.state')}</th><th scope="col">${t('hist.count')}</th><th scope="col">${t('hist.date')}</th><th scope="col"></th></tr></thead><tbody>
   ${jobs.map(j => `<tr><td>${esc(j.name)}</td><td>${t('mode.' + j.mode)}</td><td>${stateBadge(j.state)}</td><td>${j.collected}</td><td>${fmtDate(j.created)}</td>
   <td>${hb('open', j.id, '📂', 'hist.open')} ${hb('rerun', j.id, '🔁', 'hist.rerun')} ${hb('dup', j.id, '📋', 'hist.dup')}
   ${['stopped', 'failed'].includes(j.state) ? hb('resume', j.id, '▶️', 'hist.resume') : ''} ${TERMINAL.includes(j.state) ? hb('del', j.id, '🗑️', 'hist.delete') : ''}</td></tr>`).join('')}</tbody></table></div>`
    : `<div class="center">${mascot('sleepy', 90)}<p>${t('hist.none')}</p></div>`}</section>
  <section class="card"><h2>${t('hist.presets')}</h2>${presets.length ? presets.map(p => `<div class="card"><strong>${esc(p.name)}</strong> <small>${esc(p.config.mode)} · ${esc((p.config.mode === 'index' ? p.config.index?.url : (p.config.source?.url || p.config.api?.provider)) || '')}</small>
   <div class="btns">${hb('pload', p.id, '📥', 'hist.load')} ${hb('prun', p.id, '🚀', 'hist.run')} ${hb('pdel', p.id, '🗑️', 'hist.delete')}
   <label class="adv-only"><span class="sr">${t('rev.schedule')}</span><select data-h="psch" data-id="${p.id}"><option value="">${t('sch.none')}</option><option value="daily" ${p.schedule === 'daily' ? 'selected' : ''}>${t('sch.daily')}</option><option value="weekly" ${p.schedule === 'weekly' ? 'selected' : ''}>${t('sch.weekly')}</option></select></label></div></div>`).join('') : `<p class="muted">${t('hist.nopresets')}</p>`}</section>`;
  const J = id => jobs.find(j => j.id === +id), P = id => presets.find(p => p.id === +id);
  const handlers = {
    open: id => { location.hash = (TERMINAL.includes(J(id).state) ? '#/results/' : '#/live/') + id; },
    rerun: id => rerunJob(id),
    dup: id => { S.cfg = deepMerge(defaultCfg(), clone(J(id).config)); saveCfg(); location.hash = '#/source'; },
    resume: async id => { await api(`/jobs/${id}/resume`, { method: 'POST' }); location.hash = '#/live/' + id; },
    del: async id => { if (confirm(t('hist.confirm'))) { await api('/jobs/' + id, { method: 'DELETE' }); route(); } },
    pload: id => { S.cfg = deepMerge(defaultCfg(), clone(P(id).config)); saveCfg(); location.hash = '#/review'; },
    prun: async id => { const r = await api('/jobs', { method: 'POST', body: { name: P(id).name, config: P(id).config } }); location.hash = '#/live/' + r.id; },
    pdel: async id => { await api('/presets/' + id, { method: 'DELETE' }); route(); }
  };
  $$('button[data-h]', main).forEach(b => b.onclick = () => handlers[b.dataset.h](b.dataset.id).catch?.(e => toast(errMsg(e))));
  $$('select[data-h=psch]', main).forEach(s => s.onchange = () => api(`/presets/${s.dataset.id}/schedule`, { method: 'POST', body: { schedule: s.value || null } }).then(() => toast('✔')).catch(e => toast(errMsg(e))));
};

/* ---------- 11. settings ---------- */
routes.settings = async main => {
  const keys = await api('/keys');
  main.innerHTML = `<h1>${t('set.title')}</h1>
  <section class="card"><h2>${t('set.appearance')}</h2>${radio('lang', [['en', 'English', 1], ['zh-TW', '繁體中文', 1]], S.prefs.lang)}
   ${radio('theme', [['system', 'theme.system'], ['light', 'theme.light'], ['dark', 'theme.dark']], S.prefs.theme)}
   ${radio('mode', [['simple', 'mode.simple'], ['advanced', 'mode.advanced']], S.prefs.mode)}
   <label class="check"><input type="checkbox" id="notify" ${S.prefs.notify ? 'checked' : ''}><span>${t('set.notify')}</span></label></section>
  <section class="card"><h2>🔑 ${t('set.keys')}</h2><p>${t('set.keys.intro')}</p>
  ${S.meta.providers.map(p => { const k = keys[p.id]; return `<div class="cols" style="align-items:end"><div><strong>${esc(p.name)}</strong><br>${k ? `<code>${esc(k.masked)}</code> (${esc(k.source)})` : `<span class="muted">${t('api.key.none')}</span>`}</div>
   <label class="field"><span class="sr">${esc(p.name)}</span><input type="password" id="key-${p.id}" autocomplete="off" placeholder="${t('set.key.placeholder')}"></label>
   <div class="btns" style="margin:0"><button class="btn sm" data-save="${p.id}">${t('set.key.save')}</button><button class="btn ghost sm" data-del="${p.id}" ${k && k.source === 'stored' ? '' : 'disabled'}>${t('set.key.delete')}</button></div></div><hr>`; }).join('')}</section>
  <section class="card"><h2>⚖️ ${t('legal.title')}</h2><p>${t('legal.text')}</p><button class="btn ghost" id="reset">${t('set.reset')}</button></section>`;
  $$('input[name=lang]').forEach(el => el.onchange = () => setPref('lang', el.value));
  $$('input[name=theme]').forEach(el => el.onchange = () => setPref('theme', el.value));
  $$('input[name=mode]').forEach(el => el.onchange = () => setPref('mode', el.value));
  $('#notify').onchange = async e => {
    S.prefs.notify = e.target.checked;
    if (e.target.checked && 'Notification' in window && Notification.permission === 'default') await Notification.requestPermission();
    savePrefs();
  };
  $$('[data-save]', main).forEach(b => b.onclick = async () => {
    const v = $('#key-' + b.dataset.save).value.trim(); if (!v) return;
    try { await api('/keys/' + b.dataset.save, { method: 'POST', body: { key: v } }); toast(t('set.key.saved')); routes.settings(main); } catch (e) { toast(errMsg(e)); }
  });
  $$('[data-del]', main).forEach(b => b.onclick = async () => { await api('/keys/' + b.dataset.del, { method: 'DELETE' }); routes.settings(main); });
  $('#reset').onclick = () => { if (confirm(t('set.reset.confirm'))) { S.prefs.onboarded = false; S.prefs.agreed = false; savePrefs(); location.hash = '#/onboarding'; } };
};

/* ---------- init ---------- */
(async function init() {
  try {
    S.meta = await api('/meta');
    await loadLang();
    renderShell();
    window.addEventListener('hashchange', route);
    route();
  } catch (e) {
    document.body.insertAdjacentHTML('afterbegin', `<div class="alert err" role="alert">${esc(e.message)}</div>`);
  }
})();