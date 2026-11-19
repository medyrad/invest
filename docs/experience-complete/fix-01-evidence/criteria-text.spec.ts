import {test,expect} from '@playwright/test';
import {describeCriteria} from '/source/src/lib/criteria';
const notes='یادداشت کامل و بلند کاربر برای بررسی فرصت؛ این بخش پایانی نباید در سند تاریخی حذف شود.';
const criteria={route:'investor' as const,groups:[],provinces:[],amount:null,filters:{notes}};
test('document criteria preserve complete Persian notes without altering raw data',()=>{
 const before=JSON.stringify(criteria);
 expect(describeCriteria(criteria,{fullText:true}).find(c=>c.key==='notes')?.label).toContain(notes);
 expect(JSON.stringify(criteria)).toBe(before);
});
test('compact chips retain existing abbreviated presentation',()=>{
 const chip=describeCriteria(criteria).find(c=>c.key==='notes')!;
 expect(chip.label).toContain(notes.slice(0,32)+'…');
 expect(chip.label).not.toContain(notes);
});
