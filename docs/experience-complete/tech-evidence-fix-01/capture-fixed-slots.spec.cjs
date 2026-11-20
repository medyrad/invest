const {test, expect} = require('../../../.tools/pw-min/node_modules/@playwright/test');
const fs = require('node:fs');
const path = require('node:path');

const product = process.env.PRODUCT_URL || 'http://127.0.0.1:3120';
const seed = process.env.SYNTHETIC_SEED || 'seed_core_demo@0380bbf-product-baseline-79519bb8';
const binding = process.env.CAPTURE_BINDING_JSON ? JSON.parse(process.env.CAPTURE_BINDING_JSON) : null;

const captures = [
  {row: 'DES-003', name: 'proposal-summary', route: '/tools/proposal', state: 'step-3: جمع‌بندی راهنمای اولیه', widths: [360, 768], summary: true},
  {row: 'DES-009', name: 'foreign-investment-step1', route: '/tools/foreign-investment', state: 'step-1: خانواده همکاری، مسیر، پروژه و کشور', widths: [360, 390, 768], summary: false},
  {row: 'DES-014', name: 'ma-renewal-step1', route: '/tools/ma-renewal', state: 'step-1: فرم اختصاصی نوسازی و اسکان موقت', widths: [360, 768], summary: false},
  {row: 'DES-021', name: 'charity-summary', route: '/tools/charity', state: 'step-2: جمع‌بندی اثر با فرض‌ها و پیگیری', widths: [390, 768], summary: true},
];

async function stable(page) {
  await page.waitForLoadState('domcontentloaded');
  await page.evaluate(() => document.fonts.ready);
  await page.waitForTimeout(300);
}

async function fillVisible(page) {
  const editor = page.locator('.service-editor');
  for (let pass = 0; pass < 4; pass++) {
    const radios = editor.locator('form input[type=radio]:visible');
    if (await radios.count() && !await editor.locator('form input[type=radio]:checked').count()) await radios.first().check();
    for (const select of await editor.locator('form select:visible').all()) {
      if (await select.inputValue()) continue;
      const value = await select.locator('option').evaluateAll(options => options.map(option => option.value).find(value => value));
      if (value) await select.selectOption(value);
    }
    for (const input of await editor.locator('form input:not([type=checkbox]):not([type=radio]):visible, form textarea:visible').all()) {
      if (await input.inputValue()) continue;
      const label = await input.getAttribute('aria-label') || '';
      const numeric = await input.getAttribute('inputmode') === 'decimal';
      await input.fill(label.includes('مبنای شروع') ? 'unspecified' : numeric ? '10' : 'داده مصنوعی شاهد فنی');
    }
    const checks = editor.locator('form input[type=checkbox]:visible');
    if (await checks.count() && !await checks.first().isChecked()) await checks.first().check();
    await page.waitForTimeout(350);
  }
}

async function reachSummary(page) {
  for (let step = 0; step < 4 && !await page.locator('.service-summary').count(); step++) {
    await fillVisible(page);
    const next = page.getByRole('button', {name: /^ادامه به /});
    if (!await next.count()) break;
    await next.click();
    await page.waitForTimeout(450);
  }
  await expect(page.locator('.service-summary')).toBeVisible();
}

async function interactionState(page) {
  const controls = page.locator('main button:visible, main a:visible, main input:visible, main select:visible, main textarea:visible');
  const count = await controls.count();
  let focus = false;
  let hit = false;
  if (count) {
    const first = controls.first();
    await first.scrollIntoViewIfNeeded();
    await first.focus();
    focus = await first.evaluate(element => element === document.activeElement);
    hit = await first.evaluate(element => {
      const rect = element.getBoundingClientRect();
      const x = Math.max(0, Math.min(innerWidth - 1, rect.left + rect.width / 2));
      const y = Math.max(0, Math.min(innerHeight - 1, rect.top + rect.height / 2));
      const target = document.elementFromPoint(x, y);
      return target === element || Boolean(target && element.contains(target));
    });
  }
  const geometry = await page.evaluate(() => ({
    viewport: {width: innerWidth, height: innerHeight},
    canvas: {width: document.documentElement.scrollWidth, height: document.documentElement.scrollHeight},
    overflow: document.documentElement.scrollWidth > innerWidth + 1,
    fonts: document.fonts.status,
    motion: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'reduce' : 'no-preference',
  }));
  expect(count).toBeGreaterThan(0);
  expect(focus).toBeTruthy();
  expect(hit).toBeTruthy();
  expect(geometry.overflow).toBeFalsy();
  expect(geometry.fonts).toBe('loaded');
  const expandedAccordions = await page.locator('main button[aria-expanded="true"]:visible').count();
  return {controls: count, focus, hit, expanded_accordions: expandedAccordions, ...geometry};
}

async function writeEvidence(page, browser, item, width) {
  const evidence = path.join(__dirname, `design-${item.name}-${width}.png`);
  const interaction = await interactionState(page);
  await page.screenshot({path: evidence, fullPage: true, animations: 'disabled'});
  const metadata = {
    schema: 'invest.design-capture@1',
    row_id: item.row,
    route: item.route,
    state: item.state,
    identity: 'guest',
    synthetic_seed: seed,
    product_url: product,
    final_url: page.url(),
    viewport_width: width,
    viewport_height: 1000,
    browser: {engine: 'chromium', version: browser.version(), playwright: require('../../../.tools/pw-min/node_modules/@playwright/test/package.json').version},
    captured_at_utc: new Date().toISOString(),
    font_condition: 'document.fonts.ready + status=loaded',
    motion_condition: 'reduced',
    interaction,
    evidence_file: path.basename(evidence),
    ...(binding ? {runtime_binding: binding} : {}),
  };
  fs.writeFileSync(path.join(__dirname, `capture-${item.name}-${width}.json`), JSON.stringify(metadata, null, 2) + '\n');
}

for (const item of captures) for (const width of item.widths) {
  test(`${item.row} exact route/state ${width}`, async ({browser}) => {
    const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
    const page = await context.newPage();
    await page.goto(product + item.route);
    await stable(page);
    await expect(page.locator('.service-editor form')).toBeVisible();
    if (item.summary) await reachSummary(page);
    else await expect(page.locator('.service-summary')).toHaveCount(0);
    await writeEvidence(page, browser, item, width);
    await context.close();
  });
}

for (const width of [360, 390, 768, 1440]) {
  test(`DES-035 library provenance capture ${width}`, async ({browser}) => {
    const context = await browser.newContext({viewport: {width, height: 1000}, reducedMotion: 'reduce'});
    const page = await context.newPage();
    await page.goto(product + '/library');
    await stable(page);
    const accordion = page.locator('main button:visible').first();
    const before = await accordion.getAttribute('aria-expanded');
    if (before !== 'true') await accordion.click();
    const after = await accordion.getAttribute('aria-expanded');
    expect(after).toBe('true');
    await writeEvidence(page, browser, {row: 'DES-035', name: 'library', route: '/library', state: 'topic-index;accordion-open'}, width);
    await context.close();
  });
}
