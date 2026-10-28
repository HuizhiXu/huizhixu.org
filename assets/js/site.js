(() => {
  const menuButton = document.querySelector('.mobile-menu-button');
  const menu = document.querySelector('.primary-menu');
  const closeMenu = () => {
    menu?.classList.remove('is-open');
    menuButton?.setAttribute('aria-expanded', 'false');
  };
  menuButton?.addEventListener('click', () => {
    const open = menu.classList.toggle('is-open');
    menuButton.setAttribute('aria-expanded', String(open));
  });
  menu?.querySelectorAll('a').forEach(link => link.addEventListener('click', closeMenu));
  document.querySelector('.open-search')?.addEventListener('click', closeMenu);
  document.addEventListener('keydown', event => {
    if (event.key !== 'Escape') return;
    if (menu?.classList.contains('is-open')) { closeMenu(); menuButton.focus(); }
    document.querySelectorAll('.language-menu[open]').forEach(item => item.removeAttribute('open'));
  });
  document.addEventListener('click', event => {
    if (!event.target.closest('.site-header')) closeMenu();
    if (!event.target.closest('.language-menu')) document.querySelector('.language-menu')?.removeAttribute('open');
  });
  const toggle = document.querySelector('.toggle-dark-mode');
  const reflectTheme = () => toggle?.setAttribute('aria-pressed', String(document.documentElement.classList.contains('dark')));
  reflectTheme();
  toggle?.addEventListener('click', () => {
    const dark = document.documentElement.classList.toggle('dark');
    try { localStorage.setItem('darkmode', dark ? 'dark' : 'light'); } catch (_) {}
    reflectTheme();
  });
  document.querySelector('.back-to-top')?.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'instant' : 'smooth' });
  });
})();
