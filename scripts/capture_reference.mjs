// Audit the unmodified reference, not the future invest implementation.
import { chromium } from '../.tools/audit/node_modules/playwright/index.mjs';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const origin = 'http://127.0.0.1:3107';
const out = 'docs/stage1/evidence';
await fs.mkdir(out, { recursive: true });
const browser = await chromium.launch({ executablePath: '/usr/bin/google-chrome', headless: true, args: ['--no-sandbox'] });
const cases = [
  ['home', '/'], ['opportunities-start', '/opportunities'],
  ['opportunities-results', '/opportunities', 'results'],
  ['project', '/opportunities/DEMO-01'], ['compare-empty', '/compare'],
  ['compare-projects', '/compare', 'compare'], ['assistant', '/assistant'],
  ['saved-empty', '/saved'], ['saved-filled', '/saved', 'saved'], ['tools', '/tools'],
  ...['proposal','ideas','land-preparation','foreign-investment','ma-notice','ma-renewal','ma-manager','ma-exchange','charity','library','ma-profile','drafts'].map(id=>[id, `/tools/${id}`]),
  ['login', '/', 'login']
];
const manifest = { captured_at: new Date().toISOString(), target:'original reference only', browser:browser.version(), platform:process.platform, node:process.version, origin, normalizations:['reduced motion','scroll to reveal sections before capture','hide Next development portal in screenshot only','block non-local requests','animations disabled for screenshot; motion not tested'], cases:[] };
try {
  for (const width of [1440, 390]) for (const [id,path,state] of cases) {
    const context = await browser.newContext({viewport:{width,height:1000},locale:'fa-IR',timezoneId:'Asia/Tehran',reducedMotion:'reduce',deviceScaleFactor:1});
    await context.route('**/*', r=>new URL(r.request().url()).hostname==='127.0.0.1'?r.continue():r.abort());
    if (['results','compare','saved'].includes(state)) await context.addInitScript(({state})=>localStorage.setItem('hamsarmaye', JSON.stringify({version:0,state:{user:state==='saved'?{mobile:'00000000000'}:null,saved:state==='saved'?['DEMO-01','DEMO-02']:[],profiles:[],criteria:{route:'investor',groups:[],provinces:[],amount:null,filters:{}},started:true,compare:state==='compare'?['DEMO-01','DEMO-02']:[]}})),{state});
    const page = await context.newPage();
    const errors=[]; page.on('pageerror',e=>errors.push(e.message.slice(0,2000)));
    const record = {id:`${id}-${width}`,path,state:state||'default',viewport:{width,height:1000},synthetic_local_state:['results','compare','saved'].includes(state)};
    try {
      const response=await page.goto(origin+path,{waitUntil:'networkidle',timeout:60000});
      record.status=response.status();
      await page.evaluate(()=>document.fonts.ready);
      await page.addStyleTag({content:'nextjs-portal { display:none !important; }'});
      if(state==='login') await page.getByRole('button',{name:/^ورود$/}).first().click();
      await page.waitForTimeout(600);
      const height=await page.evaluate(()=>document.documentElement.scrollHeight);
      if(state!=='login') for(let y=0;y<Math.min(height,18000);y+=700){await page.evaluate(y=>window.scrollTo(0,y),y);await page.waitForTimeout(150);}
      await page.evaluate(()=>window.scrollTo(0,0)); await page.waitForTimeout(400);
      record.title=await page.title();
      record.layout=await page.evaluate(()=>({scrollWidth:document.documentElement.scrollWidth,clientWidth:document.documentElement.clientWidth,scrollHeight:document.documentElement.scrollHeight,dir:document.documentElement.dir,fonts:document.fonts.status,primary:getComputedStyle(document.documentElement).getPropertyValue('--primary').trim(),fontFamily:getComputedStyle(document.body).fontFamily}));
      record.frame_count=page.frames().length;
      record.file=`${record.id}.png`;
      await page.screenshot({path:`${out}/${record.file}`,fullPage:true,animations:'disabled'});
      record.sha256=crypto.createHash('sha256').update(await fs.readFile(`${out}/${record.file}`)).digest('hex');
    } catch(e) {record.capture_error=e.message;}
    record.page_errors=errors;manifest.cases.push(record);
    await fs.writeFile(`${out}/manifest.json`,JSON.stringify(manifest,null,2)+'\n');
    console.log(JSON.stringify({id:record.id,status:record.status,error:record.capture_error,overflow:record.layout?record.layout.scrollWidth-record.layout.clientWidth:null,page_errors:errors.length}));
    await context.close();
  }
} finally {await browser.close();}
