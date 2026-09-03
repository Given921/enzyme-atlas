const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = path.resolve(__dirname, '..');
const nodes = Object.fromEntries(
  ['classicCount', 'classicGrid', 'classicSourceStats', 'classicFilters'].map(id => [id, {
    innerHTML: '',
    textContent: '',
    addEventListener(type, handler) { this[type] = handler; }
  }])
);

global.document = { getElementById: id => nodes[id] };
global.fetch = async () => ({
  ok: true,
  json: async () => JSON.parse(fs.readFileSync(path.join(root, 'data', 'classics.json'), 'utf8'))
});

vm.runInThisContext(fs.readFileSync(path.join(root, 'classics.js'), 'utf8'), { filename: 'classics.js' });

setImmediate(() => {
  const cardCount = (nodes.classicGrid.innerHTML.match(/class="classic-card"/g) || []).length;
  const filterCount = (nodes.classicFilters.innerHTML.match(/data-source=/g) || []).length;
  const doiCount = (nodes.classicGrid.innerHTML.match(/https:\/\/doi\.org\//g) || []).length;
  if (cardCount !== 55 || filterCount !== 6 || doiCount !== 55) {
    throw new Error(`initial render mismatch: cards=${cardCount}, filters=${filterCount}, doi=${doiCount}`);
  }

  nodes.classicFilters.click({
    target: { closest: () => ({ dataset: { source: 'Cell 正刊' } }) }
  });
  const cellCards = (nodes.classicGrid.innerHTML.match(/class="classic-card"/g) || []).length;
  if (cellCards !== 7 || !nodes.classicCount.innerHTML.includes('Cell 正刊')) {
    throw new Error(`Cell filter mismatch: cards=${cellCards}`);
  }
  console.log('PASS: 55 cards, 6 source filters, 55 DOI links, Cell filter returns 7 cards');
});
