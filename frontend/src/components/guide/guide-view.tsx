"use client";
// صفحه راهنمای اقدام: پیش‌نمایش همان فایل HTML که دانلود می‌شود.
// مطابق نسخه مرجع، فایل با اطلاعات خود کاربر پر می‌شود: شرایط جست‌وجو، پاسخ پرسش‌های تخصصی، نوع پیگیری و تیک گام‌ها.
import {core} from "@/lib/core-api";
import {services} from "@/components/tools/api";
import {toCriteria} from "@/lib/store";
import {toast} from "@/lib/toast";
import {useAuth} from "@/components/auth/login-dialog";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { ArrowRight, DocumentDownload, Edit2, Printer, TickCircle } from "@/components/iconsax";
import { Button } from "@/components/ui/button";
import { Header, Footer } from "@/components/site/header";
import { NodeMark } from "@/components/brand/algo-pattern";
import { Dropdown } from "@/components/search/controls";
import { routes } from "@/data/routes";
import { describeCriteria } from "@/lib/criteria";
import { followUpKinds, guideHtml, type GuideContext } from "@/lib/guide";
import { listingById } from "@/lib/listings";
import { useHydrated, useStore } from "@/lib/store";
import type { Advisory, Opportunity } from "@/types";
import { faNumber } from "@/lib/utils";

type EffectiveAdvisoryResult={version:number;effective_answers:Record<string,string>;questions:Advisory['questions'];guidance:{why?:string;checks:string[]}};

