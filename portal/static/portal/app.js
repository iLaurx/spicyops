// Conservar el vencimiento al incorporar lecturas nuevas a la misma vista.
const panelNotices=new Map();
function bindNotices(){
document.querySelectorAll('[data-notice]:not([data-notice-bound])').forEach(notice=>{
  const key=notice.textContent.trim();
  const state=panelNotices.get(key)||{expires:Date.now()+6000,dismissed:false};
  panelNotices.set(key,state);
  if(state.dismissed || state.expires<=Date.now()){notice.remove();return;}
  notice.dataset.noticeBound='true';
  const content=document.createElement('span');
  content.append(...notice.childNodes);
  const close=document.createElement('button');
  close.type='button';close.className='notice-close';
  close.setAttribute('aria-label','Cerrar aviso');close.textContent='×';
  notice.append(content,close);
  let timer,remaining=state.expires-Date.now();
  function dismiss(){
    clearTimeout(timer);state.dismissed=true;
    document.querySelectorAll('[data-notice-bound]').forEach(item=>{
      if(item.firstElementChild?.textContent.trim()===key)item.remove();
    });
  }
  function pause(){clearTimeout(timer);remaining=Math.max(0,state.expires-Date.now());}
  function resume(){
    if(notice.matches(':hover') || notice.contains(document.activeElement))return;
    state.expires=Date.now()+remaining;timer=setTimeout(dismiss,remaining);
  }
  close.addEventListener('click',dismiss);
  notice.addEventListener('pointerenter',pause);
  notice.addEventListener('pointerleave',resume);
  notice.addEventListener('focusin',pause);
  notice.addEventListener('focusout',resume);
  timer=setTimeout(dismiss,remaining);
});
}
function bindPanel(){
bindNotices();
const connectionForm=document.getElementById('connect-form');
if(connectionForm && !connectionForm.dataset.validationBound){
  connectionForm.dataset.validationBound='true';
  const summary=connectionForm.querySelector('[data-validation-summary]');
  // Native validation runs before submit, including fields inside closed details.
  connectionForm.addEventListener('invalid',event=>{
    let section=event.target.closest('details');
    while(section){section.open=true;section=section.parentElement.closest('details');}
    event.target.setAttribute('aria-invalid','true');
    if(summary){
      const fields=[...connectionForm.elements].filter(field=>field.willValidate && !field.validity.valid);
      const names=fields.map(field=>field.labels?.[0]?.textContent.trim().replace(/:$/,'')).filter(Boolean);
      summary.textContent='Revisa los campos obligatorios o inválidos: '+names.join(', ')+'.';
      summary.hidden=false;
    }
  },true);
  connectionForm.addEventListener('input',event=>{
    if(event.target.validity?.valid)event.target.removeAttribute('aria-invalid');
    if(summary && connectionForm.querySelectorAll(':invalid').length===0)summary.hidden=true;
  });
}
document.querySelectorAll('[data-autosubmit]:not([data-bound])').forEach(select=>{select.dataset.bound='true';select.addEventListener('change',()=>{if(select.value==='all' && select.dataset.allUrl)select.form.action=select.dataset.allUrl;select.form.submit();});});
document.querySelectorAll('form:not([data-bound])').forEach(form=>{form.dataset.bound='true';form.addEventListener('submit',()=>{
  const button=form.querySelector('[data-busy]');
  if(button){button.disabled=true;button.textContent=button.dataset.busy;}
  const progress=form.querySelector('.connection-progress'); if(progress)progress.hidden=false;
});});
document.querySelectorAll('[data-open]').forEach(button=>button.addEventListener('click',()=>document.getElementById(button.dataset.open).showModal()));
document.querySelectorAll('[data-close]').forEach(button=>button.addEventListener('click',()=>button.closest('dialog').close()));
const units=document.getElementById('speed-unit');
if(units){
  function updateUnits(){document.querySelectorAll('[data-speed]').forEach(el=>el.hidden=el.dataset.speed!==units.value);document.querySelectorAll('.speed-label').forEach(el=>el.textContent=units.value==='mbs'?'MB/s':'Mbps');localStorage.setItem('spicyops-speed-unit',units.value);}
  units.value=localStorage.getItem('spicyops-speed-unit')==='mbs'?'mbs':'mbps';units.addEventListener('change',updateUnits);updateUnits();
}

}
bindPanel();

