const params = new URLSearchParams(location.search);
const initial = params.get('q') || '';
const query = document.getElementById('query');
const headerQuery = document.getElementById('headerQuery');
const title = document.getElementById('searchTitle');
const note = document.getElementById('searchNote');
const results = document.getElementById('searchResults');
let records = [];
query.value = initial;
headerQuery.value = initial;

const T = (key, vars) => EA.t(key, vars);

/** Searchable text for a record: canonical Chinese fields plus their English counterparts. */
function haystack(record) {
  const base = ['id', 'title', 'cn', 'authors', 'journal', 'date', 'topic', 'type', 'doi', 'url', 'summary', 'why', 'evidence', 'audience', 'verification']
    .map(key => record[key] || '');
  const labels = (record.labels || []).map(label => `${label} ${EA.v('labels', label)}`);
  const english = record.en
    ? ['topic', 'summary', 'why', 'evidence', 'audience', 'verification'].map(key => record.en[key] || '').concat(record.en.labels || [])
    : [];
  const topics = [EA.v('topics', record.topic)];
  return base.concat(labels, english, topics).join(' ').toLowerCase();
}

function render(value) {
  const term = value.trim().toLowerCase();
  const list = records.filter(record => !term || haystack(record).includes(term));
  title.textContent = term ? T('search_results_title', { q: value.trim() }) : T('search_title');
  note.textContent = term ? T('search_note', { n: list.length }) : T('search_idle_note');
  results.innerHTML = list.map(record => `<article class="search-row"><small>${record.date}</small><div><h2><a href="${record.url}" target="_blank" rel="noopener">${EA.paperTitle(record)} ↗</a></h2><p>${record.authors} · ${record.journal} · DOI: ${record.doi}</p></div><span>${EA.v('topics', record.topic)}</span></article>`).join('')
    || `<p class="search-note">${T('search_empty')}</p>`;
}

document.getElementById('searchForm').onsubmit = event => {
  event.preventDefault();
  history.replaceState(null, '', '?q=' + encodeURIComponent(query.value));
  render(query.value);
};

EA.onChange(() => render(query.value));

fetch('data/papers.json')
  .then(response => response.json())
  .then(data => { records = data.items; render(initial); })
  .catch(() => { note.textContent = T('search_error'); });
