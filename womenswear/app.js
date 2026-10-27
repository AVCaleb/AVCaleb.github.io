(() => {
  'use strict';
  const products = JSON.parse(document.querySelector('#catalog-data').textContent);
  const byId = new Map(products.map(p => [p.id, p]));
  const cards = [...document.querySelectorAll('.product')];
  const dialog = document.querySelector('#product-dialog');
  const storageKey = 'womenswear-edit-2026-10-favorites';
  let favorites = new Set();
  try { favorites = new Set(JSON.parse(localStorage.getItem(storageKey) || '[]').filter(id => byId.has(id))); } catch { /* Browsing remains available without storage. */ }
  const sharedPicks = new URLSearchParams(location.search).get('pick');
  if (sharedPicks) sharedPicks.split(',').filter(id => byId.has(id)).forEach(id => favorites.add(id));
  let scope = 'active', category = '全部', activeProduct = null, toastTimer;
  const escape = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const unit = p => p.currency === 'USD' ? '美元' : '澳元';
  const price = p => `<span>${p.price.toFixed(2)}<span class="unit">${unit(p)}</span></span>${p.originalPrice ? `<del>${p.originalPrice.toFixed(2)}</del>` : ''}`;

  function notify(message) {
    const el = document.querySelector('#toast');
    el.textContent = message; el.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => { el.hidden = true; }, 2400);
  }
  function updateFavorites() {
    document.querySelectorAll('[data-favorite]').forEach(button => {
      const saved = favorites.has(button.dataset.favorite);
      button.setAttribute('aria-pressed', String(saved));
      button.setAttribute('aria-label', `${saved ? '取消记下' : '记下'}${byId.get(button.dataset.favorite).name}`);
    });
    document.querySelector('#saved-count').textContent = String(favorites.size);
    document.querySelector('#share-selection').hidden = !favorites.size;
    if (activeProduct) {
      const button = document.querySelector('.dialog-save');
      if (button) { button.classList.toggle('active', favorites.has(activeProduct.id)); button.textContent = favorites.has(activeProduct.id) ? '已记下这款 ✓' : '记下这款'; button.setAttribute('aria-pressed', String(favorites.has(activeProduct.id))); }
    }
    try { localStorage.setItem(storageKey, JSON.stringify([...favorites])); } catch { /* No persistent storage required. */ }
  }
  function filter() {
    const query = document.querySelector('#search').value.trim().toLowerCase();
    const recommended = document.querySelector('#recommended-only').checked;
    const segment = document.querySelector('#segment-filter').value;
    const savedOnly = document.querySelector('#saved-only').checked;
    let count = 0;
    cards.forEach(card => {
      const p = byId.get(card.dataset.id);
      const haystack = [p.id, p.name, p.brand, p.category, p.keyword, p.color, p.buyer, p.season, p.reason].join(' ').toLowerCase();
      const visible = (scope === 'all' || (scope === 'archive' ? p.archived : !p.archived)) && (segment === 'all' || p.segment === segment) && (category === '全部' || p.category === category) && (!recommended || p.dual) && (!savedOnly || favorites.has(p.id)) && (!query || haystack.includes(query));
      card.hidden = !visible; if (visible) count++;
    });
    document.querySelector('#result-count').textContent = `${count} 款${recommended ? ' · 双渠道同类线索' : savedOnly ? ' · 我的备选' : scope === 'archive' ? ' · 仅留风格参考' : ' · 点击看证据'}`;
    document.querySelector('#empty-state').hidden = count > 0;
    document.querySelector('#share-selection').hidden = !favorites.size;
  }
  function resetFilters() {
    setScope('active'); category = '全部'; document.querySelector('#segment-filter').value = 'all'; document.querySelector('#search').value = '';
    document.querySelector('#recommended-only').checked = false; document.querySelector('#saved-only').checked = false;
    document.querySelectorAll('[data-category]').forEach(button => { const active = button.dataset.category === category; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); });
  }
  function setScope(value) {
    scope = value;
    document.querySelectorAll('[data-scope]').forEach(b => { const on = b.dataset.scope === value; b.classList.toggle('active', on); b.setAttribute('aria-pressed', String(on)); });
  }
  function snapshot(c) {
    if (c.platform.startsWith('TikTok')) return c.source.includes('/store/') ? 'evidence/tiktok-store.json' : 'evidence/tiktok-details.json';
    if ((c.source || '').includes('0a32d0a2')) return 'evidence/amazon-cardigans.json';
    if ((c.source || '').includes('2f0735a3')) return 'evidence/amazon-summer.json';
    return 'evidence/amazon-autumn.json';
  }
  function channelEvidence(c) {
    const isAmazon = c.platform.startsWith('Amazon');
    return `<section class="channel-box${isAmazon && !c.comparable ? ' near' : ''}">
      <div class="channel-head"><span>${escape(c.platform)}</span><span>${isAmazon ? (c.comparable ? '同类版型线索' : '匹配／数据待补') : '图示参考商品'}</span></div>
      <div class="channel-number">${escape(c.value || '未取得')}<small>${c.price !== null ? `USD ${Number(c.price).toFixed(2)}` : '价格未取得'}</small></div>
      <p>${escape(c.metric)} · ${escape(c.period)}<br>${escape(c.method)}<br>核查：${escape(c.observedAt)} · 商品 ID：${escape(c.id || '未核到')}</p>
      ${c.title ? `<p>${escape(c.title)}</p>` : ''}${c.match ? `<p><b>可比边界：</b>${escape(c.match)}</p>` : ''}
      <div class="channel-links">${c.url ? `<a href="${escape(c.url)}" target="_blank" rel="noopener noreferrer">商品原页 ↗</a>` : ''}${c.source ? `<a href="${escape(c.source)}" target="_blank" rel="noopener noreferrer">观察来源 ↗</a>` : ''}${c.value ? `<a href="${snapshot(c)}" target="_blank" rel="noopener noreferrer">保存的观察记录 ↗</a>` : ''}</div>
    </section>`;
  }
  function monthlyEvidence(p) {
    return `<div class="monthly-detail"><strong>逐月验证：未完成</strong><p>2025-10 至 2026-09，两个渠道均未取得可用的完整自然月销量。近月徽标与累计数均未填入月度格子。</p><details><summary>展开 12 个月的数据状态</summary><table class="monthly-mini"><thead><tr><th scope="col">自然月</th><th scope="col">Amazon</th><th scope="col">TikTok</th></tr></thead><tbody>${p.monthly.map(m => `<tr><th scope="row">${escape(m.month)}</th><td>未取得</td><td>未取得</td></tr>`).join('')}</tbody></table></details></div>`;
  }
  function openProduct(id) {
    const p = byId.get(id); if (!p) return;
    activeProduct = p;
    document.querySelector('#dialog-title').textContent = `款式 ${p.id} · ${p.archived ? '原参考档案' : '证据与客群'}`;
    const evidence = p.archived ? `<div class="archive-callout">已移出本轮候选：只有品牌风格／畅销专区线索，没有商品销售记录。原编号保留，避免旧备选链接指向别的衣服。</div>` : `<span class="detail-tag">${escape(p.decision)} · ${p.dual ? '双渠道同类线索' : '匹配／数据待补'}</span><div class="detail-channels">${p.channels.map(channelEvidence).join('')}</div><p class="evidence-footnote">两个市场的商品 ID 不同，未确认同一货号。数字保留各自口径，不相加；价格可能对应不同颜色、尺码、促销与运费条件。</p>${monthlyEvidence(p)}`;
    document.querySelector('#dialog-content').innerHTML = `
      <div class="dialog-image"><img src="${escape(p.image)}" alt="${escape(p.name)}，${escape(p.brand)} 参考图"></div>
      <div class="dialog-info"><div class="eyebrow">${escape(p.category)} / ${escape(p.season)}</div><h2 id="detail-name">${escape(p.name)}</h2>
        ${p.archived ? `<div class="product-price">${price(p)}</div><p class="price-context">原 ${escape(p.brand)} ${escape(p.market)}零售参考价 · ${escape(p.checkedAt)} 核查</p>` : ''}
        ${evidence}
        <div class="info-block"><h3>这个方向怎样处理</h3><p>${escape(p.decisionReason)}</p></div>
        <div class="info-block"><h3>卖给谁 · 定位假设</h3><p>${p.archived ? escape(p.buyer) : p.segment === 'A' ? '客群 A：先访谈 28—45 岁、需要办公室叠穿的女性；核心是常规衣长、不透与活动量。先接触已有基础针织／通勤系列、能处理进口的小型女装店。年龄与需求尚未由买家数据证实。' : '客群 B：先访谈 35—55 岁、关注腰臀活动空间与穿搭便利的女性；重点是松紧腰、宽松上衣和舒适套装。先接触现有 comfort／relaxed fit 系列的店主。年龄与需求尚未由买家数据证实。'}</p></div>
        <div class="info-block"><h3>拿样与改款重点</h3><p>${escape(p.caution)}</p></div>
        <div class="info-block"><h3>图片、材质与采购边界</h3><p>图示品牌：${escape(p.brand)}，图片来自对应商品页。${escape(p.material)} 国内供货、可售尺码、成本和返单能力尚未核实。</p></div>
        <div class="info-block"><h3>英文找款词</h3><p class="english-keyword">${escape(p.keyword)}</p></div>
        <div class="dialog-buttons"><a class="button" href="${escape(p.source)}" target="_blank" rel="noopener noreferrer">参考商品原页 ↗</a><button class="button secondary dialog-save" type="button">记下这款</button><button class="button secondary copy-keyword" type="button">复制找款词</button></div>
      </div>`;
    document.querySelector('.dialog-save').addEventListener('click', () => toggleFavorite(id));
    document.querySelector('.copy-keyword').addEventListener('click', () => copyText(p.keyword, '英文找款词已复制'));
    updateFavorites();
    if (!dialog.open) dialog.showModal();
    dialog.scrollTop = 0;
    document.body.style.overflow = 'hidden';
  }
  function toggleFavorite(id) { if (favorites.has(id)) favorites.delete(id); else favorites.add(id); updateFavorites(); filter(); }
  async function copyText(value, message) {
    try { await navigator.clipboard.writeText(value); notify(message); }
    catch { const input = document.createElement('textarea'); input.value = value; input.style.position = 'fixed'; input.style.opacity = '0'; document.body.append(input); input.select(); const copied = document.execCommand('copy'); input.remove(); notify(copied ? message : '当前浏览器不支持复制，请手动复制链接'); }
  }
  document.querySelectorAll('[data-category]').forEach(button => button.addEventListener('click', () => {
    category = button.dataset.category;
    document.querySelectorAll('[data-category]').forEach(b => { const active = b === button; b.classList.toggle('active', active); b.setAttribute('aria-pressed', String(active)); });
    filter();
  }));
  document.querySelector('#search').addEventListener('input', filter);
  document.querySelector('#recommended-only').addEventListener('change', filter);
  document.querySelector('#segment-filter').addEventListener('change', filter);
  document.querySelectorAll('[data-scope]').forEach(b => b.addEventListener('click', () => { setScope(b.dataset.scope); document.querySelector('#segment-filter').value = 'all'; document.querySelector('#recommended-only').checked = false; filter(); }));
  document.querySelectorAll('[data-segment-pick]').forEach(b => b.addEventListener('click', () => { resetFilters(); document.querySelector('#segment-filter').value = b.dataset.segmentPick; filter(); document.querySelector('#catalog').scrollIntoView({behavior: 'smooth'}); }));
  document.querySelector('#saved-only').addEventListener('change', filter);
  document.querySelectorAll('[data-open]').forEach(button => button.addEventListener('click', () => openProduct(button.dataset.open)));
  document.querySelectorAll('[data-favorite]').forEach(button => button.addEventListener('click', () => toggleFavorite(button.dataset.favorite)));
  document.querySelector('#reset-filters').addEventListener('click', () => { resetFilters(); filter(); });
  document.querySelector('#show-recommended').addEventListener('click', () => { resetFilters(); document.querySelector('#recommended-only').checked = true; filter(); document.querySelector('#catalog').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); });
  document.querySelector('#show-saved').addEventListener('click', () => { resetFilters(); setScope('all'); document.querySelector('#saved-only').checked = true; filter(); document.querySelector('#catalog').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); });
  document.querySelector('#share-selection').addEventListener('click', () => { const url = new URL(location.href); url.search = ''; url.hash = 'catalog'; url.searchParams.set('pick', [...favorites].sort().join(',')); copyText(url.href, '备选清单链接已复制，可以发给家人'); });
  document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
  dialog.addEventListener('close', () => { document.body.style.overflow = ''; activeProduct = null; });
  if (sharedPicks && favorites.size) { setScope('all'); document.querySelector('#saved-only').checked = true; }
  updateFavorites(); filter();
})();
