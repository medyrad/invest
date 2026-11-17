/* TEST-S03-02: real Chrome journeys; no trace, cookie, flow or OTP in saved results. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '../../..');
const { chromium } = require(path.join(root, 'frontend/node_modules/@playwright/test'));
const evidence = path.join(root, 'docs/stage3/retest-evidence/compatibility');
const result = { cases: [], observations: [], browser: null };
let serial = 30;
const phone = () => '0917800' + String(serial++).padStart(4,'0');
const base = 'http://127.0.0.1:3109';
const pause = ms => new Promise(r => setTimeout(r,ms));
async function run(name, action) {
  if (!['two-tabs-logout-clears-displayed-private-identity','resend-lost-response-keeps-idempotency-key'].includes(name)) return;
  const start = Date.now();
  try { await action(); result.cases.push({name, status:'passed', milliseconds:Date.now()-start}); }
  catch(e) { result.cases.push({name, status:'failed', error:e.message.replace(/\b\d{6}\b/g,'[masked]'), milliseconds:Date.now()-start}); }
  fs.writeFileSync(path.join(evidence,'independent-browser.json'),JSON.stringify(result,null,2));
  console.log(name, result.cases.at(-1).status);
}
async function open(page, origin=base) {
  await page.goto(origin);
  await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();
  await page.getByRole('dialog').waitFor({state:'visible'});
}
async function issue(page, mobile=phone()) {
  await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).fill(mobile);
  await page.getByRole('button',{name:'دریافت کد',exact:true}).click();
  await page.getByTestId('trial-code').waitFor({state:'visible'});
  return (await page.getByTestId('trial-code').textContent()).trim();
}
async function shot(page,name) {
  await page.screenshot({path:path.join(evidence,name+'.png'),animations:'disabled',mask:[page.getByTestId('trial-code'),page.locator('.code-cells'),page.locator('.account-status p[dir="ltr"]')]});
}
async function authenticated(page) {return await page.evaluate(async()=> (await (await fetch('/api/v1/auth/me')).json()).authenticated);}
(async()=>{
 const browser = await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
 result.browser = browser.version();
 try {
  await run('live-3108-login-reload-logout-old-cookie', async()=>{
   const context=await browser.newContext({viewport:{width:1440,height:1000}});const page=await context.newPage();
   try {
    await open(page,'http://127.0.0.1:3108');
    const code=await issue(page,'۰۹۱۷۸۰۰۹۹۹۱');
    await page.getByRole('textbox',{name:'کد تایید',exact:true}).fill(code);
    await page.getByRole('button',{name:'ورود',exact:true}).click();
    await page.getByRole('region',{name:'وضعیت ورود'}).waitFor();
    const cookie=(await context.cookies()).find(c=>c.name==='invest_session');assert(cookie?.httpOnly);
    await page.goto('http://127.0.0.1:3108/?history=1');await page.reload();assert(await authenticated(page));
    await shot(page,'live-3108-authenticated');
    await page.getByRole('button',{name:'خروج',exact:true}).click();
    await page.getByRole('button',{name:'ورود به حساب',exact:true}).waitFor();
    assert.equal(await authenticated(page),false);
    await context.addCookies([cookie]);assert.equal(await authenticated(page),false);
    await page.goBack();await page.reload();assert.equal(await authenticated(page),false);
   } finally {await context.close();}
  });
  const formats=['۰۹۱۷۸۰۰۰۰۳۱','+٩٨٩١٧٨٠٠٠٠٣٢','00989178000033',' 09-178 000 034 '];
  for (const [i,width] of [360,390,768,1440].entries()) await run('viewport-'+width+'-paste-focus-scroll-login',async()=>{
   const context=await browser.newContext({viewport:{width,height:width===768?1000:844},permissions:['clipboard-read','clipboard-write']});const page=await context.newPage();
   try {
    await open(page);await page.evaluate(()=>document.fonts.ready);
    assert.equal(await page.evaluate(()=>document.activeElement?.getAttribute('aria-label')),'شماره موبایل');
    await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});assert.equal(await page.getByRole('dialog').isVisible(),false);
    assert.equal(await page.evaluate(()=>document.activeElement?.textContent),'ورود به حساب');
    await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();
    const code=await issue(page,formats[i]);
    const codeBox=page.getByRole('textbox',{name:'کد تایید',exact:true});
    await page.getByTestId('trial-code').scrollIntoViewIfNeeded();
    assert(await page.getByTestId('trial-code').isVisible());
    await shot(page,'independent-code-'+width);
    await codeBox.scrollIntoViewIfNeeded();await codeBox.click();
    await page.evaluate(value=>navigator.clipboard.writeText(value),code);
    await page.keyboard.press('Control+V');assert.equal(await codeBox.inputValue(),code);
    await page.keyboard.press('Tab');
    for(let n=0;n<8;n++){await page.keyboard.press('Tab');assert(await page.evaluate(()=>document.querySelector('dialog').contains(document.activeElement)));}
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true);
    const button=page.getByRole('button',{name:'ورود',exact:true});await button.scrollIntoViewIfNeeded();await button.click();
    await page.getByRole('region',{name:'وضعیت ورود'}).waitFor();assert(await authenticated(page));
    await page.getByRole('button',{name:'خروج',exact:true}).click();
   } finally {await context.close();}
  });
  await run('invalid-input-not-truncated-newline-bidi-long',async()=>{
   const context=await browser.newContext();const page=await context.newPage();
   try {
    await open(page);const input=page.getByRole('textbox',{name:'شماره موبایل',exact:true});
    for(const value of ['091780000000','09178000035X','09178000035\u202e','9'.repeat(70)]){
     await input.fill(value);assert.equal(await input.inputValue(),value);
     await page.getByRole('button',{name:'دریافت کد',exact:true}).click();
     await page.locator('.auth-error').waitFor();assert.equal(await page.getByTestId('trial-code').count(),0);
    }
    const response=await context.request.get(base+'/api/v1/auth/csrf');const csrf=(await response.json()).csrfToken;
    const flow=await context.request.post(base+'/api/v1/auth/flows',{headers:{'X-CSRFToken':csrf},data:{}});const token=(await flow.json()).flow_token;
    const invalid=await context.request.post(base+'/api/v1/auth/issue',{headers:{'X-CSRFToken':csrf,'X-Login-Flow':token},data:{mobile:'09178000035\n',key:require('node:crypto').randomUUID()}});
    assert.equal(invalid.status(),400);
   } finally {await context.close();}
  });
  await run('lost-first-issue-response-same-key-no-extra-issuance',async()=>{
   const context=await browser.newContext();const page=await context.newPage();let key;let challenge;let count=0;
   try {
    await open(page);
    await page.route('**/api/v1/auth/issue',async route=>{
     count++;const payload=route.request().postDataJSON();
     if(count===1){key=payload.key;const response=await route.fetch();challenge=(await response.json()).challenge_id;await route.abort('failed');}
     else {assert.equal(payload.key,key);const response=await route.fetch();assert.equal((await response.json()).challenge_id,challenge);await route.fulfill({response});}
    });
    await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).fill(phone());
    await page.getByRole('button',{name:'دریافت کد',exact:true}).click();await page.locator('.auth-error').waitFor();
    await page.getByRole('button',{name:'دریافت کد',exact:true}).click();await page.getByTestId('trial-code').waitFor();assert.equal(count,2);
   } finally {await context.close();}
  });
  await run('lost-entire-verify-response-no-cookie-requires-new-flow',async()=>{
   const context=await browser.newContext();const page=await context.newPage();
   try {
    await open(page);const code=await issue(page);
    await page.route('**/api/v1/auth/verify',async route=>{
     const response=await fetch(route.request().url(),{method:'POST',headers:await route.request().allHeaders(),body:route.request().postData()});assert.equal(response.status,200);
     await route.fulfill({status:502,headers:{'Content-Type':'application/json'},body:JSON.stringify({error:{message:'پاسخ آزمون دریافت نشد.'}})});
    });
    await page.getByRole('textbox',{name:'کد تایید',exact:true}).fill(code);
    await page.getByRole('button',{name:'ورود',exact:true}).click();await page.locator('.auth-error').waitFor();
    assert.equal(await authenticated(page),false);
    await page.unroute('**/api/v1/auth/verify');
    await page.getByRole('button',{name:'ورود',exact:true}).click();
    await page.waitForTimeout(150);assert.equal(await authenticated(page),false);
    await shot(page,'lost-verify-without-cookie');
    await page.getByRole('button',{name:'بستن پنجره ورود'}).click();await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();
    await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).waitFor();
   } finally {await context.close();}
  });
  await run('two-tabs-logout-clears-displayed-private-identity',async()=>{
   const context=await browser.newContext();const a=await context.newPage();const b=await context.newPage();
   try {
    await open(a);const code=await issue(a);await a.getByRole('textbox',{name:'کد تایید',exact:true}).fill(code);await a.getByRole('button',{name:'ورود',exact:true}).click();await a.getByRole('region',{name:'وضعیت ورود'}).waitFor();
    await b.goto(base);await b.getByRole('region',{name:'وضعیت ورود'}).waitFor();
    await a.getByRole('button',{name:'خروج',exact:true}).click();await a.getByRole('button',{name:'ورود به حساب',exact:true}).waitFor();
    await b.bringToFront();await b.getByRole('region',{name:'وضعیت ورود'}).waitFor({state:'hidden'});assert.equal(await authenticated(b),false);
    const stale=await b.getByRole('region',{name:'وضعیت ورود'}).isVisible();result.observations.push({name:'other-tab-after-logout',server_authenticated:false,private_identity_still_visible:stale});
    await shot(b,'two-tabs-stale-identity');assert.equal(stale,false,'Other tab still displays private account identity after logout');
   } finally {await context.close();}
  });
  await run('natural-session-usage-request-inventory',async()=>{
   const context=await browser.newContext();const page=await context.newPage();const paths=[];
   try {
    await open(page);const code=await issue(page);await page.getByRole('textbox',{name:'کد تایید',exact:true}).fill(code);await page.getByRole('button',{name:'ورود',exact:true}).click();await page.getByRole('region',{name:'وضعیت ورود'}).waitFor();
    page.on('request',r=>{if(r.url().includes('/api/'))paths.push(new URL(r.url()).pathname);});
    await page.reload();await page.getByRole('region',{name:'وضعیت ورود'}).waitFor();
    await page.keyboard.press('Tab');await page.mouse.wheel(0,200);await pause(1200);
    assert(!paths.includes('/api/v1/auth/activity'));const before=paths.length;
    await page.getByRole('button',{name:'بررسی و تمدید نشست',exact:true}).click();await page.getByText('نشست فعال است.',{exact:true}).waitFor();
    assert(paths.slice(before).includes('/api/v1/auth/activity'));
    result.observations.push({name:'activity',natural_paths:[...new Set(paths.slice(0,before))],explicit_button_calls_activity:true});
   } finally {await context.close();}
  });
  await run('slow-network-focus-and-no-double-submit',async()=>{
   const context=await browser.newContext();const page=await context.newPage();let calls=0;
   try {
    await open(page);
    await page.route('**/api/v1/auth/issue',async route=>{calls++;await pause(1500);await route.continue();});
    await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).fill(phone());
    await page.getByRole('button',{name:'دریافت کد',exact:true}).click();
    assert.equal(await page.getByRole('button',{name:'در حال بررسی…',exact:true}).isDisabled(),true);
    await page.keyboard.press('Enter');await page.getByTestId('trial-code').waitFor();assert.equal(calls,1);
   } finally {await context.close();}
  });
  await run('resend-lost-response-keeps-idempotency-key',async()=>{
   const context=await browser.newContext();const page=await context.newPage();let lostKey;let retriedKey;let calls=0;
   try {
    await open(page);await issue(page);
    console.log('Waiting for real 60-second resend boundary');
    await page.getByRole('button',{name:'دریافت کد تازه',exact:true}).waitFor({state:'visible',timeout:65000});
    await page.route('**/api/v1/auth/issue',async route=>{
     calls++;const body=route.request().postDataJSON();
     if(calls===1){lostKey=body.key;const response=await route.fetch();assert.equal(response.status(),200);await route.abort('failed');}
     else {retriedKey=body.key;const response=await route.fetch();result.observations.push({name:'resend-lost-response',same_key:retriedKey===lostKey,retry_status:response.status()});await route.fulfill({response});}
    });
    await page.getByRole('button',{name:'دریافت کد تازه',exact:true}).click();await page.locator('.auth-error').waitFor();
    const recoveryResponse=page.waitForResponse(r=>r.url().endsWith('/api/v1/auth/issue'));
    await page.getByRole('button',{name:'تلاش دوباره برای دریافت نتیجه',exact:true}).click();
    assert.equal((await recoveryResponse).status(),200);await page.getByTestId('trial-code').waitFor({state:'visible'});
    await shot(page,'lost-resend-retry');assert.equal(retriedKey,lostKey,'Retry after lost resend generated a new idempotency key');
   } finally {await context.close();}
  });
 } finally {await browser.close();}
 result.summary={passed:result.cases.filter(x=>x.status==='passed').length,failed:result.cases.filter(x=>x.status==='failed').length};
 fs.writeFileSync(path.join(evidence,'independent-browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));process.exitCode=result.summary.failed?1:0;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
