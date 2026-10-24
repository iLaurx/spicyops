const {chromium}=require('playwright');
const fs=require('node:fs');
const assert=require('node:assert/strict');
(async()=>{
 const runtime=JSON.parse(fs.readFileSync(process.argv[2],'utf8'));
 const browser=await chromium.launch({channel:'msedge',headless:true});
 try{
  const page=await browser.newPage({viewport:{width:1280,height:900}});
  const errors=[];page.on('pageerror',e=>errors.push(e.message));
  await page.goto(runtime.launch_url);
  for(const path of ['/','/clientes/','/conexiones/','/conexiones/nueva/','/respaldo/']){
   assert.equal((await page.goto(new URL(path,runtime.launch_url).href)).status(),200);
   assert(!(await page.title()).includes('<'), 'El título contiene HTML');
   for(const width of [1280,390]){
    await page.setViewportSize({width,height:900});
    assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),path+' overflow '+width);
   }
  }
  for(const width of [1280,390]){
   await page.setViewportSize({width,height:900});
   await page.screenshot({path:`build/release-1.0.0/recovery-${process.argv[3]}-${width}.png`,fullPage:true});
  }
  assert.deepEqual(errors,[]);
  console.log('OK: cinco vistas 1280/390px sin desbordamiento ni errores JS ('+process.argv[3]+').');
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
