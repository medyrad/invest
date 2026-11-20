'use client';
import { CatalogProvider, useCatalog } from '@/lib/catalog-context';
import { HeroCompass } from './hero-ideas';
import { MainCategories, Categories, Featured, HowItWorks, HelpCenter } from './sections';
import { AlgoField } from '@/components/brand/algo-field';
import { Footer } from '@/components/site/header';
import { Button } from '@/components/ui/button';
import { HomeCatalogSkeleton, LoadFailure } from '@/components/loading/loading-system';
function Content() {
  const c = useCatalog();
  return <main className="relative isolate home-page"><AlgoField className="text-ink/[0.04]" /><HeroCompass />
    {c.hasSynthetic && c.status === 'ready' && <p role="note" className="mx-auto max-w-7xl px-6 text-sm text-muted-foreground">داده مصنوعی توسعه — این فرصت‌ها از مسیر محلی ثبت و بررسی منتشر شده‌اند؛ فرصت یا احراز واقعی نیستند.</p>}
    {c.status === 'loading' ? <HomeCatalogSkeleton /> : c.status === 'error' ? <LoadFailure message={c.error || 'دریافت کاتالوگ انجام نشد؛ داده قدیمی نمایش داده نمی‌شود.'} onRetry={() => void c.reload()} /> : c.status === 'empty' ? <section className="surface mx-auto my-12 max-w-3xl rounded-[2rem] p-10 text-center" role="status"><h2 className="text-xl font-black">کاتالوگ هنوز آماده نیست.</h2><p className="mt-3 text-sm leading-7 text-muted-foreground">پس از آماده‌شدن طبقه‌بندی رسمی، مسیرها و فرصت‌های منتشرشده اینجا نمایش داده می‌شوند.</p><Button className="mt-5 rounded-full" onClick={() => void c.reload()}>بررسی دوباره</Button></section> : <>{!c.listings.length && <section className="surface mx-auto my-10 max-w-3xl rounded-[2rem] p-9 text-center" role="status"><h2 className="text-lg font-black">هنوز فرصت عمومی منتشر نشده است.</h2><p className="mt-2 text-sm leading-7 text-muted-foreground">نقشه و فهرست فقط فرصت‌های تأیید و منتشرشده را نشان می‌دهند.</p></section>}<MainCategories /><Categories /><Featured /><HowItWorks /><HelpCenter /></>}
    <Footer /></main>;
}
export default function Home() { return <><CatalogProvider><Content /></CatalogProvider></>; }
