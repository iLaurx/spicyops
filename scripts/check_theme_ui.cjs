const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const context=await browser.newContext({viewport:{width:1440,height:1000}});
  const page=await context.newPage(),errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>new URL(route.request().url()).hostname==='127.0.0.1'?route.continue():route.abort());
  const read=mode=>JSON.parse(fs.readFileSync(`build/redesign/${mode}/runtime.json`,'utf8'));
  await page.goto(read('synthetic').launch_url);
  assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  const toggle=page.getByRole('button',{name:'Modo oscuro',exact:true});
  assert.equal(await toggle.getAttribute('aria-pressed'),'true');
  await toggle.click();
  assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
  await page.reload();assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
  // Ports change between launches; the appearance cookie must retain the choice.
  await page.goto(read('empty').launch_url);
  assert.equal(await page.locator('html').getAttribute('data-theme'),'light');
  await toggle.click();assert.equal(await page.locator('html').getAttribute('data-theme'),'dark');
  await page.goto(read('synthetic').launch_url);
  const origin=new URL(page.url()).origin;
  await page.goto(origin+'/clientes/?site=north');
  await page.locator('.client-details-button').first().click();
  await page.locator('dialog[open] input[name=alias]').fill('Borrador sin perder');
  // Switch underneath a modal via the DOM, preserving its focus trap and draft.
  await toggle.evaluate(el=>el.click());
  assert.equal(await page.locator('dialog[open] input[name=alias]').inputValue(),'Borrador sin perder');
  await toggle.evaluate(el=>el.click());await page.keyboard.press('Escape');
  await page.locator('.suspension-switch').first().click();
  for(const width of [1440,430]){
   await page.setViewportSize({width,height:900});
   await page.screenshot({path:`build/redesign/dark-confirmation-${width}.png`,fullPage:true});
  }
  await page.keyboard.press('Escape');
  await page.goto(origin+'/conexiones/nueva/');
  await page.locator('[name=name]').fill('Borrador de localidad');
  await toggle.click();await toggle.click();
  assert.equal(await page.locator('[name=name]').inputValue(),'Borrador de localidad');
  for(const width of [360,430,768,1024,1440]){
   await page.setViewportSize({width,height:900});
   assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  }
  // A denied localStorage must not prevent appearance selection or initialization.
  const fallback=await browser.newContext();
  await fallback.addInitScript(()=>{Storage.prototype.getItem=()=>{throw Error('denied')};Storage.prototype.setItem=()=>{throw Error('denied')};});
  const other=await fallback.newPage();other.on('pageerror',e=>errors.push(e.message));
  await other.goto(read('empty').launch_url);
  assert.equal(await other.locator('html').getAttribute('data-theme'),'dark');
  await other.getByRole('button',{name:'Modo oscuro',exact:true}).click();
  await other.reload();assert.equal(await other.locator('html').getAttribute('data-theme'),'light');
  await fallback.close();assert.deepEqual(errors,[]);
  console.log('OK: dark default, light/dark toggle, reload and changed-port persistence, denied storage, drafts/modals, five responsive widths; no real connections.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
