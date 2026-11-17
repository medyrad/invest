const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');const {chromium}=require(path.join(root,'frontend/node_modules/@playwright/test'));
const origin='http://127.0.0.1:3109';const rows=[];const wait=ms=>new Promise(r=>setTimeout(r,ms));
const out=path.join(root,'docs/stage3/independent-evidence/browser-boundaries.json');
async function run(name,action){try{await action();rows.push({name,status:'passed'});}catch(e){rows.push({name,status:'failed',error:e.message.replace(/\b\d{6}\b/g,'[masked]')});}fs.writeFileSync(out,JSON.stringify({cases:rows},null,2));console.log(name,rows.at(-1).status);}
async function open(browser,phone){const ctx=await browser.newContext({viewport:{width:390,height:844}});const page=await ctx.newPage();let issued;
 page.on('request',r=>{if(r.url().endsWith('/auth/issue'))issued={headers:r.headers(),body:r.postDataJSON()};});
 await page.goto(origin);await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).fill(phone);await page.getByRole('button',{name:'دریافت کد',exact:true}).click();await page.getByTestId('trial-code').waitFor();
 const code=(await page.getByTestId('trial-code').textContent()).trim();return {ctx,page,code,issued:()=>issued};}
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});try{
 await Promise.all([
 run('actual-120-second-server-expiry-and-mobile-controls',async()=>{const {ctx,page,code,issued}=await open(browser,'09178000081');try{
  let challenge;const response=await ctx.request.post(origin+'/api/v1/auth/issue',{headers:issued().headers,data:issued().body});challenge=await response.json();assert.equal(response.status(),200);
  const until=Date.parse(challenge.expires_at);const remain=until-Date.now()+200;console.log('Waiting for actual server TTL boundary');await wait(Math.max(0,remain));
  await page.getByText('اعتبار کد تمام شده است.',{exact:true}).waitFor();assert.equal(await page.getByTestId('trial-code').count(),0);assert(await page.getByRole('button',{name:'ورود',exact:true}).isDisabled());
  const expired=await ctx.request.post(origin+'/api/v1/auth/verify',{headers:issued().headers,data:{challenge_id:challenge.challenge_id,code}});assert.equal(expired.status(),410);assert.equal((await expired.json()).error.code,'challenge_expired');
  const resend=page.getByRole('button',{name:'دریافت کد تازه',exact:true});await resend.scrollIntoViewIfNeeded();await resend.click();await page.getByTestId('trial-code').waitFor();
  const fresh=(await page.getByTestId('trial-code').textContent()).trim();await page.getByRole('textbox',{name:'کد تایید',exact:true}).fill(fresh);await page.getByRole('button',{name:'ورود',exact:true}).click();await page.getByRole('region',{name:'وضعیت ورود'}).waitFor();
 }finally{await ctx.close();}}),
 run('five-wrong-codes-then-correct-code-refused-through-ui',async()=>{const {ctx,page,code}=await open(browser,'09178000082');try{
  const input=page.getByRole('textbox',{name:'کد تایید',exact:true});const wrong=code==='000000'?'111111':'000000';
  for(let i=0;i<5;i++){await input.fill(wrong);await page.getByRole('button',{name:'ورود',exact:true}).click();await page.locator('.auth-error').waitFor();}
  await input.fill(code);await page.getByRole('button',{name:'ورود',exact:true}).click();await page.getByText('تعداد تلاش این کد تمام شد؛ کد تازه بگیرید.',{exact:true}).waitFor();
  const me=await page.evaluate(async()=> (await(await fetch('/api/v1/auth/me')).json()).authenticated);assert.equal(me,false);
 }finally{await ctx.close();}}),
 run('privacy-copy-compatible-with-D26',async()=>{const ctx=await browser.newContext();const page=await ctx.newPage();try{
  await page.goto(origin);await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();const text=await page.locator('.privacy-note').innerText();assert(!text.includes('فقط برای ورود'),'Unconditional only-login promise omits D26 contact-consent and exceptional access');
 }finally{await ctx.close();}}),
 run('refresh-reopens-fresh-flow-without-storing-secrets',async()=>{const {ctx,page,code}=await open(browser,'09178000083');try{
  const data=await page.evaluate(()=>({local:Object.values(localStorage),session:Object.values(sessionStorage)}));assert(!JSON.stringify(data).includes(code));
  await page.reload();assert.equal(await page.getByTestId('trial-code').count(),0);await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).waitFor();
  await page.keyboard.press('Escape');await page.getByRole('dialog').waitFor({state:'hidden'});await page.getByRole('button',{name:'ورود به حساب',exact:true}).click();await page.getByRole('textbox',{name:'شماره موبایل',exact:true}).waitFor();
 }finally{await ctx.close();}})
 ]);
 }finally{await browser.close();}fs.writeFileSync(out,JSON.stringify({cases:rows,summary:{passed:rows.filter(r=>r.status==='passed').length,failed:rows.filter(r=>r.status==='failed').length}},null,2));process.exitCode=rows.some(r=>r.status==='failed')?1:0;})().catch(e=>{console.error(e.message);process.exitCode=1;});
