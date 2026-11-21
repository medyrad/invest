"use client";

import Link from "next/link";
import Image from "next/image";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import {
  ArchiveTick,
  Chart,
  CloseCircle,
  Edit2,
  MagicStar,
  Save2,
  Send2,
  TickCircle,
} from "@/components/iconsax";
import { AlgoPattern } from "@/components/brand/algo-pattern";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
  assistantTurnStream,
  type AssistantItem,
  type AssistantResponse,
  type AssistantStep,
} from "@/lib/assistant-api";
import { assistantValueLabel } from "@/lib/assistant-labels";
import { exactText } from "@/lib/public-values";
import { fromCriteria, useStore } from "@/lib/store";

type Turn = { id: string; question: string; response: AssistantResponse };
const examples = [
  "مسکونی در تهران تا ۳۰ میلیارد",
  "صندوق کم‌ریسک با سود ماهانه",
  "نیروگاه خورشیدی در یزد",
  "خرید ملک در شیراز",
  "اجاره دفتر در اصفهان",
  "مرمت خانه تاریخی در کاشان",
];
function Orb({ busy = false }: { busy?: boolean }) {
  const reduce = useReducedMotion();
  return (
    <motion.span
      aria-hidden
      className="relative grid size-12 shrink-0 place-items-center rounded-full bg-gradient-to-br from-teal-500 via-cobalt to-violet-600 text-white shadow-[0_18px_55px_-18px_rgb(30_64_175/0.75)]"
      animate={busy && !reduce ? { rotate: 360 } : undefined}
      transition={{ duration: 2.5, repeat: Infinity, ease: "linear" }}
    >
      <MagicStar size={23} variant="Bold" />
    </motion.span>
  );
}

function Chips({
  criteria,
  onRemove,
}: {
  criteria: Record<string, unknown>;
  onRemove: (key: string) => void;
}) {
  const labels: Record<string, string> = {
    route: "مسیر",
    kind: "نوع",
    budget_max: "سقف بودجه",
    province: "استان",
    city: "شهر",
    group: "گروه",
    risk: "ریسک",
    return: "بازده",
  };
  const values = Object.entries(criteria).filter(([key]) => key in labels);
  return (
    <div className="flex flex-wrap gap-2">
      {values.map(([key, value]) => (
        <span
          key={key}
          className="inline-flex items-center gap-1.5 rounded-full border border-ink/10 bg-white px-3 py-1.5 text-xs font-bold text-ink/75"
        >
          <span className="text-muted-foreground">{labels[key]}:</span>
          {assistantValueLabel(key, value)}
          <button
            type="button"
            onClick={() => onRemove(key)}
            aria-label={`حذف ${labels[key]}`}
            className="grid size-6 place-items-center rounded-full hover:bg-muted"
          >
            <CloseCircle size={15} />
          </button>
        </span>
      ))}
    </div>
  );
}

