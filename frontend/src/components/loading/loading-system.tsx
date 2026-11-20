"use client";

import dynamic from "next/dynamic";
import { useReducedMotion } from "motion/react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const DotLottie = dynamic(
  () => import("./local-lottie"),
  { ssr: false, loading: () => <LoaderFallback /> },
);

function LoaderFallback() {
  return (
    <svg viewBox="0 0 80 80" className="size-full" aria-hidden="true">
      <circle cx="40" cy="40" r="25" fill="none" stroke="currentColor" strokeOpacity=".14" strokeWidth="8" />
      <path d="M40 15a25 25 0 0 1 25 25" fill="none" stroke="currentColor" strokeWidth="8" strokeLinecap="round" />
    </svg>
  );
}

export function MeaningfulLoader({ label, className }: { label: string; className?: string }) {
  const reduced = useReducedMotion();
  return (
    <div data-meaningful-loader role="status" aria-live="polite" aria-busy="true" className={cn("grid place-items-center gap-3 text-center", className)}>
      <span className="relative block size-28 text-primary-ink" aria-hidden="true">
        {reduced ? <LoaderFallback /> : <DotLottie />}
      </span>
      <span className="text-sm font-bold text-ink/75">{label}</span>
      <noscript><span className="text-xs text-muted-foreground">برای ادامه، JavaScript مرورگر را فعال کنید.</span></noscript>
    </div>
  );
}

export function Skeleton({ className }: { className?: string }) {
  return <span aria-hidden="true" className={cn("loading-skeleton block rounded-2xl", className)} />;
}

export function MapSkeleton() {
  return (
    <div data-loading="home-map" role="status" aria-label="در حال دریافت نقشه فرصت‌های منتشرشده" aria-busy="true" className="mx-auto w-full max-w-[620px] px-3">
      <Skeleton className="aspect-[360/330] w-full rounded-[35%]" />
      <Skeleton className="mx-auto mt-3 h-3 w-56" />
    </div>
  );
}

function CardSkeleton() {
  return <div className="surface rounded-[1.75rem] p-4"><Skeleton className="aspect-[16/10] w-full" /><Skeleton className="mt-4 h-5 w-4/5" /><Skeleton className="mt-3 h-3 w-2/3" /><div className="mt-5 flex gap-2"><Skeleton className="h-9 flex-1 rounded-full" /><Skeleton className="size-9 rounded-full" /></div></div>;
}

export function HomeCatalogSkeleton() {
  return (
    <section data-loading="home-catalog" role="status" aria-label="در حال دریافت کاتالوگ و فرصت‌ها" aria-busy="true" className="mx-auto my-12 max-w-7xl px-4 sm:px-6">
      <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 3 }, (_, i) => <CardSkeleton key={i} />)}</div>
    </section>
  );
}

export function ResultsSkeleton() {
  return (
    <main data-loading="opportunities" role="status" aria-label="در حال دریافت فرصت‌های منتشرشده" aria-busy="true" className="mx-auto max-w-7xl px-4 py-10 sm:px-6">
      <Skeleton className="h-20 w-full rounded-3xl" />
      <div className="mt-8 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 6 }, (_, i) => <CardSkeleton key={i} />)}</div>
    </main>
  );
}

export function SavedSkeleton() {
  return (
    <section data-loading="saved" role="status" aria-label="در حال دریافت حساب و منتخب‌ها" aria-busy="true" className="mt-8">
      <Skeleton className="h-14 w-full max-w-2xl rounded-full" />
      <div className="mt-7 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">{Array.from({ length: 3 }, (_, i) => <CardSkeleton key={i} />)}</div>
    </section>
  );
}

export function ReportSkeleton({ label = "در حال ساخت پیش‌نمایش راهنما…" }: { label?: string }) {
  return (
    <div data-loading="report" className="surface min-h-[40rem] rounded-[2rem] p-8">
      <MeaningfulLoader label={label} className="min-h-72" />
      <Skeleton className="mt-4 h-8 w-2/3" /><Skeleton className="mt-5 h-4 w-full" /><Skeleton className="mt-3 h-4 w-5/6" />
    </div>
  );
}

export function LoadFailure({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <div role="alert" data-loading-error className="surface mx-auto my-10 max-w-3xl rounded-[2rem] p-8 text-center">
      <p className="font-bold leading-7 text-destructive">{message}</p>
      <Button type="button" onClick={onRetry} className="mt-5 rounded-full px-7">تلاش دوباره</Button>
    </div>
  );
}
