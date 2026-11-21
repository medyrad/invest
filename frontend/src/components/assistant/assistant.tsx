"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { ArchiveTick, ArrowLeft, Chart, CloseCircle, Edit2, MagicStar, Save2, Send2, TickCircle } from "@/components/iconsax";
import { AlgoPattern } from "@/components/brand/algo-pattern";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { assistantTurnStream, type AssistantItem, type AssistantResponse, type AssistantStep } from "@/lib/assistant-api";
import { assistantValueLabel } from "@/lib/assistant-labels";
import { fromCriteria, useStore } from "@/lib/store";

type Turn = { id: string; question: string; response: AssistantResponse };
const examples = [
  "مسکونی در تهران تا ۳۰ میلیارد",
  "صندوق کم‌ریسک با پرداخت ماهانه",
  "نیروگاه خورشیدی در یزد",
  "خرید ملک در شیراز",
  "اجاره دفتر در اصفهان",
  "مرمت خانه تاریخی در کاشان",
];
const routeChoices = [
  ["investor", "سرمایه‌گذاری"], ["fund", "صندوق"], ["buyer", "خرید"],
  ["lessee", "اجاره"], ["contractor", "پیمانکاری"], ["heritage", "مرمت"],
] as const;

function Orb({ busy = false }: { busy?: boolean }) {
  const reduce = useReducedMotion();
  return <motion.span aria-hidden className="relative grid size-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-teal-500 via-cobalt to-violet-600 text-white shadow-[0_18px_55px_-18px_rgb(30_64_175/0.75)]" animate={busy && !reduce ? { rotate: 360 } : undefined} transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}><MagicStar size={23} variant="Bold" /></motion.span>;
}

function Chips({ criteria, onRemove }: { criteria: Record<string, unknown>; onRemove: (key: string) => void }) {
  const labels: Record<string, string> = { route: "مسیر", kind: "نوع", budget_max: "سقف بودجه", province: "استان", city: "شهر", group: "گروه", risk: "ریسک", return: "بازده" };
  const values = Object.entries(criteria).filter(([key]) => key in labels);
  return <div className="flex flex-wrap gap-2">{values.map(([key, value]) => <span key={key} className="inline-flex items-center gap-1.5 rounded-full border border-ink/10 bg-white px-3 py-1.5 text-xs font-bold text-ink/75"><span className="text-muted-foreground">{labels[key]}:</span>{assistantValueLabel(key, value)}<button type="button" onClick={() => onRemove(key)} aria-label={`حذف ${labels[key]}`} className="grid size-6 place-items-center rounded-full hover:bg-muted"><CloseCircle size={15} /></button></span>)}</div>;
}

