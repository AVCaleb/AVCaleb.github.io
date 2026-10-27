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
  let category = '全部', activeProduct = null, toastTimer;
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
    const savedOnly = document.querySelector('#saved-only').checked;
    let count = 0;
    cards.forEach(card => {
      const p = byId.get(card.dataset.id);
      const haystack = [p.id, p.name, p.brand, p.category, p.keyword, p.color, p.buyer, p.season, p.reason].join(' ').toLowerCase();
      const visible = (category === '全部' || p.category === category) && (!recommended || p.recommended) && (!savedOnly || favorites.has(p.id)) && (!query || haystack.includes(query));
      card.hidden = !visible; if (visible) count++;
    });
    document.querySelector('#result-count').textContent = `${count} 款${recommended ? ' · 首批候选' : savedOnly ? ' · 我的备选' : ' · 可点图片看详情'}`;
    document.querySelector('#empty-state').hidden = count > 0;
    document.querySelector('#share-selection').hidden = !favorites.size;
  }
  function resetFilters() {
    category = '全部'; document.querySelector('#search').value = '';
    document.querySelector('#recommended-only').checked = false; document.querySelector('#saved-only').checked = false;
    document.querySelectorAll('[data-category]').forEach(button => { const active = button.dataset.category === category; button.classList.toggle('active', active); button.setAttribute('aria-pressed', String(active)); });
  }
  function openProduct(id) {
    const p = byId.get(id); if (!p) return;
    activeProduct = p;
    document.querySelector('#dialog-title').textContent = `款式 ${p.id} · ${p.brand}`;
    document.querySelector('#dialog-content').innerHTML = `
      <div class="dialog-image"><img src="${escape(p.image)}" alt="${escape(p.name)}，${escape(p.color)}，${escape(p.brand)} 品牌参考图"></div>
      <div class="dialog-info">
        <div class="eyebrow">${escape(p.category)} / ${escape(p.season)}</div>
        <h2 id="detail-name">${escape(p.name)}</h2>
        <div class="product-price">${price(p)}</div>
        <p class="price-context">${escape(p.brand)} ${escape(p.market)}零售参考价 · ${escape(p.checkedAt)} 核查<br>价格随促销与尺码变化，实际以品牌原页及结算为准。</p>
        <div class="info-block"><h3>这款看什么</h3><p>${escape(p.reason)}</p></div>
        <div class="info-block"><h3>适合卖给谁</h3><p>${escape(p.buyer)} · ${escape(p.season)}</p></div>
        <div class="info-block"><h3>参考材质与颜色</h3><p>${escape(p.material)}<br>图示颜色：${escape(p.color)}。国内样衣需重新核实成分和实际尺寸。</p></div>
        <div class="info-block"><h3>拿样先问清</h3><p>${escape(p.caution)}</p></div>
        <div class="info-block"><h3>英文找款词</h3><p class="english-keyword">${escape(p.keyword)}</p></div>
        <div class="info-block"><h3>选入依据</h3><p>${escape(p.evidence)}。<a href="${escape(p.evidenceUrl)}" target="_blank" rel="noopener noreferrer" style="text-decoration:underline">查看畅销专区 ↗</a></p></div>
        <div class="dialog-buttons"><a class="button" href="${escape(p.source)}" target="_blank" rel="noopener noreferrer">品牌原页 ↗</a><button class="button secondary dialog-save" type="button">记下这款</button><button class="button secondary copy-keyword" type="button">复制找款词</button></div>
      </div>`;
    document.querySelector('.dialog-save').addEventListener('click', () => toggleFavorite(id));
    document.querySelector('.copy-keyword').addEventListener('click', () => copyText(p.keyword, '英文找款词已复制'));
    updateFavorites();
    if (!dialog.open) dialog.showModal();
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
  document.querySelector('#saved-only').addEventListener('change', filter);
  document.querySelectorAll('[data-open]').forEach(button => button.addEventListener('click', () => openProduct(button.dataset.open)));
  document.querySelectorAll('[data-favorite]').forEach(button => button.addEventListener('click', () => toggleFavorite(button.dataset.favorite)));
  document.querySelector('#reset-filters').addEventListener('click', () => { resetFilters(); filter(); });
  document.querySelector('#show-recommended').addEventListener('click', () => { resetFilters(); document.querySelector('#recommended-only').checked = true; filter(); document.querySelector('#catalog').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); });
  document.querySelector('#show-saved').addEventListener('click', () => { resetFilters(); document.querySelector('#saved-only').checked = true; filter(); document.querySelector('#catalog').scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'instant':'smooth'}); });
  document.querySelector('#share-selection').addEventListener('click', () => { const url = new URL(location.href); url.search = ''; url.hash = 'catalog'; url.searchParams.set('pick', [...favorites].sort().join(',')); copyText(url.href, '备选清单链接已复制，可以发给家人'); });
  document.querySelector('#close-dialog').addEventListener('click', () => dialog.close());
  dialog.addEventListener('click', event => { if (event.target === dialog) { const r = dialog.getBoundingClientRect(); if (event.clientX < r.left || event.clientX > r.right || event.clientY < r.top || event.clientY > r.bottom) dialog.close(); } });
  dialog.addEventListener('close', () => { document.body.style.overflow = ''; activeProduct = null; });
  if (sharedPicks && favorites.size) document.querySelector('#saved-only').checked = true;
  updateFavorites(); filter();
})();
