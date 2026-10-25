// Native browser validation against a server-rendered, isolated form fixture.
// All requests are intercepted: this test cannot connect to a Raspberry/router.
const {chromium}=require('playwright');
const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1024,height:768}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.route('**/*',route=>{
   const url=new URL(route.request().url());
   if(url.pathname==='/conexiones/nueva/')return route.fulfill({contentType:'text/html',body:fs.readFileSync('build/form-validation/connect.html')});
   if(url.pathname.startsWith('/static/portal/')){
    const file=path.resolve('portal/static/portal',url.pathname.slice('/static/portal/'.length));
    assert(file.startsWith(path.resolve('portal/static/portal')+path.sep));
    return route.fulfill({path:file});
   }
   return route.abort();
  });
  await page.goto('http://127.0.0.1/conexiones/nueva/');
  await page.evaluate(()=>{
   window.submissions=0;
   document.querySelector('#connect-form').addEventListener('submit',event=>{event.preventDefault();window.submissions++;});
  });
  for(const [name,value] of Object.entries({name:'Prueba aislada',host:'127.0.0.1',ssh_user:'synthetic',ssh_password:'synthetic-only',router_user:'synthetic',router_password:'synthetic-only'}))await page.locator(`[name=${name}]`).fill(value);
  assert.equal(await page.locator('details').getAttribute('open'),null);
  await page.locator('[data-busy]').click();
  assert.equal(await page.evaluate(()=>window.submissions),0);
  assert(await page.locator('details').evaluate(el=>el.open));
  assert(await page.locator('[data-validation-summary]').isVisible());
  assert((await page.locator('[data-validation-summary]').textContent()).includes('Certificado CA en Raspberry'));
  assert(await page.locator('[name=ca_file]').evaluate(el=>el===document.activeElement));
  assert(!(await page.locator('[data-busy]').isDisabled()));
  // A second hidden mandatory field must be revealed on Enter too.
  await page.locator('[name=ca_file]').fill('/tmp/synthetic-ca.crt');
  await page.locator('[name=python_path]').fill('');
  await page.locator('summary').click();
  await page.locator('[name=router_password]').press('Enter');
  assert.equal(await page.evaluate(()=>window.submissions),0);
  assert(await page.locator('details').evaluate(el=>el.open));
  assert((await page.locator('[data-validation-summary]').textContent()).includes('Python con librouteros'));
  await page.locator('[name=python_path]').fill('/usr/bin/python3');
  assert(!(await page.locator('[data-validation-summary]').isVisible()));
  await page.locator('[data-busy]').click();
  assert.equal(await page.evaluate(()=>window.submissions),1);
  assert(await page.locator('[data-busy]').isDisabled());
  assert(await page.locator('.connection-progress').isVisible());
  assert.deepEqual(errors,[]);
  console.log('OK: missing CA and Python open their section and show clear errors; mouse/Enter, focus, retry and valid-submit progress work. No network connection.');
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
