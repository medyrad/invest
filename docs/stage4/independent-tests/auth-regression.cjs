/* TEST-S03-03: independent targeted retest; no raw OTP, cookie or flow saved. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict'),{execFileSync}=require('node:child_process');
const root=path.resolve(__dirname,'../../..');const {chromium,expect}=require(path.join(root,'frontend/node_modules/@playwright/test'));
const origin='http://127.0.0.1:3109',out=path.join(root,'docs/stage4/independent-evidence/auth');
const resultName=process.env.RETEST_ONLY?'IT001-rerun.json':'targeted.json';
const results={version:'S04-f811d439b069',cases:[],observations:[],human_design_approved:false};let index=Number(process.env.RETEST_FIXTURE_SEED||500);
const phone=()=> '0917600'+String(index++).padStart(4,'0');
const frame=page=>page.evaluate(()=>new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve))));
async function run(name,work){if(process.env.RETEST_ONLY&&!name.startsWith(process.env.RETEST_ONLY))return;try{await work();results.cases.push({name,status:'passed'});}catch(error){results.cases.push({name,status:'failed',error:error.message.replace(/\b\d{6}\b/g,'[masked]')});}fs.writeFileSync(path.join(out,resultName),JSON.stringify(results,null,2));console.log(name,results.cases.at(-1).status);}
async function open(page){await page.goto(origin);await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();await expect(page.getByRole('dialog')).toBeVisible();}
async function issue(page,mobile=phone()){
 await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).fill(mobile);
 const pending=page.waitForResponse(r=>r.url().endsWith('/auth/issue'));
 await page.getByRole('button',{name:'دریافت کد',exact:true}).click();const r=await pending;assert.equal(r.status(),200);const data=await r.json();await expect(page.getByTestId('trial-code')).toBeVisible();return data;
}
async function finish(page,receipt){await page.getByRole('textbox',{name:'کد تایید',exact:true}).fill(receipt.notification.code);await page.getByRole('button',{name:'ورود',exact:true}).click();await expect(page.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();}
async function login(page,mobile=phone()){await open(page);const r=await issue(page,mobile);await finish(page,r);return r;}
async function me(page){return await page.evaluate(async()=> (await(await fetch('/api/v1/auth/me',{cache:'no-store'})).json()));}
async function post(context,action,data={}){const csrf=(await(await context.request.get(origin+'/api/v1/auth/csrf')).json()).csrfToken;return await context.request.post(origin+'/api/v1/auth/'+action,{headers:{'X-CSRFToken':csrf},data});}
function inspect(challenge){
 assert.match(challenge,/^[a-f0-9-]{36}$/);
 const code=`import json;from django.conf import settings;from apps.identity.models import OTPChallenge,IssueEvent,AuthSession;assert settings.INVEST_ENV=='test' and settings.DATABASES['default']['NAME']=='invest_browser';c=OTPChallenge.objects.get(pk='${challenge}');print(json.dumps({'issues':IssueEvent.objects.filter(user_id=c.user_id).count(),'challenges':list(OTPChallenge.objects.filter(user_id=c.user_id).order_by('issued_at').values('id','state','issued_at','expires_at')),'sessions':list(AuthSession.objects.filter(user_id=c.user_id).order_by('id').values('id','last_activity','revoked'))},default=str))`;
 const raw=execFileSync('docker',['compose','--env-file','.env','-f','deploy/compose.yaml','exec','-T','browser-api','/app/.venv/bin/python','manage.py','shell','-c',code],{cwd:root,encoding:'utf8'});return JSON.parse(raw.trim().split('\n').at(-1));
}
async function shot(page,name){await page.screenshot({path:path.join(out,name+'.png'),animations:'disabled',mask:[page.getByTestId('trial-code'),page.locator('.code-cells'),page.getByRole('button',{name:'حساب کاربری',exact:true})]});}
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});results.browser=browser.version();let intentionalClose=false;browser.on('disconnected',()=>{if(!intentionalClose){results.unexpected_browser_disconnect=true;console.log('Unexpected browser disconnect');}});try{
 await run('IT002-cross-tab-clearing-device-independence-and-secret-free-signals',async()=>{
  const context=await browser.newContext(),device=await browser.newContext();const emitted=[];
  await context.exposeBinding('captureSignal',(_source,data)=>{emitted.push(data);});
  await context.addInitScript(()=>{const original=BroadcastChannel.prototype.postMessage;BroadcastChannel.prototype.postMessage=function(data){void window.captureSignal(data);return original.call(this,data);};});
  const a=await context.newPage(),b=await context.newPage(),d=await device.newPage();const mobile=phone();
  try{const r=await login(a,mobile);await b.goto(origin);await expect(b.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();await login(d,mobile);const before=inspect(r.challenge_id);
   await a.getByRole('button',{name:'حساب کاربری',exact:true}).click();await a.getByRole('menuitem',{name:'خروج',exact:true}).click();await b.bringToFront();await expect(b.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);assert.equal((await me(b)).authenticated,false);assert.equal(await b.getByRole('button',{name:'حساب کاربری',exact:true}).count(),0);
   assert.equal((await me(d)).authenticated,true);await expect(d.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();
   const after=inspect(r.challenge_id);assert.deepEqual(after.sessions.map(s=>[s.id,s.last_activity]),before.sessions.map(s=>[s.id,s.last_activity]));
   await expect.poll(()=>emitted.length).toBeGreaterThan(0);assert(emitted.every(e=>JSON.stringify(e)===JSON.stringify({type:'session-invalidated'})));
   results.observations.push({case:'IT002-signals',messages:emitted,idle_unchanged:true,independent_device_authenticated:true});await shot(b,'IT002-cleared-tab');
  }finally{await context.close();await device.close();}
 });
 await run('IT002-late-authenticated-me-does-not-resurrect-identity',async()=>{
  const context=await browser.newContext(),a=await context.newPage(),b=await context.newPage();let release;const gate=new Promise(resolve=>{release=resolve;});let capturedResolve;const captured=new Promise(resolve=>{capturedResolve=resolve;});let held=false;
  try{await login(a);await b.goto(origin);await expect(b.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();
   await b.route('**/api/v1/auth/me',async route=>{
    if(held){await route.continue();return;}held=true;const response=await route.fetch();assert.equal((await response.json()).authenticated,true);capturedResolve();await gate;await route.fulfill({response});
   });
   await b.evaluate(()=>window.dispatchEvent(new Event('focus')));await captured;
   await a.getByRole('button',{name:'حساب کاربری',exact:true}).click();await a.getByRole('menuitem',{name:'خروج',exact:true}).click();await expect(b.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);
   const oldDelivered=b.waitForResponse(async r=>r.url().endsWith('/auth/me')&&(await r.json()).authenticated===true);release();await(await oldDelivered).finished();await frame(b);
   await expect(b.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);await expect(b.getByRole('button',{name:'ورود به حساب',exact:true})).toBeVisible();
   const fresh=b.waitForResponse(r=>r.url().endsWith('/auth/me'));await b.evaluate(()=>window.dispatchEvent(new Event('pageshow')));assert.equal((await(await fresh).json()).authenticated,false);await expect(b.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);
  }finally{release();await context.close();}
 });
 await run('IT002-focus-visibility-pageshow-history-and-idle',async()=>{
  const context=await browser.newContext(),page=await context.newPage();try{const r=await login(page);const before=inspect(r.challenge_id);const paths=[];page.on('request',req=>{if(req.url().includes('/api/'))paths.push(new URL(req.url()).pathname);});
   for(const event of ['focus','visibilitychange','pageshow']){
    const pending=page.waitForResponse(r=>r.url().endsWith('/auth/me'));await page.evaluate(type=>(type==='visibilitychange'?document:window).dispatchEvent(new Event(type)),event);assert.equal((await(await pending).json()).authenticated,true);
   }
   await page.goto(origin+'/?return=1');await expect(page.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();assert.equal((await post(context,'logout')).status(),200);await page.goBack();await expect(page.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);await expect(page.getByRole('button',{name:'ورود به حساب',exact:true})).toBeVisible();
   assert.deepEqual(inspect(r.challenge_id).sessions.map(s=>s.last_activity),before.sessions.map(s=>s.last_activity));assert(!paths.includes('/api/v1/auth/activity'));
   results.observations.push({case:'IT002-events',events:['focus','visibilitychange','pageshow'],history_back:true,idle_unchanged:true,activity_requests:0});
  }finally{await context.close();}
 });
 await run('IT002-spoofed-channel-message-cannot-grant-identity',async()=>{
  const context=await browser.newContext(),page=await context.newPage();try{await page.goto(origin);await expect(page.getByRole('button',{name:'ورود به حساب',exact:true})).toBeEnabled();const fresh=page.waitForResponse(r=>r.url().endsWith('/auth/me'));
   await page.evaluate(()=>{const c=new BroadcastChannel('invest-auth-events-v1');c.postMessage({type:'session-invalidated',authenticated:true,user:{role:'admin',mobile:'synthetic'}});c.close();});
   assert.equal((await(await fresh).json()).authenticated,false);await frame(page);await expect(page.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);
  }finally{await context.close();}
 });
 for(const width of [360,390,768,1440])await run('IT003-copy-layout-controls-'+width,async()=>{
  const context=await browser.newContext({viewport:{width,height:width===360?800:width===390?844:1000},reducedMotion:'reduce'}),page=await context.newPage();
  try{await open(page);await page.evaluate(()=>document.fonts.ready);await page.locator('.login-visual img').first().evaluate(img=>img.decode());
   const note=page.locator('.privacy-note');const text=await note.innerText();assert(!text.includes('فقط برای ورود'));assert(text.includes('پیگیری فرصت فقط با رضایت شما'));assert(text.includes('گیرندهٔ مشخص'));
   await note.scrollIntoViewIfNeeded();const metrics=await note.evaluate(el=>{
    const range=document.createRange();range.selectNodeContents(el);const rect=el.getBoundingClientRect();const lines=[...range.getClientRects()].filter(r=>r.width>0);const style=getComputedStyle(el);return {width:el.clientWidth,scroll:el.scrollWidth,height:rect.height,fontSize:style.fontSize,lineHeight:style.lineHeight,fontWeight:style.fontWeight,lineTops:[...new Set(lines.map(r=>Math.round(r.top)))],textInside:lines.every(r=>r.left>=rect.left-1&&r.right<=rect.right+1),dialogNoOverflow:document.querySelector('dialog').scrollWidth<=document.querySelector('dialog').clientWidth};
   });assert.equal(metrics.textInside,true);assert.equal(metrics.dialogNoOverflow,true);assert(metrics.scroll<=metrics.width);assert.equal(metrics.fontSize,'12px');assert.equal(metrics.fontWeight,'600');assert(metrics.height<=6*parseFloat(metrics.lineHeight));
   results.observations.push({case:'IT003-layout',viewport:width,metrics});await shot(page,'IT003-privacy-'+width);await note.screenshot({path:path.join(out,'IT003-note-'+width+'.png'),animations:'disabled'});
   if(width===1440){await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).click();await page.getByRole('dialog').screenshot({path:path.join(out,'IT003-dialog-1440.png'),animations:'disabled'});}
   const mobile=page.getByRole('textbox',{name:'شماره موبایل',exact:true});await mobile.scrollIntoViewIfNeeded();await mobile.click();await mobile.fill(phone());
   const response=page.waitForResponse(r=>r.url().endsWith('/auth/issue'));await page.getByRole('button',{name:'دریافت کد',exact:true}).click();assert.equal((await response).status(),200);await expect(page.getByTestId('trial-code')).toBeVisible();await page.getByTestId('trial-code').scrollIntoViewIfNeeded();
   const code=(await page.getByTestId('trial-code').textContent()).trim();const input=page.getByRole('textbox',{name:'کد تایید',exact:true});await input.scrollIntoViewIfNeeded();await input.click();await input.fill(code);await page.getByRole('button',{name:'ورود',exact:true}).click();await expect(page.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();
  }finally{await context.close();}
 });
 await run('affected-login-reload-logout-old-cookie-and-validation-errors',async()=>{
  const context=await browser.newContext(),page=await context.newPage();try{await open(page);
   await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).fill('09176000100X');await page.getByRole('button',{name:'دریافت کد',exact:true}).click();await expect(page.locator('.auth-error')).toBeVisible();
   const r=await issue(page);const wrong=r.notification.code==='000000'?'111111':'000000';await page.getByRole('textbox',{name:'کد تایید',exact:true}).fill(wrong);await page.getByRole('button',{name:'ورود',exact:true}).click();await expect(page.locator('.auth-error')).toContainText('کد صحیح نیست');await finish(page,r);
   const cookie=(await context.cookies()).find(c=>c.name==='invest_session');assert(cookie.httpOnly);await page.goto(origin+'/saved');await page.getByRole('link',{name:'بازگشت به خانه',exact:true}).click();await page.waitForURL(origin+'/');await expect(page.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();await page.reload();await expect(page.getByRole('region',{name:'وضعیت ورود'})).toBeVisible();await page.getByRole('button',{name:'حساب کاربری',exact:true}).click();await page.getByRole('menuitem',{name:'خروج',exact:true}).click();await expect(page.getByRole('region',{name:'وضعیت ورود'})).toHaveCount(0);await context.addCookies([cookie]);assert.equal((await me(page)).authenticated,false);
  }finally{await context.close();}
 });
 await run('IT001-recover-accepted-resend-payload-challenge-TTL-quota-and-login',async()=>{
  const context=await browser.newContext(),page=await context.newPage();const requests=[];let accepted,recovered;
  try{await open(page);const initial=await issue(page);assert.equal(inspect(initial.challenge_id).issues,1);
   console.log('Waiting on real resend control (60-second boundary)');await page.getByRole('button',{name:'دریافت کد تازه',exact:true}).waitFor({state:'visible',timeout:65000});
   await page.route('**/api/v1/auth/issue',async route=>{
    requests.push({body:route.request().postDataJSON(),flow:route.request().headers()['x-login-flow']});const response=await route.fetch();assert.equal(response.status(),200);const body=await response.json();
    if(requests.length===1){accepted=body;await route.abort('failed');}else{recovered=body;await route.fulfill({response});}
   });
   await page.getByRole('button',{name:'دریافت کد تازه',exact:true}).click();await expect(page.locator('.auth-error')).toBeVisible();await expect(page.getByTestId('trial-code')).toHaveCount(0);await expect(page.getByRole('button',{name:'ورود',exact:true})).toBeDisabled();await expect(page.locator('.code-timing')).toContainText('نتیجه درخواست مشخص نیست');assert.equal(await page.getByRole('textbox',{name:'کد تایید',exact:true}).inputValue(),'');
   const pending=inspect(initial.challenge_id);assert.equal(pending.issues,2);assert.equal(pending.challenges[0].state,'replaced');assert.equal(pending.challenges[1].state,'active');await shot(page,'IT001-unknown-hides-old-code');
   const response=page.waitForResponse(r=>r.url().endsWith('/auth/issue'));await page.getByRole('button',{name:'تلاش دوباره برای دریافت نتیجه',exact:true}).click();assert.equal((await response).status(),200);await expect(page.getByTestId('trial-code')).toBeVisible();
   assert.equal(requests.length,2);assert.deepEqual(requests[1],requests[0]);assert.equal(recovered.challenge_id,accepted.challenge_id);assert.notEqual(recovered.challenge_id,initial.challenge_id);assert.equal(recovered.expires_at,accepted.expires_at);assert.equal(recovered.resend_at,accepted.resend_at);
   const after=inspect(initial.challenge_id);assert.equal(after.issues,2);assert.equal(after.challenges.length,2);assert.equal(after.challenges[1].expires_at,pending.challenges[1].expires_at);assert.equal((await page.getByTestId('trial-code').textContent()).trim(),accepted.notification.code);await shot(page,'IT001-recovered');
   await finish(page,recovered);assert.equal((await me(page)).authenticated,true);const done=inspect(initial.challenge_id);assert.equal(done.issues,2);assert.equal(done.sessions.length,1);
   results.observations.push({case:'IT001',same_key:true,same_canonical_payload:true,same_flow:true,recovered_same_challenge:true,TTL_unchanged:true,issued_events_before:1,issued_events_unknown:2,issued_events_after_recovery:2,issued_events_after_login:2,challenge_count:2,old_code_hidden:true,login_success:true,sessions_created:1});
  }finally{await context.close();}
 });
 }finally{intentionalClose=true;await browser.close();}
 results.summary={passed:results.cases.filter(c=>c.status==='passed').length,failed:results.cases.filter(c=>c.status==='failed').length};fs.writeFileSync(path.join(out,resultName),JSON.stringify(results,null,2));console.log(JSON.stringify(results.summary));process.exitCode=results.summary.failed?1:0;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
