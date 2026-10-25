// Run before the stylesheet to restore appearance without a light flash.
(() => {
  const key = 'spicyops-guide-theme-v1';
  let theme = 'dark';
  try {
    if (localStorage.getItem(key) === 'light') theme = 'light';
  } catch { /* Reading the guide never depends on browser storage. */ }

  function apply(value) {
    theme = value === 'light' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme;
    const button = document.getElementById('theme-toggle');
    if (!button) return;
    button.hidden = false;
    button.setAttribute('aria-pressed', String(theme === 'dark'));
    button.title = theme === 'dark' ? 'Cambiar a modo claro' : 'Cambiar a modo oscuro';
    button.querySelector('[data-theme-label]').textContent = theme === 'dark' ? 'Oscuro' : 'Claro';
  }
  apply(theme);
  document.addEventListener('DOMContentLoaded', () => {
    apply(theme);
    document.getElementById('theme-toggle').addEventListener('click', () => {
      apply(theme === 'dark' ? 'light' : 'dark');
      try { localStorage.setItem(key, theme); } catch { /* Still works in this tab. */ }
    });
  });
  window.addEventListener('storage', event => {
    if (event.key === key || event.key === null) apply(event.newValue);
  });
})();
