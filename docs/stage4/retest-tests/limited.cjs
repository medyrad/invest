/* TEST-S04-02: existing Playwright/Chrome, current image, read-only client interactions. */
const path=require('node:path'),fs=require('node:fs'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'../../..');const {chromium,expect}=require(path.join(root,'frontend/node_modules/@playwright/test'));
const out=path.join(root,'docs/stage4/retest-evidence'),base='http://127.0.0.1:3108';
const result={version:'S04-FIX-5d2794c593b5',started_utc:new Date().toISOString(),cases:[],observations:[]};const started=performance.now();
async function run(name,work){const t=performance.now();try{await work();result.cases.push({name,status:'passed',seconds:(performance.now()-t)/1000});}catch(e){result.cases.push({name,status:'failed',error:e.message,seconds:(performance.now()-t)/1000});}console.log(name,result.cases.at(-1).status);}
(async()=>{const browser=await chromium.launch({executablePath:'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});result.browser=browser.version();try{
 for(const width of [360,390,768,1440])await run('city-text-parent-controls-home-menu-'+width,async()=>{
  const context=await browser.newContext({viewport:{width,height:width===360?800:width===390?844:1000},hasTouch:width<1024,reducedMotion:'reduce'}),page=await context.newPage();const consoleErrors=[],badFavicon=[];
  page.on('console',m=>{if(m.type()==='error')consoleErrors.push({text:m.text(),url:m.location().url});});page.on('response',r=>{if(new URL(r.url()).pathname==='/favicon.ico'&&r.status()>=400)badFavicon.push(r.status());});
  try{
   await page.goto(base);const province=page.getByLabel('استان',{exact:true}),county=page.getByLabel('شهرستان',{exact:true}),city=page.getByLabel('شهر',{exact:true});await expect(province).toBeEnabled();await expect(page.locator('[data-section="hero"]')).toBeVisible();
   const icon=page.locator('head link[rel~="icon"]');assert.equal(await icon.count(),1);assert.equal(new URL(await icon.getAttribute('href'),base).pathname,'/favicon.ico');assert.equal(await icon.getAttribute('type'),'image/x-icon');
   const decoded=await page.evaluate(async()=>{const href=document.querySelector('link[rel~="icon"]').href;const image=new Image();image.src=href;await image.decode();return {width:image.naturalWidth,height:image.naturalHeight,href};});assert(decoded.width>0&&decoded.height>0);
   await province.selectOption('province-00');await county.selectOption({label:'هوراند'});const horand=await county.inputValue();await expect(city).toBeDisabled();await expect(city).toHaveValue('');
   const message=page.getByText('فهرست شهرهای این شهرستان فعلاً در دسترس نیست؛ انتخاب شهرستان شما حفظ شده است.',{exact:true});await expect(message).toBeVisible();await expect(county).toHaveValue(horand);
   const panel=page.locator('[data-section="selectors"]');assert(!/پیوند|منبع|حدس/.test(await panel.innerText()));await message.scrollIntoViewIfNeeded();
   const geometry=await panel.evaluate(el=>{const parent=el.getBoundingClientRect();const bad=[...el.querySelectorAll('label,select,p,button')].filter(x=>{const r=x.getBoundingClientRect();return r.width>2&&(r.left<parent.left-1||r.right>parent.right+1||r.left< -1||r.right>innerWidth+1);}).map(x=>x.tagName);return {bad,scrollWidth:el.scrollWidth,clientWidth:el.clientWidth};});assert.deepEqual(geometry.bad,[]);assert(geometry.scrollWidth<=geometry.clientWidth);
   if(width===360||width===1440)await panel.screenshot({path:path.join(out,'city-'+width+'.png'),animations:'disabled'});
   const help=page.getByRole('button',{name:'درباره انتخاب‌ها',exact:true});await help.click();await expect(page.getByRole('dialog')).toContainText('انتخاب شهرستان شما حفظ می‌شود');assert(!/پیوند|منبع/.test(await page.getByRole('dialog').innerText()));await page.keyboard.press('Escape');await expect(help).toBeFocused();
   await province.selectOption('province-07');await expect(county).toHaveValue('');await expect(city).toHaveValue('');await county.selectOption({label:'تهران'});await expect(city).toBeEnabled();await city.selectOption({label:'تهران'});assert.notEqual(await city.inputValue(),'');assert.equal(await city.locator('option:checked').innerText(),'تهران');
   await province.selectOption('province-00');await expect(county).toHaveValue('');await expect(city).toHaveValue('');await county.selectOption({label:'تبریز'});await city.selectOption({label:'تبریز'});await county.selectOption({label:'هوراند'});await expect(city).toHaveValue('');await expect(city).toBeDisabled();await expect(county).toHaveValue(horand);
   if(width<1024){const menu=page.getByRole('button',{name:'منوی اصلی',exact:true});await menu.scrollIntoViewIfNeeded();await menu.tap();await expect(page.getByRole('menuitem',{name:'دستیار',exact:true})).toBeVisible();await page.keyboard.press('Escape');await expect(menu).toBeFocused();}
   else {const header=page.locator('header');await header.scrollIntoViewIfNeeded();await expect(header.getByRole('link',{name:'دستیار',exact:true})).toBeVisible();const menu=header.getByRole('button',{name:'منوی اصلی',exact:true});assert.equal(await menu.isVisible(),false);}
   assert.deepEqual(badFavicon,[]);assert(!consoleErrors.some(x=>x.url.includes('favicon.ico')||/favicon.*404/i.test(x.text)));
   result.observations.push({width,horand_preserved:true,tehran_city_selected:true,province_and_county_clear_invalid_city:true,geometry,icon:decoded,favicon_errors:badFavicon,console_errors:consoleErrors});
  }finally{await context.close();}
 });
 }finally{await browser.close();}result.finished_utc=new Date().toISOString();result.wall_seconds=(performance.now()-started)/1000;result.summary={passed:result.cases.filter(x=>x.status==='passed').length,failed:result.cases.filter(x=>x.status==='failed').length};fs.writeFileSync(path.join(out,'browser.json'),JSON.stringify(result,null,2));console.log(JSON.stringify(result.summary),result.wall_seconds.toFixed(2)+'s');process.exitCode=result.summary.failed?1:0;
})().catch(e=>{console.error(e.message);process.exitCode=1});
