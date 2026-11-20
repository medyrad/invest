"use client";
import Image from "next/image";
import Link from "next/link";
import { useEffect, useMemo, useRef, useState } from "react";
import { AnimatePresence, motion, useReducedMotion } from "motion/react";
import { IranMap, cityXY } from "@/components/brand/iran-map";
import { useCatalog } from "@/lib/catalog-context";
import { cn } from "@/lib/utils";
import type { Listing } from "@/types";
import { MapSkeleton } from "@/components/loading/loading-system";
export function cityPoints(listings: Listing[]) {
  const m = new Map<string, { city: string; province: string; count: number }>();
  for (const l of listings) if (l.city && l.province) { const k = l.city; m.set(k, { city: k, province: l.province, count: (m.get(k)?.count ?? 0) + 1 }); }
  return [...m.values()];
}

export const ease = [0.22, 1, 0.36, 1] as const;

/* کارت پروژه‌های تازه روی نقشه */
const LIFE = 9000; // هر کارت کمتر از ۱۰ ثانیه می‌ماند
const EVERY = 3400;
type FeedItem = { key: number; id: string; born: number };

function useFeed(listings: Listing[]) {
  const reduce = useReducedMotion();
  // صف پروژه‌ها طوری چیده می‌شود که کارت‌های پشت‌سرهم از استان‌های متفاوت باشند
  const pool = useMemo(() => {
    const by = new Map<string, typeof listings>();
    for (const l of listings) if (l.city && l.province && cityXY(l.city)) by.set(l.province, [...(by.get(l.province) ?? []), l]);
    const cols = [...by.values()]; const out: typeof listings = [];
    for (let i = 0; cols.some((c) => c[i]); i++) for (const c of cols) if (c[i]) out.push(c[i]);
    return out;
  }, [listings]);
  const [items, setItems] = useState<FeedItem[]>([]);
  const cursor = useRef(0);
  useEffect(() => {
    if (reduce || !pool.length) return;
    const tick = () => setItems((prev) => {
      const now = Date.now();
      const alive = prev.filter((x) => now - x.born < LIFE);
      const taken = alive.map((x) => cityXY(pool.find((l) => l.id === x.id)!.city!)!);
      for (let n = 0; n < pool.length; n++) {
        const l = pool[(cursor.current + n) % pool.length]; const p = cityXY(l.city!)!;
        if (taken.every((t) => Math.hypot(t.x - p.x, t.y - p.y) > 95)) { cursor.current = (cursor.current + n + 1) % pool.length; return [...alive, { key: now, id: l.id, born: now }]; }
      }
      return alive;
    });
    const first = setTimeout(tick, 900);
    const t = setInterval(tick, EVERY);
    return () => { clearTimeout(first); clearInterval(t); };
  }, [pool, reduce]);
  const still = useMemo(() => {
    const result: FeedItem[] = [];
    for (const listing of pool) {
      const point = cityXY(listing.city!)!;
      if (result.every(item => { const other = cityXY(pool.find(x => x.id === item.id)!.city!)!; return Math.hypot(other.x - point.x, other.y - point.y) > 95; })) result.push({ key: -result.length - 1, id: listing.id, born: 0 });
      if (result.length === 2) break;
    }
    return result;
  }, [pool]);
  return reduce ? still : items;
}

/** نقشه هیرو. active استان‌های انتخاب‌شده را پررنگ می‌کند، focus به‌جای کارت‌های چرخان فقط یک پروژه را نشان می‌دهد. */
export function MapScene({ active = [], focus, caption = "تازه‌ترین پروژه‌ها از سراسر ایران" }: { active?: string[]; focus?: string; caption?: string }) {
  const { listings, hasSynthetic, status } = useCatalog();
  const points = useMemo(() => cityPoints(listings), [listings]);
  const all = useFeed(listings);
  const feed = focus ? [] : all;
  const fl = focus ? listings.find((l) => l.id === focus) : null; const fp = fl?.city ? cityXY(fl.city) : null;
  if (status === "loading") return <MapSkeleton />;
  return (
    <motion.div initial={{ opacity: 0, scale: 0.94 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 1, delay: 0.15, ease }} data-map-scene className="relative mx-auto w-full max-w-[620px]">
      <IranMap points={points} active={active} labels={false} links={false}>
        {fp && <g key={focus}><circle cx={fp.x} cy={fp.y} r="6" className="fill-primary" /><circle cx={fp.x} cy={fp.y} r="6" className="fill-none stroke-primary" strokeWidth="1.2" style={{ transformOrigin: `${fp.x}px ${fp.y}px`, animation: "pulse-node 1.8s ease-out infinite" }} /></g>}
        {feed.map((f) => { const l = listings.find((x) => x.id === f.id)!; const p = cityXY(l.city!)!;
          return <g key={f.key}><circle cx={p.x} cy={p.y} r="5" className="fill-primary" /><circle cx={p.x} cy={p.y} r="5" className="fill-none stroke-primary" strokeWidth="1" style={{ transformOrigin: `${p.x}px ${p.y}px`, animation: "pulse-node 1.8s ease-out infinite" }} /></g>; })}
      </IranMap>
      <AnimatePresence>
        {feed.map((f) => {
          const l = listings.find((x) => x.id === f.id)!; const p = cityXY(l.city!)!;
          const left = Math.min(74, Math.max(26, (p.x / 360) * 100)); const below = p.y < 95;
          return (
            <motion.div data-map-feed key={f.key} style={{ left: `${left}%`, top: `${(p.y / 330) * 100}%` }} className="absolute z-10"
              initial={{ opacity: 0, y: below ? -8 : 8, scale: 0.9 }} animate={{ opacity: 1, y: 0, scale: 1 }} exit={{ opacity: 0, scale: 0.92, transition: { duration: 0.35 } }} transition={{ duration: 0.5, ease }}>
              <Link href={`/opportunities/${l.id}`} className={cn("surface absolute right-1/2 flex w-60 translate-x-0 min-[501px]:translate-x-1/2 items-center gap-2.5 rounded-[1.25rem] p-2 pl-3 transition-shadow hover:shadow-xl", below ? "top-4" : "bottom-4")}>
                <span className="relative size-12 shrink-0 overflow-hidden rounded-xl"><Image src={l.image} alt="" fill sizes="48px" className="object-cover" /></span>
                <span className="min-w-0 flex-1">
                  <span className="flex items-center gap-1.5 text-[11px] font-extrabold text-primary-ink"><span className="size-1.5 rounded-full bg-primary" style={{ animation: "node-blink 1.4s ease-in-out infinite" }} />{l.province}، {l.city}</span>
                  <span className="mt-0.5 block truncate text-[13px] font-extrabold text-ink">{l.title}</span>
                  <span className="block truncate text-[11px] text-muted-foreground">{l.stats[0].label}: {l.stats[0].value}</span>
                </span>
              </Link>
            </motion.div>
          );
        })}
      </AnimatePresence>
      <p className="mt-1 text-center text-xs font-semibold text-muted-foreground">{listings.length ? caption + (hasSynthetic ? " — داده مصنوعی توسعه" : "") : "نقشه ایران؛ هنوز فرصت عمومی منتشرشده‌ای وجود ندارد"}</p>
    </motion.div>
  );
}
