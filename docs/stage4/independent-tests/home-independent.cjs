const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');const {chromium,expect}=require(path.join(root,'frontend/node_modules/@playwright/test'));
const out=path.join(root,'docs/stage4/independent-evidence'),origin='http://127.0.0.1:3109';const result={version:'S04-f811d439b069',cases:[],observations:[],errors:[]};
async function run(name,fn){if(process.env.HOME_CASE&&name!==process.env.HOME_CASE)return;try{await fn();result.cases.push({name,status:'passed'});}catch(e){result.cases.push({name,status:'failed',error:e.message});}fs.writeFileSync(path.join(out,process.env.HOME_CASE?'home-tablet-rerun.json':'home-independent.json'),JSON.stringify(result,null,2));console.log(name,result.cases.at(-1).status);}
async function ready(page){await page.goto(origin);await expect(page.getByLabel('دسته‌بندی',{exact:true})).toBeEnabled();}
async function snap(page,name){await page.screenshot({path:path.join(out,name+'.png'),animations:'disabled'});}
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});result.browser=browser.version();try{
 for(const width of [360,390,768,1440])await run('all-sections-navigation-and-layout-'+width,async()=>{
  const ctx=await browser.newContext({viewport:{width,height:width<768?844:1000},reducedMotion:'reduce',hasTouch:width<1024}),page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
  try{await ready(page);for(const name of ['hero','main-categories','categories','featured','how','help','footer']){
   const section=name==='footer'?page.locator('main > footer'):page.locator(`[data-section="${name}"]`);await expect(section).toHaveCount(1);await section.scrollIntoViewIfNeeded();
   await expect.poll(()=>section.locator('h1,h2,h3,p,button,a,input,select,article').evaluateAll(es=>es.filter(e=>{const r=e.getBoundingClientRect(),s=getComputedStyle(e);return r.width>2&&r.height>2&&s.visibility!=='hidden'&&!e.closest('[aria-hidden="true"],[inert]');}).filter(e=>{const r=e.getBoundingClientRect();return r.left< -1||r.right>innerWidth+1;}).map(e=>({tag:e.tagName,text:e.textContent?.trim().slice(0,90)}))),{message:name+' visible content clipped'}).toEqual([]);
   if(['hero','selectors','footer'].includes(name))await snap(page,name+'-'+width);
  }
  const how=page.locator('[data-section="how"]');const steps=how.locator('ol').first().locator('> li > button');assert.equal(await steps.count(),3);for(let i=0;i<3;i++){await steps.nth(i).click();await expect(steps.nth(i)).toHaveAttribute('aria-pressed','true');}
  if(width<1024){const menu=page.getByRole('button',{name:'منوی اصلی',exact:true});await menu.scrollIntoViewIfNeeded();await menu.tap();await expect(page.getByRole('menuitem',{name:'دستیار',exact:true})).toBeVisible();await page.keyboard.press('Escape');await expect(menu).toBeFocused();await menu.tap();await page.getByRole('menuitem',{name:'دستیار',exact:true}).click();}
  else await page.locator('header').getByRole('link',{name:'دستیار',exact:true}).click();
  await expect(page.getByText('این مقصد در نسخه آزمایشی فعلی فعال نیست',{exact:false})).toBeVisible();await page.reload();await page.goBack();await expect(page.getByLabel('دسته‌بندی',{exact:true})).toBeEnabled();assert.deepEqual(errors,[]);result.errors.push(...errors);
  }finally{await ctx.close();}
 });
 await run('all-live-links-direct-refresh-and-no-fake-success',async()=>{
  const ctx=await browser.newContext({reducedMotion:'reduce'}),page=await ctx.newPage();try{await ready(page);
   const paths=await page.locator('a[href]').evaluateAll(es=>[...new Set(es.map(e=>e.getAttribute('href')).filter(h=>h&&h.startsWith('/')))]);const statuses=[];
   for(const href of paths){const r=await ctx.request.get(origin+href);statuses.push({href,status:r.status()});assert(r.status()<400,href+' => '+r.status());}
   result.observations.push({case:'links',links:statuses});
   for(const dest of ['/opportunities','/opportunities/DEMO-01','/assistant','/compare','/saved','/tools','/tools/synthetic']){await page.goto(origin+dest);await expect(page.getByText('این مقصد در نسخه آزمایشی فعلی فعال نیست',{exact:false})).toBeVisible();assert(!await page.getByText('ذخیره شد',{exact:true}).count());await page.getByRole('link',{name:'بازگشت به خانه',exact:true}).click();await expect(page.getByLabel('دسته‌بندی',{exact:true})).toBeEnabled();}
  }finally{await ctx.close();}
 });
 await run('selectors-touch-keyboard-parent-clear-and-rapid-changes',async()=>{
  const ctx=await browser.newContext({viewport:{width:360,height:844},hasTouch:true,reducedMotion:'reduce'}),page=await ctx.newPage();try{await ready(page);const g=page.getByLabel('دسته‌بندی',{exact:true}),s=page.getByLabel('زیردسته',{exact:true}),p=page.getByLabel('استان',{exact:true}),c=page.getByLabel('شهرستان',{exact:true}),city=page.getByLabel('شهرهای پیوندخورده در منبع',{exact:true});
   await g.focus();await page.keyboard.press('Home');await page.keyboard.press('ArrowDown');await page.keyboard.press('Enter');await expect(g).toHaveValue('building');await s.selectOption('residential');await g.selectOption('energy');await expect(s).toHaveValue('');
   await p.selectOption('province-07');await c.selectOption({label:'تهران'});await city.selectOption({label:'تهران'});await p.selectOption('province-00');await expect(c).toHaveValue('');await expect(city).toHaveValue('');
   for(const v of ['province-03','province-30','province-07','province-00'])await p.selectOption(v);await expect(p).toHaveValue('province-00');await expect(c.locator('option')).toHaveCount(22);await c.selectOption({label:'هوراند'});await expect(city).toBeDisabled();await expect(page.getByText('برای این شهرستان پیوند شهری در منبع ثبت نشده است؛ نامی حدس زده نمی‌شود.',{exact:true})).toBeVisible();
   await page.getByRole('button',{name:'حذف استان',exact:true}).tap();await expect(p).toHaveValue('');await expect(c).toHaveValue('');await page.getByRole('button',{name:'پاک‌کردن انتخاب‌ها',exact:true}).tap();await expect(g).toHaveValue('');
   const about=page.getByRole('button',{name:'درباره انتخاب‌ها',exact:true});await about.tap();await expect(page.getByRole('dialog')).toContainText('فقط بر امتیاز');await page.keyboard.press('Escape');await expect(about).toBeFocused();
   await snap(page,'selector-language-mobile');result.observations.push({case:'language',city_label:await city.getAttribute('aria-label'),missing_city_text:'برای این شهرستان پیوند شهری در منبع ثبت نشده است؛ نامی حدس زده نمی‌شود.'});
  }finally{await ctx.close();}
 });
 await run('API-is-only-source-and-long-text-is-readable',async()=>{
  const ctx=await browser.newContext({viewport:{width:360,height:844},reducedMotion:'reduce'}),page=await ctx.newPage();try{
   const taxonomy=JSON.parse(fs.readFileSync(path.join(out,'source-expected.json'))).groups;taxonomy[0].name='دسته مصنوعی مستقل با نام بلند برای بررسی خوانایی و انتخاب';
   await page.route('**/catalog/taxonomy',r=>r.fulfill({contentType:'application/json',body:JSON.stringify({version:'independent',groups:taxonomy})}));await ready(page);const g=page.getByLabel('دسته‌بندی',{exact:true});await expect(g.locator('option').nth(1)).toHaveText(taxonomy[0].name);assert(!await g.locator('option',{hasText:/^ساختمان$/}).count());await g.selectOption('building');await expect(page.getByLabel('زیردسته',{exact:true})).toBeEnabled();await snap(page,'long-selection-mobile');
  }finally{await ctx.close();}
 });
 await run('API-cut-delay-empty-and-retry-with-no-hidden-fallback',async()=>{
  const ctx=await browser.newContext({reducedMotion:'reduce'}),page=await ctx.newPage();let release;const gate=new Promise(r=>{release=r;});
  try{await page.route('**/api/v1/catalog/taxonomy',async r=>{await gate;await r.abort('failed');});await page.goto(origin);await expect(page.getByRole('region',{name:'وضعیت کاتالوگ'})).toContainText('در حال دریافت');assert.equal(await page.getByLabel('دسته‌بندی',{exact:true}).count(),0);release();await expect(page.getByRole('region',{name:'وضعیت کاتالوگ'})).toContainText('دریافت کاتالوگ انجام نشد');await expect(page.locator('[data-section="featured"] article')).toHaveCount(0);
   await page.unroute('**/api/v1/catalog/taxonomy');await page.route('**/api/v1/catalog/taxonomy',r=>r.fulfill({contentType:'application/json',body:JSON.stringify({version:'empty',groups:[]})}));await page.getByRole('button',{name:'تلاش دوباره',exact:true}).click();await expect(page.getByRole('region',{name:'وضعیت کاتالوگ'})).toContainText('کاتالوگ هنوز داده‌ای ندارد');
   await page.unroute('**/api/v1/catalog/taxonomy');await page.getByRole('button',{name:'تلاش دوباره',exact:true}).click();await expect(page.getByLabel('دسته‌بندی',{exact:true})).toBeEnabled();
  }finally{release();await ctx.close();}
 });
 await run('public-real-API-and-rendered-home-contain-no-synthetic-items',async()=>{
  const ctx=await browser.newContext({reducedMotion:'reduce'}),page=await ctx.newPage();try{
   const api=await ctx.request.get('http://127.0.0.1:8011/api/v1/catalog/preview');assert.equal(api.status(),200);const body=await api.json();assert.equal(body.enabled,false);assert.deepEqual(body.listings,[]);
   await page.route('**/api/v1/catalog/**',async route=>{const uri=new URL(route.request().url());const response=await route.fetch({url:'http://127.0.0.1:8011'+uri.pathname});await route.fulfill({response});});await ready(page);await expect(page.locator('[data-section="featured"] article')).toHaveCount(0);await expect(page.locator('[data-map-feed] a')).toHaveCount(0);await expect(page.getByText('فرصت نمایشی در حالت عمومی فعال نیست.',{exact:true})).toBeVisible();
   const titles=JSON.parse(fs.readFileSync(path.join(root,'backend/apps/catalog/fixtures/preview-v1.json'))).listings.map(l=>l.title);const text=await page.locator('body').innerText();const shown=titles.filter(t=>text.includes(t));assert.deepEqual(shown,[]);result.observations.push({case:'public',preview_enabled:false,rendered_sample_titles:shown,map_cards:0,featured_cards:0});await page.locator('[data-section="featured"]').scrollIntoViewIfNeeded();await snap(page,'public-home');
  }finally{await ctx.close();}
 });
 await run('sample-labels-score-not-calculated-and-contact-hidden',async()=>{
  const ctx=await browser.newContext({reducedMotion:'reduce'}),page=await ctx.newPage();try{await ready(page);await expect(page.getByRole('note')).toContainText('داده نمونه');await expect(page.locator('[data-section="featured"] article')).toHaveCount(6);const body=await page.locator('body').innerText();assert(!/09[0-9]{9}/.test(body));assert(!/[۰-۹0-9]+٪ تطابق/.test(body));assert(body.includes('میلیارد تومان'));assert(body.includes('فقط بر امتیاز'));await page.locator('[data-section="featured"]').scrollIntoViewIfNeeded();await snap(page,'samples-and-score');
  }finally{await ctx.close();}
 });
 await run('normal-motion-versus-reduced-motion-browser-errors',async()=>{
  const values=[];
  for(const reducedMotion of ['reduce','no-preference']){const ctx=await browser.newContext({viewport:{width:1440,height:1000},reducedMotion}),page=await ctx.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));try{await page.clock.install();await ready(page);const ring=page.locator('[data-section="hero"] svg').filter({has:page.locator('line')});await page.clock.runFor(1200);const a=await ring.evaluate(e=>getComputedStyle(e).transform);await page.clock.runFor(2200);const b=await ring.evaluate(e=>getComputedStyle(e).transform);assert.equal(a===b,reducedMotion==='reduce');assert.deepEqual(errors,[]);values.push({mode:reducedMotion,changed:a!==b,errors});}finally{await ctx.close();}}
  result.observations.push({case:'motion',values});
 });
 }finally{await browser.close();}result.summary={passed:result.cases.filter(c=>c.status==='passed').length,failed:result.cases.filter(c=>c.status==='failed').length};fs.writeFileSync(path.join(out,process.env.HOME_CASE?'home-tablet-rerun.json':'home-independent.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary));process.exitCode=result.summary.failed?1:0;
})().catch(e=>{console.error(e.message);process.exitCode=1;});
