let papers = [];
let editionObservations = [];
const paperDialog = document.getElementById('paperDialog');
const subscribeDialog = document.getElementById('subscribeDialog');
const savedDialog = document.getElementById('savedDialog');
const storageKey = 'enzyme-atlas-reading-state';
const state = { saved: [], later: [], read: [], hidden: [], subscriptions: [], ...JSON.parse(localStorage.getItem(storageKey) || '{}') };
const unique = values => [...new Set(values)];
const paper = id => papers.find(item => item.id === id);
const isActive = (id, kind) => state[kind].includes(id);
const typeLabel = type => ({ review: '综述', perspective: '观点', original: '原创研究' }[type] || '论文');

function persist() {
  ['saved', 'later', 'read', 'hidden', 'subscriptions'].forEach(key => state[key] = unique(state[key] || []));
  localStorage.setItem(storageKey, JSON.stringify(state));
  document.getElementById('savedBadge').textContent = state.saved.length + state.later.length;
}

function move(id, kind) {
  const alreadyActive = kind !== 'clear' && isActive(id, kind);
  ['saved', 'later', 'read', 'hidden'].forEach(key => state[key] = state[key].filter(item => item !== id));
  if (kind !== 'clear' && !alreadyActive) state[kind].push(id);
  persist();
  renderAll();
}

function labels(item) { return item.labels.map(label => `<span class="recommend-label">${label}</span>`).join(''); }

function actionButtons(item, compact = false) {
  return [`<button class="action-button ${isActive(item.id, 'saved') ? 'active' : ''}" onclick="move('${item.id}','saved')">${isActive(item.id, 'saved') ? '已收藏' : '收藏'}</button>`, `<button class="action-button ${isActive(item.id, 'later') ? 'active' : ''}" onclick="move('${item.id}','later')">${isActive(item.id, 'later') ? '已加入' : '稍后读'}</button>`, compact ? '' : `<button class="action-button ${isActive(item.id, 'read') ? 'active' : ''}" onclick="move('${item.id}','read')">${isActive(item.id, 'read') ? '已读' : '标为已读'}</button>`].join('');
}

function featureCard(item) {
  const type = typeLabel(item.type);
  return `<article class="feature-card"><div class="card-meta"><span>${item.topic} · ${type}</span><span>${item.minutes} 分钟</span></div><h3>${item.cn}</h3><p class="card-summary">${item.summary}</p><p class="card-why"><b>推荐理由</b>${item.why}</p><div class="card-labels">${labels(item)}</div><p class="card-audience">适合：${item.audience}</p><div class="card-actions"><span><button class="read-link" onclick="openPaper('${item.id}')">快速扫读</button><a class="source-link" href="${item.url}" target="_blank" rel="noopener">DOI / 原文 ↗</a></span><button class="save-btn ${isActive(item.id, 'saved') ? 'saved' : ''}" aria-label="${isActive(item.id, 'saved') ? '取消收藏' : '收藏'}" onclick="move('${item.id}','saved')">${isActive(item.id, 'saved') ? '★' : '☆'}</button></div></article>`;
}

function renderEdition(data) {
  const featuredCount = papers.filter(item => item.featured).length;
  document.getElementById('editionDate').textContent = `第 01 期 · ${data.updatedAt.replaceAll('-', '.')}`;
  document.getElementById('editionSummary').innerHTML = `<strong>${papers.length}</strong> 篇完整收录 <i></i> <strong>${featuredCount}</strong> 篇编辑精选 <i></i> 覆盖 ${data.periodStart.slice(5).replace('-', '.')}–${data.periodEnd.slice(5).replace('-', '.')}`;
  document.getElementById('featuredTitle').textContent = `本周最值得读的 ${featuredCount} 篇`;
}

function renderFeatured() { document.getElementById('featuredGrid').innerHTML = papers.filter(item => item.featured).slice(0, 5).map(featureCard).join(''); }

function renderObservations() {
  const items = editionObservations.length ? editionObservations : [['本期重点', '正在整理本期研究脉络。'], ['证据边界', '正在核验推荐论文的证据层级。'], ['栏目覆盖', '正在核对各研究专题的本期覆盖情况。']];
  document.getElementById('observationGrid').innerHTML = items.map((item, index) => `<article><span>0${index + 1}</span><h3>${item[0]}</h3><p>${item[1]}</p></article>`).join('');
}

