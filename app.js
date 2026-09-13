let papers = [];
let editionObservations = [];
let currentEdition = null;
let editionManifest = null;
const paperDialog = document.getElementById('paperDialog');
const subscribeDialog = document.getElementById('subscribeDialog');
const savedDialog = document.getElementById('savedDialog');
const storageKey = 'enzyme-atlas-reading-state';
const state = { saved: [], later: [], read: [], hidden: [], subscriptions: [], ...JSON.parse(localStorage.getItem(storageKey) || '{}') };
const unique = values => [...new Set(values)];
const paper = id => papers.find(item => item.id === id);
const isActive = (id, kind) => state[kind].includes(id);
const T = (key, vars) => EA.t(key, vars);
const typeLabel = type => EA.typeLabel(type);
const editionLabel = num => String(num).padStart(2, '0');

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

function labels(item) { return EA.pickList(item, 'labels').map(label => `<span class="recommend-label">${label}</span>`).join(''); }

function actionButtons(item, compact = false) {
  return [`<button class="action-button ${isActive(item.id, 'saved') ? 'active' : ''}" onclick="move('${item.id}','saved')">${isActive(item.id, 'saved') ? T('act_saved') : T('act_save')}</button>`, `<button class="action-button ${isActive(item.id, 'later') ? 'active' : ''}" onclick="move('${item.id}','later')">${isActive(item.id, 'later') ? T('act_later_on') : T('act_later')}</button>`, compact ? '' : `<button class="action-button ${isActive(item.id, 'read') ? 'active' : ''}" onclick="move('${item.id}','read')">${isActive(item.id, 'read') ? T('act_read_on') : T('act_read')}</button>`].join('');
}

function featureCard(item) {
  const type = typeLabel(item.type);
  return `<article class="feature-card"><div class="card-meta"><span>${EA.v('topics', item.topic)} · ${type}</span><span>${T('minutes_short', { n: item.minutes })}</span></div><h3>${EA.paperTitle(item)}</h3><p class="card-summary">${EA.pick(item, 'summary')}</p><p class="card-why"><b>${T('card_why')}</b>${EA.pick(item, 'why')}</p><div class="card-labels">${labels(item)}</div><p class="card-audience">${T('card_audience_prefix')}${EA.pick(item, 'audience')}</p><div class="card-actions"><span><button class="read-link" onclick="openPaper('${item.id}')">${T('act_quick')}</button><a class="source-link" href="${item.url}" target="_blank" rel="noopener">${T('act_doi')}</a></span><button class="save-btn ${isActive(item.id, 'saved') ? 'saved' : ''}" aria-label="${isActive(item.id, 'saved') ? T('act_saved') : T('act_save')}" onclick="move('${item.id}','saved')">${isActive(item.id, 'saved') ? '★' : '☆'}</button></div></article>`;
}

function renderEdition() {
  if (!currentEdition) return;
  const featuredCount = papers.filter(item => item.featured).length;
  const range = `${currentEdition.periodStart.slice(5).replace('-', '.')}–${currentEdition.periodEnd.slice(5).replace('-', '.')}`;
  document.getElementById('editionDate').textContent = T('edition_date', {
    num: editionLabel(currentEdition.edition),
    date: currentEdition.updatedAt.replaceAll('-', '.'),
  });
  document.getElementById('editionSummary').innerHTML = T('edition_summary_html', {
    total: papers.length,
    featured: featuredCount,
    range,
  });
  document.getElementById('featuredTitle').textContent = T('featured_title', { n: featuredCount });
}

function renderFeatured() { document.getElementById('featuredGrid').innerHTML = papers.filter(item => item.featured).slice(0, 5).map(featureCard).join(''); }

function renderObservations() {
  const fallback = [[T('obs_f1'), T('obs_f1_body')], [T('obs_f2'), T('obs_f2_body')], [T('obs_f3'), T('obs_f3_body')]];
  const localized = editionObservations.length
    ? editionObservations.map((item, index) => {
        const en = (currentEdition && currentEdition.observationsEn) ? currentEdition.observationsEn[index] : null;
        return (EA.getLang() === 'en' && en) ? en : item;
      })
    : fallback;
  document.getElementById('observationGrid').innerHTML = localized.map((item, index) => `<article><span>0${index + 1}</span><h3>${item[0]}</h3><p>${item[1]}</p></article>`).join('');
}

function renderPapers() {
  const list = [...papers].filter(item => !state.hidden.includes(item.id)).sort((a, b) => b.date.localeCompare(a.date));
  document.getElementById('resultCount').innerHTML = T('intake_count_html', { total: papers.length, shown: list.length, hidden: state.hidden.length });
  document.getElementById('paperList').innerHTML = list.map(item => `<article class="paper-row"><span class="paper-date">${item.date}</span><div class="paper-main"><a class="paper-title paper-title-link" href="${item.url}" target="_blank" rel="noopener">${EA.paperTitle(item)} ↗</a><div class="paper-sub">${item.authors} · ${item.journal}</div><div class="row-labels"><span class="topic-label">${EA.v('topics', item.topic)}</span>${labels(item)}</div></div><div class="paper-score"><b>${item.minutes}</b><span>${T('minutes_unit')}</span></div><div class="read-state">${actionButtons(item, true)}<button class="muted-button" onclick="move('${item.id}','hidden')">${T('act_hide')}</button></div></article>`).join('') || `<p class="empty-state">${T('empty_intake')}</p>`;
}

