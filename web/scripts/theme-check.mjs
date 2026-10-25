import { chromium } from '@playwright/test';
import assert from 'node:assert/strict';
import { mkdirSync } from 'node:fs';

const base = process.env.QA_URL || 'http://127.0.0.1:4173/';
const browser = await chromium.launch({ channel: 'msedge', headless: true });
try {
  const context = await browser.newContext({ reducedMotion: 'reduce' });
  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto(base);
  await page.evaluate(() => document.fonts.ready);
  const theme = () => page.locator('html').getAttribute('data-theme');
  const toggle = page.locator('#theme-toggle');
  assert.equal(await theme(), 'dark');
  assert.equal(await toggle.getAttribute('aria-pressed'), 'true');
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor), 'rgb(20, 27, 34)');
  mkdirSync('evidence', { recursive: true });
  for (const width of [320, 360, 430, 768, 1024, 1440]) {
    await page.setViewportSize({ width, height: 1000 });
    assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth), `dark overflow at ${width}`);
    assert.ok(await toggle.evaluate(button => {
      const bounds = button.getBoundingClientRect();
      return bounds.left >= 0 && bounds.right <= innerWidth && bounds.top >= 0;
    }));
    if ([360, 1440].includes(width)) await page.screenshot({ path: `evidence/theme-dark-${width}.png` });
  }
  await toggle.focus();
  await page.keyboard.press('Space');
  assert.equal(await theme(), 'light');
  assert.equal(await toggle.getAttribute('aria-pressed'), 'false');
  await page.reload();
  assert.equal(await theme(), 'light');
  await page.screenshot({ path: 'evidence/theme-light-1440.png' });
  await toggle.click();
  await page.reload();
  assert.equal(await theme(), 'dark');
  const other = await context.newPage();
  await other.goto(base);
  await toggle.click();
  await other.waitForFunction(() => document.documentElement.dataset.theme === 'light');
  await other.close();
  await toggle.click();
  // Progress reset does not erase appearance.
  await page.locator('.progress-panel summary').click();
  await page.locator('#clear').click();
  assert.equal(await page.evaluate(() => localStorage.getItem('spicyops-guide-theme-v1')), 'dark');
  await page.locator('#search').fill('IP mismatch');
  assert.ok(await page.locator('#errores').isVisible());
  await page.locator('#search').fill('');
  await page.emulateMedia({ media: 'print' });
  assert.equal(await page.evaluate(() => getComputedStyle(document.documentElement).backgroundColor), 'rgb(255, 255, 255)');
  assert.equal(await toggle.isVisible(), false);
  assert.ok(await page.locator('#tailscale-raspberry').isVisible());
  await page.emulateMedia({ media: 'screen' });
  assert.equal(await theme(), 'dark');
  assert.deepEqual(errors, []);
  // Blocked storage still allows both themes and keeps the guide usable.
  const blocked = await browser.newContext();
  await blocked.addInitScript(() => Object.defineProperty(window, 'localStorage', { get() { throw new Error('Storage blocked'); } }));
  const privatePage = await blocked.newPage();
  await privatePage.goto(base);
  await privatePage.locator('#theme-toggle').click();
  assert.equal(await privatePage.locator('html').getAttribute('data-theme'), 'light');
  assert.ok(await privatePage.locator('#search').isVisible());
  await blocked.close();
  const noJs = await browser.newContext({ javaScriptEnabled: false });
  const staticPage = await noJs.newPage();
  await staticPage.goto(base);
  assert.equal(await staticPage.locator('#theme-toggle').isVisible(), false);
  assert.equal(await staticPage.locator('#chapters .chapter').count(), 17);
  await noJs.close();
  await context.close();
  console.log('Theme checks passed: palette, 6 widths, keyboard, reload, tabs, progress isolation, search, print, blocked storage and no-JS.');
} finally {
  await browser.close();
}
