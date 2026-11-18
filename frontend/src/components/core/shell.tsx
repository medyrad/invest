'use client';
import {useAuth} from '@/components/auth/login-dialog';
import {Header,Footer} from '@/components/site/header';
import Link from 'next/link';
import {AlgoField} from '@/components/brand/algo-field';
import '@/components/workspace/workspace.css';
export function Private({children}:{children:React.ReactNode}) { const {account,ready,start}=useAuth(); return account ? <div key={account.id}>{children}</div> : <section className="workspace-section"><h1>ورود و ادامه</h1><p>برای مشاهده اطلاعات خصوصی حساب خود وارد شوید.</p><button disabled={!ready} onClick={()=>void start()}>ورود و ادامه</button></section>; }
export default function CoreShell({children}:{children:React.ReactNode}) {return <><Header/><main className="workspace-page min-h-[65vh]"><AlgoField className="text-ink/[0.04]"/><div className="workspace-container"><nav className="flex flex-wrap gap-4 mb-7 text-sm font-bold"><Link href="/opportunities">فرصت‌ها</Link><Link href="/drafts">ثبت فرصت</Link><Link href="/workspace">فضای مالک</Link><Link href="/requests">درخواست‌ها</Link><Link href="/saved">منتخب‌ها</Link><Link href="/profile">پروفایل و اعلان‌ها</Link><Link href="/library">کتابخانه</Link></nav>{children}</div></main><Footer/></>}
