/* Research topics: aggregate classics + weekly papers under each unified topic. */
const browserNode = document.getElementById('topicsBrowser');

const T = (key, vars) => EA.t(key, vars);

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, char => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[char]));
}

function doiUrl(doi) {
  return `https://doi.org/${encodeURI(doi)}`;
}

let topics = [];
let classics = [];
let papers = [];       // current + archived weekly papers (with edition/date)
let openTopic = null;  // key of the currently expanded topic

function topicLabel(key) {
  return EA.getLang() === 'zh' ? key : (EA.v('topics', key) || key);
}

function topicDescription(topic) {
  return EA.getLang() === 'zh' ? topic.description : (topic.en_description || topic.description);
}

function renderTopicClassics(topicKey) {
  const items = classics.filter(item => (item.topics || []).includes(topicKey));
  if (!items.length) return '';
  return `
    <div class="topic-group">
      <h4>${T('topics_classics')}</h4>
      <ul class="topic-item-list">
        ${items.map(item => `
          <li class="topic-item">
            <span class="topic-item-year">${item.year}</span>
            <div class="topic-item-main">
              <a href="${doiUrl(item.doi)}" target="_blank" rel="noopener">${escapeHtml(item.title)} ↗</a>
              <span class="topic-item-meta">${escapeHtml(item.authors)} · ${escapeHtml(item.journal)}</span>
            </div>
          </li>`).join('')}
      </ul>
    </div>`;
}

function renderTopicPapers(topicKey) {
  const items = papers.filter(item => (item.topics || []).includes(topicKey));
  if (!items.length) return '';
  return `
    <div class="topic-group">
      <h4>${T('topics_weekly')}</h4>
      <ul class="topic-item-list">
        ${items.map(item => `
          <li class="topic-item">
            <span class="topic-item-year">${item.date}</span>
            <div class="topic-item-main">
              <a href="${doiUrl(item.doi)}" target="_blank" rel="noopener">${escapeHtml(EA.paperTitle(item))} ↗</a>
              <span class="topic-item-meta">${escapeHtml(item.authors)} · ${escapeHtml(item.journal)}</span>
            </div>
          </li>`).join('')}
      </ul>
    </div>`;
}

function renderTopics() {
  browserNode.innerHTML = topics.map((topic, index) => {
    const isOpen = topic.key === openTopic;
    const count = topic.total;
    return `
      <article class="topic-card${isOpen ? ' open' : ''}" data-topic="${escapeHtml(topic.key)}">
        <button type="button" class="topic-card-head" aria-expanded="${isOpen}">
          <small>${String(index + 1).padStart(2, '0')}</small>
          <div class="topic-card-title">
            <h2>${escapeHtml(topicLabel(topic.key))}</h2>
            <p>${escapeHtml(topicDescription(topic))}</p>
          </div>
          <span class="topic-card-count">${count}</span>
          <span class="topic-card-chevron" aria-hidden="true">${isOpen ? '−' : '+'}</span>
        </button>
        ${isOpen ? `<div class="topic-card-body">
          ${renderTopicClassics(topic.key)}
          ${renderTopicPapers(topic.key)}
          ${count === 0 ? `<p class="topic-empty">${T('topics_empty')}</p>` : ''}
        </div>` : ''}
      </article>`;
  }).join('');
}

browserNode.addEventListener('click', event => {
  const head = event.target.closest('.topic-card-head');
  if (!head) return;
  const card = head.closest('.topic-card');
  const key = card.dataset.topic;
  openTopic = (openTopic === key) ? null : key;
  renderTopics();
});

EA.onChange(() => { if (topics.length) renderTopics(); });

Promise.all([
  fetch('data/topics.json').then(r => r.json()),
  fetch('data/classics.json').then(r => r.json()),
  fetch('data/papers.json').then(r => r.json()),
  fetch('data/editions.json').then(r => r.json()).catch(() => null),
]).then(([topicsData, classicsData, papersData, manifest]) => {
  topics = topicsData.topics;
  classics = classicsData.items;
  papers = papersData.items;

  // include archived weekly editions so a topic spans current + past weeks
  if (manifest && Array.isArray(manifest.editions)) {
    const historyPaths = manifest.editions
      .map(entry => entry.path)
      .filter(path => path && path.startsWith('data/history/'));
    return Promise.all(historyPaths.map(path => fetch(path).then(r => r.json()).catch(() => null)));
  }
  return [];
}).then(historyData => {
  for (const data of historyData) {
    if (data && Array.isArray(data.items)) papers.push(...data.items);
  }
  // sort weekly papers by date descending
  papers.sort((a, b) => (a.date < b.date ? 1 : -1));
  renderTopics();
}).catch(error => {
  console.error('研究专题载入失败', error);
  browserNode.innerHTML = `<p class="empty-state">${T('topics_error')}</p>`;
});
