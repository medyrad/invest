"use client";
// حالت چندعکسی پروژه: در کارت با حرکت نشانگر عکس عوض می‌شود، در صفحه جزئیات بندانگشتی‌ها و نمای بزرگ.
import { useEffect, useState } from "react";
import { useReducedMotion } from "motion/react";
const galleryOf = (l: Listing) => l.gallery ?? [{ src: l.image, caption: l.title }];
import type { Listing } from "@/types";
import { cn } from "@/lib/utils";

/** عکس‌های کارت: با هاور روی کارت، هر ۴ ثانیه عکس بعدی با محو شدن نرم می‌آید، نوار بالای عکس زمان را نشان می‌دهد */
const STEP = 4000;
export function useHoverGallery(l: Listing) {
  const pics = galleryOf(l);
  const reduce = useReducedMotion();
  const [i, setI] = useState(0);
  const [hover, setHover] = useState(false);
  useEffect(() => {
    if (reduce || !hover || pics.length < 2) return;
    const t = window.setInterval(() => setI((x) => (x + 1) % pics.length), STEP);
    return () => window.clearInterval(t);
  }, [hover, pics.length, reduce]);
  const bind = { onMouseEnter: () => setHover(true), onMouseLeave: () => { setHover(false); setI(0); } };
  const dots = pics.length > 1 ? (
    <span className={cn("pointer-events-none absolute inset-x-4 top-2.5 z-10 flex gap-1 transition-opacity duration-300", hover ? "opacity-100" : "opacity-0")} aria-hidden>
      {pics.map((_, k) => (
        <span key={k} className="h-[3px] flex-1 overflow-hidden rounded-full bg-white/35">
          <span key={`${k}-${i}-${hover}`} className={cn("block h-full rounded-full bg-white", k < i ? "w-full" : k === i && hover ? "animate-[fill-bar_4s_linear_forwards]" : "w-0")} />
        </span>
      ))}
    </span>
  ) : null;
  return { srcs: pics.map((p) => p.src), active: i, bind, dots, count: pics.length };
}