// Consultar HTML local no dispara una lectura de red ni crea coordinadores.
// Durante edición/confirmación se difiere el reemplazo hasta que sea seguro.
let liveFetching=false;
function editingPanel(){
  return document.querySelector('dialog[open], form[data-dirty="true"], form[data-submitting="true"]') ||
    document.activeElement?.matches('input,textarea,select');
}
document.addEventListener('input',event=>{
  const form=event.target.closest('form');
  if(form && event.target.id!=='speed-unit')form.dataset.dirty='true';
});
document.addEventListener('change',event=>{
  const form=event.target.closest('form');
  if(form && event.target.id!=='speed-unit')form.dataset.dirty='true';
});
document.addEventListener('submit',event=>{if(!event.defaultPrevented)event.target.dataset.submitting='true';});
document.addEventListener('close',event=>{
  event.target.querySelectorAll?.('form').forEach(form=>delete form.dataset.dirty);
},true);
async function updatePanel(){
  const current=document.querySelector('main[data-live-revision]');
  if(liveFetching || !current || !['analytics','clients','connections'].includes(current.dataset.page))return;
  liveFetching=true;
  try{
    const targetUrl=new URL(location.href);
    if(current.dataset.liveSite)targetUrl.searchParams.set('site',current.dataset.liveSite);
    const response=await fetch(targetUrl,{headers:{'X-SpicyOps-Live':'1'},cache:'no-store'});
    if(!response.ok)return;
    const next=new DOMParser().parseFromString(await response.text(),'text/html');
    const incoming=next.querySelector('main[data-live-revision]');
    if(!incoming || incoming.dataset.liveRevision===current.dataset.liveRevision || editingPanel())return;
    const position={x:scrollX,y:scrollY};
    const scrolls=[...current.querySelectorAll('.table-scroll,.bar-chart-scroll')].map(el=>el.scrollLeft);
    current.replaceWith(incoming);
    for(const selector of ['footer','.sidebar-locality']){
      const target=document.querySelector(selector),source=next.querySelector(selector);
      if(target && source)target.replaceWith(source);
    }
    const picker=document.getElementById('site-picker'),newPicker=next.getElementById('site-picker');
    if(picker && newPicker){
      const selected=picker.value;
      picker.innerHTML=newPicker.innerHTML;
      picker.value=selected;
    }
    bindPanel();
    bindDiagnostics();
    document.querySelectorAll('main .table-scroll,main .bar-chart-scroll').forEach((el,i)=>el.scrollLeft=scrolls[i]||0);
    window.scrollTo(position.x,position.y);
  }catch(error){/* Se conserva la vista cuando el servidor local no responde. */}
  finally{liveFetching=false;}
}
setInterval(updatePanel,5000);

// Cada localidad conserva y consulta su propio diagnóstico, sin recargar la vista.
function bindDiagnostics(){
document.querySelectorAll('[data-diagnostic]:not([data-bound])').forEach(root=>{
  root.dataset.bound='true';
  const form=root.querySelector('form'), button=root.querySelector('button');
  const error=root.querySelector('.diagnostic-error');
  let running=false;
  const labels={pendiente:'Pendiente',comprobando:'Comprobando',correcto:'Correcto',advertencia:'Advertencia',error:'Error',no_comprobada:'No comprobada'};
  function show(data,historical=false){
    if(!data.stages)return;
    running=data.running; button.disabled=running;
    root.querySelector('.diagnostic-result').hidden=false;
    const date=new Date(data.started*1000).toLocaleString('es-MX',{timeZone:'America/Mexico_City'});
    root.querySelector('.diagnostic-date').textContent=(running?'Diagnóstico en curso':historical?'Resultado guardado (histórico)':'Diagnóstico terminado')+' · '+date+(data.finished?' · Fin: '+new Date(data.finished*1000).toLocaleTimeString('es-MX',{timeZone:'America/Mexico_City'}):'');
    root.querySelector('.diagnostic-stale').hidden=!data.stale;
    const list=root.querySelector('ol'); list.replaceChildren();
    data.stages.forEach(step=>{
      const li=document.createElement('li'), line=document.createElement('div');
      li.dataset.state=Object.hasOwn(labels,step.state)?step.state:'no_comprobada';
      const title=document.createElement('strong'), status=document.createElement('span'), message=document.createElement('p');
      title.textContent=step.label; status.textContent=labels[step.state]||'No comprobada'; status.className='diagnostic-state';message.textContent=step.message;
      line.append(title,status);li.append(line,message);list.append(li);
    });
    root.querySelector('.diagnostic-summary').textContent=data.summary;
  }
  async function responseData(response){
    const data=await response.json();
    if(!response.ok)throw new Error(data.message||'No se pudo consultar el diagnóstico.');
    return data;
  }
  async function poll(){
    if(!root.isConnected)return;
    try{
      const data=await responseData(await fetch(root.dataset.status,{cache:'no-store'}));
      error.hidden=true;show(data);
      if(data.running)setTimeout(poll,700);
    }catch(e){
      if(!root.isConnected)return;
      error.textContent='No se pudo consultar el progreso. Reintentando…';error.hidden=false;
      setTimeout(poll,2000);
    }
  }
  form.addEventListener('submit',async event=>{
    event.preventDefault();if(running)return;
    running=true;button.disabled=true;error.hidden=true;
    try{
      const data=await responseData(await fetch(root.dataset.start,{method:'POST',body:new FormData(form)}));
      show(data);setTimeout(poll,300);
    }catch(e){
      error.textContent=e.message||'No se pudo iniciar el diagnóstico. Recarga para consultar el resultado guardado.';error.hidden=false;
      running=false;button.disabled=false;
    }
  });
  if(root.dataset.running==='true'){running=true;button.disabled=true;poll();}
});
}
bindDiagnostics();
