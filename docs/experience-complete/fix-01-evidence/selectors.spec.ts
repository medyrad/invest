import {test,expect} from '@playwright/test';
import fs from 'node:fs';
for(const width of [360,390,768,1440])test('land grouped selectors retain independent choices and keyboard '+width,async({browser})=>{
 const context=await browser.newContext({viewport:{width,height:1000},reducedMotion:'reduce'});const page=await context.newPage();
 await page.goto('/tools/land-preparation');await page.evaluate(()=>document.fonts.ready);
 const groups=page.locator('.service-option-group');await expect(groups).toHaveCount(2);
 const selected=[];
 for(let i=0;i<2;i++){
  const trigger=groups.nth(i).getByRole('combobox');await trigger.click();await expect(trigger).toHaveAttribute('aria-expanded','true');
  const option=page.getByRole('dialog').locator('label').first();const title=await option.locator('span.block').first().innerText();
  await option.click();await expect(trigger).toContainText(title);await page.keyboard.press('Escape');await expect(trigger).toHaveAttribute('aria-expanded','false');
  selected.push(title);
 }
 for(let i=0;i<2;i++)await expect(groups.nth(i).getByRole('combobox')).toContainText(selected[i]);
 const first=groups.first().getByRole('combobox');await first.focus();await page.keyboard.press('Enter');
 await expect(first).toHaveAttribute('aria-expanded','true');await expect(page.getByRole('dialog').getByRole('checkbox').first()).toBeChecked();
 await page.keyboard.press('Escape');await first.scrollIntoViewIfNeeded();
 const hit=await first.evaluate(e=>{const r=e.getBoundingClientRect();const target=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return e===target||e.contains(target)});expect(hit).toBe(true);
 await page.screenshot({path:`/evidence/land-selected-${width}.png`,fullPage:true});fs.writeFileSync(`/evidence/land-selected-${width}.json`,JSON.stringify({width,selected,hit}));await context.close();
});
