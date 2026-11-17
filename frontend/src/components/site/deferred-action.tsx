'use client';
import Link from 'next/link';
import { ArchiveAdd, Convertshape2 } from '@/components/iconsax';
export function DeferredAction({ kind }: { kind: 'saved' | 'compare' }) {
  const I = kind === 'saved' ? ArchiveAdd : Convertshape2;
  return <Link href={'/' + kind} aria-label={kind === 'saved' ? 'ذخیره پروژه — وابسته به S07' : 'مقایسه — وابسته به S07'} className="inline-flex size-10 items-center justify-center rounded-full bg-teal-900/50 text-white backdrop-blur-sm hover:bg-teal-800/75"><I size={20} /></Link>;
}
