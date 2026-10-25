// Apply the saved appearance before the stylesheet paints. No private data here.
(()=>{
  const key='spicyops-theme';
  let theme='dark';
  try{
    const saved=document.cookie.split('; ').find(value=>value.startsWith('spicyops_theme='))?.split('=')[1] || localStorage.getItem(key);
    if(saved==='light')theme='light';
  }catch{}
  function apply(value){
    theme=value==='light'?'light':'dark';
    document.documentElement.dataset.theme=theme;
    document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
      button.setAttribute('aria-pressed',String(theme==='dark'));
      button.querySelector('[data-theme-label]').textContent=theme==='dark'?'Oscuro':'Claro';
      button.title=theme==='dark'?'Cambiar a modo claro':'Cambiar a modo oscuro';
    });
  }
  apply(theme);
  document.addEventListener('DOMContentLoaded',()=>{
    apply(theme);
    document.querySelectorAll('[data-theme-toggle]').forEach(button=>{
      button.addEventListener('click',()=>{
        apply(theme==='dark'?'light':'dark');
        // A non-sensitive cookie also retains the choice when the local port changes.
        try{document.cookie=`spicyops_theme=${theme}; Path=/; Max-Age=31536000; SameSite=Strict`;}catch{}
        try{localStorage.setItem(key,theme);}catch{}
      });
    });
  });
  addEventListener('storage',event=>{if(event.key===key)apply(event.newValue);});
})();
