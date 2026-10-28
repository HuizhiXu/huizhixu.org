(() => {
  const ui = document.querySelector('.search-ui');
  if (!ui) return;
  const input = ui.querySelector('input');
  const list = ui.querySelector('.search-list');
  const status = ui.querySelector('.search-status');
  const retry = ui.querySelector('.search-retry');
  const trigger = document.querySelector('.open-search');
  let fuse, loading, previousFocus;

  function render() {
    list.replaceChildren();
    if (!fuse) return;
    const term = input.value.trim();
    if (!term) { status.textContent = ''; return; }
    const results = fuse.search(term).slice(0, 5);
    status.textContent = results.length ? ui.dataset.results : ui.dataset.empty;
    for (const { item } of results) {
      const li = document.createElement('li');
      const link = document.createElement('a');
      link.href = item.permalink;
      link.className = 'search-result-link block mb-2 px-4 py-2 rounded border-b border-gray-200 dark:border-gray-600 focus:bg-gray-100 dark:focus:bg-gray-700';
      const title = document.createElement('div');
      title.className = 'text-xl font-bold';
      title.textContent = item.title;
      const summary = document.createElement('p');
      summary.className = 'text-sm font-light';
      summary.textContent = item.summary || '';
      link.append(title, summary);
      li.append(link);
      list.append(li);
    }
  }

  async function load() {
    if (fuse) { render(); return; }
    if (loading) return loading;
    status.textContent = ui.dataset.loading;
    retry.hidden = true;
    ui.setAttribute('aria-busy', 'true');
    loading = (async () => {
      try {
        const response = await fetch(ui.dataset.indexUrl);
        if (!response.ok) throw new Error(`Search index: ${response.status}`);
        const data = await response.json();
        fuse = new Fuse(data, {
          shouldSort: true, ignoreLocation: true, threshold: 0.4,
          minMatchCharLength: 1, keys: ['title', 'tags', 'contents'],
        });
        render();
      } catch (error) {
        status.textContent = ui.dataset.error;
        retry.hidden = false;
      } finally {
        ui.setAttribute('aria-busy', 'false');
        loading = undefined;
      }
    })();
    return loading;
  }

  function open() {
    if (ui.classList.contains('hidden')) previousFocus = document.activeElement;
    const mobileMenu = document.querySelector('.mobile-menu');
    mobileMenu?.classList.add('hidden');
    mobileMenu?.classList.remove('flex');
    ui.classList.remove('hidden');
    trigger?.setAttribute('aria-expanded', 'true');
    input.focus();
    load();
  }

  function close() {
    ui.classList.add('hidden');
    trigger?.setAttribute('aria-expanded', 'false');
    const menu = document.querySelector('.primary-menu');
    const menuButton = document.querySelector('.mobile-menu-button');
    if (menu && previousFocus && menu.contains(previousFocus) && !menu.classList.contains('is-open') && menuButton?.offsetParent) {
      menuButton.focus();
    } else {
      previousFocus?.focus();
    }
  }

  trigger?.addEventListener('click', open);
  ui.querySelector('.close-search').addEventListener('click', close);
  retry.addEventListener('click', load);
  input.addEventListener('input', render);
  document.addEventListener('keydown', event => {
    if ((event.metaKey || event.ctrlKey) && event.key === '/') {
      event.preventDefault();
      open();
    }
    if (ui.classList.contains('hidden')) return;
    if (event.key === 'Escape') { event.preventDefault(); close(); }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      const items = [input, ...list.querySelectorAll('a')];
      const index = items.indexOf(document.activeElement);
      if (index < 0) return;
      event.preventDefault();
      items[Math.max(0, Math.min(items.length - 1, index + (event.key === 'ArrowDown' ? 1 : -1)))].focus();
    }
    if (event.key === 'Tab') {
      const items = [...ui.querySelectorAll('button:not([hidden]), input, a[href]')];
      const first = items[0], last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
  });
})();
