import {expect,test,type Page} from '@playwright/test';
import fs from 'node:fs';

const product='http://127.0.0.1:3109';
const widths=[360,390,768,1440];
const detail={fund:'468adec1-0aa0-4eeb-af9a-acc068d9c014',sale:'699e857d-40a9-4e99-ac49-108a3a0ba3b7'};

async function fonts(page:Page){await page.evaluate(()=>document.fonts.ready)}
async function login(page:Page,role:string){
  await page.goto(product+'/local-roles');
  await page.getByRole('button',{name:new RegExp(` · ${role}$`)}).first().click();
  await page.waitForURL(url=>!url.pathname.includes('local-roles'));
}
async function stable(page:Page){
  await page.waitForLoadState('domcontentloaded');
  await fonts(page);
  await page.waitForTimeout(250);
}

for(const width of widths)test(`current detail kinds ${width}`,async({browser})=>{
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();
  for(const [kind,id] of Object.entries(detail)){
    await page.goto(product+'/opportunities/'+id);await stable(page);
    await expect(page.locator('main')).toBeVisible();
    await page.screenshot({path:`/evidence/design-detail-${kind}-${width}.png`,fullPage:true});
  }
  await context.close();
});

const panels=[
  {id:'workspace',route:'/workspace',role:'owner'},
  {id:'drafts',route:'/drafts',role:'owner'},
  {id:'requests',route:'/requests',role:'user'},
  {id:'admin',route:'/admin',role:'admin'},
  {id:'expert',route:'/expert',role:'expert'},
];
for(const width of widths)test(`role panels and real controls ${width}`,async({browser})=>{
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();const rows=[];
  for(const panel of panels){
    await login(page,panel.role);await page.goto(product+panel.route);await stable(page);
    await expect(page.locator('main')).toBeVisible();
    const controls=page.locator('main button:visible,main a:visible,main input:visible,main select:visible,main textarea:visible');
    const count=await controls.count();let focused=false;let hit=true;
    if(count){
      const first=controls.first();await first.focus();focused=await first.evaluate(el=>el===document.activeElement);
      hit=await first.evaluate(el=>{const r=el.getBoundingClientRect();const x=Math.max(0,Math.min(innerWidth-1,r.left+r.width/2));const y=Math.max(0,Math.min(innerHeight-1,r.top+r.height/2));const target=document.elementFromPoint(x,y);return target===el||!!target&&el.contains(target)});
    }
    const overflow=await page.evaluate(()=>document.documentElement.scrollWidth>innerWidth+1);
    expect(overflow).toBeFalsy();expect(hit).toBeTruthy();if(count)expect(focused).toBeTruthy();
    rows.push({panel:panel.id,route:panel.route,role:panel.role,width,controls:count,focus:focused,hit,overflow});
    await page.screenshot({path:`/evidence/design-${panel.id}-${width}.png`,fullPage:true});
  }
  fs.writeFileSync(`/evidence/design-interaction-${width}.json`,JSON.stringify(rows,null,2));
  await context.close();
});

for(const width of widths)test(`current library and frozen report ${width}`,async({browser})=>{
  const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});
  const page=await context.newPage();
  await page.goto(product+'/library');await stable(page);
  await expect(page.locator('main')).toBeVisible();
  await page.screenshot({path:`/evidence/design-library-${width}.png`,fullPage:true});
  const html=fs.readFileSync('/current-report/fresh-report.html','utf8');
  await page.setContent(html,{waitUntil:'load'});await stable(page);
  await expect(page.locator('body')).toContainText('مسیر: سرمایه‌گذار');
  await page.screenshot({path:`/evidence/design-report-current-${width}.png`,fullPage:true});
  await context.close();
});
