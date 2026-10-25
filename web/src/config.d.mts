export type Config = {router:string;lan:string;host:string;port:string;linux:string;api:string};
export const defaults: Config;
export function ipv4(s:string):boolean;
export function validate(c:Config):string;
export function substitute(text:string,c:Config):string;