function ResultCard({ item, index }: { item: AssistantItem; index: number }) {
  const title = String(item.fields.title || "فرصت بدون عنوان");
  const score = item.matching?.score;
  const image = itemImage(item);
  const location = itemLocation(item);
  const amount = itemAmount(item);
  const checks = (item.matching?.checks || [])
    .filter((check) => check.state === "met")
    .slice(0, 3);
  return (
    <article className="group relative flex flex-col overflow-hidden rounded-[1.75rem] border border-border bg-white transition-[transform,box-shadow] duration-300 hover:-translate-y-1 hover:shadow-[0_26px_56px_-32px_rgb(22_32_48/0.4)] motion-reduce:transition-none">
      <Link
        href={`/opportunities/${item.id}`}
        aria-label={title}
        className="relative m-2 block aspect-[16/10] overflow-hidden rounded-[1.35rem] bg-muted"
      >
        <Image
          src={image}
          alt=""
          fill
          unoptimized
          sizes="(min-width: 768px) 30vw, 90vw"
          className="object-cover transition-transform duration-700 motion-reduce:transition-none group-hover:scale-[1.04]"
        />
        <span className="absolute inset-0 bg-[linear-gradient(to_top,rgb(0_0_0/0.65),transparent_55%)]" />
        <span className="absolute right-3 top-3 rounded-full bg-white px-2.5 py-0.5 text-[11px] font-black text-ink">
          پیشنهاد {index + 1}
        </span>
        <span className="absolute bottom-3 left-3 grid size-[58px] place-items-center rounded-full border-[3.5px] border-white bg-teal-900/50 text-[13px] font-extrabold text-white">
          {score == null ? "—" : `${Number(score).toFixed(0)}٪`}
        </span>
        <span className="absolute bottom-3.5 right-3 flex items-center gap-1 text-xs font-bold text-white">
          ● {location}
        </span>
      </Link>
      <div className="flex flex-1 flex-col gap-2.5 px-4 pb-4 pt-1.5">
        <h3 className="line-clamp-2 min-h-12 text-[15px] font-extrabold leading-6 text-ink">
          {title}
        </h3>
        <p className="text-xs font-semibold text-muted-foreground">
          {item.kind === "project" ? "حداقل ورود" : "مبلغ"}: {amount}
        </p>
        <div className="mt-auto flex flex-wrap gap-1.5">
          {checks.length ? (
            checks.map((check) => (
              <span
                key={check.axis}
                className="flex items-center gap-1 rounded-full bg-ink/[0.05] px-2 py-0.5 text-[11px] font-bold text-primary-ink"
              >
                ✓ {check.axis}
              </span>
            ))
          ) : (
            <span className="rounded-full bg-ink/[0.05] px-2 py-0.5 text-[11px] font-bold text-muted-foreground">
              داده عمومی قابل مشاهده
            </span>
          )}
        </div>
      </div>
    </article>
  );
}

function itemImage(item: AssistantItem) {
  const subtype = String(item.fields.subtype || "");
  return String(
    item.images?.[0] ||
      item.fields.image_url ||
      item.fields.image ||
      (subtype ? "/images/types/" + subtype + ".webp" : "") ||
      "/images/hero/construction.jpg",
  );
}

function itemLocation(item: AssistantItem) {
  const city = exactText(item.fields.city);
  const province = exactText(item.fields.province);
  if (city !== "اعلام نشده" && city !== "نامعلوم") return city;
  if (province !== "اعلام نشده" && province !== "نامعلوم") return province;
  return "موقعیت نامعلوم";
}

function itemAmount(item: AssistantItem) {
  const value =
    item.fields.minimum_investment ||
    item.fields.min_capital ||
    item.fields.budget ||
    item.fields.price;
  return value ? exactText(value) : "مبلغ نامعلوم";
}

function CompactResult({
  item,
  index,
}: {
  item: AssistantItem;
  index: number;
}) {
  const image = itemImage(item);
  const score = item.matching?.score;
  return (
    <article className="group relative flex min-h-[82px] items-center gap-3 rounded-[1.5rem] border border-border bg-white p-2 pl-3 transition-[transform,box-shadow,border-color] duration-300 hover:-translate-y-0.5 hover:border-ink/25 hover:shadow-[0_22px_44px_-32px_rgb(22_32_48/0.4)] motion-reduce:transition-none sm:gap-4 sm:pl-4">
      <span className="w-6 shrink-0 text-center text-sm font-black text-muted-foreground">
        {index + 1}
      </span>
      <Image
        src={image}
        alt=""
        width={112}
        height={80}
        unoptimized
        className="h-16 w-20 shrink-0 rounded-xl object-cover sm:w-24"
      />
      <Link href={`/opportunities/${item.id}`} className="min-w-0 flex-1">
        <h3 className="truncate text-sm font-black sm:text-base">
          {String(item.fields.title || "فرصت بدون عنوان")}
        </h3>
        <p className="mt-2 truncate text-[11px] font-bold text-muted-foreground">
          {itemLocation(item)} · {itemAmount(item)}
        </p>
      </Link>
      <button
        type="button"
        aria-label={`ذخیره ${String(item.fields.title || "فرصت")}`}
        className="relative z-20 grid size-10 shrink-0 place-items-center rounded-full bg-muted text-ink"
      >
        <Save2 size={19} />
      </button>
      <span className="grid size-12 shrink-0 place-items-center rounded-full border-[4px] border-teal-500/25 text-xs font-black sm:size-14 sm:text-sm">
        {score == null ? "—" : `${Number(score).toFixed(0)}٪`}
      </span>
    </article>
  );
}

