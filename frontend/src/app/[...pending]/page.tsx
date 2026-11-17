import Link from 'next/link';
import { notFound } from 'next/navigation';
const stages: Record<string, [string, string]> = {opportunities:['پروژه‌ها و جزئیات','S06'],assistant:['دستیار متصل','S09'],saved:['ذخیره و فضای شخصی','S07'],compare:['مقایسه','S07'],tools:['خدمات تخصصی و راهنما','S07/S08']};
export default async function Pending({params}: {params: Promise<{pending:string[]}>}) {
  const { pending } = await params; const entry=stages[pending[0]]; if(!entry)notFound();
  return <main className="mx-auto max-w-3xl px-6 py-24"><h1 className="text-3xl font-black">{entry[0]}</h1><p className="mt-6 leading-8">این مقصد در نسخه آزمایشی فعلی فعال نیست؛ وابسته به مرحله {entry[1]} است. هیچ ذخیره، ارسال، تطبیق یا پرداختی انجام نشده است.</p><Link href="/" className="mt-8 inline-block rounded-full bg-primary px-6 py-3 text-white">بازگشت به خانه</Link></main>;
}
