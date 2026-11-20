"use client";
import {useStore} from "@/lib/store";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { motion, useReducedMotion } from "motion/react";
import { ArrowLeft } from "@/components/iconsax";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Header } from "@/components/site/header";
import { AlgoPattern, NodeMark } from "@/components/brand/algo-pattern";
import { MapScene, ease } from "@/components/home/hero";
import { useHomeSelection } from "@/lib/catalog-context";
import { cn } from "@/lib/utils";
const samplePrompts = [
  "مسکونی در تهران تا ۳۰ میلیارد",
  "صندوق کم‌ریسک با سود ماهانه",
  "نیروگاه خورشیدی در یزد",
  "خرید ملک در شیراز",
  "اجاره دفتر در اصفهان",
  "مرمت خانه تاریخی در کاشان",
];
/* ───────── پوسته مشترک ───────── */
function Shell({ children, map }: { children: React.ReactNode; map: React.ReactNode }) {
  return (
    <section data-section="hero" className="focus-blur relative isolate overflow-hidden pb-6">
      <div aria-hidden className="absolute inset-0 -z-10 bg-[radial-gradient(45%_55%_at_88%_0%,rgb(59_110_180/0.07),transparent),linear-gradient(to_bottom,#ffffff,var(--background))]" />
      <AlgoPattern animated className="-top-10 right-0 -z-10 h-[30rem] w-[44rem] text-ink/[0.07]" fade="radial" />
      <Header />
      <div className="mx-auto grid min-h-[calc(100dvh-7rem)] max-w-7xl grid-cols-[1.05fr_1fr] items-center gap-12 px-8 pb-10 pt-10">
        <motion.div initial={{ opacity: 0, y: 28 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.9, ease }}>{children}</motion.div>
        {map}
      </div>
    </section>
  );
}

function Eyebrow({ children }: { children?: React.ReactNode }) {
  return <Badge variant="outline" className="gap-2.5 border-border bg-white/80 px-4 py-2 text-[13px] font-bold text-ink backdrop-blur"><NodeMark className="text-primary-ink" />{children ?? "مشاور سرمایه‌گذاری"}</Badge>;
}

const useGo = () => {
  const router = useRouter();
  const { begin: setCriteria } = useHomeSelection();
  return {
    ask: (q: string) => { if (q) sessionStorage.setItem("invest:assistant-draft", q); router.push("/assistant"); },
    browse: (c: Parameters<typeof setCriteria>[0] = {}) => { setCriteria({ route: "investor", groups: [], provinces: [], amount: null, filters: {}, ...c });useStore.getState().begin({route:"investor",groups:[],provinces:[],amount:null,filters:{},...c});  router.push("/opportunities"); },
  };
};

/* ───────── ایده ۱: قطب‌نما ───────── */

/** نمونه درخواست‌ها جای placeholder کلمه‌به‌کلمه نوشته می‌شوند تا بی‌شلوغی، راه شروع را نشان دهند. */
function TypingHint({ hidden }: { hidden: boolean }) {
  const reduce = useReducedMotion();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);
  const [i, setI] = useState(0); const [n, setN] = useState(0);
  const words = samplePrompts[i].split(" ");
  useEffect(() => {
    if (!mounted || reduce) return;
    const t = n < words.length ? setTimeout(() => setN(n + 1), 170) : setTimeout(() => { setN(0); setI((i + 1) % samplePrompts.length); }, 3200);
    return () => clearTimeout(t);
  }, [n, i, words.length, reduce, mounted]);
  if (hidden) return null;
  return <span aria-hidden className="pointer-events-none absolute inset-y-0 right-0 flex items-center text-[15px] text-muted-foreground">{mounted && reduce ? samplePrompts[0] : words.slice(0, n).join(" ")}<span className="ms-0.5 inline-block h-5 w-px animate-pulse bg-primary" /></span>;
}