function SavedPicker({
  onPick,
}: {
  onPick: (criteria: Record<string, unknown>) => void;
}) {
  const {
    profiles,
    user,
    addProfile,
    updateProfile,
    removeProfile,
    openLogin,
  } = useStore();
  const [open, setOpen] = useState(false);
  const [selected, setSelected] = useState<string | null>(null);
  const [naming, setNaming] = useState(false);
  const [name, setName] = useState("شرایط دستیار");
  const picked = profiles.find((profile) => profile.id === selected);
  const current = () => {
    try {
      const value = JSON.parse(
        sessionStorage.getItem("invest:assistant-criteria") || "{}",
      );
      return value && typeof value === "object" ? value : {};
    } catch {
      return {};
    }
  };
  const criteria = current();
  const persist = async () => {
    const criteria = current();
    if (!user) {
      openLogin({ type: "save-criteria", name });
      return;
    }
    await addProfile(name.trim() || "شرایط دستیار", fromCriteria(criteria));
    setNaming(false);
  };
  return (
    <div className="relative">
      <Button
        type="button"
        variant="plain"
        size="auto"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        className="h-11 rounded-full border border-border bg-white px-4 text-xs font-extrabold"
      >
        <ArchiveTick size={17} />
        {picked?.name || "شرایط من"}
      </Button>
      {open && (
        <div className="absolute bottom-14 right-0 z-30 w-[min(24rem,calc(100vw-2rem))] rounded-3xl border border-border bg-white p-2 shadow-2xl">
          <div className="flex items-center justify-between px-3 py-2">
            <p className="text-xs font-bold text-muted-foreground">
              نام پروفایل برای مدل ارسال نمی‌شود.
            </p>
            <button
              type="button"
              onClick={() => setNaming(true)}
              className="text-xs font-extrabold text-cobalt"
            >
              ذخیره فعلی
            </button>
          </div>
          {profiles.length ? (
            profiles.map((profile) => (
              <div
                key={profile.id}
                className="flex items-center rounded-2xl hover:bg-muted"
              >
                <button
                  type="button"
                  className="min-w-0 flex-1 px-3 py-3 text-right text-sm font-extrabold"
                  onClick={() => {
                    setSelected(profile.id);
                    onPick(profile.serverCriteria || {});
                    setOpen(false);
                  }}
                >
                  {profile.name}
                </button>
                <button
                  type="button"
                  aria-label={`جایگزینی ${profile.name}`}
                  className="px-2 text-[11px] font-bold text-cobalt"
                  onClick={() =>
                    void updateProfile(profile.id, {
                      criteria: fromCriteria(criteria),
                    })
                  }
                >
                  جایگزینی
                </button>
                <button
                  type="button"
                  aria-label={`حذف ${profile.name}`}
                  className="px-2 text-[11px] font-bold text-destructive"
                  onClick={() => void removeProfile(profile.id)}
                >
                  حذف
                </button>
              </div>
            ))
          ) : (
            <p className="px-3 py-4 text-sm text-muted-foreground">
              شرایط ذخیره‌شده‌ای ندارید.
            </p>
          )}
        </div>
      )}
      {naming && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="نام‌گذاری شرایط"
          className="fixed inset-0 z-50 grid place-items-center bg-ink/30 p-4"
        >
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void persist();
            }}
            className="w-full max-w-sm rounded-3xl bg-white p-5 shadow-2xl"
          >
            <h2 className="font-black">نام این شرایط</h2>
            <input
              autoFocus
              value={name}
              onChange={(event) => setName(event.target.value.slice(0, 80))}
              className="mt-4 h-11 w-full rounded-xl border border-border px-3 text-sm"
            />
            <div className="mt-4 flex gap-2">
              <Button type="submit" className="rounded-full">
                ذخیره با رسید سرور
              </Button>
              <Button
                type="button"
                variant="plain"
                onClick={() => setNaming(false)}
                className="rounded-full"
              >
                انصراف
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

function CompletedSteps({ steps }: { steps?: AssistantResponse["steps"] }) {
  const labels = {
    interpretation: "برداشت نیاز",
    public_data: "بازخوانی داده عمومی",
    explanation: "توضیح مستند",
  };
  if (!steps) return null;
  return (
    <ol className="mx-auto grid max-w-4xl gap-2 sm:grid-cols-3">
      {steps.map((step) => (
        <li
          key={step.id}
          className="flex items-center gap-2 rounded-2xl border border-border bg-white px-4 py-3 text-xs font-bold"
        >
          <span
            className={
              step.status === "completed"
                ? "text-primary"
                : step.status === "failed"
                  ? "text-amber-700"
                  : "text-muted-foreground"
            }
          >
            {step.status === "completed"
              ? "✓"
              : step.status === "failed"
                ? "!"
                : "—"}
          </span>
          {labels[step.id]}
        </li>
      ))}
    </ol>
  );
}

const initialSteps: AssistantStep[] = [
  {
    id: "interpretation",
    status: "pending",
    detail: "در انتظار خواندن درخواست",
  },
  { id: "public_data", status: "pending", detail: "در انتظار داده عمومی" },
  {
    id: "explanation",
    status: "pending",
    detail: "در انتظار تولید و اعتبارسنجی",
  },
];
const processingLabels = {
  interpretation: "خواندن شرایط شما",
  public_data: "تطبیق با پروژه‌ها",
  explanation: "مرتب‌سازی بر اساس درصد تطابق",
};
function Processing({
  question,
  steps,
}: {
  question: string;
  steps: AssistantStep[];
}) {
  const reduce = useReducedMotion();
  return (
    <motion.article
      initial={reduce ? false : { opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      className="space-y-5"
      aria-live="polite"
      aria-busy="true"
    >
      <div className="mx-auto flex max-w-[976px] justify-end">
        <p className="max-w-2xl rounded-[1.4rem] rounded-tr-md bg-teal-800 px-6 py-3 text-sm font-bold leading-7 text-white">
          {question}
        </p>
      </div>
      <div className="relative mx-auto mr-auto mt-1 w-[408px] max-w-[calc(100vw-2rem)] rounded-[1.5rem] rounded-tl-md bg-white px-5 py-4 shadow-[0_22px_55px_-38px_rgb(22_32_48/0.7)] sm:ml-[52px] lg:ml-[116px]">
        <span className="absolute -top-12 left-2 grid size-10 place-items-center rounded-full border-4 border-white bg-ink text-white shadow-lg sm:-left-[52px] sm:top-0">
          <MagicStar size={20} variant="Bold" />
        </span>
        <h2 className="mb-3 text-xs font-extrabold text-teal-800">
          در حال بررسی...
        </h2>
        <ol className="relative space-y-3 before:absolute before:right-[1.05rem] before:top-5 before:h-[calc(100%-2.5rem)] before:w-px before:bg-teal-200">
          {steps.map((step) => (
            <li
              key={step.id}
              className="relative flex min-h-10 items-start gap-3"
            >
              <motion.span
                animate={
                  !reduce && step.status === "active"
                    ? { scale: [1, 1.12, 1] }
                    : undefined
                }
                transition={{ repeat: Infinity, duration: 1.1 }}
                className={`z-10 grid size-9 shrink-0 place-items-center rounded-full text-xs font-black ${step.status === "completed" ? "bg-teal-500 text-white" : step.status === "active" ? "bg-teal-50 text-teal-700 ring-2 ring-teal-400" : step.status === "failed" ? "bg-amber-100 text-amber-800" : "bg-muted text-muted-foreground/50"}`}
              >
                {step.status === "completed"
                  ? "✓"
                  : step.status === "failed"
                    ? "!"
                    : "◌"}
              </motion.span>
              <div>
                <h3
                  className={`text-sm font-extrabold ${step.status === "pending" ? "text-muted-foreground/45" : "text-ink"}`}
                >
                  {processingLabels[step.id]}
                </h3>
                {(step.status === "completed" || step.status === "failed") && (
                  <p className="mt-1 text-[11px] leading-5 text-muted-foreground">
                    {step.detail}
                  </p>
                )}
              </div>
            </li>
          ))}
        </ol>
      </div>
      <div className="mx-auto grid w-full max-w-[924px] gap-4 lg:translate-x-[26px] md:grid-cols-3">
        {[0, 1, 2].map((value) => (
          <div
            key={value}
            className="rounded-[1.75rem] border border-border bg-white p-2 shadow-sm"
          >
            <div className="aspect-[16/10] animate-pulse rounded-[1.35rem] bg-[#edf1f6] motion-reduce:animate-none" />
            <div className="space-y-3 px-2 pb-2 pt-4">
              <div className="h-3 w-3/4 rounded-full bg-[#edf1f6]" />
              <div className="mr-auto h-3 w-1/2 rounded-full bg-[#edf1f6]" />
            </div>
          </div>
        ))}
      </div>
    </motion.article>
  );
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
  const [processing, setProcessing] = useState<{
    question: string;
    steps: AssistantStep[];
  } | null>(null);
  const retryKey = useRef<string | null>(null);
  const end = useRef<HTMLDivElement>(null);
  useEffect(() => {
    const draft = sessionStorage.getItem("invest:assistant-draft");
    if (draft) {
      setText(draft.slice(0, 4000));
      sessionStorage.removeItem("invest:assistant-draft");
    }
    const saved = sessionStorage.getItem("invest:assistant-session");
    if (saved)
      try {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed)) setTurns(parsed.slice(-12));
      } catch {
        sessionStorage.removeItem("invest:assistant-session");
      }
    const opportunity = sessionStorage.getItem("invest:assistant-opportunity");
    if (opportunity) {
      setContextIds([opportunity]);
      sessionStorage.removeItem("invest:assistant-opportunity");
    }
  }, []);
  useEffect(() => {
    sessionStorage.setItem(
      "invest:assistant-session",
      JSON.stringify(turns.slice(-12)),
    );
    if (turns.length) end.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);
  useEffect(() => {
    sessionStorage.setItem(
      "invest:assistant-criteria",
      JSON.stringify(criteria),
    );
  }, [criteria]);
  const latest = turns.at(-1)?.response;
  const items = useMemo(() => latest?.server_result?.items || [], [latest]);
  const submit = async (value = text) => {
    const message = value.trim();
    if (!message || busy) return;
    setBusy(true);
    setError("");
    setProcessing({ question: message, steps: initialSteps });
    try {
      const history = turns
        .flatMap((turn) => [
          { role: "user", text: turn.question },
          ...(turn.response.answer
            ? [{ role: "assistant", text: turn.response.answer }]
            : []),
        ])
        .slice(-12);
      const key = retryKey.current || crypto.randomUUID();
      retryKey.current = key;
      const { value: response } = await assistantTurnStream(
        {
          message,
          ...(Object.keys(criteria).length ? { criteria } : {}),
          ...(contextIds.length ? { opportunity_ids: contextIds } : {}),
          history,
        },
        (event) => {
          if (event.event !== "progress") return;
          setProcessing((current) =>
            current
              ? {
                  ...current,
                  steps: current.steps.map((step) =>
                    step.id === event.stage
                      ? {
                          ...step,
                          status: event.status,
                          detail: event.detail || step.detail,
                        }
                      : step,
                  ),
                }
              : current,
          );
        },
        key,
      );
      if (response.interpretation)
        setCriteria(response.interpretation.criteria);
      setTurns((current) => [
        ...current,
        { id: crypto.randomUUID(), question: message, response },
      ]);
      if (response.state === "failed") {
        setError(response.error?.message || "پاسخ کامل نشد.");
        setText(message);
      } else {
        setText("");
        setEditing(false);
        retryKey.current = null;
      }
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "پاسخ دریافت نشد.");
      setText(message);
    } finally {
      setBusy(false);
      setProcessing(null);
    }
  };
  const manual = () => {
    const converted = fromCriteria(criteria);
    useStore.getState().begin(converted);
    router.push("/opportunities");
  };
  const save = async () => {
    const converted = fromCriteria(criteria);
    useStore.getState().begin(converted);
    if (!user)
      return openLogin({ type: "save-criteria", name: "شرایط دستیار" });
    try {
      await addProfile("شرایط دستیار", converted);
    } catch {
      /* store keeps the input and reports the server failure */
    }
  };
  const compare = () => {
    if (items.length >= 2) {
      setCompare(items.slice(0, 4).map((item) => item.id));
      router.push("/compare");
    }
  };
  return (
    <main className="focus-blur relative min-h-[calc(100dvh-5rem)] overflow-x-hidden bg-[#eef3f9]">
      <AlgoPattern
        className="pointer-events-none fixed inset-0 h-full w-full text-ink/[0.045]"
        fade="radial"
      />
      <div className="relative mx-auto min-h-[calc(100dvh-5rem)] max-w-6xl px-4 pb-56 pt-8 sm:px-6">
        {!turns.length && !processing && (
          <header className="mx-auto max-w-3xl pt-8 text-center">
            <div className="flex justify-center">
              <Orb />
            </div>
            <h1 className="mt-5 text-3xl font-black sm:text-4xl">
              شرایطتان را بگویید.
            </h1>
            <p className="mt-3 text-sm font-semibold text-muted-foreground">
              پروژه‌های مناسب را با درصد تطابق نشانتان می‌دهیم.
            </p>
            <div className="mt-8 flex flex-wrap justify-center gap-2">
              {examples.map((example) => (
                <Button
                  key={example}
                  type="button"
                  variant="plain"
                  onClick={() => {
                    setText(example);
                    void submit(example);
                  }}
                  className="h-auto rounded-full border border-border bg-white px-4 py-2 text-xs font-bold"
                >
                  {example}
                </Button>
              ))}
            </div>
          </header>
        )}
        <section aria-live="polite" className="space-y-7">
          <AnimatePresence>
            {processing && (
              <Processing
                question={processing.question}
                steps={processing.steps}
              />
            )}
          </AnimatePresence>
          {turns.map((turn) => (
            <motion.article
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              key={turn.id}
              className="space-y-5"
            >
              <div className="flex justify-end">
                <p className="max-w-2xl rounded-[1.4rem] rounded-tr-md bg-teal-800 px-6 py-3 text-sm font-bold leading-7 text-white">
                  {turn.question}
                </p>
              </div>
              <CompletedSteps steps={turn.response.steps} />
              {turn.response.interpretation && (
                <div className="mx-auto max-w-4xl rounded-[1.7rem] bg-white p-5 shadow-sm">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h2 className="flex items-center gap-2 text-sm font-black">
                      <TickCircle size={18} className="text-primary" />
                      برداشت من از درخواست شما
                    </h2>
                    <Button
                      type="button"
                      variant="plain"
                      size="auto"
                      onClick={() => {
                        setText(turn.question);
                        setEditing(true);
                      }}
                      className="rounded-full px-3 text-xs font-bold"
                    >
                      <Edit2 size={15} />
                      تغییر درخواست
                    </Button>
                  </div>
                  <div className="mt-4">
                    <Chips
                      criteria={
                        turn.id === turns.at(-1)?.id
                          ? criteria
                          : turn.response.interpretation.criteria
                      }
                      onRemove={(key) =>
                        setCriteria((current) => {
                          const next = { ...current };
                          delete next[key];
                          return next;
                        })
                      }
                    />
                  </div>
                </div>
              )}
              <div className="mx-auto flex max-w-4xl flex-row-reverse items-start gap-3">
                <Orb />
                <div className="min-w-0 flex-1 rounded-[1.4rem] rounded-tl-md bg-white px-5 py-4 text-sm font-semibold leading-8 shadow-sm">
                  {turn.response.answer ||
                    turn.response.error?.message ||
                    "نتایج سرور آماده است."}
                  {turn.response.state === "failed" && (
                    <p className="mt-3 rounded-xl bg-amber-50 p-3 text-xs text-amber-900">
                      موفقیت ثبت نشده است. متن و شرط‌ها در همین مرورگر محفوظ
                      مانده‌اند.
                    </p>
                  )}
                </div>
              </div>
              {!!turn.response.server_result?.items?.length && (
                <>
                  <motion.div
                    initial="hidden"
                    animate="show"
                    variants={{
                      show: { transition: { staggerChildren: 0.07 } },
                    }}
                    className="mx-auto grid w-full max-w-[924px] gap-4 lg:translate-x-[26px] md:grid-cols-3"
                  >
                    {turn.response.server_result.items
                      .slice(0, 3)
                      .map((item, index) => (
                        <motion.div
                          variants={{
                            hidden: { opacity: 0, y: 10 },
                            show: { opacity: 1, y: 0 },
                          }}
                          key={item.id}
                        >
                          <ResultCard item={item} index={index} />
                        </motion.div>
                      ))}
                  </motion.div>
                  <div className="mx-auto max-w-[924px] space-y-2.5 lg:translate-x-[26px]">
                    {turn.response.server_result.items
                      .slice(3)
                      .map((item, index) => (
                        <CompactResult
                          key={item.id}
                          item={item}
                          index={index + 3}
                        />
                      ))}
                  </div>
                </>
              )}
              <div className="mx-auto flex max-w-4xl flex-wrap justify-center gap-2">
                <Button
                  type="button"
                  onClick={manual}
                  disabled={!criteria.route}
                  className="rounded-full px-5 font-extrabold"
                >
                  دقیق‌تر کردن با فیلترها
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={save}
                  disabled={!criteria.route}
                  className="rounded-full px-5 font-extrabold"
                >
                  <Save2 size={17} />
                  ذخیره شرایط
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={compare}
                  disabled={items.length < 2}
                  className="rounded-full px-5 font-extrabold"
                >
                  <Chart size={17} />
                  مقایسه ۳ پیشنهاد اول
                </Button>
              </div>
            </motion.article>
          ))}
          <div ref={end} />
        </section>
        {error && (
          <div
            role="alert"
            className="mx-auto mt-5 flex max-w-3xl flex-wrap items-center justify-center gap-3 text-sm font-bold text-destructive"
          >
            <span>{error}</span>
            <Button
              type="button"
              variant="outline"
              onClick={() => void submit()}
              disabled={busy}
              className="rounded-full px-4"
            >
              تلاش دوباره با همان رسید
            </Button>
          </div>
        )}
      </div>
      <div className="pointer-events-none fixed inset-x-0 bottom-0 z-20 bg-gradient-to-t from-[#eef3f9] via-[#eef3f9]/95 to-transparent px-4 pb-4 pt-16">
        <div
          className="pointer-events-auto mx-auto mb-3 flex max-w-[766px] flex-nowrap justify-start gap-2 overflow-x-auto pb-1 sm:flex-wrap sm:justify-center"
          aria-label="پیشنهادهای سریع"
        >
          {examples.slice(1).map((example) => (
            <button
              key={example}
              type="button"
              onClick={() => {
                setText(example);
                void submit(example);
              }}
              className="rounded-full border border-border bg-white px-4 py-2 text-[11px] font-bold shadow-sm"
            >
              {example}
            </button>
          ))}
        </div>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            void submit();
          }}
          aria-busy={busy}
          className="pointer-events-auto mx-auto flex min-h-[68px] max-w-[766px] items-end gap-2 rounded-[2rem] border border-border bg-white p-2 pr-4 shadow-[0_24px_65px_-30px_rgb(22_32_48/0.45)]"
        >
          {user && (
            <SavedPicker
              onPick={(value) => {
                setCriteria(value);
                setEditing(true);
              }}
            />
          )}
          <Textarea
            value={text}
            onChange={(event) => setText(event.target.value)}
            aria-label="شرایط شما برای دستیار"
            placeholder={
              editing
                ? "متن یا شرط‌ها را اصلاح کنید"
                : "شرط تازه‌ای دارید؟ بنویسید..."
            }
            rows={1}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                void submit();
              }
            }}
            className="field-sizing-content max-h-28 min-h-11 flex-1 resize-none border-0 !bg-transparent px-1 py-2 text-sm shadow-none focus-visible:ring-0"
          />
          <Button
            type="submit"
            aria-label={busy ? "در حال بررسی" : "ارسال برای بررسی"}
            disabled={!text.trim() || busy}
            className="grid size-11 shrink-0 place-items-center rounded-full p-0"
          >
            <Send2 size={19} variant="Bold" />
          </Button>
        </form>
        <p className="mt-2 text-center text-[10px] font-semibold text-muted-foreground">
          برای فرستادن Enter و برای خط تازه Shift+Enter
        </p>
      </div>
    </main>
  );
}
