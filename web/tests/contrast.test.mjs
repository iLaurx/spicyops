import {test} from 'node:test';
import assert from 'node:assert/strict';
function luminance(hex){const c=hex.match(/\w\w/g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return .2126*c[0]+.7152*c[1]+.0722*c[2];}
test('text palette meets 4.5:1 on the selected paper backgrounds',()=>{
 for(const fg of ['18213d','4f535b','59594f','236c70'])for(const bg of ['f6eddd','efe3d1','e9dcca','f9f2e5','f8f0e3']){
  const a=luminance(fg),b=luminance(bg),ratio=(Math.max(a,b)+.05)/(Math.min(a,b)+.05);
  assert.ok(ratio>=4.5,`${fg}/${bg}: ${ratio.toFixed(2)}`);
 }
 assert.ok((luminance('f9f2e5')+.05)/(luminance('18213d')+.05)>=4.5);
});
