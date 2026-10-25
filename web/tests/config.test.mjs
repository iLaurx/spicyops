import { test } from 'node:test';
import assert from 'node:assert/strict';
import { defaults, validate, substitute, ipv4 } from '../src/config.mjs';
test('scenario and valid DNS/port boundaries',()=>{
 assert.equal(validate(defaults),'');
 assert.equal(validate({...defaults,host:'raspberry.tail-example.ts.net',port:'65535'}),'');
 for(const value of ['256.0.0.1','01.2.3.4','1.2.3','1.2.3.4/32','http://1.2.3.4','::1']) assert.equal(ipv4(value),false);
 for(const port of ['0','65536','22.5','-1','22\n'])assert.ok(validate({...defaults,port}));
});
test('reject shell injection and HTML in every configurable field',()=>{
 for(const field of Object.keys(defaults)) for(const attack of ['$(whoami)','`whoami`','a;b','a\nb','a\rb','a\0b','a"b',"a'b",'<script>alert(1)</script>','../../etc/passwd','/a b']) assert.ok(validate({...defaults,[field]:attack}),`${field}: ${attack}`);
});
test('substitutions do not cascade and preserve shell syntax',()=>{
 const config={...defaults,router:'192.168.88.90',lan:'10.0.0.2',linux:'tecnico',api:'consulta',host:'rpi.tail.ts.net',port:'2222'};
 const text='192.168.88.1 192.168.88.90 ssh -p 22 operador@100.70.10.1 /home/operador spicyops-agent';
 assert.equal(substitute(text,config),'192.168.88.90 10.0.0.2 ssh -p 2222 tecnico@rpi.tail.ts.net /home/tecnico consulta');
});
