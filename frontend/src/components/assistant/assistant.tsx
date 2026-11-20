"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { ArchiveTick, ArrowLeft, Chart, CloseCircle, Edit2, MagicStar, Save2, Send2, TickCircle } from "@/components/iconsax";
import { AlgoPattern } from "@/components/brand/algo-pattern";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { assistantTurn, type AssistantItem, type AssistantResponse } from "@/lib/assistant-api";
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
  return <div className="flex flex-wrap gap-2">{values.map(([key, value]) => <span key={key} className="inline-flex items-center gap-1.5 rounded-full border border-ink/10 bg-white px-3 py-1.5 text-xs font-bold text-ink/75"><span className="text-muted-foreground">{labels[key]}:</span>{typeof value === "string" ? value : Array.isArray(value) ? value.join("، ") : "ثبت‌شده"}<button type="button" onClick={() => onRemove(key)} aria-label={`حذف ${labels[key]}`} className="grid size-6 place-items-center rounded-full hover:bg-muted"><CloseCircle size={15} /></button></span>)}</div>;
}

function ResultCard({ item, index }: { item: AssistantItem; index: number }) {
  const title = String(item.fields.title || "فرصت بدون عنوان");
  const score = item.matching?.score;
  const coverage = item.matching?.coverage;
  return <article className="surface flex min-h-64 flex-col rounded-[1.75rem] p-5"><div className="flex items-start justify-between gap-3"><span className="grid size-9 place-items-center rounded-full bg-cobalt-soft text-sm font-black text-cobalt">{index + 1}</span><span className="rounded-full bg-muted px-3 py-1 text-[11px] font-bold text-muted-foreground">نسخه {item.revision.slice(0, 8)}</span></div><h3 className="mt-5 text-lg font-black leading-8">{title}</h3><div className="mt-4 grid grid-cols-2 gap-2 text-xs"><div className="rounded-2xl bg-muted p-3"><span className="block text-muted-foreground">امتیاز سرور</span><strong className="mt-1 block text-base">{score === null || score === undefined ? "بدون ترجیح" : `${Number(score).toFixed(0)}٪`}</strong></div><div className="rounded-2xl bg-muted p-3"><span className="block text-muted-foreground">پوشش داده</span><strong className="mt-1 block text-base">{coverage === null || coverage === undefined ? "نامعلوم" : `${Number(coverage).toFixed(0)}٪`}</strong></div></div><p className="mt-3 text-xs leading-6 text-muted-foreground">امتیاز احتمال سود یا تأیید مناسب‌بودن نیست.</p><Link className="mt-auto pt-5 text-sm font-extrabold text-cobalt" href={`/opportunities/${item.id}`}>دیدن نسخه عمومی <ArrowLeft className="inline" size={15} /></Link></article>;
}

function SavedPicker({ onPick }: { onPick: (criteria: Record<string, unknown>) => void }) {
  const profiles = useStore((state) => state.profiles);
  const [open, setOpen] = useState(false);
  return <div className="relative"><Button type="button" variant="plain" size="auto" onClick={() => setOpen(!open)} aria-expanded={open} className="h-11 rounded-full border border-border bg-white px-4 text-xs font-extrabold"><ArchiveTick size={17} />شرایط من</Button>{open && <div className="absolute bottom-14 right-0 z-30 w-[min(22rem,calc(100vw-2rem))] rounded-3xl border border-border bg-white p-2 shadow-2xl"><p className="px-3 py-2 text-xs font-bold text-muted-foreground">فقط با انتخاب و بازبینی شما</p>{profiles.length ? profiles.map((profile) => <button key={profile.id} type="button" className="block w-full rounded-2xl px-3 py-3 text-right text-sm font-extrabold hover:bg-muted" onClick={() => { onPick(profile.serverCriteria || {}); setOpen(false); }}>{profile.name}</button>) : <p className="px-3 py-4 text-sm text-muted-foreground">شرایط ذخیره‌شده‌ای ندارید.</p>}</div>}</div>;
}

