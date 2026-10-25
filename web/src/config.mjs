export const defaults = { router:'192.168.88.1', lan:'192.168.88.90', host:'100.70.10.1', port:'22', linux:'operador', api:'spicyops-agent' };
export function ipv4(s) {
 return /^(?:0|[1-9]\d{0,2})(?:\.(?:0|[1-9]\d{0,2})){3}$/.test(s) && s.split('.').every(n=>Number(n)<=255);
}
export function validate(c) {
 if (!ipv4(c.router) || !ipv4(c.lan)) return 'Usa IPv4 válidas de cuatro octetos para MikroTik y Raspberry LAN.';
 if (!c.host || c.host.length>253 || !c.host.split('.').every(p=>/^[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?$/.test(p)) || (/^[\d.]+$/.test(c.host) && !ipv4(c.host))) return 'Indica una IP o nombre de Raspberry válido, sin URL ni comandos.';
 if (!/^[1-9]\d{0,4}$/.test(c.port) || Number(c.port)>65535) return 'El puerto SSH debe ser un entero entre 1 y 65535.';
 if (![c.linux,c.api].every(s=>/^[a-z_][a-z0-9_-]{0,31}$/.test(s))) return 'Usuarios: hasta 32 letras minúsculas, números, guion o guion bajo; empieza con letra o guion bajo.';
 return '';
}
export function substitute(text,c) {
 // One pass: values cannot become executable shell syntax or replace one another.
 const map = { '192.168.88.1':c.router,'192.168.88.90':c.lan,'100.70.10.1':c.host,operador:c.linux,'spicyops-agent':c.api };
 if(text==='22')return c.port;
 return text.replace(/192\.168\.88\.90|192\.168\.88\.1(?!\d)|100\.70\.10\.1(?!\d)|spicyops-agent|operador/g,s=>map[s]).replace(/ssh -p 22/g,`ssh -p ${c.port}`).replace(/scp -P 22/g,`scp -P ${c.port}`).replace(/-Port 22/g,`-Port ${c.port}`).replace(/tcp:22/g,`tcp:${c.port}`).replace(/sport = :22/g,`sport = :${c.port}`).replace(/TCP 22/g,`TCP ${c.port}`);
}