function CompassRing() {
  const ticks = Array.from({ length: 72 });
  return (
    <div aria-hidden className="pointer-events-none absolute left-1/2 top-[47%] -z-10 aspect-square w-[112%] -translate-x-1/2 -translate-y-1/2">
      <motion.svg viewBox="0 0 200 200" className="absolute inset-0 size-full" animate={{ rotate: 360 }} transition={{ duration: 160, repeat: Infinity, ease: "linear" }}>
        {ticks.map((_, i) => <line key={i} x1="100" y1="3" x2="100" y2={i % 6 === 0 ? 8.5 : 6} transform={`rotate(${i * 5} 100 100)`} strokeWidth={i % 18 === 0 ? 0.7 : 0.35} className={i % 18 === 0 ? "stroke-ink/45" : "stroke-ink/15"} />)}
      </motion.svg>
      <svg viewBox="0 0 200 200" className="absolute inset-0 size-full">
        <circle cx="100" cy="100" r="96.5" fill="none" strokeWidth="0.35" className="stroke-ink/15" />
        <circle cx="100" cy="100" r="86" fill="none" strokeWidth="0.3" strokeDasharray="0.6 2.4" className="stroke-ink/25" />
      </svg>
      {[["شمال", "top-[1.5%] left-1/2 -translate-x-1/2"], ["جنوب", "bottom-[1.5%] left-1/2 -translate-x-1/2"], ["شرق", "right-[0.5%] top-1/2 -translate-y-1/2"], ["غرب", "left-[0.5%] top-1/2 -translate-y-1/2"]].map(([t, c]) => (
        <span key={t} className={cn("absolute rounded-full bg-background/90 px-1.5 text-[10px] font-extrabold text-ink/45", c)}>{t}</span>
      ))}
    </div>
  );
}

export function HeroCompass() {
  const { ask, browse } = useGo();
  const [prompt, setPrompt] = useState("");
  const [ready, setReady] = useState(false);
  useEffect(() => setReady(true), []);
  return (
    <Shell map={<div className="relative mx-auto w-full max-w-[600px] py-10"><CompassRing /><MapScene /></div>}>
      <Eyebrow />
      <h1 className="mt-7 text-[3.6rem] font-black leading-[1.3] tracking-tight text-ink">
        سرمایه‌تان را<br />به{" "}
        <span className="relative inline-block text-ink">
          سمت درست
          <svg aria-hidden viewBox="0 0 300 20" preserveAspectRatio="none" className="absolute -bottom-2 left-0 h-4 w-full">
            <motion.path d="M4 14 C 80 4, 200 4, 296 12" fill="none" strokeWidth="5" strokeLinecap="round" className="stroke-cobalt/70" initial={{ pathLength: 0 }} animate={{ pathLength: 1 }} transition={{ duration: 1.1, delay: 0.7, ease }} />
          </svg>
        </span>{" "}ببرید.
      </h1>
      <p className="mt-5 max-w-lg text-[17px] leading-9 text-ink/65">دسته و مکان را انتخاب کنید؛ تطبیق در مرحله بعد فعال می‌شود.</p>
      <form onSubmit={(e) => { e.preventDefault(); if (prompt.trim()) ask(prompt); }} className="surface mt-8 flex items-center gap-2 rounded-full p-2 pr-7 transition-shadow focus-within:shadow-[0_0_0_4px_rgb(0_173_171/0.12),0_24px_50px_-30px_rgb(22_32_48/0.3)]">
        <span className="relative min-w-0 flex-1">
          <Input value={prompt} onChange={(e) => setPrompt(e.target.value)} aria-label="شرایط شما برای دستیار" className="h-14 rounded-none border-0 !bg-transparent px-0 text-[15px] font-semibold text-ink shadow-none focus-visible:ring-0 md:text-[15px]" />
          <TypingHint hidden={!!prompt} />
        </span>
        <Button type="submit" variant="plain" size="auto" disabled={!ready || !prompt.trim()} className="group h-14 gap-2 rounded-full bg-primary px-7 font-extrabold text-white shadow-[0_18px_36px_-18px_var(--primary)] hover:bg-teal-700">پیشنهاد بگیرید<ArrowLeft size={20} className="transition-transform group-hover:-translate-x-1" /></Button>
      </form>
      <Button variant="plain" size="auto" onClick={() => browse()} className="group mt-4 gap-1.5 px-3 text-sm font-bold text-ink/60 hover:text-ink">مشاهده همه پروژه‌ها<ArrowLeft size={16} className="transition-transform group-hover:-translate-x-1" /></Button>
    </Shell>
  );
}
