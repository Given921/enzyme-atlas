const sourceOrder = ['全部', 'Nature 正刊', 'Science 正刊', 'Cell 正刊', 'Nature 子刊', '其他精选'];
const countNode = document.getElementById('classicCount');
const gridNode = document.getElementById('classicGrid');
const statsNode = document.getElementById('classicSourceStats');
const filtersNode = document.getElementById('classicFilters');

let classics = [];
let activeSource = '全部';

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

function doiUrl(doi) {
  return `https://doi.org/${encodeURI(doi)}`;
}

function renderStats() {
  const counts = Object.fromEntries(sourceOrder.slice(1).map(source => [
    source,
    classics.filter(item => item.sourceGroup === source).length
  ]));
  statsNode.innerHTML = sourceOrder.slice(1).map(source => `
    <div class="classic-source-stat">
      <strong>${counts[source]}</strong>
      <span>${escapeHtml(source)}</span>
    </div>
  `).join('');
}

function renderFilters() {
  filtersNode.innerHTML = sourceOrder.map(source => {
    const selected = source === activeSource;
    return `<button type="button" class="classic-filter${selected ? ' active' : ''}" data-source="${escapeHtml(source)}" aria-pressed="${selected}">${escapeHtml(source)}</button>`;
  }).join('');
}

function renderGrid() {
  const visible = activeSource === '全部'
    ? classics
    : classics.filter(item => item.sourceGroup === activeSource);
  const topicCount = new Set(visible.map(item => item.topic)).size;
  countNode.innerHTML = activeSource === '全部'
    ? `共整理 <strong>${classics.length}</strong> 篇 · 覆盖 ${topicCount} 条阅读路径 · 每篇均有 DOI / 出版社入口`
    : `${escapeHtml(activeSource)} <strong>${visible.length}</strong> 篇 · 覆盖 ${topicCount} 条阅读路径`;
  gridNode.innerHTML = visible.map(item => `
    <article class="classic-card">
      <div class="classic-meta"><span>${escapeHtml(item.topic)}</span><span>${item.year}</span></div>
      <div class="classic-badges"><span class="source-badge">${escapeHtml(item.sourceGroup)}</span><span>${escapeHtml(item.kind)}</span></div>
      <h2>${escapeHtml(item.title)}</h2>
      <p class="classic-note">${escapeHtml(item.note)}</p>
      <div class="classic-bottom">
        <div class="classic-citation">${escapeHtml(item.authors)} · ${escapeHtml(item.journal)}</div>
        <a href="${doiUrl(item.doi)}" target="_blank" rel="noopener">打开 DOI / 出版社页面 ↗</a>
      </div>
    </article>
  `).join('');
}

filtersNode.addEventListener('click', event => {
  const button = event.target.closest('button[data-source]');
  if (!button) return;
  activeSource = button.dataset.source;
  renderFilters();
  renderGrid();
});

fetch('data/classics.json')
  .then(response => {
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  })
  .then(data => {
    classics = data.items;
    renderStats();
    renderFilters();
    renderGrid();
  })
  .catch(error => {
    console.error('经典论文载入失败', error);
    countNode.textContent = '经典论文暂时无法载入，请稍后刷新。';
  });
