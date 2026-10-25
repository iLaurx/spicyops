// Review actual loopback pages, with synthetic and empty states prepared separately.
const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
const out='build/redesign';
const prefix=process.env.SPICYOPS_UI_THEME==='light'?'light-':'';
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const errors=[], external=[];
 try{
  for(const mode of ['synthetic','empty']){
   for(let attempt=0;attempt<100&&!fs.existsSync(`${out}/${mode}/runtime.json`);attempt++)await new Promise(resolve=>setTimeout(resolve,100));
   const runtime=JSON.parse(fs.readFileSync(`${out}/${mode}/runtime.json`,'utf8'));
   const page=await browser.newPage({viewport:{width:1440,height:1000}});
   if(prefix)await page.addInitScript(()=>localStorage.setItem('spicyops-theme','light'));
   page.on('pageerror',error=>errors.push(error.message));
   await page.route('**/*',route=>{
    if(new URL(route.request().url()).hostname!=='127.0.0.1'){external.push(route.request().url());return route.abort();}
    return route.continue();
   });
   await page.goto(runtime.launch_url);
   const paths=mode==='synthetic'?['/','/clientes/','/clientes/?site=all','/conexiones/','/conexiones/nueva/','/conexiones/north/configurar/','/inventario/north/','/respaldo/']:['/','/clientes/','/conexiones/','/conexiones/nueva/','/respaldo/'];
   for(const path of paths){
    const response=await page.goto(new URL(path,runtime.launch_url).href);
    assert.equal(response.status(),200,path);
    await page.evaluate(async()=>{await Promise.all(['Barlow','Barlow Semi Condensed','JetBrains Mono'].map(font=>document.fonts.load(`16px "${font}"`)));await document.fonts.ready;});
    assert.equal(await page.locator('h1').count(),1,path);
    for(const width of [360,430,768,1024,1440]){
     await page.setViewportSize({width,height:1000});
     assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),`${mode} ${path} overflow ${width}`);
     if([430,1440].includes(width)&&['/','/clientes/','/conexiones/','/conexiones/nueva/','/respaldo/'].includes(path)){
      const name=path==='/'?'analytics':path.split('/').filter(Boolean).join('-');
      await page.screenshot({path:`${out}/${prefix}${mode}-${name}-${width}.png`,fullPage:true});
     }
    }
    await page.setViewportSize({width:720,height:450}); // equivalent layout space at 200% on 1440×900
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),path+' zoom layout');
    await page.setViewportSize({width:1440,height:1000});
    await page.evaluate(()=>document.documentElement.style.zoom='2');
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),path+' 200% CSS zoom');
    await page.evaluate(()=>document.documentElement.style.zoom='');
    const fonts=await page.evaluate(async()=>{const names=['Barlow','Barlow Semi Condensed','JetBrains Mono'];await Promise.all(names.map(font=>document.fonts.load(`16px "${font}"`)));return names.every(font=>document.fonts.check(`16px "${font}"`));});
    assert(fonts,'Local fonts did not load: '+path);
   }
   if(mode==='synthetic'){
    await page.goto(new URL('/clientes/?site=north',runtime.launch_url).href);
    await page.locator('.suspension-switch').first().click();
    assert.equal(await page.locator('dialog[open]').count(),1);
    for(const width of [1440,430,360]){
     await page.setViewportSize({width,height:900});
     const box=await page.locator('dialog[open]').boundingBox();assert(box.x>=0&&box.x+box.width<=width);
     await page.screenshot({path:`${out}/${prefix}confirmation-${width}.png`,fullPage:true});
    }
    await page.keyboard.press('Escape');assert.equal(await page.locator('dialog[open]').count(),0);
    assert(await page.locator('.suspension-switch').first().evaluate(el=>el===document.activeElement),'Dialog focus must return');
    await page.locator('.client-details-button').first().click();
    await page.locator('dialog[open] input[name=alias]').fill('Borrador visual');
    await page.evaluate(()=>updatePanel());
    assert.equal(await page.locator('dialog[open] input[name=alias]').inputValue(),'Borrador visual');
    await page.keyboard.press('Escape');
    await page.locator('#speed-unit').selectOption('mbs');
    assert.equal(await page.locator('.speed-label').textContent(),'MB/s');
    await page.reload();assert.equal(await page.locator('#speed-unit').inputValue(),'mbs');
    await page.locator('#speed-unit').selectOption('mbps');
    await page.goto(new URL('/clientes/?site=all&q=Valle%20del%20Sur',runtime.launch_url).href);
    assert.equal(await page.locator('.clients-table tbody tr').count(),7);
    await page.goto(new URL('/',runtime.launch_url).href);
    await page.locator('.bar-column').first().focus();
    assert(await page.locator('.bar-column').first().getAttribute('aria-label'));
   }
   await page.emulateMedia({reducedMotion:'reduce'});
   assert.equal(await page.evaluate(()=>getComputedStyle(document.querySelector('.button')).transitionDuration),'0s');
   await page.close();
  }
  const locked=await browser.newPage({viewport:{width:430,height:900}});
  const runtime=JSON.parse(fs.readFileSync(`${out}/empty/runtime.json`,'utf8'));
  assert.equal((await locked.goto(new URL('/',runtime.launch_url).href)).status(),401);
  assert.equal(await locked.locator('h1').textContent(),'SpicyOps');
  assert(await locked.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await locked.screenshot({path:`${out}/${prefix}locked-430.png`,fullPage:true});
  await locked.close();
  assert.deepEqual(errors,[]);assert.deepEqual(external,[]);
  console.log('OK: empty/synthetic pages at 360/430/768/1024/1440 and 720×450; local fonts, offline assets, modals/focus/drafts, units, locality search, chart keyboard labels, reduced motion; no JS errors.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
