'use client';
import {ProfessionalForm} from '@/components/core/profile';
import Link from 'next/link';
export type ToolSection={title:string;fields:string[];optional?:boolean};
export function LegacyTool({opener}:{opener:string;root:string;sections?:ToolSection[]}){return <p className="leading-8">{opener.includes('profile')?<ProfessionalForm/>:<Link href="/tools">این خدمت تخصصی در بسته S08 تحویل می‌شود؛ رفتن به معرفی خدمات ←</Link>}</p>}