function CompletedSteps({ steps }: { steps?: AssistantResponse["steps"] }) {
  const labels = { interpretation: "برداشت نیاز", public_data: "بازخوانی داده عمومی", explanation: "توضیح مستند" };
  if (!steps) return null;
  return <ol className="mx-auto grid max-w-4xl gap-2 sm:grid-cols-3">{steps.map((step) => <li key={step.id} className="flex items-center gap-2 rounded-2xl border border-border bg-white px-4 py-3 text-xs font-bold"><span className={step.status === "completed" ? "text-primary" : step.status === "failed" ? "text-amber-700" : "text-muted-foreground"}>{step.status === "completed" ? "✓" : step.status === "failed" ? "!" : "—"}</span>{labels[step.id]}</li>)}</ol>;
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
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const draft = sessionStorage.getItem("invest:assistant-draft");
    if (draft) { setText(draft.slice(0, 4000)); sessionStorage.removeItem("invest:assistant-draft"); }
    const saved = sessionStorage.getItem("invest:assistant-session");
    if (saved) try { const parsed = JSON.parse(saved); if (Array.isArray(parsed)) setTurns(parsed.slice(-12)); } catch { sessionStorage.removeItem("invest:assistant-session"); }
    const opportunity = sessionStorage.getItem("invest:assistant-opportunity");
    if (opportunity) { setContextIds([opportunity]); sessionStorage.removeItem("invest:assistant-opportunity"); }
  }, []);
  useEffect(() => { sessionStorage.setItem("invest:assistant-session", JSON.stringify(turns.slice(-12))); end.current?.scrollIntoView({ behavior: "smooth" }); }, [turns]);
  const latest = turns.at(-1)?.response;
  const items = useMemo(() => latest?.server_result?.items || [], [latest]);
  const submit = async (value = text) => {
    const message = value.trim();
    if (!message || busy) return;
    setBusy(true); setError("");
    try {
      const history = turns.flatMap((turn) => [
        { role: "user", text: turn.question },
        ...(turn.response.answer ? [{ role: "assistant", text: turn.response.answer }] : []),
      ]).slice(-12);
      const response = await assistantTurn({
        message,
        ...(Object.keys(criteria).length ? { criteria } : {}),
        ...(contextIds.length ? { opportunity_ids: contextIds } : {}),
        history,
      });
      if (response.interpretation) setCriteria(response.interpretation.criteria);
      setTurns((current) => [...current, { id: crypto.randomUUID(), question: message, response }]);
      setText(""); setEditing(false);
    } catch (cause) { setError(cause instanceof Error ? cause.message : "پاسخ دریافت نشد."); }
    finally { setBusy(false); }
  };
  const manual = () => { const converted = fromCriteria(criteria); useStore.getState().begin(converted); router.push("/opportunities"); };
  const save = async () => {
    const converted = fromCriteria(criteria);
    useStore.getState().begin(converted);
    if (!user) return openLogin({ type: "save-criteria", name: "شرایط دستیار" });
    try { await addProfile("شرایط دستیار", converted); } catch { /* store keeps the input and reports the server failure */ }
  };
  const compare = () => { if (items.length >= 2) { setCompare(items.slice(0, 4).map((item) => item.id)); router.push("/compare"); } };
  return <main className="focus-blur relative min-h-[calc(100dvh-5rem)] overflow-hidden bg-[#f4f6f9]"><AlgoPattern className="pointer-events-none absolute -right-36 -top-28 h-[34rem] w-[50rem] text-ink/[0.045]" fade="radial" /><div className="relative mx-auto flex min-h-[calc(100dvh-5rem)] max-w-6xl flex-col px-4 pb-52 pt-10 sm:px-6"><header className="mx-auto max-w-3xl text-center"><div className="mx-auto flex justify-center"><Orb busy={busy} /></div><h1 className="mt-5 text-3xl font-black sm:text-4xl">شرایطتان را بگویید</h1><p className="mt-3 text-sm leading-7 text-muted-foreground">برداشت را قبل از هر ادامه‌ای ببینید و اصلاح کنید. هیچ پیامی درخواست سرمایه‌گذاری ارسال نمی‌کند.</p><p className="mt-2 text-xs leading-6 text-muted-foreground">متن برای تولید پاسخ به ارائه‌دهنده مدل فرستاده می‌شود؛ اطلاعات خصوصی وارد نکنید. ذخیره‌نشدن درخواست نزد ارائه‌دهنده به‌معنی تضمین ZDR نیست.</p></header>{!turns.length && <section className="mx-auto mt-9 grid w-full max-w-3xl gap-2 sm:grid-cols-2">{examples.map((example) => <Button key={example} type="button" variant="plain" onClick={() => { setText(example); void submit(example); }} className="h-auto justify-between whitespace-normal rounded-2xl border border-border bg-white px-4 py-3 text-right text-sm font-bold leading-7">{example}<ArrowLeft size={16} /></Button>)}</section>}<section aria-live="polite" className="mt-9 space-y-8">{turns.map((turn) => <article key={turn.id} className="space-y-4"><div className="flex justify-start"><p className="max-w-2xl rounded-[1.4rem] rounded-tr-md bg-teal-800 px-5 py-3 text-sm font-bold leading-7 text-white">{turn.question}</p></div><CompletedSteps steps={turn.response.steps} />{turn.response.interpretation && <div className="surface mx-auto max-w-4xl rounded-[1.75rem] p-5"><div className="flex flex-wrap items-center justify-between gap-3"><h2 className="flex items-center gap-2 text-sm font-black"><TickCircle size={18} className="text-primary" />برداشت قابل اصلاح</h2><Button type="button" variant="plain" size="auto" onClick={() => { setText(turn.question); setEditing(true); }} className="h-9 rounded-full px-3 text-xs font-bold"><Edit2 size={15} />اصلاح متن</Button></div><div className="mt-4"><Chips criteria={turn.id === turns.at(-1)?.id ? criteria : turn.response.interpretation.criteria} onRemove={(key) => setCriteria((current) => { const next = { ...current }; delete next[key]; return next; })} /></div></div>}<div className="mx-auto flex max-w-4xl flex-row-reverse items-start gap-3"><Orb /><div className="min-w-0 flex-1 rounded-[1.4rem] rounded-tl-md bg-white px-5 py-4 text-sm font-semibold leading-8 shadow-sm">{turn.response.answer || turn.response.error?.message || "نتایج سرور آماده است؛ برای ادامه دستی از دکمه پایین استفاده کنید."}{turn.response.state === "failed" && <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">موفقیت ثبت نشده است. متن و شرط‌ها در همین مرورگر محفوظ مانده‌اند.</p>}</div></div>{turn.response.server_result?.items && <><div className="mx-auto grid max-w-5xl gap-4 md:grid-cols-3">{turn.response.server_result.items.slice(0, 3).map((item, index) => <ResultCard key={item.id} item={item} index={index} />)}</div>{turn.response.server_result.items.length > 3 && <div className="mx-auto max-w-5xl space-y-2">{turn.response.server_result.items.slice(3).map((item) => <Link key={item.id} href={`/opportunities/${item.id}`} className="surface flex items-center justify-between rounded-2xl px-5 py-3 text-sm font-bold">{String(item.fields.title || "فرصت")}<ArrowLeft size={16} /></Link>)}</div>}</>}<div className="mx-auto flex max-w-4xl flex-wrap gap-2"><Button type="button" onClick={manual} disabled={!criteria.route} className="rounded-full px-5 font-extrabold">ادامه با فیلتر دستی</Button><Button type="button" variant="outline" onClick={save} disabled={!criteria.route} className="rounded-full px-5 font-extrabold"><Save2 size={17} />ذخیره با رسید سرور</Button><Button type="button" variant="outline" onClick={compare} disabled={items.length < 2} className="rounded-full px-5 font-extrabold"><Chart size={17} />مقایسه ۲ تا ۴ مورد</Button></div></article>)}<div ref={end} /></section>{error && <p role="alert" className="mx-auto mt-5 max-w-3xl text-sm font-bold text-destructive">{error}</p>}</div><div className="fixed inset-x-0 bottom-0 z-20 border-t border-border bg-[#f4f6f9]/95 px-4 py-3 backdrop-blur"><div className="mx-auto mb-2 flex max-w-4xl gap-1.5 overflow-x-auto pb-1" aria-label="انتخاب مسیر">{routeChoices.map(([id,label]) => <button key={id} type="button" onClick={() => setCriteria((current) => ({...current,route:id,kind:id==='fund'?'fund':id==='buyer'?'sale':'project'}))} aria-pressed={criteria.route===id} className="shrink-0 rounded-full border border-border bg-white px-3 py-1.5 text-[11px] font-bold aria-pressed:border-primary aria-pressed:bg-teal-50 aria-pressed:text-primary-ink">{label}</button>)}</div><form onSubmit={(event) => { event.preventDefault(); void submit(); }} className="mx-auto flex max-w-4xl items-end gap-2 rounded-[1.6rem] border border-border bg-white p-2 pr-4 shadow-[0_20px_60px_-30px_rgb(22_32_48/0.5)]"><SavedPicker onPick={(value) => { setCriteria(value); setEditing(true); }} /><Textarea value={text} onChange={(event) => setText(event.target.value)} aria-label="شرایط شما برای دستیار" placeholder={editing ? "متن یا شرط‌ها را اصلاح کنید" : "مثلاً: پروژه مسکونی تهران تا ۳۰ میلیارد"} rows={1} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); } }} className="field-sizing-content max-h-28 min-h-11 flex-1 resize-none border-0 !bg-transparent px-1 py-2 text-sm shadow-none focus-visible:ring-0" /><Button type="submit" aria-label="ارسال برای بررسی" disabled={!text.trim() || busy} className="grid size-11 shrink-0 place-items-center rounded-full p-0"><Send2 size={19} variant="Bold" /></Button></form><p className="mx-auto mt-2 max-w-4xl text-center text-[10.5px] font-semibold text-muted-foreground">پاسخ متصل ممکن است در دسترس نباشد؛ جست‌وجو و ادامه دستی همیشه باقی می‌ماند.</p></div></main>;
}