function renderPapers() {
  const list = [...papers].filter(item => !state.hidden.includes(item.id)).sort((a, b) => b.date.localeCompare(a.date));
  document.getElementById('resultCount').innerHTML = `<strong>${papers.length}</strong> 篇真实 DOI 文献 · 当前显示 ${list.length} 篇 · 已隐藏 ${state.hidden.length} 篇`;
  document.getElementById('paperList').innerHTML = list.map(item => `<article class="paper-row"><span class="paper-date">${item.date}</span><div class="paper-main"><a class="paper-title paper-title-link" href="${item.url}" target="_blank" rel="noopener">${item.cn} ↗</a><div class="paper-sub">${item.authors} · ${item.journal}</div><div class="row-labels"><span class="topic-label">${item.topic}</span>${labels(item)}</div></div><div class="paper-score"><b>${item.minutes}</b><span>分钟扫读</span></div><div class="read-state">${actionButtons(item, true)}<button class="muted-button" onclick="move('${item.id}','hidden')">隐藏</button></div></article>`).join('') || '<p class="empty-state">当前没有可显示的收录文献。可在阅读清单中恢复已隐藏条目。</p>';
}

function openPaper(id) {
  const item = paper(id);
  document.getElementById('dialogContent').innerHTML = `<div class="modal-copy quick-card"><p class="eyebrow">${item.topic} · ${typeLabel(item.type)} · ${item.minutes} 分钟扫读</p><h2>${item.cn}</h2><p class="detail-meta">${item.title}<br>${item.authors} · ${item.journal} · ${item.date}</p><div class="quick-grid"><div><h3>一句话结论</h3><p>${item.summary}</p></div><div><h3>为什么进入精选</h3><p>${item.why}</p></div><div><h3>关键证据</h3><p>${item.evidence}</p></div><div><h3>适合谁读</h3><p>${item.audience}</p></div></div><p class="verification-note"><b>来源核验</b>${item.verification}</p><div class="detail-actions">${actionButtons(item)}<a class="primary-button" href="${item.url}" target="_blank" rel="noopener">打开 DOI / 原文 ↗</a></div></div>`;
  paperDialog.showModal();
}

function bib(item) { return `@article{${item.id},\n  title={${item.title}},\n  author={${item.authors}},\n  journal={${item.journal}},\n  year={${item.date.slice(0, 4)}},\n  doi={${item.doi}},\n  url={${item.url}}\n}`; }

function exportSaved() {
  const records = state.saved.map(paper).filter(Boolean);
  if (!records.length) { document.getElementById('savedList').insertAdjacentHTML('afterbegin', '<p class="form-note">请先收藏至少一篇文献。</p>'); return; }
  const blob = new Blob([records.map(bib).join('\n\n')], { type: 'application/x-bibtex' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'enzyme-atlas-reading-list.bib';
  link.click();
  URL.revokeObjectURL(link.href);
}

function readingSection(label, key) {
  const records = state[key].map(paper).filter(Boolean);
  return `<section class="reading-section"><h3>${label} <small>${records.length}</small></h3>${records.length ? records.map(item => `<div class="saved-item"><span><b>${item.cn}</b><small>${item.journal} · ${item.date}</small></span><span><a href="${item.url}" target="_blank" rel="noopener">DOI ↗</a><button onclick="move('${item.id}','clear')">移除</button></span></div>`).join('') : '<p>暂无条目。</p>'}</section>`;
}

function renderSaved() { document.getElementById('savedList').innerHTML = `<button class="export-button" onclick="exportSaved()">导出收藏为 BibTeX</button>${readingSection('收藏', 'saved')}${readingSection('稍后读', 'later')}${readingSection('已读', 'read')}${readingSection('已隐藏', 'hidden')}`; }

function renderSubscriptionTopics() {
  const topics = unique(papers.map(item => item.topic));
  document.getElementById('subscriptionTopics').innerHTML = topics.map(topic => `<label class="topic-check"><input type="checkbox" value="${topic}" ${state.subscriptions.includes(topic) ? 'checked' : ''}> ${topic}</label>`).join('');
}

function renderAll() { renderFeatured(); renderObservations(); renderPapers(); renderSaved(); persist(); }

async function init() {
  try {
    const response = await fetch('data/papers.json');
    if (!response.ok) throw new Error('data unavailable');
    const data = await response.json();
    papers = data.items;
    editionObservations = data.observations || [];
    renderEdition(data);
  } catch (error) {
    document.getElementById('resultCount').textContent = '文献数据未能载入，请确认本地服务器正在运行。';
    return;
  }
  renderSubscriptionTopics();
  renderAll();
}

document.getElementById('subscribeBtn').onclick = () => { renderSubscriptionTopics(); subscribeDialog.showModal(); };
document.getElementById('confirmSubscribe').onclick = () => {
  const email = document.getElementById('emailInput');
  state.subscriptions = [...document.querySelectorAll('#subscriptionTopics input:checked')].map(input => input.value);
  persist();
  document.getElementById('subscribeNote').textContent = email.checkValidity() ? '订阅偏好已保存：每周一发送，且不会改变公共推荐排序。' : '请输入有效的邮箱地址。';
};
document.getElementById('openSaved').onclick = () => { renderSaved(); savedDialog.showModal(); };
init();
