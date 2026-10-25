import { defineConfig } from 'vite';
export default defineConfig({ base: process.env.SITE_BASE || '/', server: { host: '127.0.0.1' } });