function ResultCard({ item, index }: { item: AssistantItem; index: number }) {
  const title = String(item.fields.title || "فرصت بدون عنوان");
  const score = item.matching?.score;
  const image = String(item.fields.image_url || item.fields.image || "/images/hero/construction.jpg");
  const location = String(item.fields.city || item.fields.province || "موقعیت نامعلوم");
  const amount = String(item.fields.minimum_investment || item.fields.budget || item.fields.price || "مبلغ نامعلوم");
  const checks = (item.matching?.checks || []).filter((check) => check.state === "met").slice(0, 3);
  return <article className="group overflow-hidden rounded-[1.8rem] border-[8px] border-white bg-white shadow-[0_18px_45px_-34px_rgb(22_32_48/0.55)]">
    <Link href={`/opportunities/${item.id}`} className="relative block h-48 overflow-hidden rounded-[1.35rem] bg-muted sm:h-52">
      <Image src={image} alt="" fill unoptimized sizes="(min-width: 768px) 320px, 100vw" className="object-cover transition-transform duration-500 motion-reduce:transition-none group-hover:scale-[1.02]" />
      <span className="absolute right-3 top-3 rounded-full bg-white px-3 py-1 text-xs font-black">پیشنهاد {index + 1}</span>
      <span className="absolute bottom-3 left-3 grid size-16 place-items-center rounded-full border-4 border-white bg-teal-900/70 text-lg font-black text-white backdrop-blur">{score == null ? "—" : `${Number(score).toFixed(0)}٪`}</span>
      <span className="absolute bottom-4 right-4 text-xs font-bold text-white drop-shadow">● {location}</span>
    </Link>
    <div className="flex min-h-44 flex-col px-4 pb-4 pt-3"><h3 className="text-base font-black leading-8">{title}</h3><p className="mt-2 text-xs font-bold text-ink/75">{amount}</p><div className="mt-auto flex flex-wrap gap-1.5 pt-3">{checks.length ? checks.map((check) => <span key={check.axis} className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-bold text-teal-800">✓ {check.axis}</span>) : <span className="rounded-full bg-muted px-2.5 py-1 text-[10px] font-bold text-muted-foreground">جزئیات در نسخه عمومی</span>}</div></div>
  </article>;
}

function CompactResult({ item, index }: { item: AssistantItem; index: number }) {
  const image = String(item.fields.image_url || item.fields.image || "/images/hero/construction.jpg");
  const score = item.matching?.score;
  return <article className="flex min-h-24 items-center gap-3 rounded-[1.7rem] bg-white p-2.5 shadow-[0_14px_35px_-30px_rgb(22_32_48/0.6)] sm:gap-5 sm:p-3">
    <span className="w-6 shrink-0 text-center text-sm font-black text-muted-foreground">{index + 1}</span>
    <Image src={image} alt="" width={112} height={80} unoptimized className="size-20 shrink-0 rounded-2xl object-cover sm:h-20 sm:w-28" />
    <Link href={`/opportunities/${item.id}`} className="min-w-0 flex-1"><h3 className="truncate text-sm font-black sm:text-base">{String(item.fields.title || "فرصت بدون عنوان")}</h3><p className="mt-2 truncate text-[11px] font-bold text-muted-foreground">{String(item.fields.city || item.fields.province || "موقعیت نامعلوم")} · {String(item.fields.minimum_investment || item.fields.price || "مبلغ نامعلوم")}</p></Link>
    <button type="button" aria-label={`ذخیره ${String(item.fields.title || "فرصت")}`} className="grid size-10 shrink-0 place-items-center rounded-full bg-muted text-xl">☆</button>
    <span className="grid size-14 shrink-0 place-items-center rounded-full border-[5px] border-teal-500/25 text-sm font-black">{score == null ? "—" : `${Number(score).toFixed(0)}٪`}</span>
  </article>;
}

function SavedPicker({ onPick }: { onPick: (criteria: Record<string, unknown>) => void }) {
  const { profiles, user, addProfile, updateProfile, removeProfile, openLogin } = useStore();
  const [open, setOpen] = useState(false); const [selected, setSelected] = useState<string | null>(null); const [naming, setNaming] = useState(false); const [name, setName] = useState("شرایط دستیار");
  const picked = profiles.find((profile) => profile.id === selected);
  const current = () => { try { const value = JSON.parse(sessionStorage.getItem("invest:assistant-criteria") || "{}"); return value && typeof value === "object" ? value : {}; } catch { return {}; } };
  const criteria = current();
  const persist = async () => { const criteria = current(); if (!user) { openLogin({ type: "save-criteria", name }); return; } await addProfile(name.trim() || "شرایط دستیار", fromCriteria(criteria)); setNaming(false); };
  return <div className="relative"><Button type="button" variant="plain" size="auto" onClick={() => setOpen(!open)} aria-expanded={open} className="h-11 rounded-full border border-border bg-white px-4 text-xs font-extrabold"><ArchiveTick size={17} />{picked?.name || "شرایط من"}</Button>{open && <div className="absolute bottom-14 right-0 z-30 w-[min(24rem,calc(100vw-2rem))] rounded-3xl border border-border bg-white p-2 shadow-2xl"><div className="flex items-center justify-between px-3 py-2"><p className="text-xs font-bold text-muted-foreground">نام پروفایل برای مدل ارسال نمی‌شود.</p><button type="button" onClick={() => setNaming(true)} className="text-xs font-extrabold text-cobalt">ذخیره فعلی</button></div>{profiles.length ? profiles.map((profile) => <div key={profile.id} className="flex items-center rounded-2xl hover:bg-muted"><button type="button" className="min-w-0 flex-1 px-3 py-3 text-right text-sm font-extrabold" onClick={() => { setSelected(profile.id); onPick(profile.serverCriteria || {}); setOpen(false); }}>{profile.name}</button><button type="button" aria-label={`جایگزینی ${profile.name}`} className="px-2 text-[11px] font-bold text-cobalt" onClick={() => void updateProfile(profile.id, { criteria: fromCriteria(criteria) })}>جایگزینی</button><button type="button" aria-label={`حذف ${profile.name}`} className="px-2 text-[11px] font-bold text-destructive" onClick={() => void removeProfile(profile.id)}>حذف</button></div>) : <p className="px-3 py-4 text-sm text-muted-foreground">شرایط ذخیره‌شده‌ای ندارید.</p>}</div>}{naming && <div role="dialog" aria-modal="true" aria-label="نام‌گذاری شرایط" className="fixed inset-0 z-50 grid place-items-center bg-ink/30 p-4"><form onSubmit={(event) => { event.preventDefault(); void persist(); }} className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl"><h2 className="font-black">نام این شرایط</h2><input autoFocus value={name} onChange={(event) => setName(event.target.value.slice(0, 80))} className="mt-4 h-11 w-full rounded-xl border border-border px-3 text-sm"/><div className="mt-4 flex gap-2"><Button type="submit" className="rounded-full">ذخیره با رسید سرور</Button><Button type="button" variant="plain" onClick={() => setNaming(false)} className="rounded-full">انصراف</Button></div></form></div>}</div>;
}

function CompletedSteps({ steps }: { steps?: AssistantResponse["steps"] }) {
  const labels = { interpretation: "برداشت نیاز", public_data: "بازخوانی داده عمومی", explanation: "توضیح مستند" };
  if (!steps) return null;
  return <ol className="mx-auto grid max-w-4xl gap-2 sm:grid-cols-3">{steps.map((step) => <li key={step.id} className="flex items-center gap-2 rounded-2xl border border-border bg-white px-4 py-3 text-xs font-bold"><span className={step.status === "completed" ? "text-primary" : step.status === "failed" ? "text-amber-700" : "text-muted-foreground"}>{step.status === "completed" ? "✓" : step.status === "failed" ? "!" : "—"}</span>{labels[step.id]}</li>)}</ol>;
}

const initialSteps: AssistantStep[] = [
  { id: "interpretation", status: "pending", detail: "در انتظار خواندن درخواست" },
  { id: "public_data", status: "pending", detail: "در انتظار داده عمومی" },
  { id: "explanation", status: "pending", detail: "در انتظار تولید و اعتبارسنجی" },
];
const processingLabels = { interpretation: "خواندن شرایط شما", public_data: "تطبیق با پروژه‌ها", explanation: "مرتب‌سازی بر اساس درصد تطابق" };
function Processing({ question, steps }: { question: string; steps: AssistantStep[] }) {
  const reduce = useReducedMotion();
  return <motion.article initial={reduce ? false : { opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="space-y-5" aria-live="polite" aria-busy="true"><div className="flex justify-end"><p className="max-w-2xl rounded-[1.4rem] rounded-tr-md bg-teal-800 px-6 py-3 text-sm font-bold leading-7 text-white">{question}</p></div><div className="relative mr-auto w-full max-w-sm rounded-[1.8rem] bg-white p-6 shadow-[0_22px_55px_-38px_rgb(22_32_48/0.7)] sm:ml-16"><span className="absolute -left-14 top-3 hidden rounded-full border-4 border-white bg-ink p-2 text-white shadow-lg sm:block"><MagicStar size={20} variant="Bold" /></span><h2 className="mb-3 text-sm font-black text-teal-800">در حال بررسی...</h2><ol className="relative space-y-1 before:absolute before:right-[1.05rem] before:top-7 before:h-[calc(100%-3.5rem)] before:w-px before:bg-teal-200">{steps.map((step) => <li key={step.id} className="relative flex gap-3 py-2"><motion.span animate={!reduce && step.status === "active" ? { scale: [1, 1.12, 1] } : undefined} transition={{ repeat: Infinity, duration: 1.1 }} className={`z-10 grid size-9 shrink-0 place-items-center rounded-full text-xs font-black ${step.status === "completed" ? "bg-teal-500 text-white" : step.status === "active" ? "bg-teal-50 text-teal-700 ring-2 ring-teal-400" : step.status === "failed" ? "bg-amber-100 text-amber-800" : "bg-muted text-muted-foreground/50"}`}>{step.status === "completed" ? "✓" : step.status === "failed" ? "!" : "◌"}</motion.span><div><h3 className={`text-sm font-extrabold ${step.status === "pending" ? "text-muted-foreground/45" : ""}`}>{processingLabels[step.id]}</h3>{step.status !== "pending" && <p className="mt-1 text-[11px] leading-5 text-muted-foreground">{step.detail}</p>}</div></li>)}</ol></div><div className="mx-auto grid max-w-5xl gap-4 md:grid-cols-3">{[0,1,2].map((value) => <div key={value} className="rounded-[1.8rem] border-[8px] border-white bg-white p-0 shadow-sm"><div className="h-44 animate-pulse rounded-[1.35rem] bg-[#edf1f6] motion-reduce:animate-none"/><div className="space-y-3 p-4"><div className="h-3 w-3/4 rounded-full bg-[#edf1f6]"/><div className="mr-auto h-3 w-1/2 rounded-full bg-[#edf1f6]"/></div></div>)}</div></motion.article>;
}

export function Assistant() {
  const router = useRouter();
  const { user, addProfile, openLogin, setCompare } = useStore();
  const [text, setText] = useState("");
  const [criteria, setCriteria] = useState<Record<string, unknown>>({});
  const [turns, setTurns] = useState<Turn[]>([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [contextIds, setContextIds] = useState<string[]>([]);
  const [processing, setProcessing] = useState<{ question: string; steps: AssistantStep[] } | null>(null);
  const retryKey = useRef<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const draft = sessionStorage.getItem("invest:assistant-draft");
    if (draft) { setText(draft.slice(0, 4000)); sessionStorage.removeItem("invest:assistant-draft"); }
    const saved = sessionStorage.getItem("invest:assistant-session");
    if (saved) try { const parsed = JSON.parse(saved); if (Array.isArray(parsed)) setTurns(parsed.slice(-12)); } catch { sessionStorage.removeItem("invest:assistant-session"); }
    const opportunity = sessionStorage.getItem("invest:assistant-opportunity");
    if (opportunity) { setContextIds([opportunity]); sessionStorage.removeItem("invest:assistant-opportunity"); }
  }, []);
  useEffect(() => { sessionStorage.setItem("invest:assistant-session", JSON.stringify(turns.slice(-12))); if (turns.length) end.current?.scrollIntoView({ behavior: "smooth" }); }, [turns]);
  useEffect(() => { sessionStorage.setItem("invest:assistant-criteria", JSON.stringify(criteria)); }, [criteria]);
  const latest = turns.at(-1)?.response;
  const items = useMemo(() => latest?.server_result?.items || [], [latest]);
  const submit = async (value = text) => {
    const message = value.trim();
    if (!message || busy) return;
    setBusy(true); setError(""); setProcessing({ question: message, steps: initialSteps });
    try {
      const history = turns.flatMap((turn) => [
        { role: "user", text: turn.question },
        ...(turn.response.answer ? [{ role: "assistant", text: turn.response.answer }] : []),
      ]).slice(-12);
      const key = retryKey.current || crypto.randomUUID();
      retryKey.current = key;
      const { value: response } = await assistantTurnStream({
        message,
        ...(Object.keys(criteria).length ? { criteria } : {}),
        ...(contextIds.length ? { opportunity_ids: contextIds } : {}),
        history,
      }, (event) => {
        if (event.event !== "progress") return;
        setProcessing((current) => current ? { ...current, steps: current.steps.map((step) => step.id === event.stage ? { ...step, status: event.status, detail: event.detail || step.detail } : step) } : current);
      }, key);
      if (response.interpretation) setCriteria(response.interpretation.criteria);
      setTurns((current) => [...current, { id: crypto.randomUUID(), question: message, response }]);
      if (response.state === "failed") { setError(response.error?.message || "پاسخ کامل نشد."); setText(message); }
      else { setText(""); setEditing(false); retryKey.current = null; }
    } catch (cause) { setError(cause instanceof Error ? cause.message : "پاسخ دریافت نشد."); setText(message); }
    finally { setBusy(false); setProcessing(null); }
  };
  const manual = () => { const converted = fromCriteria(criteria); useStore.getState().begin(converted); router.push("/opportunities"); };
  const save = async () => {
    const converted = fromCriteria(criteria);
    useStore.getState().begin(converted);
    if (!user) return openLogin({ type: "save-criteria", name: "شرایط دستیار" });
    try { await addProfile("شرایط دستیار", converted); } catch { /* store keeps the input and reports the server failure */ }
  };
  const compare = () => { if (items.length >= 2) { setCompare(items.slice(0, 4).map((item) => item.id)); router.push("/compare"); } };
  if (items.length >= 0) return <main className="focus-blur relative min-h-[calc(100dvh-5rem)] overflow-x-hidden bg-[#eef3f9]">
    <AlgoPattern className="pointer-events-none fixed inset-0 h-full w-full text-ink/[0.045]" fade="radial" />
    <div className="relative mx-auto min-h-[calc(100dvh-5rem)] max-w-6xl px-4 pb-56 pt-8 sm:px-6">
      {!turns.length && !processing && <header className="mx-auto max-w-3xl pt-8 text-center"><Orb /><h1 className="mt-5 text-3xl font-black sm:text-4xl">شرایطتان را بگویید.</h1><p className="mt-3 text-sm font-semibold text-muted-foreground">پروژه‌های مناسب را با درصد تطابق نشانتان می‌دهیم.</p><div className="mt-8 flex flex-wrap justify-center gap-2">{examples.map((example) => <Button key={example} type="button" variant="plain" onClick={() => { setText(example); void submit(example); }} className="h-auto rounded-full border border-border bg-white px-4 py-2 text-xs font-bold">{example}</Button>)}</div></header>}
      <section aria-live="polite" className="space-y-7"><AnimatePresence>{processing && <Processing question={processing.question} steps={processing.steps}/>}</AnimatePresence>{turns.map((turn) => <motion.article initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} key={turn.id} className="space-y-5">
        <div className="flex justify-end"><p className="max-w-2xl rounded-[1.4rem] rounded-tr-md bg-teal-800 px-6 py-3 text-sm font-bold leading-7 text-white">{turn.question}</p></div>
        <CompletedSteps steps={turn.response.steps} />
        {turn.response.interpretation && <div className="mx-auto max-w-4xl rounded-[1.7rem] bg-white p-5 shadow-sm"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="flex items-center gap-2 text-sm font-black"><TickCircle size={18} className="text-primary" />برداشت من از درخواست شما</h2><Button type="button" variant="plain" size="auto" onClick={() => { setText(turn.question); setEditing(true); }} className="rounded-full px-3 text-xs font-bold"><Edit2 size={15}/>تغییر درخواست</Button></div><div className="mt-4"><Chips criteria={turn.id === turns.at(-1)?.id ? criteria : turn.response.interpretation.criteria} onRemove={(key) => setCriteria((current) => { const next={...current}; delete next[key]; return next; })}/></div></div>}
        <div className="mx-auto flex max-w-4xl flex-row-reverse items-start gap-3"><Orb/><div className="min-w-0 flex-1 rounded-[1.4rem] rounded-tl-md bg-white px-5 py-4 text-sm font-semibold leading-8 shadow-sm">{turn.response.answer || turn.response.error?.message || "نتایج سرور آماده است."}{turn.response.state === "failed" && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">موفقیت ثبت نشده است. متن و شرط‌ها در همین مرورگر محفوظ مانده‌اند.</p>}</div></div>
        {!!turn.response.server_result?.items?.length && <><motion.div initial="hidden" animate="show" variants={{show:{transition:{staggerChildren:.07}}}} className="mx-auto grid max-w-5xl gap-5 md:grid-cols-3">{turn.response.server_result.items.slice(0,3).map((item,index)=><motion.div variants={{hidden:{opacity:0,y:10},show:{opacity:1,y:0}}} key={item.id}><ResultCard item={item} index={index}/></motion.div>)}</motion.div><div className="mx-auto max-w-5xl space-y-3">{turn.response.server_result.items.slice(3).map((item,index)=><CompactResult key={item.id} item={item} index={index+3}/>)}</div></>}
        <div className="mx-auto flex max-w-4xl flex-wrap justify-center gap-2"><Button type="button" onClick={manual} disabled={!criteria.route} className="rounded-full px-5 font-extrabold">دقیق‌تر کردن با فیلترها</Button><Button type="button" variant="outline" onClick={save} disabled={!criteria.route} className="rounded-full px-5 font-extrabold"><Save2 size={17}/>ذخیره شرایط</Button><Button type="button" variant="outline" onClick={compare} disabled={items.length<2} className="rounded-full px-5 font-extrabold"><Chart size={17}/>مقایسه ۳ پیشنهاد اول</Button></div>
      </motion.article>)}<div ref={end}/></section>
      {error && <div role="alert" className="mx-auto mt-5 flex max-w-3xl flex-wrap items-center justify-center gap-3 text-sm font-bold text-destructive"><span>{error}</span><Button type="button" variant="outline" onClick={() => void submit()} disabled={busy} className="rounded-full px-4">تلاش دوباره با همان رسید</Button></div>}
    </div>
    <div className="pointer-events-none fixed inset-x-0 bottom-0 z-20 bg-gradient-to-t from-[#eef3f9] via-[#eef3f9]/95 to-transparent px-4 pb-4 pt-16"><div className="pointer-events-auto mx-auto mb-2 flex max-w-4xl gap-1.5 overflow-x-auto" aria-label="انتخاب مسیر">{routeChoices.map(([id,label])=><button key={id} type="button" onClick={()=>setCriteria((current)=>({...current,route:id,kind:id==='fund'?'fund':id==='buyer'?'sale':'project'}))} aria-pressed={criteria.route===id} className="shrink-0 rounded-full border border-border bg-white px-3 py-1.5 text-[11px] font-bold aria-pressed:border-primary aria-pressed:bg-teal-50">{label}</button>)}</div><div className="pointer-events-auto mx-auto mb-3 flex max-w-4xl flex-wrap justify-center gap-2" aria-label="پیشنهادهای سریع">{examples.slice(1).map((example)=><button key={example} type="button" onClick={()=>{setText(example);void submit(example)}} className="rounded-full border border-border bg-white px-4 py-2 text-[11px] font-bold shadow-sm">{example}</button>)}</div><form onSubmit={(event)=>{event.preventDefault();void submit()}} aria-busy={busy} className="pointer-events-auto mx-auto flex max-w-4xl items-end gap-2 rounded-[2rem] border border-border bg-white p-2 pr-4 shadow-[0_24px_65px_-30px_rgb(22_32_48/0.45)]"><SavedPicker onPick={(value)=>{setCriteria(value);setEditing(true)}}/><Textarea value={text} onChange={(event)=>setText(event.target.value)} aria-label="شرایط شما برای دستیار" placeholder={editing?"متن یا شرط‌ها را اصلاح کنید":"شرط تازه‌ای دارید؟ بنویسید..."} rows={1} onKeyDown={(event)=>{if(event.key==="Enter"&&!event.shiftKey){event.preventDefault();void submit()}}} className="field-sizing-content max-h-28 min-h-11 flex-1 resize-none border-0 !bg-transparent px-1 py-2 text-sm shadow-none focus-visible:ring-0"/><Button type="submit" aria-label={busy?"در حال بررسی":"ارسال برای بررسی"} disabled={!text.trim()||busy} className="grid size-11 shrink-0 place-items-center rounded-full p-0"><Send2 size={19} variant="Bold"/></Button></form><p className="mt-2 text-center text-[10px] font-semibold text-muted-foreground">برای فرستادن Enter و برای خط تازه Shift+Enter</p></div>
  </main>;
  return <main className="focus-blur relative min-h-[calc(100dvh-5rem)] overflow-hidden bg-[#f4f6f9]"><AlgoPattern className="pointer-events-none absolute -right-36 -top-28 h-[34rem] w-[50rem] text-ink/[0.045]" fade="radial" /><div className="relative mx-auto flex min-h-[calc(100dvh-5rem)] max-w-6xl flex-col px-4 pb-52 pt-10 sm:px-6"><header className="mx-auto max-w-3xl text-center"><div className="mx-auto flex justify-center"><Orb busy={busy} /></div><h1 className="mt-5 text-3xl font-black sm:text-4xl">شرایطتان را بگویید</h1><p className="mt-3 text-sm leading-7 text-muted-foreground">برداشت را قبل از هر ادامه‌ای ببینید و اصلاح کنید. هیچ پیامی درخواست سرمایه‌گذاری ارسال نمی‌کند.</p><p className="mt-2 text-xs leading-6 text-muted-foreground">متن برای تولید پاسخ به ارائه‌دهنده مدل فرستاده می‌شود؛ اطلاعات خصوصی وارد نکنید. ذخیره‌نشدن درخواست نزد ارائه‌دهنده به‌معنی تضمین ZDR نیست.</p></header>{!turns.length && !processing && <section className="mx-auto mt-9 flex w-full max-w-3xl flex-wrap justify-center gap-2">{examples.map((example) => <Button key={example} type="button" variant="plain" onClick={() => { setText(example); void submit(example); }} className="h-auto whitespace-normal rounded-full border border-border bg-white px-4 py-2 text-right text-xs font-bold leading-6">{example}<ArrowLeft size={14} /></Button>)}</section>}<section aria-live="polite" className="mt-9 space-y-8">{turns.map((turn) => <motion.article initial={{opacity:0,y:10}} animate={{opacity:1,y:0}} key={turn.id} className="space-y-4"><div className="flex justify-start"><p className="max-w-2xl rounded-[1.4rem] rounded-tr-md bg-teal-800 px-5 py-3 text-sm font-bold leading-7 text-white">{turn.question}</p></div><CompletedSteps steps={turn.response.steps} />{turn.response.interpretation && <div className="surface mx-auto max-w-4xl rounded-[1.75rem] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="flex items-center gap-2 text-sm font-black"><TickCircle size={18} className="text-primary" />برداشت قابل اصلاح</h2><Button type="button" variant="plain" size="auto" onClick={() => { setText(turn.question); setEditing(true); }} className="h-9 rounded-full px-3 text-xs font-bold"><Edit2 size={15} />اصلاح متن</Button></div><div className="mt-4"><Chips criteria={turn.id === turns.at(-1)?.id ? criteria : turn.response.interpretation.criteria} onRemove={(key) => setCriteria((current) => { const next = { ...current }; delete next[key]; return next; })} /></div></div>}<div className="mx-auto flex max-w-4xl flex-row-reverse items-start gap-3"><Orb /><div className="min-w-0 flex-1 rounded-[1.4rem] rounded-tl-md bg-white px-5 py-4 text-sm font-semibold leading-8 shadow-sm">{turn.response.answer || turn.response.error?.message || "نتایج سرور آماده است؛ برای ادامه دستی از دکمه پایین استفاده کنید."}{turn.response.state === "failed" && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">موفقیت ثبت نشده است. متن و شرط‌ها در همین مرورگر محفوظ مانده‌اند.</p>}</div></div>{turn.response.server_result?.items && <motion.div initial="hidden" animate="show" variants={{show:{transition:{staggerChildren:.08}}}} className="mx-auto grid max-w-5xl gap-4 md:grid-cols-3">{turn.response.server_result.items.slice(0, 3).map((item, index) => <motion.div variants={{hidden:{opacity:0,y:10},show:{opacity:1,y:0}}} key={item.id}><ResultCard item={item} index={index} /></motion.div>)}</motion.div>}<div className="mx-auto flex max-w-4xl flex-wrap gap-2"><Button type="button" onClick={manual} disabled={!criteria.route} className="rounded-full px-5 font-extrabold">ادامه با فیلتر دستی</Button><Button type="button" variant="outline" onClick={save} disabled={!criteria.route} className="rounded-full px-5 font-extrabold"><Save2 size={17} />ذخیره با رسید سرور</Button><Button type="button" variant="outline" onClick={compare} disabled={items.length < 2} className="rounded-full px-5 font-extrabold"><Chart size={17} />مقایسه ۲ تا ۴ مورد</Button></div></motion.article>)}<AnimatePresence>{processing && <Processing question={processing.question} steps={processing.steps}/>}</AnimatePresence><div ref={end} /></section>{error && <div role="alert" className="mx-auto mt-5 flex max-w-3xl flex-wrap items-center gap-3 text-sm font-bold text-destructive"><span>{error}</span><Button type="button" variant="outline" size="auto" onClick={() => void submit()} disabled={busy} className="rounded-full px-4">تلاش دوباره با همان رسید</Button></div>}</div><div className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-[#f4f6f9]/95 px-4 py-3 backdrop-blur"><div className="mx-auto mb-2 flex max-w-4xl gap-1.5 overflow-x-auto pb-1" aria-label="انتخاب مسیر">{routeChoices.map(([id,label]) => <button key={id} type="button" onClick={() => setCriteria((current) => ({...current,route:id,kind:id==='fund'?'fund':id==='buyer'?'sale':'project'}))} aria-pressed={criteria.route===id} className="shrink-0 rounded-full border border-border bg-white px-3 py-1.5 text-[11px] font-bold aria-pressed:border-primary aria-pressed:bg-teal-50 aria-pressed:text-primary-ink">{label}</button>)}</div><form onSubmit={(event) => { event.preventDefault(); void submit(); }} aria-busy={busy} className="mx-auto flex max-w-4xl items-end gap-2 rounded-[1.6rem] border border-border bg-white p-2 pr-4 shadow-[0_20px_60px_-30px_rgb(22_32_48/0.5)]"><SavedPicker onPick={(value) => { setCriteria(value); setEditing(true); }} /><Textarea value={text} onChange={(event) => setText(event.target.value)} aria-label="شرایط شما برای دستیار" placeholder={editing ? "متن یا شرط‌ها را اصلاح کنید" : "مثلاً: پروژه مسکونی تهران تا ۳۰ میلیارد"} rows={1} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); } }} className="field-sizing-content max-h-28 min-h-11 flex-1 resize-none border-0 !bg-transparent px-1 py-2 text-sm shadow-none focus-visible:ring-0" /><Button type="submit" aria-label={busy?"در حال بررسی":"ارسال برای بررسی"} disabled={!text.trim() || busy} className="grid size-11 shrink-0 place-items-center rounded-full p-0"><Send2 size={19} variant="Bold" /></Button></form><p className="mx-auto mt-2 max-w-4xl text-center text-[10.5px] font-semibold text-muted-foreground">پاسخ متصل ممکن است در دسترس نباشد؛ جست‌وجو و ادامه دستی همیشه باقی می‌ماند.</p></div></main>;
}
