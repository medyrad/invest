"use client";
// صفحه جزئیات: روایت پروژه به‌جای متن پشت‌سرهم. همه فیلدهای داده نمایش داده می‌شوند،
// هر جا داده‌ای نیست «ثبت نشده» می‌آید تا ساختار صفحه برای همه پروژه‌ها یکسان بماند.
import {RequestAction} from "@/components/core/request-action";
import {ExactFacts,DeclaredTimes} from "@/components/core/exact-facts";
import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useMemo, useState } from "react";
import { motion } from "motion/react";
import { toast } from "@/lib/toast";
import {
  ArrowLeft, ArrowRight, Call,  DocumentDownload, Location, Warning2, ShieldSearch, WalletMoney, MoneyRecive, Key,
  Timer1, Lock1, Chart, Calendar, Building, TickCircle, InfoCircle, Danger, Convertshape2, AddCircle, DocumentText, MagicStar, type Icon,
} from "@/components/iconsax";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Header, Footer } from "@/components/site/header";
import { LocationMap } from "@/components/brand/iran-map";
import { Reveal } from "@/components/brand/reveal";
import { SignaturePhoto } from "./signature-photo";
import { HeroGallery } from "./gallery";
import { ListingCard, SaveButton } from "./listing-card";
import { galleryOf, listingById, listings, payoutLabel } from "@/lib/listings";
import { dossier, factGroups, splitPending, type DossierSection, type FactGroup } from "@/lib/facts";
import { projectGroups } from "@/data/taxonomy";
import { advisories } from "@/data/advisories";
import { useHydrated, useStore } from "@/lib/store";
import { COMPARE_MAX, oppOf } from "@/lib/compare";
import { sheetOf } from "@/lib/sheet";
import { hasAnyCriteria } from "@/lib/criteria";
import { rank } from "@/lib/match";
import { CompareTray } from "@/components/compare/tray";
import type { Advisory, Fund, Listing, Opportunity, RouteId, SaleItem } from "@/types";
import { routeSteps } from "@/data/routes";
import { cn, faNumber, incomeLabel, legalLabel } from "@/lib/utils";


const ease = [0.22, 1, 0.36, 1] as const;
const NA = "ثبت نشده";

/** عنوان هر فصل: بدون شماره و بدون زیرعنوان روبه‌رو */
function Chapter({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Reveal className="relative">
      <div className="mb-5 flex items-center gap-3">
        <h2 className="text-xl font-black text-ink">{title}</h2>
        <span className="h-px flex-1 bg-gradient-to-l from-border to-transparent" />
      </div>
      {children}
    </Reveal>
  );
}

function Tile({ I, label, value, sub }: { I: Icon; label: string; value: string; sub?: string }) {
  return (
    <Card className="surface gap-3 rounded-[1.5rem] p-5 shadow-none">
      <span className="grid size-10 place-items-center rounded-xl bg-ink/[0.06] text-primary-ink"><I size={20} variant="Bulk" /></span>
      <span>
        <span className="block text-xs font-semibold text-muted-foreground">{label}</span>
        <span className="mt-1 block text-xl font-black leading-8 text-ink">{value}</span>
        {sub && <span className="block text-[11px] font-semibold text-muted-foreground">{sub}</span>}
      </span>
    </Card>
  );
}

/** شناسنامه: بخش‌های تمام‌عرض بازشونده (فلش برای باز و بسته)، هر ردیف «عنوان | مقدار»، اولی پیش‌فرض باز است.
 *  ارتفاع به متن وابسته نیست چون کارت‌ها کنار هم نیستند. */
const groupIcon: Record<string, Icon> = { project: Building, money: WalletMoney, status: ShieldSearch };
function Facts({ groups }: { groups: FactGroup[] }) {
  return (
    <Accordion type="multiple" defaultValue={groups[0] ? [groups[0].id] : []} className="space-y-3">
      {groups.map((g) => { const I = groupIcon[g.id] ?? Building; const { known, pending } = splitPending(g.items);
        return (
          <AccordionItem key={g.id} value={g.id} className="surface overflow-hidden rounded-[1.5rem] border-0 last:border-b-0">
            <AccordionTrigger className="items-center px-6 py-4 text-right hover:no-underline [&>svg]:size-5 [&>svg]:text-ink/50">
              <span className="flex items-center gap-3">
                <span className="grid size-9 place-items-center rounded-xl bg-ink/[0.05] text-primary-ink"><I size={18} variant="Bulk" /></span>
                <span className="text-[15px] font-extrabold text-ink">{g.title}</span>
                <span className="text-[12px] font-semibold text-muted-foreground">{faNumber(known.length)} مورد</span>
              </span>
            </AccordionTrigger>
            <AccordionContent className="border-t border-border/80 px-6 pb-3 pt-0">
              <dl className="divide-y divide-border/70">
                {known.map(([k, v]) => (
                  <div key={k} className="grid grid-cols-[13rem_minmax(0,1fr)] items-baseline gap-6 py-3">
                    <dt className="text-[13px] font-semibold text-muted-foreground">{k}</dt>
                    <dd className={cn("text-[14px] font-bold leading-7", v === NA ? "font-semibold text-ink/35" : "text-ink")}>{v}</dd>
                  </div>
                ))}
              </dl>
              {pending.length > 0 && <p className="mb-1 mt-1 border-t border-dashed border-border pt-3 text-[12.5px] leading-6 text-muted-foreground"><b className="font-extrabold text-ink/70">ثبت نشده: </b>{pending.join("، ")}</p>}
            </AccordionContent>
          </AccordionItem>
        ); })}
    </Accordion>
  );
}

