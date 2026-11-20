const {test, expect} = require('../../../.tools/pw-min/node_modules/@playwright/test');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');

const product = process.env.PRODUCT_URL || 'http://127.0.0.1:3120';
const cases = [
  {name: 'proposal-summary', route: '/tools/proposal', width: 360, summary: true, marker: 'جمع‌بندی معرفی طرح و نیاز مالی', capture: true},
  {name: 'foreign-investment-step1', route: '/tools/foreign-investment', width: 390, summary: false, marker: 'سرمایه‌گذاری، تامین مالی و همکاری بین‌المللی'},
  {name: 'ma-renewal-step1', route: '/tools/ma-renewal', width: 360, summary: false, marker: 'پرونده فرصت و خدمات تکمیلی'},
  {name: 'charity-summary', route: '/tools/charity', width: 390, summary: true, marker: 'جمع‌بندی همراهی در کار خیر'},
];

async function stable(page) {
  await page.waitForLoadState('domcontentloaded');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(250);
}

async function fill(page) {
  const editor = page.locator('.service-editor');
  for (let pass = 0; pass < 4; pass++) {
    const radios = editor.locator('form input[type=radio]:visible');
    if (await radios.count() && !await editor.locator('form input[type=radio]:checked').count()) await radios.first().check();
    for (const select of await editor.locator('form select:visible').all()) {
      if (await select.inputValue()) continue;
      const value = await select.locator('option').evaluateAll(options => options.map(o => o.value).find(Boolean));
      if (value) await select.selectOption(value);
    }
    for (const input of await editor.locator('form input:not([type=checkbox]):not([type=radio]):visible, form textarea:visible').all()) {
      if (await input.inputValue()) continue;
      const numeric = await input.getAttribute('inputmode') === 'decimal';
      const label = await input.getAttribute('aria-label') || '';
      await input.fill(label.includes('مبنای شروع') ? 'unspecified' : numeric ? '10' : 'داده مصنوعی بازآزمایی مستقل');
    }
    const checks = editor.locator('form input[type=checkbox]:visible');
    if (await checks.count() && !await checks.first().isChecked()) await checks.first().check();
    await page.waitForTimeout(250);
  }
}

async function summary(page) {
  for (let step = 0; step < 4 && !await page.locator('.service-summary').count(); step++) {
    await fill(page);
    const next = page.getByRole('button', {name: /^ادامه به /});
    if (!await next.count()) break;
    await next.click();
    await page.waitForTimeout(350);
  }
  await expect(page.locator('.service-summary')).toBeVisible();
}

for (const item of cases) test(`independent ${item.name}`, async ({browser}) => {
  const context = await browser.newContext({viewport: {width: item.width, height: 1000}, reducedMotion: 'reduce'});
  const page = await context.newPage();
  await page.goto(product + item.route);
  await stable(page);
  await expect(page.locator('.service-editor')).toBeVisible();
  if (item.summary) await summary(page);
  else await expect(page.locator('.service-summary')).toHaveCount(0);
  await expect(page.locator('main')).toContainText(item.marker);
  const control = page.locator('main button:visible, main input:visible, main select:visible, main textarea:visible').first();
  await control.scrollIntoViewIfNeeded();
  await control.focus();
  const focus = await control.evaluate(el => el === document.activeElement);
  const hit = await control.evaluate(el => { const r=el.getBoundingClientRect(); const t=document.elementFromPoint(r.left+r.width/2,r.top+r.height/2); return t===el || Boolean(t&&el.contains(t)); });
  const geometry = await page.evaluate(() => ({width: innerWidth, canvas: document.documentElement.scrollWidth, overflow: document.documentElement.scrollWidth > innerWidth + 1, fonts: document.fonts.status, motion: matchMedia('(prefers-reduced-motion: reduce)').matches}));
  expect(focus).toBeTruthy(); expect(hit).toBeTruthy(); expect(geometry.overflow).toBeFalsy(); expect(geometry.fonts).toBe('loaded'); expect(geometry.motion).toBeTruthy();
  const observation = {route: item.route, state: item.summary ? 'summary' : 'step-1', marker: item.marker, width: item.width, final_url: page.url(), focus, hit, geometry};
  fs.writeFileSync(path.join(__dirname, `browser-${item.name}.json`), JSON.stringify(observation, null, 2) + '\n');
  if (item.capture) {
    const screenshot = path.join(__dirname, 'independent-proposal-summary-360.png');
    await page.screenshot({path: screenshot, fullPage: true, animations: 'disabled'});
    const metadata = {
      schema: 'invest.tech-evidence-fix.independent-capture@1', route: item.route, state: 'step-3: جمع‌بندی راهنمای اولیه', identity: 'guest',
      synthetic_seed: 'independent-retest-01', product_url: product, final_url: page.url(), viewport_width: item.width, viewport_height: 1000,
      browser: {engine: 'chromium', version: browser.version(), playwright: require('../../../.tools/pw-min/node_modules/@playwright/test/package.json').version},
      captured_at_utc: new Date().toISOString(), font_condition: 'document.fonts.ready + status=loaded', motion_condition: 'reduced',
      runtime: {frontend_image_id: process.env.FRONTEND_IMAGE_ID, backend_image_id: process.env.BACKEND_IMAGE_ID, frontend_build_id: process.env.FRONTEND_BUILD_ID},
      evidence_file: path.basename(screenshot), evidence_sha256: crypto.createHash('sha256').update(fs.readFileSync(screenshot)).digest('hex'), observation,
    };
    fs.writeFileSync(path.join(__dirname, 'independent-capture-provenance.json'), JSON.stringify(metadata, null, 2) + '\n');
  }
  await context.close();
});

