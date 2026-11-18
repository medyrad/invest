'use client';
import { CatalogProvider, useCatalog } from '@/lib/catalog-context';
import { HeroCompass } from './hero-ideas';
import { MainCategories, Categories, Featured, HowItWorks, HelpCenter } from './sections';
import { AlgoField } from '@/components/brand/algo-field';
import { Footer } from '@/components/site/header';
import { Button } from '@/components/ui/button';
function Content() {
  const c = useCatalog();
  return <main className="relative isolate home-page"><AlgoField className="text-ink/[0.04]" /><HeroCompass />
    {c.previewEnabled && c.status === 'ready' && <p role="note" className="mx-auto max-w-7xl px-6 text-sm text-muted-foreground">داده مصنوعی توسعه — این فرصت‌ها از مسیر محلی ثبت و بررسی منتشر شده‌اند؛ فرصت یا احراز واقعی نیستند.</p>}
    {c.status === 'ready' ? <><MainCategories /><Categories /><Featured /><HowItWorks /><HelpCenter /></> : <section className="surface mx-auto my-12 max-w-4xl rounded-3xl p-8" aria-label="وضعیت کاتالوگ"><p role="status">{c.status === 'loading' ? 'در حال دریافت کاتالوگ…' : c.status === 'empty' ? 'کاتالوگ هنوز داده‌ای ندارد.' : 'دریافت کاتالوگ انجام نشد؛ داده تازه‌ای نمایش داده نمی‌شود.'}</p>{c.status !== 'loading' && <Button onClick={() => void c.reload()}>تلاش دوباره</Button>}</section>}
    <Footer /></main>;
}
export default function Home() { return <><CatalogProvider><Content /></CatalogProvider></>; }
