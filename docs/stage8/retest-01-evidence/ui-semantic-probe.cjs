const fs = require('fs');
const {chromium} = require('@playwright/test');

const baseURL = 'http://127.0.0.1:3108';
const output = '/repo/docs/stage8/retest-01-evidence';
const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE;
const kinds = [
  'proposal', 'ideas', 'land-preparation', 'foreign-investment',
  'ma-notice', 'ma-renewal', 'ma-manager', 'ma-exchange', 'charity',
];

async function fillVisible(page) {
  for (let pass = 0; pass < 4; pass += 1) {
    const radios = page.locator('.service-editor form input[type="radio"]:visible');
    if (await radios.count() && !await page.locator('.service-editor form input[type="radio"]:checked').count()) {
      await radios.first().check();
    }
    for (const select of await page.locator('.service-editor form select:visible').all()) {
      if (await select.inputValue()) continue;
      const value = await select.locator('option').evaluateAll(options =>
        options.map(option => option.value).find(Boolean));
      if (value) await select.selectOption(value);
    }
    for (const input of await page.locator(
      '.service-editor form textarea:visible, .service-editor form input:visible:not([type="checkbox"]):not([type="radio"])'
    ).all()) {
      if (await input.inputValue()) continue;
      await input.fill(await input.getAttribute('inputmode') === 'decimal' ? '1' : 'داده مصنوعی بازآزمایی');
    }
  }
}

(async () => {
  const browser = await chromium.launch({executablePath});
  const result = {titles: {}, boolean: {}};
  try {
    for (const kind of kinds) {
      const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
      const response = await page.goto(`${baseURL}/tools/${kind}`, {waitUntil: 'domcontentloaded'});
      await page.locator('.service-editor form').waitFor({state: 'visible', timeout: 20000});
      const labels = await page.locator('.service-steps,.service-compact-steps').innerText();
      if (/renewal|notice|manager|exchange|true|false/.test(labels) || !/[آ-ی]/.test(labels)) {
        throw new Error(`non-Persian step label for ${kind}: ${labels}`);
      }
      result.titles[kind] = {status: response.status(), labels};
      await page.close();
    }

    const page = await browser.newPage({viewport: {width: 1440, height: 1000}});
    await page.goto(`${baseURL}/tools/charity`, {waitUntil: 'domcontentloaded'});
    const field = page.locator('[data-service-field="demo"]');
    const checkbox = field.locator('input[type="checkbox"]');
    result.boolean.unanswered = (await field.innerText()).includes('هنوز پاسخ داده نشده');
    await checkbox.check();
    result.boolean.trueLabel = (await field.innerText()).includes('پاسخ: بله');
    await checkbox.uncheck();
    result.boolean.falseLabel = (await field.innerText()).includes('پاسخ: خیر');
    await fillVisible(page);
    await page.locator('[data-service-field="type"] select').selectOption('cash');
    await page.locator('[data-service-field="amount"] select').first().selectOption('known');
    await page.locator('[data-service-field="amount"] input').fill('1');
    await page.locator('[data-service-field="frequency"] select').selectOption('once');
    await page.getByRole('button', {name: /^ادامه به /}).click();
    try {
      await page.locator('.service-summary').waitFor({state: 'visible', timeout: 20000});
    } catch {
      result.boolean.formErrors = await page.locator('[role="alert"]').allTextContents();
      await page.screenshot({path: `${output}/charity-probe-form-error.png`, fullPage: true});
      throw new Error(`charity form did not reach summary: ${JSON.stringify(result.boolean.formErrors)}`);
    }
    const row = page.locator('.service-summary dl>div').filter({has: page.locator('dt', {hasText: 'سناریوی آموزشی محله فرضی الف'})});
    result.boolean.summary = await row.locator('dd').innerText();
    if (!result.boolean.unanswered || !result.boolean.trueLabel || !result.boolean.falseLabel || result.boolean.summary !== 'خیر') {
      throw new Error(`boolean display mismatch: ${JSON.stringify(result.boolean)}`);
    }
    await page.screenshot({path: `${output}/charity-false-summary-1440.png`, fullPage: true});

    const html = fs.readFileSync(`${output}/fresh-charity-false.html`, 'utf8');
    await page.setViewportSize({width: 360, height: 800});
    await page.setContent(html);
    result.freshHtml = {
      title: await page.title(),
      overflow: await page.evaluate(() => document.documentElement.scrollWidth > innerWidth),
      falseLabel: (await page.locator('body').innerText()).includes('خیر'),
    };
    if (result.freshHtml.overflow || !result.freshHtml.falseLabel) throw new Error('fresh HTML rendering failed');
    await page.screenshot({path: `${output}/fresh-charity-false-360.png`, fullPage: true});
    await page.close();

    fs.writeFileSync(`${output}/ui-semantic-probe.json`, JSON.stringify(result, null, 2) + '\n');
    console.log(JSON.stringify(result, null, 2));
  } finally {
    await browser.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