const riskTone: Record<number, { text: string; stroke: string; soft: string; bar: string }> = {
  1: { text: "text-primary-ink", stroke: "stroke-primary", soft: "bg-ink/[0.06]", bar: "bg-primary" },
  2: { text: "text-warn", stroke: "stroke-warn", soft: "bg-warn/10", bar: "bg-warn" },
  3: { text: "text-destructive", stroke: "stroke-destructive", soft: "bg-destructive/10", bar: "bg-destructive" },
};
const riskLevel = (risk: string) => ({ low: 1, medium: 2, high: 3 }[risk] ?? 0);

/** نوار سه‌قسمتی فشرده: فقط سطح فعلی رنگ می‌گیرد تا سطح بالا همه نوار را قرمز نکند. */
function RiskMeter({ risk }: { risk: string }) {
  const level = riskLevel(risk);
  return (
    <div>
      <div className="flex gap-1.5">{[1, 2, 3].map((i) => <span key={i} className={cn("h-2 flex-1 rounded-full", i === level ? riskTone[i].bar : i < level ? cn(riskTone[level].bar, "opacity-25") : "bg-muted")} />)}</div>
      <div className="mt-2 grid grid-cols-3 text-[11px]">{["کم", "متوسط", "زیاد"].map((t, i) => <span key={t} className={cn("text-center first:text-right last:text-left", i + 1 === level ? cn("font-extrabold", riskTone[level].text) : "font-semibold text-muted-foreground")}>{t}</span>)}</div>
    </div>
  );
}

/** عقربه نیم‌دایره: کم در راست، زیاد در چپ (هم‌جهت با خواندن راست‌به‌چپ). */
/** گیج ریسک راست‌به‌چپ: مثل خواندن فارسی از راست (کم) شروع می‌شود و تا سطح پروژه پر می‌شود،
 *  رنگ هر نقطه از کمان به جایگاهش بسته است، پس سطح بالاتر یعنی پیمودن رنگ‌های بیشتر. */
const riskHex = ["#94a3a0", "#00adab", "#d4532f", "#b4291c"];
function RiskGauge({ risk }: { risk: string }) {
  const level = riskLevel(risk);
  const frac = level / 3;
  const pt = (deg: number, r = 80) => [100 + r * Math.cos((deg * Math.PI) / 180), 100 - r * Math.sin((deg * Math.PI) / 180)] as const;
  const arcD = "M180 100 A80 80 0 0 0 20 100";
  const [ex, ey] = pt(frac * 180);
  const labels = ["کم", "متوسط", "زیاد"];
  return (
    <div className="relative mx-auto w-full max-w-[18rem]">
      <svg viewBox="0 -14 200 128" className="block w-full overflow-visible" aria-hidden>
        <defs>
          {/* گرادیان از راست به چپ: x1 سمت راست کمان است */}
          <linearGradient id="risk-rtl" gradientUnits="userSpaceOnUse" x1="180" y1="0" x2="20" y2="0">
            <stop offset="0" stopColor="#00adab" /><stop offset="0.3" stopColor="#5dd0cf" />
            <stop offset="0.46" stopColor="#ec8f5e" /><stop offset="0.72" stopColor="#d4532f" /><stop offset="1" stopColor="#b4291c" />
          </linearGradient>
          <filter id="risk-soft" x="-20%" y="-40%" width="140%" height="180%"><feGaussianBlur stdDeviation="3" /></filter>
        </defs>
        {/* ریل خاکستری کامل و دو جداکننده سطح */}
        <path d={arcD} fill="none" strokeWidth={12} strokeLinecap="round" className="stroke-muted" />
        {[60, 120].map((d) => { const [x0, y0] = pt(d, 72), [x1, y1] = pt(d, 88); return <line key={d} x1={x0} y1={y0} x2={x1} y2={y1} stroke="white" strokeWidth={2.5} />; })}
        {level > 0 && <>
          <motion.path d={arcD} fill="none" stroke="url(#risk-rtl)" strokeWidth={12} strokeLinecap="round" opacity={0.35} filter="url(#risk-soft)"
            initial={{ pathLength: 0 }} whileInView={{ pathLength: frac }} viewport={{ once: true }} transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }} />
          <motion.path d={arcD} fill="none" stroke="url(#risk-rtl)" strokeWidth={12} strokeLinecap="round"
            initial={{ pathLength: 0 }} whileInView={{ pathLength: frac }} viewport={{ once: true }} transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }} />
          {[60, 120].filter((d) => d < frac * 180).map((d) => { const [x0, y0] = pt(d, 72), [x1, y1] = pt(d, 88); return <line key={d} x1={x0} y1={y0} x2={x1} y2={y1} stroke="white" strokeWidth={2.5} />; })}
          <motion.g initial={{ opacity: 0, scale: 0.4 }} whileInView={{ opacity: 1, scale: 1 }} viewport={{ once: true }} transition={{ delay: 0.95, type: "spring", stiffness: 260, damping: 16 }} style={{ transformBox: "fill-box", transformOrigin: "center" }}>
            <circle cx={ex} cy={ey} r={10} fill="white" stroke={riskHex[level]} strokeWidth={3.5} />
            <circle cx={ex} cy={ey} r={3.5} fill={riskHex[level]} />
          </motion.g>
        </>}
        {/* برچسب سه سطح بیرون کمان، از راست به چپ */}
        {labels.map((t, i) => { const [x, y] = pt(30 + i * 60, 103);
          return <text key={t} x={x} y={y + 3} textAnchor="middle" fontSize={8} fontWeight={600} fill="#8a9290">{t}</text>; })}
      </svg>
      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-col items-center">
        <span className={cn("font-black leading-none", level ? "text-[1.65rem]" : "text-lg")} style={{ color: riskHex[level] }}>{level ? labels[level - 1] : "ارزیابی‌نشده"}</span>
        <span className="mt-1.5 text-[11px] font-semibold text-muted-foreground">{level ? `سطح ${faNumber(level)} از ${faNumber(3)}` : "سطح ریسک ثبت نشده است"}</span>
      </div>
    </div>
  );
}

