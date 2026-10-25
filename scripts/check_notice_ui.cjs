// Revisión en navegador del programa con un estado temporal vacío.
const {chromium} = require('playwright');
const fs = require('node:fs');
const assert = require('node:assert/strict');

(async()=>{
  fs.mkdirSync('build/interfaz-limpia',{recursive:true});
  const runtime=JSON.parse(fs.readFileSync(process.argv[2]||'.local/ui-cleanup-preview/runtime.json','utf8'));
  const browser=await chromium.launch({channel:'msedge',headless:true});
  try {
    const page=await browser.newPage({viewport:{width:1280,height:900}});
    const errors=[];page.on('pageerror',error=>errors.push(error.message));
    assert.equal((await page.goto(runtime.launch_url)).status(),200,'Reinicia la vista temporal para renovar el enlace');
    await page.clock.install();
    for(const path of ['/','/clientes/','/conexiones/','/conexiones/nueva/']){
      assert.equal((await page.goto(new URL(path,runtime.launch_url).href)).status(),200);
      assert.equal(await page.locator('h1').count(),1);
      for(const width of [1280,390]){
        await page.setViewportSize({width,height:900});
        assert(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),path+' desborda');
      }
    }
    await page.goto(new URL('/',runtime.launch_url).href);
    await page.setViewportSize({width:1280,height:900});
    await page.screenshot({path:'build/interfaz-limpia/analytics-desktop.png',fullPage:true});
    async function notice(text){
      await page.evaluate(text=>{
        const node=document.createElement('div');node.className='flash';
        node.dataset.notice='';node.textContent=text;
        document.querySelector('main').prepend(node);bindNotices();
      },text);
    }
    await notice('Guardado de prueba');
    assert.equal(await page.getByRole('button',{name:'Cerrar aviso'}).count(),1);
    await page.clock.fastForward(6100);
    assert.equal(await page.locator('[data-notice]').count(),0);
    await notice('Guardado de prueba');
    assert.equal(await page.locator('[data-notice]').count(),0,'No debe reaparecer al actualizar');
    await notice('Cierre manual de prueba');
    await page.getByRole('button',{name:'Cerrar aviso'}).click();
    assert.equal(await page.locator('[data-notice]').count(),0);
    await notice('Pausa con teclado');
    await page.getByRole('button',{name:'Cerrar aviso'}).focus();
    await page.clock.fastForward(7000);
    assert.equal(await page.locator('[data-notice]').count(),1);
    await page.getByRole('button',{name:'Cerrar aviso'}).evaluate(el=>el.blur());
    await page.mouse.move(0,0);
    await page.clock.fastForward(6100);
    assert.equal(await page.locator('[data-notice]').count(),0);
    assert.deepEqual(errors,[]);
    console.log('OK: cuatro pantallas a 1280/390px; cierre automático, manual, pausa de teclado y avisos sin repetición.');
  } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