export function GuideView({ id }: { id: string }) {
  const l = listingById(id)!;
  const {account,start}=useAuth();
  const pending=useRef<object|null>(null);
  const [saving,setSaving]=useState(false);
  const o = l.kind === "project" ? (l.raw as Opportunity) : null;
  const hydrated = useHydrated();
  const criteria = useStore((s) => s.criteria);
  const [kind, setKind] = useState<string | undefined>();
  const [checked, setChecked] = useState<string[]>([]);
  const frame = useRef<HTMLIFrameElement>(null);
  const [height, setHeight] = useState(1400);
  const [effective,setEffective]=useState<EffectiveAdvisoryResult|null>(null);
  const [advisoryState,setAdvisoryState]=useState<'idle'|'loading'|'ready'|'error'>('idle');
  useEffect(()=>{if(!o){setEffective(null);setAdvisoryState('ready');return;}const answers=Object.fromEntries(Object.entries(criteria.filters).filter(([k,v])=>k.startsWith(`adv:${o.subtype}:`)&&typeof v==='string').map(([k,v])=>[k.slice(`adv:${o.subtype}:`.length),String(v)]));let live=true;setAdvisoryState('loading');void services<EffectiveAdvisoryResult>(`advisories/${o.subtype}`,{answers,funding:'own',role:'investor'}).then(x=>{if(live){setEffective(x);setAdvisoryState('ready')}}).catch(()=>{if(live){setEffective(null);setAdvisoryState('error')}});return()=>{live=false}},[o?.subtype,criteria.filters]);
  const effectiveAdvisory=useMemo<Advisory|undefined>(()=>effective?{context:effective.guidance.why||'',baseChecks:effective.guidance.checks,questions:effective.questions,example:{}}:undefined,[effective]);

  const ctx = useMemo<GuideContext>(() => {
    if (!hydrated) return {};
    const mine: [string, string][] = [];
    const answers: Record<string, string> = {};
    const mineOk = l.routes.includes(criteria.route);
    if (mineOk) {
      const chips = describeCriteria(criteria).filter((c) => !c.key.startsWith("adv:"));
      if (chips.length) mine.push(["مسیر ورود", routes.find((r) => r.id === criteria.route)!.name]);
      const provs = chips.filter((c) => c.kind === "province").map((c) => c.label), groups = chips.filter((c) => c.kind === "group").map((c) => c.label);
      if (provs.length) mine.push(["محدوده", provs.join("، ")]);
      if (groups.length) mine.push(["حوزه", groups.join("، ")]);
      for (const c of chips) {
        if (c.kind === "amount") mine.push(["بودجه", c.label]);
        if (c.kind === "filter") { const i = c.label.indexOf(": "); mine.push(i > 0 ? [c.label.slice(0, i), c.label.slice(i + 2)] : [c.label, "بله"]); }
      }
    }
    if (o&&effective) Object.assign(answers,effective.effective_answers);
    return { mine, answers, kind, checked,advisory_version:effective?.version };
  }, [hydrated, criteria, kind, checked, l, o, effective]);

  const html = useMemo(() => guideHtml(l, ctx,effectiveAdvisory), [l, ctx,effectiveAdvisory]);
  // تیک‌ها داخل خود سند زده می‌شوند، پیش از هر بازسازی یا دانلود از سند خوانده می‌شوند تا از بین نروند
  const ticks = () => Array.from(frame.current?.contentDocument?.querySelectorAll<HTMLInputElement>("input[data-k]:checked") ?? []).map((i) => i.dataset.k!);
  const changeKind = (v: string | undefined) => { setChecked(ticks()); setKind(v); };
  const download = async () => {
    if(!account){await start();return;}
    if(saving)return;setSaving(true);
    pending.current ||= {key:crypto.randomUUID(),action:'report',id:l.id,value:{criteria:toCriteria(criteria),guide_context:{...ctx,checked:ticks()}}};
    try {
      const receipt=await core<{report_id:string;download:string}>('personal',pending.current);
      const a=document.createElement('a');a.href=receipt.download;a.download='guide-'+receipt.report_id+'.html';document.body.appendChild(a);a.click();a.remove();pending.current=null;
      toast('گزارش با snapshot ثابت ذخیره و دریافت شد؛ پرونده‌ای ارسال نشد.');
    }catch(e){toast(e instanceof Error?e.message:'دریافت انجام نشد.');if(e&&typeof e==='object'&&'status'in e)pending.current=null}finally{setSaving(false)}
  };
  const filled = (ctx.mine?.length ?? 0) + Object.keys(ctx.answers ?? {}).length;

  return (
    <>
      <Header />
      <main className="focus-blur mx-auto max-w-7xl px-3 pt-6 sm:px-6">
        <Link href={`/opportunities/${l.id}`} className="mb-4 inline-flex items-center gap-2 text-sm font-bold text-ink/70 hover:text-ink"><ArrowRight size={18} />بازگشت به پروژه</Link>
        <div className="grid min-w-0 grid-cols-1 items-start gap-5 lg:grid-cols-[minmax(0,1fr)_21rem]">
          <iframe ref={frame} title="راهنمای اقدام" srcDoc={html} onLoad={() => { const d = frame.current?.contentDocument; if (d) setHeight(d.documentElement.scrollHeight + 8); }}
            className="w-full rounded-[2rem] border border-border bg-muted" style={{ height }} />

          <aside className="min-w-0 space-y-4 lg:sticky lg:top-24">
            <div className="surface rounded-[1.75rem] p-5">
              <p className="flex items-center gap-2 text-[13px] font-extrabold text-primary-ink"><NodeMark />راهنمای اقدام</p>
              <h1 className="mt-2 text-lg font-black leading-8 text-ink">{l.title}</h1>
              <div className="mt-4 space-y-2">
                <Button disabled={saving||(!!o&&advisoryState!=='ready')} onClick={download} className="h-12 w-full gap-2 rounded-full font-extrabold"><DocumentDownload size={18} variant="Bold" />{advisoryState==='loading'?'دریافت راهنمای مؤثر…':'دانلود فایل راهنما'}</Button>
                {advisoryState==='error'&&<p role="alert" className="text-xs font-bold leading-6 text-red-700">راهنمای نسخه‌دار از سرور دریافت نشد؛ صفحه را تازه کنید و دوباره تلاش کنید.</p>}
                <Button variant="outline" onClick={() => frame.current?.contentWindow?.print()} className="h-11 w-full gap-2 rounded-full bg-white font-bold shadow-none"><Printer size={18} />چاپ یا PDF</Button>
              </div>
            </div>

            <div className="surface space-y-5 rounded-[1.75rem] p-5">
              <div>
                <h2 className="flex items-center gap-2 text-[15px] font-extrabold text-ink"><Edit2 size={18} variant="Bulk" className="text-primary-ink" />راهنما را با اطلاعات خودتان کامل کنید</h2>
                <p className="mt-1.5 text-xs leading-6 text-muted-foreground">هرچه این‌جا مشخص کنید همان لحظه در فایل می‌آید.</p>
              </div>
              <div>
                <p className="mb-2 text-[13px] font-bold text-ink/80">نوع پیگیری</p>
                <Dropdown options={followUpKinds} value={kind} onChange={changeKind} />
              </div>
              <p className="flex items-start gap-2 rounded-2xl bg-ink/[0.05] p-3.5 text-xs font-semibold leading-6 text-ink/80"><TickCircle size={17} variant="Bold" className="mt-0.5 shrink-0 text-primary-ink" />موارد «پیش از اقدام» و «گام‌های اقدام» را در خود راهنما تیک بزنید، تیک‌ها در فایل دانلودی و چاپ می‌مانند.</p>
              <div className="rounded-2xl bg-muted p-3.5 text-xs font-semibold leading-6 text-ink/75">
                {filled > 0
                  ? <>{faNumber(filled)} مورد از شرایط و پاسخ‌های شما در بخش «شرایط شما» و پرسش‌ها آمده است.</>
                  : <>شرایط جست‌وجو و پاسخ پرسش‌های تخصصی شما، اگر در صفحه پروژه‌ها وارد کرده باشید، خودکار در فایل می‌آید.</>}
                <Link href="/opportunities" className="mt-1 block font-extrabold text-primary-ink hover:underline">ویرایش شرایط در صفحه پروژه‌ها</Link>
              </div>
            </div>
          </aside>
        </div>
      </main>
      <Footer />
    </>
  );
}
