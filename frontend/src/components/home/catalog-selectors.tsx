'use client';
import { useCatalog } from '@/lib/catalog-context';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';

export function CatalogSelectors() {
  const c = useCatalog();
  const group = c.groups.find(g => g.id === c.group);
  const province = c.provinces.find(p => p.id === c.province);
  const county = province?.counties.find(p => p.id === c.county);
  const fields = [
    { label: 'دسته‌بندی', value: c.group, change: c.chooseGroup, options: c.groups },
    { label: 'زیردسته', value: c.subtype, change: c.chooseSubtype, options: group?.subtypes ?? [] },
    { label: 'استان', value: c.province, change: c.chooseProvince, options: c.provinces },
    { label: 'شهرستان', value: c.county, change: c.chooseCounty, options: province?.counties ?? [] },
    { label: 'شهر', value: c.city, change: c.chooseCity, options: county?.cities ?? [] },
  ];
  return <div className="surface mt-6 rounded-3xl p-6" data-section="selectors">
    <div className="flex flex-wrap items-center justify-between gap-3"><p className="font-bold text-ink">انتخاب دسته و مکان — ترجیح شما</p><Popover><PopoverTrigger asChild><Button variant="outline">درباره انتخاب‌ها</Button></PopoverTrigger><PopoverContent dir="rtl" className="max-w-[calc(100vw-2rem)] rounded-2xl text-sm leading-7">بودجه و مکان فقط بر امتیاز پیشنهادها اثر دارند؛ پیشنهادهای متناسب هنوز در این نسخه فعال نیستند. فهرست شهرهای بعضی شهرستان‌ها فعلاً در دسترس نیست؛ انتخاب شهرستان شما حفظ می‌شود.</PopoverContent></Popover></div>
    <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{fields.map(f => <label key={f.label} className="block text-sm font-semibold text-ink"><span className="mb-2 block">{f.label}</span><select aria-label={f.label} disabled={!f.options.length} value={f.value} onChange={e => f.change(e.target.value)} className="h-12 w-full min-w-0 rounded-xl border border-border bg-white px-3 outline-cobalt"><option value="">انتخاب نشده</option>{f.options.map(o => <option key={o.id} value={o.id}>{o.name}</option>)}</select></label>)}</div>
    {county && !county.cities.length && <p role="status" className="mt-3 text-sm text-muted-foreground">فهرست شهرهای این شهرستان فعلاً در دسترس نیست؛ انتخاب شهرستان شما حفظ شده است.</p>}
    <div className="mt-4 flex flex-wrap gap-2">{fields.filter(f => f.value).map(f => <Button key={f.label} variant="outline" onClick={() => f.change('')} aria-label={`حذف ${f.label}`}>حذف {f.label}</Button>)}<Button variant="plain" onClick={c.clear}>پاک‌کردن انتخاب‌ها</Button></div>
  </div>;
}
