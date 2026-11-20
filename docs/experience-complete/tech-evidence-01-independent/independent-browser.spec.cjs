const {test, expect} = require('../../../.tools/pw-min/node_modules/@playwright/test');
const fs = require('node:fs');

const product = process.env.PRODUCT_URL || 'http://127.0.0.1:3118';
const widths = [360, 390, 768, 1440];

for (const width of widths) {
  test(`independent interactive sample ${width}`, async ({browser}) => {
    const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
    const page = await context.newPage();
    page.setDefaultTimeout(15_000);
    await page.goto(product + '/library');
    await page.evaluate(() => document.fonts.ready);
    const controls = page.locator('main button:visible, main a:visible, main input:visible, main select:visible, main textarea:visible');
    expect(await controls.count()).toBeGreaterThan(0);
    const first = controls.first();
    await first.focus();
    const focus = await first.evaluate(el => el === document.activeElement);
    const hit = await first.evaluate(el => {
      const r = el.getBoundingClientRect();
      const x = Math.max(0, Math.min(innerWidth - 1, r.left + r.width / 2));
      const y = Math.max(0, Math.min(innerHeight - 1, r.top + r.height / 2));
      const target = document.elementFromPoint(x, y);
      return target === el || Boolean(target && el.contains(target));
    });
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth + 1);
    expect(focus).toBeTruthy();
    expect(hit).toBeTruthy();
    expect(overflow).toBeFalsy();

    const input = page.locator('main input:visible').first();
    let libraryInput = false;
    if (await input.count()) {
      await input.fill('زمین');
      libraryInput = (await input.inputValue()) === 'زمین';
      expect(libraryInput).toBeTruthy();
    }
    const accordion = page.locator('main button:visible').first();
    const expandedBefore = await accordion.getAttribute('aria-expanded');
    await accordion.click();
    const expandedAfter = await accordion.getAttribute('aria-expanded');
    const accordionClick = expandedBefore !== expandedAfter;
    expect(accordionClick).toBeTruthy();
    const row = {width, route: '/library', focus, hit, overflow, libraryInput, accordionClick, expandedBefore, expandedAfter, fonts: 'document.fonts.ready', motion: 'reduce'};
    fs.writeFileSync(`${__dirname}/browser-interaction-${width}.json`, JSON.stringify(row, null, 2) + '\n');
    await page.screenshot({path: `${__dirname}/browser-library-${width}.png`, fullPage: true});
    await context.close();
  });
}
