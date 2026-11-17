'use strict';
/* Index-crawl UI. Loaded BEFORE app.js; it only uses app.js globals ($, S, api, t, esc, forms ...) at call time. */

const IDX_LIGHT = { high: 'green', low: 'yellow', none: 'red' };
const IDX_DOT = { high: '🟢', low: '🟡', none: '🔴' };

function indexBody(f, c) {
  const n = (p, l, o) => f.inp(p, l, { type: 'number', ...o });
  const sc = S.scan, pg = sc && sc.pagination;
  const badge = pg ? `<div class="light ${IDX_LIGHT[pg.confidence] || 'yellow'}"><span class="dot" aria-hidden="true">${IDX_DOT[pg.confidence] || '🟡'}</span><strong>${t('idx.det.' + pg.kind)}</strong><span>${t('idx.conf.' + pg.confidence)}</span></div>` : '';
  const sugg = sc && sc.patterns.length
    ? `<div class="btns">${sc.patterns.map((p, i) => `<button class="btn ghost sm pat" data-pat="${i}" title="${esc(p.samples.join('\n'))}">${esc(p.pattern)} <span class="muted">(${p.count})</span></button>`).join('')}</div>` : '';
  return `<div class="card"><h2>📑 ${t('mode.index')}</h2><p class="muted">${t('idx.intro')}</p>
    ${f.inp('index.url', 'idx.url', { hint: 'idx.url.hint', ph: 'https://www.bbc.com/pages/content-index/2026/11/01', auto: 'url' })}
    <button class="btn" id="idxScan">🔍 ${t('idx.analyze')}</button> <span id="idxScanOut" role="status">${sc ? esc(t('idx.scanned', { n: sc.link_count })) : ''}</span></div>
  <div class="card"><h2>1️⃣ ${t('idx.pages.title')}</h2>${badge}<p class="muted">${t('idx.pages.hint')}</p>
    ${f.inp('index.page_template', 'idx.template', { hint: 'idx.template.hint', ph: 'https://example.com/list?page={n}' })}
    <div class="cols">${n('index.page_start', 'idx.start', { min: 0 })}${n('index.page_end', 'idx.end', { min: 1 })}${n('index.page_step', 'idx.step', { min: 1, cls: 'adv-only' })}${n('index.stop_empty', 'idx.stop_empty', { min: 0, hint: 'idx.stop_empty.hint' })}</div>
    ${f.inp('index.include_first', 'idx.first', { type: 'checkbox' })}${f.inp('index.follow_next', 'idx.follow', { type: 'checkbox' })}
    <div id="idxPages" aria-live="polite"></div></div>
  <div class="card"><h2>2️⃣ ${t('idx.pattern.title')}</h2><p class="muted">${t('idx.pattern.hint')}</p>${sugg}
    ${f.inp('index.link_pattern', 'idx.pattern', { ph: '/news/articles/[A-Za-z0-9]+$' })}
    <div id="idxTest" aria-live="polite"></div></div>`;
}

function wireIndex(main) {
  const c = S.cfg, ix = c.index;
  const pagesOut = $('#idxPages'), testOut = $('#idxTest');
  const li = u => `<li><code>${esc(u)}</code></li>`;

  const refreshPages = async () => {
    if (!(ix.url || '').trim()) { pagesOut.textContent = ''; return; }
    try {
      const r = await api('/index/pages', { method: 'POST', body: ix });
      const list = r.first.map(li).join('') + (r.last.length ? '<li>…</li>' + r.last.map(li).join('') : '');
      pagesOut.innerHTML = `<p><strong>${ix.follow_next ? t('idx.pages.follow', { n: r.count }) : t('idx.pages.count', { n: r.count })}</strong></p><ul class="samples">${list}</ul>`;
    } catch (e) { pagesOut.innerHTML = `<div class="alert err" role="alert">${esc(errMsg(e))}</div>`; }
  };
  const refreshTest = async () => {
    if (!S.scan) { testOut.innerHTML = `<p class="muted">${t('idx.test.need')}</p>`; return; }
    try {
      const r = await api('/index/test', { method: 'POST', body: { pattern: ix.link_pattern, links: S.scan.links } });
      testOut.innerHTML = `<div class="light ${r.count ? 'green' : 'yellow'}"><strong>${t('idx.test.result', { n: r.count, total: r.total })}</strong>${r.count ? '' : `<span>${t('idx.test.zero')}</span>`}</div><ul class="samples">${r.samples.map(li).join('')}</ul>`;
    } catch (e) { testOut.innerHTML = `<div class="alert err" role="alert">${esc(errMsg(e))}</div>`; }
  };
  const dPages = debounce(refreshPages, 300), dTest = debounce(refreshTest, 300);

  $('#idxScan').onclick = async () => {
    const btn = $('#idxScan');
    btn.disabled = true; $('#idxScanOut').textContent = t('loading');
    try {
      const r = await api('/index/analyze', { method: 'POST', body: { url: ix.url } });
      S.scan = r;
      const p = r.pagination;
      Object.assign(ix, { url: r.url, page_template: p.template, page_start: p.start, page_end: p.end, page_step: p.step, include_first: p.include_first, follow_next: p.follow_next });
      if (r.patterns[0]) ix.link_pattern = r.patterns[0].pattern;
      saveCfg();
      routes.source(main);
    } catch (e) { toast(errMsg(e)); btn.disabled = false; $('#idxScanOut').textContent = ''; }
  };

  $$('[data-pat]', main).forEach(b => b.onclick = () => {
    ix.link_pattern = S.scan.patterns[+b.dataset.pat].pattern; saveCfg();
    $('[data-bind="index.link_pattern"]').value = ix.link_pattern;
    refreshTest();
  });

  $$('[data-bind^="index."]', main).forEach(el => el.addEventListener(el.type === 'checkbox' ? 'change' : 'input', () => {
    const k = el.dataset.bind;
    if (k === 'index.url') { S.scan = null; dTest(); }
    if (k === 'index.link_pattern') dTest(); else dPages();
  }));

  refreshPages();
  refreshTest();
}