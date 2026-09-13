/**
 * Edition archive page.
 *
 * Without ?e= it lists every archived edition; with ?e=<number> it renders that
 * edition read-only (featured picks, full intake, editorial notes).
 * Data contract: data/editions.json lists every edition with the path to its
 * data file (the current edition points at data/papers.json, past editions at
 * data/history/papers-<date>.json).
 */
const T = (key, vars) => EA.t(key, vars);
const editionLabel = num => String(num).padStart(2, '0');
const statusNode = document.getElementById('archiveStatus');
const switcherNode = document.getElementById('editionSwitcher');
const listNode = document.getElementById('archiveList');
const detailNode = document.getElementById('archiveDetail');
const viewingNode = document.getElementById('archiveViewing');
const backNode = document.getElementById('archiveBack');
const noteNode = document.getElementById('archiveNote');

let manifest = null;
let activeEdition = null;

function requestedEdition() {
  const value = new URLSearchParams(location.search).get('e');
  if (!value) return null;
  const parsed = Number.parseInt(value, 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}

function renderSwitcher() {
  const editions = manifest.editions;
  switcherNode.innerHTML = editions.map(entry => {
    const selected = activeEdition && entry.edition === activeEdition.edition;
    const latest = entry.edition === manifest.current ? `<span class="edition-latest">${T('archive_latest_tag')}</span>` : '';
    return `<a class="classic-filter${selected ? ' active' : ''}" href="archive.html?e=${entry.edition}" aria-pressed="${selected}">${T('editions_card_meta', { date: entry.updatedAt.replaceAll('-', '.'), num: editionLabel(entry.edition) })}${latest}</a>`;
  }).join('');
}

function renderList() {
  listNode.innerHTML = manifest.editions.map(entry => `
    <a class="edition-card" href="archive.html?e=${entry.edition}">
      <div class="edition-card-top"><span class="edition-number">${editionLabel(entry.edition)}</span><span class="edition-tag">${T('archive_open')}</span></div>
      <p class="edition-card-meta">${T('editions_card_meta', { date: entry.updatedAt.replaceAll('-', '.'), num: editionLabel(entry.edition) })}</p>
      <h3>${EA.pick(entry, 'headline') || entry.updatedAt}</h3>
      <p class="edition-card-counts">${T('editions_card_counts', { total: entry.itemCount, featured: entry.featuredCount })}</p>
    </a>
  `).join('');
}

function featureCard(item) {
  return `<article class="feature-card"><div class="card-meta"><span>${EA.v('topics', item.topic)} · ${EA.typeLabel(item.type)}</span><span>${T('minutes_short', { n: item.minutes })}</span></div><h3>${EA.paperTitle(item)}</h3><p class="card-summary">${EA.pick(item, 'summary')}</p><p class="card-why"><b>${T('card_why')}</b>${EA.pick(item, 'why')}</p><div class="card-labels">${EA.pickList(item, 'labels').map(label => `<span class="recommend-label">${label}</span>`).join('')}</div><p class="card-audience">${T('card_audience_prefix')}${EA.pick(item, 'audience')}</p><div class="card-actions"><span><a class="source-link" href="${item.url}" target="_blank" rel="noopener">${T('act_doi')}</a></span></div></article>`;
}

function renderDetail(data) {
  const featured = data.items.filter(item => item.featured);
  document.getElementById('archiveFeaturedTitle').textContent = T('archive_featured_title', { n: featured.length });
  document.getElementById('archiveFeatured').innerHTML = featured.map(featureCard).join('');
  const sorted = [...data.items].sort((a, b) => b.date.localeCompare(a.date));
  document.getElementById('archiveCount').innerHTML = `<strong>${data.items.length}</strong> · ${data.updatedAt}`;
  document.getElementById('archivePapers').innerHTML = sorted.map(item => `<article class="paper-row"><span class="paper-date">${item.date}</span><div class="paper-main"><a class="paper-title paper-title-link" href="${item.url}" target="_blank" rel="noopener">${EA.paperTitle(item)} ↗</a><div class="paper-sub">${item.authors} · ${item.journal}</div><div class="row-labels"><span class="topic-label">${EA.v('topics', item.topic)}</span>${EA.pickList(item, 'labels').map(label => `<span class="recommend-label">${label}</span>`).join('')}</div></div><div class="paper-score"><b>${item.minutes}</b><span>${T('minutes_unit')}</span></div></article>`).join('');
  const observations = (data.observations || []).map((item, index) => {
    const en = data.observationsEn ? data.observationsEn[index] : null;
    return (EA.getLang() === 'en' && en) ? en : item;
  });
  document.getElementById('archiveObservations').innerHTML = observations.map((item, index) => `<article><span>0${index + 1}</span><h3>${item[0]}</h3><p>${item[1]}</p></article>`).join('');
}

async function loadEdition(entry) {
  const response = await fetch(entry.path);
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  return response.json();
}

async function showEdition(number) {
  const entry = manifest.editions.find(item => item.edition === number);
  if (!entry) {
    statusNode.textContent = T('archive_notfound');
    return;
  }
  activeEdition = entry;
  const data = await loadEdition(entry);
  renderSwitcher();
  renderDetail(data);
  statusNode.textContent = T('editions_card_counts', { total: data.items.length, featured: data.items.filter(i => i.featured).length });
  viewingNode.textContent = T('archive_viewing', { num: editionLabel(entry.edition), date: entry.updatedAt.replaceAll('-', '.') });
  viewingNode.hidden = false;
  noteNode.hidden = false;
  backNode.hidden = false;
  detailNode.hidden = false;
  listNode.hidden = true;
}

async function boot() {
  try {
    const response = await fetch('data/editions.json');
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    manifest = await response.json();
  } catch (error) {
    console.error('期号清单载入失败', error);
    statusNode.textContent = T('archive_error');
    return;
  }
  const requested = requestedEdition();
  if (requested) {
    try {
      await showEdition(requested);
    } catch (error) {
      console.error('期号数据载入失败', error);
      statusNode.textContent = T('archive_error');
      renderSwitcher();
      renderList();
    }
    return;
  }
  statusNode.textContent = T('editions_card_counts', {
    total: manifest.editions.length,
    featured: manifest.current,
  });
  renderSwitcher();
  renderList();
  detailNode.hidden = true;
  listNode.hidden = false;
}

EA.onChange(async () => {
  if (!manifest) return;
  if (activeEdition) {
    try {
      await showEdition(activeEdition.edition);
    } catch (error) {
      statusNode.textContent = T('archive_error');
    }
    return;
  }
  boot();
});

boot();
