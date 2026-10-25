import {test} from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync,readdirSync} from 'node:fs';
const guide=JSON.parse(readFileSync('src/content/guide.json','utf8'));
test('ten preparation stages plus quick access, both permission paths, valid local download',()=>{
 assert.deepEqual(guide.filter(g=>g.step).map(g=>g.step),Array.from({length:10},(_,i)=>i+1));
 const body=guide.map(g=>g.body).join('\n');
 assert.ok(body.includes('read,write,api'));assert.ok(body.includes('read,api,!write'));
 assert.equal(readFileSync('public/downloads/spicyops-check-api.py','utf8').trim(),guide.find(g=>g.id==='lecturas-api').body.match(/```python\n([\s\S]*?)\n```/)[1]);
});
test('generated HTML is complete without JS; markers block copy; no secret input',()=>{
 const html=readFileSync('index.html','utf8');
 assert.equal((html.match(/data-step=/g)||[]).length,10);
 for(const match of html.matchAll(/<figure class="command"[\s\S]*?<\/figure>/g)) {
  if(/&lt;[A-Z_]+&gt;/.test(match[0]))assert.match(match[0],/class="copy" disabled/);
 }
 assert.doesNotMatch(html,/<input[^>]+type="password"/);
 assert.doesNotMatch(html,/<script[^>]+src="https?:/);
 assert.ok(html.includes('id="modo-escritura"'));
});
test('published artifact allowlist excludes private state and internal sources',()=>{
 const walk=dir=>readdirSync(dir,{withFileTypes:true}).flatMap(f=>f.isDirectory()?walk(`${dir}/${f.name}`):[`${dir}/${f.name}`]);
 for(const path of walk('dist'))assert.match(path,/^dist\/(index\.html|assets\/[\w.-]+\.(js|css)|fonts\/[\w.-]+\.(woff2|txt)|downloads\/(guia-spicyops\.md|spicyops-check-api\.py))$/);
});
