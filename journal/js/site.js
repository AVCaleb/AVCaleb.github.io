(() => {
  'use strict';

  const fallback = document.body.dataset.fallback;
  document.querySelectorAll('img').forEach(image => {
    const recover = () => {
      if (image.dataset.recovered || !fallback || !image.getAttribute('src')) return;
      image.dataset.recovered = 'true';
      image.src = fallback;
      image.alt = `${image.alt || '图片'}（原图暂不可用，显示《拾穗者》）`;
    };
    image.addEventListener('error', recover);
    if (image.complete && image.naturalWidth === 0) recover();
  });

  document.querySelectorAll('.prose table').forEach(table => {
    if (table.closest('.highlight') || table.parentElement.classList.contains('table-scroll')) return;
    const wrapper = document.createElement('div');
    wrapper.className = 'table-scroll';
    wrapper.tabIndex = 0;
    wrapper.setAttribute('role', 'region');
    wrapper.setAttribute('aria-label', '表格，可横向滚动');
    table.before(wrapper);
    wrapper.append(table);
  });

  const toc = document.querySelector('.article-toc');
  if (toc && matchMedia('(max-width: 700px)').matches) toc.open = false;

  const viewer = document.querySelector('#image-viewer');
  if (viewer?.showModal) {
    document.querySelectorAll('.prose img').forEach(image => {
      image.addEventListener('click', () => {
        if (image.closest('a')) return;
        const enlarged = viewer.querySelector('img');
        enlarged.src = image.currentSrc || image.src;
        enlarged.alt = image.alt;
        viewer.showModal();
      });
    });
    viewer.addEventListener('click', event => {
      if (event.target === viewer) viewer.close();
    });
  }

  const search = document.querySelector('.search-page');
  if (!search) return;
  const form = search.querySelector('form');
  const input = search.querySelector('input');
  const status = search.querySelector('#search-status');
  const results = search.querySelector('#search-results');
  let indexPromise;
  let requestNumber = 0;

  async function showResults() {
    const request = ++requestNumber;
    const query = input.value.trim().slice(0, 200);
    results.replaceChildren();
    if (!query) {
      status.textContent = '输入关键词，开始检索。';
      return;
    }
    status.textContent = '正在检索文章…';
    try {
      indexPromise ||= fetch(search.dataset.index).then(response => {
        if (!response.ok) throw new Error('Search index unavailable');
        return response.json();
      });
      const index = await indexPromise;
      if (request !== requestNumber) return;
      const terms = query.toLocaleLowerCase().split(/\s+/).filter(Boolean);
      const matches = index.map(entry => {
        const title = entry.title.toLocaleLowerCase();
        const tags = entry.tags.join(' ').toLocaleLowerCase();
        const text = entry.text.toLocaleLowerCase();
        const combined = `${title} ${tags} ${text}`;
        if (!terms.every(term => combined.includes(term))) return null;
        return { entry, score: terms.reduce((score, term) => score + (title.includes(term) ? 6 : 0) + (tags.includes(term) ? 3 : 0) + (text.includes(term) ? 1 : 0), 0) };
      }).filter(Boolean).sort((a, b) => b.score - a.score);
      status.textContent = matches.length ? `“${query}” · 找到 ${matches.length} 篇文章` : `没有找到“${query}”。试试更短的关键词，或从分类与归档继续查找。`;
      const fragment = document.createDocumentFragment();
      matches.forEach(({ entry }) => {
        const destination = new URL(entry.path, new URL(search.dataset.base, location.origin));
        if (destination.origin !== location.origin) return;
        const article = document.createElement('article');
        article.className = 'search-result';
        const heading = document.createElement('h2');
        const link = document.createElement('a');
        link.href = destination.href;
        link.textContent = entry.title;
        heading.append(link);
        const summary = document.createElement('p');
        const firstMatch = Math.max(0, entry.text.toLocaleLowerCase().indexOf(terms[0]));
        const start = Math.max(0, firstMatch - 30);
        summary.textContent = `${start ? '…' : ''}${entry.text.slice(start, start + 160)}${entry.text.length > start + 160 ? '…' : ''}`;
        article.append(heading, summary);
        if (entry.tags.length) {
          const labels = document.createElement('p');
          labels.className = 'result-tags';
          labels.textContent = entry.tags.join(' · ');
          article.append(labels);
        }
        fragment.append(article);
      });
      results.append(fragment);
    } catch {
      indexPromise = undefined;
      if (request === requestNumber) status.textContent = '暂时无法加载文章索引，请重新搜索，或从归档继续阅读。';
    }
  }

  form.addEventListener('submit', event => {
    event.preventDefault();
    const url = new URL(location.href);
    const query = input.value.trim().slice(0, 200);
    if (query) url.searchParams.set('q', query);
    else url.searchParams.delete('q');
    history.pushState({}, '', url);
    void showResults();
  });
  function fromLocation() {
    input.value = (new URLSearchParams(location.search).get('q') || '').slice(0, 200);
    void showResults();
  }
  addEventListener('popstate', fromLocation);
  fromLocation();
})();
