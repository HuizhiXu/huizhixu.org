const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const Fuse = require('../themes/blist/assets/js/fuse.min.js');

function setup(fetch) {
  let document;
  class Element {
    constructor(tag = 'div', classes = []) {
      this.tag = tag; this.children = []; this.events = {}; this.attrs = {};
      this.value = ''; this.textContent = ''; this.hidden = false;
      const set = new Set(classes);
      this.classList = { add: c => set.add(c), remove: c => set.delete(c), contains: c => set.has(c) };
    }
    addEventListener(name, fn) { this.events[name] = fn; }
    setAttribute(name, value) { this.attrs[name] = value; }
    focus() { document.activeElement = this; }
    append(...elements) { this.children.push(...elements); }
    replaceChildren(...elements) { this.children = elements; }
    querySelectorAll(selector) { return this.children.flatMap(li => li.children).filter(child => child.tag === 'a'); }
  }
  const ui = new Element('div', ['hidden']);
  const input = new Element('input');
  const list = new Element('ul');
  const status = new Element();
  const retry = new Element('button');
  const trigger = new Element('button');
  const close = new Element('button');
  const mobile = new Element('ul', ['hidden']);
  const elements = { '.search-ui': ui, '.open-search': trigger, '.mobile-menu': mobile };
  ui.dataset = { indexUrl: '/index.json', loading: 'Loading', results: 'Results', empty: 'Empty', error: 'Error' };
  ui.querySelector = selector => ({ input, '.search-list': list, '.search-status': status, '.search-retry': retry, '.close-search': close })[selector];
  ui.querySelectorAll = () => [close, input, ...(!retry.hidden ? [retry] : []), ...list.querySelectorAll('a')];
  document = { events: {}, activeElement: trigger, querySelector: selector => elements[selector],
    createElement: tag => new Element(tag), addEventListener(name, fn) { this.events[name] = fn; } };
  vm.runInNewContext(fs.readFileSync('assets/js/search.js', 'utf8'), { document, fetch, Fuse });
  const key = (key, extra = {}) => document.events.keydown({ key, preventDefault() {}, ...extra });
  return { ui, input, list, status, retry, trigger, close, mobile, document, key };
}
const flush = () => new Promise(resolve => setImmediate(resolve));
const data = [{ title: '测试标题', contents: '只在正文深处的量子计算', summary: '摘要', tags: ['ai'], permalink: '/article/' }];

test('Chinese root index, typing during loading, then latest query and full-text results', async () => {
  let resolve;
  const paths = [];
  const app = setup(path => { paths.push(path); return new Promise(r => { resolve = r; }); });
  app.trigger.events.click();
  app.input.value = '量子计算';
  assert.doesNotThrow(() => app.input.events.input());
  app.trigger.events.click();
  assert.equal(paths.length, 1);
  assert.equal(paths[0], '/index.json');
  assert.equal(app.mobile.classList.contains('hidden'), true);
  resolve({ ok: true, json: async () => data });
  await flush();
  assert.equal(app.list.children.length, 1);
  assert.equal(app.list.children[0].children[0].href, '/article/');
  app.key('ArrowDown');
  assert.equal(app.document.activeElement, app.list.children[0].children[0]);
  app.key('ArrowUp');
  assert.equal(app.document.activeElement, app.input);
  app.key('Escape');
  assert.equal(app.document.activeElement, app.trigger);
  assert.equal(app.ui.classList.contains('hidden'), true);
});

test('failed fetch can retry and tags are searchable', async () => {
  let calls = 0;
  const app = setup(async () => ++calls === 1 ? { ok: false, status: 404 } : { ok: true, json: async () => data });
  app.trigger.events.click();
  await flush();
  assert.equal(app.status.textContent, 'Error');
  assert.equal(app.retry.hidden, false);
  app.input.value = 'ai';
  await app.retry.events.click();
  assert.equal(app.list.children.length, 1);
  assert.equal(app.retry.hidden, true);
});

test('untrusted titles are text; empty query clears results and dialog traps focus', async () => {
  const app = setup(async () => ({ ok: true, json: async () => [{ ...data[0], title: '<img src=x onerror=alert(1)>' }] }));
  app.trigger.events.click();
  await flush();
  app.input.value = 'ai'; app.input.events.input();
  const title = app.list.children[0].children[0].children[0];
  assert.equal(title.textContent, '<img src=x onerror=alert(1)>');
  assert.equal(title.children.length, 0);
  app.input.value = ''; app.input.events.input();
  assert.equal(app.list.children.length, 0);
  app.input.focus(); app.key('Tab');
  assert.equal(app.document.activeElement, app.close);
  app.key('Tab', { shiftKey: true });
  assert.equal(app.document.activeElement, app.input);
});
