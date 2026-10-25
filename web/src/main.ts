import { defaults, validate, substitute, type Config } from './config.mjs';
const $ = <T extends HTMLElement>(s:string)=>document.querySelector<T>(s)!;
const chapters = [...document.querySelectorAll<HTMLElement>('.chapter')];
const steps = [...document.querySelectorAll<HTMLInputElement>('[data-step]')];
const notice = (s:string)=>{ $('#notice').textContent=s; };
const remember = $<HTMLInputElement>('#remember');
const key = 'spicyops-guide-progress-v1';
function progress() {
 const ids=steps.filter(s=>s.checked).map(s=>s.dataset.step!);
 $<HTMLProgressElement>('progress').value=ids.length;
 $('#progress-text').textContent=`${ids.length} de ${steps.length} etapas comprobadas`;
 try { if(remember.checked) localStorage.setItem(key,JSON.stringify({version:1,ids})); else localStorage.removeItem(key); }
 catch { notice('El navegador no permite guardar progreso. Puedes continuar sin guardarlo.'); }
}
try {
 const saved=JSON.parse(localStorage.getItem(key)||'null');
 if(saved?.version===1 && Array.isArray(saved.ids)) {remember.checked=true; steps.forEach(s=>s.checked=saved.ids.includes(s.dataset.step));}
} catch { /* An unavailable or invalid store never blocks reading. */ }
progress();
steps.forEach(s=>s.addEventListener('change',progress));
remember.addEventListener('change',progress);
$('#clear').addEventListener('click',()=>{remember.checked=false;steps.forEach(s=>s.checked=false);progress();notice('Progreso local borrado.');});
document.querySelectorAll<HTMLButtonElement>('.copy').forEach(button=>button.addEventListener('click',async()=>{
 const code=button.closest('figure')!.querySelector('code')!;
 try {await navigator.clipboard.writeText(code.textContent||'');notice('Comando copiado. Revisa el equipo de destino.');}
 catch {const range=document.createRange();range.selectNodeContents(code);const selection=window.getSelection();selection?.removeAllRanges();selection?.addRange(range);notice('Seleccionado: usa Copiar en tu navegador o Ctrl+C.');}
}));
$('#search').addEventListener('input',()=>{
 const query=$<HTMLInputElement>('#search').value.toLocaleLowerCase('es').trim();
 let matches=0;
 chapters.forEach(c=>{c.hidden=!!query&&!c.textContent!.toLocaleLowerCase('es').includes(query);if(!c.hidden){matches++;if(query && c instanceof HTMLDetailsElement)c.open=true;}});
 $('#search-status').textContent=query?`${matches} secciones encontradas. Borra la búsqueda para ver toda la guía.`:'';
});
const clearSearch=()=>{ $<HTMLInputElement>('#search').value='';chapters.forEach(c=>c.hidden=false);$('#search-status').textContent=''; };
const select=$<HTMLSelectElement>('#stage-select');
function navigate(id:string) {clearSearch();location.hash=id;select.value=id;}
select.addEventListener('change',()=>navigate(select.value));
$('#previous').addEventListener('click',()=>{navigate(select.options[Math.max(0,select.selectedIndex-1)].value);});
$('#next').addEventListener('click',()=>{navigate(select.options[Math.min(select.options.length-1,select.selectedIndex+1)].value);});
function hashChange() {
 clearSearch(); const id=location.hash.slice(1);
 const target=document.getElementById(id);
 if(target instanceof HTMLDetailsElement) {target.open=true;target.scrollIntoView();}
 if([...select.options].some(o=>o.value===id))select.value=id;
 document.querySelectorAll('.sidebar nav a').forEach(a=>{if(a.getAttribute('href')===location.hash)a.setAttribute('aria-current','location');else a.removeAttribute('aria-current');});
}
window.addEventListener('hashchange',hashChange);hashChange();
document.querySelectorAll<HTMLAnchorElement>('a[href^="#"]').forEach(link=>link.addEventListener('click',()=>{
 const target=document.getElementById(link.hash.slice(1));
 if(target instanceof HTMLDetailsElement)target.open=true;
}));
$('#prepare-all').addEventListener('click',()=>{
 chapters.forEach(c=>{if(c instanceof HTMLDetailsElement && c.querySelector('[data-step]'))c.open=true;});
 navigate('antes-de-empezar');
});
window.addEventListener('beforeprint',()=>{
 document.querySelectorAll<HTMLDetailsElement>('.chapter').forEach(c=>{c.dataset.wasOpen=String(c.open);c.open=true;});
});
window.addEventListener('afterprint',()=>{
 document.querySelectorAll<HTMLDetailsElement>('.chapter').forEach(c=>c.open=c.dataset.wasOpen==='true');
});
$('#print').addEventListener('click',()=>window.print());
document.querySelectorAll<HTMLInputElement>('[name=mode]').forEach(input=>input.addEventListener('change',()=>{
 $('#mode-note').textContent=input.value==='control'?'En el paso 7 utiliza spicyops-control. Write concede capacidad amplia en RouterOS; continúa con la política y límites de Morosos.':'En el paso 7 utiliza spicyops-read. No necesitas escritura para conectar.';
 document.body.dataset.mode=input.value;
}));
const textNodes: {node:Text;original:string}[]=[];
const walker=document.createTreeWalker($('#chapters'),NodeFilter.SHOW_TEXT);
while(walker.nextNode()) {const node=walker.currentNode as Text;if(node.textContent) textNodes.push({node,original:node.textContent});}
const form=$<HTMLFormElement>('#config-form');
let current={...defaults};let blobUrl='';
function updateDownload() {
 if(blobUrl)URL.revokeObjectURL(blobUrl);
 const py=$('#lecturas-api [data-language=python] code').textContent!;
 blobUrl=URL.createObjectURL(new Blob([py+'\n'],{type:'text/x-python'}));
 $<HTMLAnchorElement>('#download-python').href=blobUrl;
}
function apply(config:Config) {
 current=config;
 textNodes.forEach(({node,original})=>node.textContent=substitute(original,config));
 updateDownload();
 $('#config-status').textContent='Ejemplos actualizados solo en esta pestaña. Puerto del servicio SSH: revisa que coincida con el elegido; esta guía no reconfigura sshd. Diagrama e instalación inicial muestran el puerto habitual 22.';
}
form.addEventListener('submit',event=>{
 event.preventDefault(); const config=Object.fromEntries(new FormData(form)) as Config;
 const error=validate(config);$('#config-status').textContent=error;
 if(error)return;apply(config);
});
form.addEventListener('reset',()=>{apply({...defaults});$('#config-status').textContent='Restablecido el escenario ficticio.';});
// Configuration is never stored, sent, or added to the URL.
void current;