function renderEditions() {
  const grid = document.getElementById('editionGrid');
  const note = document.getElementById('editionsNote');
  if (!grid) return;
  const all = (editionManifest && editionManifest.editions) || [];
  const current = currentEdition ? currentEdition.edition : null;
  const past = all.filter(entry => entry.edition !== current);
  if (!past.length) {
    grid.innerHTML = '';
    if (note) note.hidden = false;
    return;
  }
  if (note) note.hidden = true;
  grid.innerHTML = past.map(entry => `
    <a class="edition-card" href="archive.html?e=${entry.edition}">
      <div class="edition-card-top"><span class="edition-number">${editionLabel(entry.edition)}</span><span class="edition-tag">${T('archive_open')}</span></div>
      <p class="edition-card-meta">${T('editions_card_meta', { date: entry.updatedAt.replaceAll('-', '.'), num: editionLabel(entry.edition) })}</p>
      <h3>${EA.pick(entry, 'headline') || entry.updatedAt}</h3>
      <p class="edition-card-counts">${T('editions_card_counts', { total: entry.itemCount, featured: entry.featuredCount })}</p>
    </a>
  `).join('');
}

function openPaper(id) {
  const item = paper(id);
  document.getElementById('dialogContent').innerHTML = `<div class="modal-copy quick-card"><p class="eyebrow">${EA.v('topics', item.topic)} · ${typeLabel(item.type)} · ${T('min_scan', { n: item.minutes })}</p><h2>${EA.paperTitle(item)}</h2><p class="detail-meta">${item.title}<br>${item.authors} · ${item.journal} · ${item.date}</p><div class="quick-grid"><div><h3>${T('q_summary')}</h3><p>${EA.pick(item, 'summary')}</p></div><div><h3>${T('q_why')}</h3><p>${EA.pick(item, 'why')}</p></div><div><h3>${T('q_evidence')}</h3><p>${EA.pick(item, 'evidence')}</p></div><div><h3>${T('q_audience')}</h3><p>${EA.pick(item, 'audience')}</p></div></div><p class="verification-note"><b>${T('q_verification')}</b>${EA.pick(item, 'verification')}</p><div class="detail-actions">${actionButtons(item)}<a class="primary-button" href="${item.url}" target="_blank" rel="noopener">${T('q_doi')}</a></div></div>`;
  paperDialog.showModal();
}

function bib(item) { return `@article{${item.id},\n  title={${item.title}},\n  author={${item.authors}},\n  journal={${item.journal}},\n  year={${item.date.slice(0, 4)}},\n  doi={${item.doi}},\n  url={${item.url}}\n}`; }

function exportSaved() {
  const records = state.saved.map(paper).filter(Boolean);
  if (!records.length) { document.getElementById('savedList').insertAdjacentHTML('afterbegin', `<p class="form-note">${T('export_needs_saved')}</p>`); return; }
  const blob = new Blob([records.map(bib).join('\n\n')], { type: 'application/x-bibtex' });
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'enzyme-atlas-reading-list.bib';
  link.click();
  URL.revokeObjectURL(link.href);
}

function readingSection(label, key) {
  const records = state[key].map(paper).filter(Boolean);
  return `<section class="reading-section"><h3>${label} <small>${records.length}</small></h3>${records.length ? records.map(item => `<div class="saved-item"><span><b>${EA.paperTitle(item)}</b><small>${item.journal} · ${item.date}</small></span><span><a href="${item.url}" target="_blank" rel="noopener">DOI ↗</a><button onclick="move('${item.id}','clear')">${T('act_remove')}</button></span></div>`).join('') : `<p>${T('list_empty')}</p>`}</section>`;
}

function renderSaved() { document.getElementById('savedList').innerHTML = `<button class="export-button" onclick="exportSaved()">${T('export_bibtex')}</button>${readingSection(T('sec_saved'), 'saved')}${readingSection(T('sec_later'), 'later')}${readingSection(T('sec_read'), 'read')}${readingSection(T('sec_hidden'), 'hidden')}`; }

function renderSubscriptionTopics() {
  const topics = unique(papers.map(item => item.topic));
  document.getElementById('subscriptionTopics').innerHTML = topics.map(topic => `<label class="topic-check"><input type="checkbox" value="${topic}" ${state.subscriptions.includes(topic) ? 'checked' : ''}> ${EA.v('topics', topic)}</label>`).join('');
}

function renderAll() { renderFeatured(); renderObservations(); renderPapers(); renderSaved(); persist(); }

async function init() {
  try {
    const [papersResponse, manifestResponse] = await Promise.all([
      fetch('data/papers.json'),
      fetch('data/editions.json'),
    ]);
    if (!papersResponse.ok) throw new Error('data unavailable');
    const data = await papersResponse.json();
    papers = data.items;
    editionObservations = data.observations || [];
    currentEdition = data;
    if (manifestResponse.ok) editionManifest = await manifestResponse.json();
    renderEdition();
  } catch (error) {
    document.getElementById('resultCount').textContent = T('data_error');
    return;
  }
  renderSubscriptionTopics();
  renderAll();
  renderEditions();
}

document.getElementById('subscribeBtn').onclick = () => { renderSubscriptionTopics(); subscribeDialog.showModal(); };
document.getElementById('confirmSubscribe').onclick = () => {
  const email = document.getElementById('emailInput');
  state.subscriptions = [...document.querySelectorAll('#subscriptionTopics input:checked')].map(input => input.value);
  persist();
  document.getElementById('subscribeNote').textContent = email.checkValidity() ? T('subscribe_ok') : T('subscribe_bad_email');
};
document.getElementById('openSaved').onclick = () => { renderSaved(); savedDialog.showModal(); };

EA.onChange(() => {
  renderEdition();
  renderAll();
  renderEditions();
  renderSubscriptionTopics();
});

init();