/** مسیر پول به شکل ردیف‌های «عنوان | متن» (مثل شناسنامه)، داخل همان کارت «پول شما در طول زمان» */
function MoneyFlow({ o }: { o: { finance?: string; repay?: string; ownership?: string | null } }) {
  const nodes = [
    { I: WalletMoney, t: "پول از کجا می‌آید", d: o.finance },
    { I: MoneyRecive, t: "چطور برمی‌گردد", d: o.repay },
    { I: Key, t: "مالکیت و سهم", d: o.ownership },
  ].filter((x) => x.d);
  return (
    <dl className="divide-y divide-border/70">
      {nodes.map((x) => (
        <div key={x.t} className="grid grid-cols-[13rem_minmax(0,1fr)] items-start gap-6 py-3.5">
          <dt className="flex items-center gap-2.5 text-[13px] font-bold text-ink/70"><span className="grid size-8 shrink-0 place-items-center rounded-lg bg-ink/[0.05] text-primary-ink"><x.I size={17} variant="Bulk" /></span>{x.t}</dt>
          <dd className="pt-1 text-[14.5px] font-semibold leading-7 text-ink">{x.d}</dd>
        </div>
      ))}
    </dl>
  );
}

/** نقاط عطف زمانی روی محور نمودار بازگشت (به‌جای ردیف جدای زیر نمودار) */
const ordinal = ["اول", "دوم", "سوم", "چهارم", "پنجم", "ششم", "هفتم", "هشتم", "نهم", "دهم"];
function Steps({ steps }: { steps: string[] }) {
  return (
    <ol>
      {steps.map((s, i) => (
        <li key={s} className="relative flex gap-4 pb-3 last:pb-0">
          {i < steps.length - 1 && <span aria-hidden className="absolute bottom-0 right-[1.375rem] top-11 border-r-2 border-dashed border-ink/15" />}
          <span className={cn("relative z-10 grid size-11 shrink-0 place-items-center rounded-full text-base font-black", i === 0 ? "bg-primary text-white shadow-[0_10px_24px_-12px_var(--primary)]" : "bg-white text-primary-ink ring-1 ring-border")}>{faNumber(i + 1)}</span>
          <div className="surface min-w-0 flex-1 rounded-2xl px-5 py-3.5">
            <p className="text-[12px] font-extrabold text-primary-ink">گام {ordinal[i] ?? faNumber(i + 1)}</p>
            <p className="mt-0.5 text-[15px] font-bold leading-7 text-ink">{s}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

/** پرونده کامل: بخش‌های جزئیات نسخه مرجع، هر کدام در یک آکاردئون تا صفحه شلوغ نشود */
function Dossier({ sections }: { sections: DossierSection[] }) {
  return (
    <Accordion type="multiple" defaultValue={[(sections.find((x) => /^terms|^heritage|^rights/.test(x.id)) ?? sections[0]).id]} className="surface rounded-[1.75rem] px-6">
      {sections.map((sec) => (
        <AccordionItem key={sec.id} value={sec.id} className="border-border">
          <AccordionTrigger className="py-4 text-right text-[15px] font-extrabold text-ink hover:no-underline">{sec.title}</AccordionTrigger>
          <AccordionContent className="pb-5">
            {sec.note && <p className="mb-3 text-[13px] font-semibold leading-6 text-muted-foreground">{sec.note}</p>}
            {(() => { const { known, pending } = splitPending(sec.rows);
              return <>
                {known.length > 0 && (
                  <dl className="grid grid-cols-2 gap-x-8">
                    {known.map(([k, v]) => (
                      <div key={k} className="border-b border-dashed border-border/80 py-3">
                        <dt className="text-xs font-semibold text-muted-foreground">{k}</dt>
                        <dd className="mt-1 text-sm font-extrabold leading-7 text-ink">{v}</dd>
                      </div>
                    ))}
                  </dl>
                )}
                {pending.length > 0 && (
                  <div className={cn("rounded-2xl border border-dashed border-border px-4 py-3", known.length > 0 && "mt-4")}>
                    <p className="text-xs font-extrabold text-ink/70">هنوز ثبت نشده و با دریافت اسناد کامل می‌شود ({faNumber(pending.length)} مورد)</p>
                    <div className="mt-2 flex flex-wrap gap-1.5">{pending.map((k) => <span key={k} className="rounded-full bg-muted px-2.5 py-0.5 text-xs font-semibold text-ink/60">{k}</span>)}</div>
                  </div>
                )}
              </>; })()}
            {!!sec.notes?.length && <div className="mt-4 grid grid-cols-2 gap-3">{sec.notes.map(([t, d]) => (
              <div key={t} className="rounded-2xl bg-muted/70 px-4 py-3"><p className="text-[13px] font-extrabold text-ink">{t}</p><p className="mt-1 text-[13px] font-semibold leading-6 text-ink/70">{d}</p></div>
            ))}</div>}
          </AccordionContent>
        </AccordionItem>
      ))}
    </Accordion>
  );
}

/** پرسش‌های تخصصی نوع پروژه از نسخه مرجع، فقط برای خواندن */
function AdvisoryBlock({ a }: { a: Advisory }) {
  return (
    <div className="space-y-4">
      <p className="border-r-2 border-primary pr-4 text-[15px] font-semibold leading-8 text-ink/85">{a.context}</p>
      {a.baseChecks.length > 0 && (
        <ul className="grid grid-cols-2 gap-2">
          {a.baseChecks.map((c) => <li key={c} className="surface flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm font-semibold leading-7 text-ink/85"><TickCircle size={18} variant="Bulk" className="mt-1 shrink-0 text-primary-ink" />{c}</li>)}
        </ul>
      )}
      <Accordion type="multiple" className="surface rounded-[1.75rem] px-5">
        {a.questions.map((q, i) => (
          <AccordionItem key={q.id} value={q.id} className="border-border">
            <AccordionTrigger className="py-4 text-right text-[15px] font-bold leading-7 text-ink hover:no-underline"><span className="flex items-start gap-3"><span className="mt-0.5 grid size-6 shrink-0 place-items-center rounded-full bg-muted text-[11px] font-black">{faNumber(i + 1)}</span>{q.label}</span></AccordionTrigger>
            <AccordionContent className="pb-5 pr-9">
              {/* گزینه‌ها بدون پس‌زمینه، عنوان هر گزینه با بولت */}
              <ul className="space-y-3">
                {q.options.map((op) => {
                  const block = q.block.includes(op.value), review = q.review.includes(op.value);
                  return (
                    <li key={op.value} className="relative pr-4">
                      <span aria-hidden className="absolute right-0 top-[0.7rem] size-1.5 rounded-full bg-ink/45" />
                      <p className="flex flex-wrap items-center gap-2 text-sm font-bold leading-7 text-ink">{op.label}
                        {block && <Badge variant="outline" className="gap-1 border-destructive/30 bg-destructive/5 text-[11px] text-destructive"><Danger size={12} variant="Bold" />مانع ادامه</Badge>}
                        {review && <Badge variant="outline" className="bg-white text-[11px] text-ink/70">نیازمند بررسی</Badge>}
                      </p>
                      {q.actions[op.value] && <p className="text-[13px] leading-6 text-muted-foreground">{q.actions[op.value]}</p>}
                    </li>
                  );
                })}
              </ul>
            </AccordionContent>
          </AccordionItem>
        ))}
      </Accordion>
    </div>
  );
}

/** کارت اقدام: کارشناس و شماره (آیکون کپی داخل خود فیلد) یا فایل راهنما */
function Contact({l}:{l:Listing}) {return <RequestAction id={l.id}/>;}

function useNearby(l:Listing,needPayback=false){
 const criteria=useStore(s=>s.criteria);const hydrated=useHydrated();
 return useMemo(()=>hydrated?rank(listings,criteria).map(r=>r.listing).filter(x=>x.kind==='project'&&x.id!==l.id&&(!needPayback||oppOf(x).paybackYears!=null)).slice(0,3):[],[criteria,hydrated,l,needPayback]);
}

/** کنار پروژه‌های نزدیک بسنجید: در ستون کناری و کم‌اولویت‌تر از تماس، هر پروژه جدا به مقایسه اضافه می‌شود */
function CompareCard({ l, near }: { l: Listing; near: Listing[] }) {
  const router = useRouter();
  const { compare, toggleCompare, setCompare, criteria } = useStore();
  const hydrated = useHydrated();
  const inList = (id: string) => hydrated && compare.includes(id);
  const add = (id: string) => { if (!inList(id) && compare.length >= COMPARE_MAX) return toast("حداکثر چهار پروژه را می‌توانید مقایسه کنید."); toggleCompare(id); };
  if (!near.length) return null;
  return (
    <div className="surface rounded-[1.75rem] p-5">
      <p className="flex items-center gap-2 text-[13.5px] font-extrabold text-ink"><Convertshape2 size={18} variant="Bulk" className="text-cobalt" />با پروژه‌های نزدیک بسنجید</p>
      <p className="mt-1 text-[11.5px] font-semibold leading-5 text-muted-foreground">{hydrated && hasAnyCriteria(criteria) ? "فرصت‌های دیگر با ترتیب سروری شرایط شما" : "فرصت‌های دیگر همین مسیر"}</p>
      <ul className="mt-3 space-y-1">
        {near.map((x) => { const ox = oppOf(x); const on = inList(x.id);
          return (
            <li key={x.id} className="flex items-center gap-2.5 rounded-2xl p-1.5 transition-colors hover:bg-muted/60">
              <Link href={`/opportunities/${x.id}`} className="relative size-11 shrink-0 overflow-hidden rounded-xl bg-muted"><Image src={x.image} alt="" fill sizes="44px" className="object-cover" /></Link>
              <Link href={`/opportunities/${x.id}`} className="min-w-0 flex-1">
                <span className="block truncate text-[12.5px] font-extrabold text-ink" title={x.title}>{x.title}</span>
                <span className="block truncate text-[11px] font-semibold text-muted-foreground">{ox.minCapital != null ? `ورود از ${faNumber(ox.minCapital)} میلیارد` : x.city}{ox.paybackYears != null && ` · بازگشت ${faNumber(ox.paybackYears)} سال`}</span>
              </Link>
              <Button type="button" variant="plain" size="auto" aria-pressed={on} onClick={() => add(x.id)} aria-label={on ? `برداشتن ${x.title} از مقایسه` : `افزودن ${x.title} به مقایسه`} title={on ? "در مقایسه است" : "افزودن به مقایسه"}
                className={cn("grid size-8 shrink-0 place-items-center rounded-full transition-colors", on ? "bg-cobalt text-white" : "border border-border text-ink/50 hover:border-cobalt/40 hover:text-cobalt")}>
                {on ? <TickCircle size={16} variant="Bold" /> : <AddCircle size={16} />}
              </Button>
            </li>
          ); })}
      </ul>
      <Button type="button" variant="plain" size="auto" onClick={() => { setCompare([l.id, ...near.map((x) => x.id)]); router.push("/compare"); }}
        className="group mt-3 flex h-11 w-full items-center justify-center gap-2 rounded-full bg-cobalt-soft text-[13px] font-extrabold text-cobalt-deep transition-colors hover:bg-cobalt hover:text-white">
        مقایسه این پروژه با هر {near.length === 3 ? "سه" : near.length === 2 ? "دو" : "یک"}<ArrowLeft size={16} className="transition-transform group-hover:-translate-x-0.5" />
      </Button>
    </div>
  );
}

/** یک برچسب زمان: زیر یک سال به ماه، بالاتر به سال و ماه (مثل «۸ سال و ۶ ماه») */
function InfoCompleteness({ l }: { l: Listing }) {
  const known = sheetOf(l).known;
  const ok = known.filter((k) => k.ok), miss = known.filter((k) => !k.ok);
  return (
    <div className="surface grid grid-cols-1 lg:grid-cols-[17rem_minmax(0,1fr)] gap-8 rounded-[1.75rem] p-6">
      <div>
        <p className="flex items-center gap-2 text-[13px] font-extrabold text-ink/70"><DocumentText size={18} variant="Bulk" className="text-cobalt" />کامل بودن اطلاعات</p>
        <p className="mt-2 text-[1.6rem] font-black leading-10 text-ink">{faNumber(ok.length)} <span className="text-[15px] font-bold text-ink/60">از {faNumber(known.length)} داده کلیدی</span></p>
        <div className="mt-3 flex flex-wrap gap-1" aria-hidden>{known.map((k) => <span key={k.label} className={cn("h-2 flex-1 rounded-full", k.ok ? "bg-cobalt" : "bg-ink/10")} />)}</div>
        <p className="mt-3 text-[12px] font-semibold leading-6 text-muted-foreground">هرچه داده‌های اعلام‌شده کمتر باشد، پیش از تصمیم پرسش بیشتری باید بپرسید.</p>
      </div>
      <div className="space-y-4">
        <div>
          <p className="text-[12px] font-extrabold text-ink/70">اعلام شده</p>
          <ul className="mt-2 flex flex-wrap gap-1.5">{ok.map((k) => <li key={k.label} className="inline-flex items-center gap-1 rounded-full bg-cobalt-soft px-2.5 py-1 text-[12px] font-bold text-cobalt-deep"><TickCircle size={13} variant="Bold" />{k.label}</li>)}</ul>
        </div>
        {miss.length > 0 && <div>
          <p className="text-[12px] font-extrabold text-ink/70">اعلام نشده، پیش از تصمیم از کارشناس بپرسید</p>
          <ul className="mt-2 flex flex-wrap gap-1.5">{miss.map((k) => <li key={k.label} className="rounded-full border border-dashed border-ink/25 px-2.5 py-1 text-[12px] font-semibold text-ink/55">{k.label}</li>)}</ul>
        </div>}
      </div>
    </div>
  );
}

/** شناسه پروژه زیر عنوان: گروه، نوع، مدل همکاری و وضعیت در یک نوار، جای بج‌های روی عکس و جمله‌ی تکراری معرفی */
function IdentityStrip({ items, note }: { items: [string, string][]; note?: React.ReactNode }) {
  if (!items.length) return null;
  return (
    <div className="surface mt-5 overflow-hidden rounded-[1.5rem]">
      <dl className="grid [&>div+div]:border-r [&>div+div]:border-border" style={{ gridTemplateColumns: `repeat(${items.length}, minmax(0, 1fr))` }}>
        {items.map(([k, v]) => (
          <div key={k} className="min-w-0 px-5 py-4">
            <dt className="text-[11.5px] font-semibold text-muted-foreground">{k}</dt>
            <dd className="mt-1 text-[14.5px] font-extrabold leading-6 text-ink">{v}</dd>
          </div>
        ))}
      </dl>
      {note && <div className="flex items-start gap-2.5 border-t border-border bg-[#f8fafc] px-5 py-3 text-[13px] font-semibold leading-7 text-ink/75"><InfoCircle size={17} variant="Bulk" className="mt-1 shrink-0 text-ink/45" /><span>{note}</span></div>}
    </div>
  );
}

/** بازه‌های زمانی روی یک محور ماه: اجرا، قفل سرمایه و کل طرح، اولین دریافت به شکل نشانگر.
 *  وقتی دوره بازگشت اعلام نشده، جای نمودار بازگشت را می‌گیرد تا زمان‌بندی با یک نگاه خوانده شود. */
export function Detail({ id }: { id: string }) {
  const [photo, setPhoto] = useState(0);
  const l = listingById(id)!;
  const o = l.kind === "project" ? (l.raw as Opportunity) : null;
  const fund = l.kind === "fund" ? (l.raw as Fund) : null;
  const sale = l.kind === "sale" ? (l.raw as SaleItem) : null;
  const group = projectGroups.find((g) => g.id === l.group);
  const subtype = group?.subtypes.find((s) => s.id === l.subtype);
  const advisory = o ? advisories[o.subtype] : undefined;
  const similar = listings.filter((x) => x.id !== l.id && x.kind === l.kind && (l.kind !== "project" || x.group === l.group))
    .sort((a, b) => Math.abs((a.amount ?? 1e9) - (l.amount ?? 0)) - Math.abs((b.amount ?? 1e9) - (l.amount ?? 0))).slice(0, 3);
  const near = useNearby(l);
  const peers = useNearby(l, true);
  // اگر هم‌گروه کافی نبود، نزدیک‌ترین پروژه‌ها جای خالی را پر می‌کنند تا این بخش در همه پروژه‌ها سه کارت داشته باشد
  const sameCount = similar.length;
  const similarAll = o && similar.length < 3 ? [...similar, ...near.filter((x) => !similar.some((y) => y.id === x.id))].slice(0, 3) : similar;


  const tiles: { I: Icon; label: string; value: string; sub?: string }[] = o
    ? [
        { I: WalletMoney, label: l.amountLabel, value: l.amount != null ? faNumber(l.amount) : NA, sub: l.amount != null ? "میلیارد تومان" : undefined },
        { I: Timer1, label: "دوره بازگشت", value: o.paybackYears != null ? `${faNumber(o.paybackYears)} سال` : NA, sub: o.paybackDownsideYears != null ? `بدبینانه ${faNumber(o.paybackDownsideYears)} سال` : undefined },
        o.metric ? { I: Building, label: o.metric.label, value: faNumber(o.metric.value), sub: o.metric.unit } : { I: Lock1, label: "قفل سرمایه", value: o.lockupMonths != null ? `${faNumber(o.lockupMonths)} ماه` : NA },
        { I: Chart, label: "نوع درآمد", value: incomeLabel[o.income] ?? o.income },
      ]
    : l.stats.map((s, i) => ({ I: [WalletMoney, Chart, ShieldSearch, Calendar][i], label: s.label, value: s.value }));

  // گروه و نوع یک بار، همین‌جا، بج‌های روی عکس و جمله‌ی معرفی که همین‌ها را تکرار می‌کردند حذف شده‌اند
  const identity = ([
    o ? ["گروه", group?.name] : ["دسته", l.tags[0]],
    o ? ["نوع پروژه", subtype?.name] : ["نوع", l.tags[1]],
    [o ? "مدل همکاری" : "شیوه", (o ?? fund ?? sale)?.model],
    ["وضعیت", (o ?? fund ?? sale)?.stage],
  ] as [string, string | undefined][]).filter((x): x is [string, string] => !!x[1]);
  const groups = factGroups(l);
  const pics = galleryOf(l);
  const text = (o ?? fund ?? sale)!;
  const hasFlow = !!(text.finance || text.repay || text.ownership);
  const sections = dossier(l);
  const nextSteps = o?.steps.length ? o.steps : fund?.steps?.length ? fund.steps : routeSteps[l.routes[0] as RouteId];
  const sameGroup = listings.filter((x) => x.kind === l.kind && (l.kind !== "project" || x.group === l.group) && x.routes.includes(l.routes[0])).length;

  return (
    <>
      <Header />
      <main className="focus-blur mx-auto max-w-7xl px-6 pt-6">
        <Link href="/opportunities" className="mb-4 inline-flex items-center gap-2 text-sm font-bold text-ink/70 hover:text-ink"><ArrowRight size={18} />بازگشت به پروژه‌ها</Link>

        {/* پرده اول: تصویر و عنوان */}
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.6, ease }}>
          <SignaturePhoto src={l.image} srcs={pics.map((p) => p.src)} active={photo} alt={l.title} priority sizes="100vw" className="h-[27rem] rounded-[2.25rem]">
            <HeroGallery l={l} index={photo} onIndex={setPhoto} />
            <div className="absolute right-5 top-5 z-10"><SaveButton id={l.id} className="size-12" /></div>
          </SignaturePhoto>
        </motion.div>

        {/* عنوان و شناسه زیر عکس، نه روی آن */}
        <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.08, ease }} className="mt-7">
          <h1 className="max-w-5xl text-[2.25rem] font-black leading-[1.35] text-ink text-balance">{l.title}</h1>
          <p className="mt-2.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[14px] font-semibold text-muted-foreground">
            {l.city && <span className="flex items-center gap-1.5 text-ink/75"><Location size={17} variant="Bulk" className="text-ink/45" />{l.province}، {l.city}{sale?.neighborhood ? `، ${sale.neighborhood}` : ""}</span>}
          </p>
          <IdentityStrip items={identity} note={subtype?.examples ? <><b className="font-extrabold text-ink">{subtype.name} یعنی: </b>{subtype.examples}</> : undefined} />
        </motion.div>

        <div className="mt-8 grid grid-cols-[1fr_22rem] gap-8">
          <div className="min-w-0 space-y-14">
            <div className="grid grid-cols-2 xl:grid-cols-4 gap-3">{tiles.map((t) => <Tile key={t.label} {...t} />)}</div>

            <Chapter title="شناسنامه پروژه"><Facts groups={groups}/><ExactFacts id={l.id}/></Chapter>

            {/* ساختار یکسان همه صفحه‌ها، به همین ترتیب: شناسنامه، پول، مقایسه بازگشت، ریسک، پرسش‌ها، پرونده، اطلاعات تکمیلی، گام‌ها، موارد مشابه.
                بخشی که برای یک نوع (پروژه، صندوق، ملک) داده ندارد حذف می‌شود و بقیه جایشان را حفظ می‌کنند. */}
            {o && <Chapter title={o.routes.length === 1 && o.routes[0] === "operator" ? "دوره کار بهره‌برداری" : "سرمایه شما در طول زمان"}><DeclaredTimes id={l.id}/></Chapter>}
            {hasFlow && !o && <Chapter title="مسیر پول"><div className="surface rounded-[1.75rem] px-6 py-2"><MoneyFlow o={text} /></div></Chapter>}
            {fund && (
              <Chapter title="دریافت سود و خروج">
                <div className="grid grid-cols-2 gap-4">
                  <div className="surface rounded-[1.75rem] p-6"><h3 className="text-sm font-extrabold text-primary-ink">پرداخت سود</h3><p className="mt-2 text-xl font-black text-ink">{payoutLabel[fund.payout] ?? fund.payout}</p><p className="mt-1 text-sm text-muted-foreground">مدت: {fund.durationMonths != null ? `${faNumber(fund.durationMonths)} ماه` : NA}</p></div>
                  <div className="rounded-[1.75rem] bg-white p-6 ring-1 ring-border"><span className="grid size-11 place-items-center rounded-2xl bg-warn/10 text-warn"><Warning2 size={22} variant="Bulk" /></span><h3 className="mt-3 text-sm font-extrabold text-ink">شرایط خروج</h3><p className="mt-2 text-[15px] font-semibold leading-8 text-ink/85">{fund.exit || NA}</p></div>
                </div>
              </Chapter>
            )}
            {o && peers.length > 0 && (
              <Chapter title="بازگشت سرمایه در برابر پروژه‌های مشابه"><div className="surface rounded-[1.75rem] p-6"><p className="leading-7">واحد و مبنای زمان‌ها باید سازگار باشند؛ از زمان یک پروژه، بازده یا جریان نقدی پروژه دیگر برآورد نمی‌شود.</p><Button asChild className="mt-5"><Link href="/compare">مقایسه شاخص‌های ثبت‌شده</Link></Button></div></Chapter>
            )}

            {o && (
              <Chapter title="ریسک و نکته‌های مهم">
                <div className="grid grid-cols-[minmax(0,5fr)_minmax(0,7fr)] gap-4">
                  <div className="surface flex flex-col items-center rounded-[1.75rem] p-6 text-center">
                    <h3 className="self-stretch text-right text-sm font-extrabold text-ink">سطح ریسک</h3>
                    <div className="mt-5 w-full"><RiskGauge risk={o.risk} /></div>
                  </div>
                  <div className="flex flex-col gap-4">
                    <div className="surface flex items-center gap-4 rounded-[1.75rem] p-5">
                      <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-ink/[0.06] text-primary-ink"><ShieldSearch size={22} variant="Bulk" /></span>
                      <span className="min-w-0 flex-1"><span className="block text-xs font-bold text-muted-foreground">وضعیت حقوقی</span><span className="mt-0.5 block text-base font-extrabold text-ink">{legalLabel[o.legalStatus] ?? o.legalStatus}</span></span>
                    </div>
                    {o.caution && <div className="flex flex-1 items-start gap-4 rounded-[1.75rem] bg-white p-5 ring-1 ring-border">
                      <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-warn/10 text-warn"><Warning2 size={22} variant="Bulk" /></span>
                      <span className="min-w-0 flex-1"><span className="block text-sm font-extrabold text-ink">پیش از تصمیم بدانید</span><span className="mt-1.5 block text-[15px] font-semibold leading-8 text-ink/85">{o.caution}</span></span>
                    </div>}
                  </div>
                </div>
                {!!o.checks?.length && <>
                  <h3 className="mb-2 mt-6 text-sm font-extrabold text-ink">این موارد را بررسی کنید</h3>
                  <ul className="grid grid-cols-2 gap-2">{o.checks.map((c) => <li key={c} className="surface flex items-start gap-2.5 rounded-2xl px-4 py-3 text-sm font-semibold leading-7 text-ink/85"><InfoCircle size={18} variant="Bulk" className="mt-1 shrink-0 text-primary-ink" />{c}</li>)}</ul>
                </>}
              </Chapter>
            )}

            {/* صندوق و ملک: همان جای بخش ریسک پروژه‌ها */}
            {!o && (fund || text.caution) && (
              <Chapter title="ریسک و نکته‌های مهم">
                <div className={cn("grid gap-4", fund && text.caution ? "grid-cols-[minmax(0,5fr)_minmax(0,7fr)]" : "grid-cols-1")}>
                  {fund && <div className="surface rounded-[1.75rem] p-6"><h3 className="text-sm font-extrabold text-ink">سطح ریسک</h3><div className="mt-5"><RiskMeter risk={fund.risk} /></div></div>}
                  {text.caution && (
                    <div className="flex items-start gap-4 rounded-[1.75rem] bg-white p-6 ring-1 ring-border">
                      <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-warn/10 text-warn"><Warning2 size={22} variant="Bulk" /></span>
                      <span><span className="block text-sm font-extrabold text-ink">پیش از تصمیم بدانید</span><span className="mt-1 block text-[15px] font-semibold leading-8 text-ink/85">{text.caution}</span></span>
                    </div>
                  )}
                </div>
              </Chapter>
            )}
            {fund && (
              <Chapter title="تضمین بانکی">
                <div className="grid grid-cols-3 gap-3">
                  {([["تضمین بانکی", fund.bank.exists], ["تضمین اصل سرمایه", fund.bank.principal], ["تضمین سود", fund.bank.profit]] as const).map(([t, v]) => (
                    <div key={t} className="surface flex items-center justify-between rounded-[1.5rem] p-5"><span className="text-sm font-bold text-ink">{t}</span>
                      <span className={cn("inline-flex items-center gap-1 rounded-full px-3 py-1 text-xs font-extrabold", v ? "bg-primary text-white" : v === false ? "bg-muted text-ink/70" : "bg-muted text-ink/70")}>{v ? <><TickCircle size={14} variant="Bold" />دارد</> : v === false ? "ندارد" : "نامعلوم"}</span></div>
                  ))}
                </div>
                {!fund.bank.verified && <p className="mt-3 flex items-center gap-2 text-sm font-semibold text-muted-foreground"><InfoCircle size={16} variant="Bulk" />مستندات تضمین احراز نشده است.</p>}
              </Chapter>
            )}

            {o && advisory && <Chapter title="پرسش‌هایی که باید پاسخشان را آماده کنید"><AdvisoryBlock a={advisory} /></Chapter>}

            <Chapter title="پرونده کامل"><Dossier sections={sections} /></Chapter>

            <Chapter title="اطلاعات تکمیلی"><InfoCompleteness l={l} /></Chapter>

            {nextSteps && nextSteps.length > 0 && (
              <Chapter title="گام‌های ورود و مدارک لازم">
                <Steps steps={nextSteps} />
                <div className="mt-5 flex items-center justify-between gap-4 rounded-[1.75rem] bg-ink/[0.05] p-5 pr-7">
                  <p className="text-[15px] font-extrabold text-ink">{o?.expert ? `برای شروع، با ${o.expert.name} تماس بگیرید.` : "این گام‌ها را در راهنمای اقدام تیک بزنید و همراه خود داشته باشید."}</p>
                  {o?.expert
                    ? <Button asChild className="h-12 gap-2 rounded-full px-6 font-extrabold"><Link href="/requests"><Call size={18} variant="Bold"/>پیگیری پرونده</Link></Button>
                    : <Button asChild className="h-12 gap-2 rounded-full px-6 font-extrabold"><Link href={`/guide/${l.id}`}><DocumentDownload size={18} variant="Bold" />دیدن راهنمای اقدام</Link></Button>}
                  <Button asChild variant="outline" className="h-12 gap-2 rounded-full px-6 font-extrabold"><Link href="/assistant" onClick={() => { sessionStorage.setItem("invest:assistant-opportunity", l.id); sessionStorage.setItem("invest:assistant-draft", `این فرصت را با شرایط من توضیح بده: ${l.title}`); }}><MagicStar size={18} variant="Bold" />پرسیدن از دستیار</Link></Button>
                </div>
              </Chapter>
            )}

            {/* پروژه‌های مشابه، پایین صفحه */}
            {similarAll.length > 0 && (
              <Chapter title="در کنار موارد مشابه">
                <div className="-mt-2 mb-4 flex items-center justify-between gap-4">
                  <p className="text-[13.5px] font-semibold text-muted-foreground">{sameCount >= similarAll.length ? `${faNumber(similarAll.length)} پروژه نزدیک به این پروژه${group ? ` در گروه «${group.name}»` : ""}، با مبلغ ورود نزدیک.` : sameCount > 0 ? `${faNumber(sameCount)} پروژه هم‌گروه و ${faNumber(similarAll.length - sameCount)} پروژه نزدیک از گروه‌های دیگر.` : "پروژه هم‌گروهی نبود، نزدیک‌ترین پروژه‌ها از گروه‌های دیگر آمده‌اند."}</p>
                  <Link href="/opportunities" onClick={() => { useStore.getState().begin({ route: l.routes[0] as never, ...(l.group ? { groups: [l.group] } : {}) }); useStore.getState().setStarted(true); }}
                    className="group inline-flex h-10 shrink-0 items-center gap-1.5 rounded-full border border-border bg-white px-4 text-[13px] font-extrabold text-ink hover:border-ink/30">مشاهده همه {faNumber(sameGroup)} پروژه<ArrowLeft size={15} className="transition-transform group-hover:-translate-x-0.5" /></Link>
                </div>
                <div className="grid grid-cols-3 gap-4">{similarAll.map((x, i) => <ListingCard key={x.id} listing={x} index={i} comparable />)}</div>
              </Chapter>
            )}
          </div>

          <aside className="sticky top-24 space-y-4 self-start">
            <Contact l={l} />
            {o && <CompareCard l={l} near={near} />}
            {l.city && (
              <div className="surface overflow-hidden rounded-[1.75rem]">
                <div className="flex items-center gap-3 p-4">
                  <span className="grid size-11 shrink-0 place-items-center rounded-2xl bg-ink/[0.06] text-primary-ink"><Location size={22} variant="Bulk" /></span>
                  <p className="min-w-0 flex-1 text-base font-extrabold leading-6 text-ink">{l.city}<span className="block text-xs font-semibold text-muted-foreground">استان {l.province}{sale?.neighborhood ? `، ${sale.neighborhood}` : ""}</span></p>
                </div>
                <LocationMap city={l.city} province={l.province!} className="h-40 border-t border-border" />
                <Link href="/opportunities" onClick={() => { useStore.getState().begin({ route: l.routes[0] as never, provinces: [l.province!] }); useStore.getState().setStarted(true); }}
                  className="flex items-center justify-between border-t border-border px-5 py-3 text-[13px] font-bold text-primary-ink hover:bg-ink/[0.03]">پروژه‌های دیگر در {l.province}<ArrowLeft size={16} /></Link>
              </div>
            )}
          </aside>
        </div>

        <CompareTray />
      </main>
      <Footer />
    </>
  );
}
