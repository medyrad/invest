'use client';

import Link from 'next/link';
import {useEffect,useMemo,useRef,useState} from 'react';
import {ArrowLeft,TickCircle} from '@/components/iconsax';
import {useAuth} from '@/components/auth/login-dialog';
import {MultiDrop} from '@/components/tools/multi-drop';
import {core} from '@/lib/core-api';
import {faNumber} from '@/lib/utils';
import {writeProProfile,useProProfileState} from '@/components/search/pro-profile';
import {provinces} from '@/data/provinces';
import {useStore} from '@/lib/store';
import CoreShell,{Private} from './shell';

type State={profile:Record<string,string>;notifications:{id:number;text:string;path:string;read:boolean}[];reports:{id:string;created_at:string;download:string;title:string}[]};

function Content(){
 const [state,setState]=useState<State|null>(null),[form,setForm]=useState<Record<string,string>>({}),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false);
 const basicAttempt=useRef<{payload:string;key:string}|null>(null);
 useEffect(()=>{let live=true;void core<State>('personal').then(s=>{if(live){setState(s);setForm(Object.fromEntries(Object.entries(s.profile).filter(([k])=>k!=='professional')))}}).catch(e=>{if(live)setError(e.message)});return()=>{live=false}},[]);
 async function save(){
  setBusy(true);setError('');setNotice('');const payload=JSON.stringify([form,state?.profile]);
  if(basicAttempt.current?.payload!==payload)basicAttempt.current={payload,key:crypto.randomUUID()};
  try{const s=await core<State>('personal',{key:basicAttempt.current.key,action:'profile',id:null,value:form,base:state?.profile});basicAttempt.current=null;setState(s);window.dispatchEvent(new Event('invest-profile'));setNotice('پروفایل اختیاری در حساب ذخیره شد.')}
  catch(e){setError(e instanceof Error?e.message:'ذخیره انجام نشد.')}
  finally{setBusy(false)}
 }
 return <>
  <h1>پروفایل و اعلان‌ها</h1><p>این اطلاعات اختیاری است؛ شغل یا تخصص، مجوز نقش ادمین/کارشناس ایجاد نمی‌کند.</p>
  {error&&<p role="alert" className="workspace-error">{error}</p>}<p role="status">{notice}</p>
  <form className="workspace-section" onSubmit={e=>{e.preventDefault();void save()}}>{Object.entries({name:'نام نمایشی',profession:'حوزه و نقش حرفه‌ای',experience:'سوابق و تجربه',interests:'علاقه‌مندی و تخصص',description:'شرح توان اجرایی و ظرفیت'}).map(([k,l])=><label key={k}>{l}<textarea value={form[k]||''} onChange={e=>{setNotice('');setForm(f=>({...f,[k]:e.target.value}))}}/></label>)}<button disabled={busy}>ذخیره پروفایل اختیاری</button></form>
  <section className="workspace-section"><h2>اطلاعات حرفه‌ای برای اعمال اختیاری در جست‌وجو</h2><ProfessionalForm/></section>
  <section className="workspace-section"><h2>اعلان‌های داخل سامانه</h2>{state?.notifications.map(n=><p key={n.id}><Link href={n.path}>{n.read?'':'● '}{n.text}</Link><button onClick={()=>{void core<State>('personal',{key:crypto.randomUUID(),action:'notification_read',id:n.id,value:null}).then(setState).catch(e=>setError(e.message))}}>خواندم</button></p>)}</section>
  <section className="workspace-section"><h2>گزارش‌های ذخیره‌شده</h2>{state?.reports.map(r=><p key={r.id}><a href={r.download}>دریافت {r.title||'گزارش ثبت‌شده'} · {new Date(r.created_at).toLocaleString('fa-IR')}</a></p>)}</section>
 </>;
}

const professionalRoles=[['investor','سرمایه‌گذار'],['builder','سازنده / توسعه‌گر'],['contractor','پیمانکار'],['manager','مدیر املاک استیجاری'],['consultant','مشاور / تسهیل‌گر']] as const;
const labels:Record<string,string>={name:'عنوان دلخواه پروفایل',entity:'نوع فعالیت',province:'استان',specialty:'حوزه تخصص و نوع پروژه',capacity:'ظرفیت و توان اجرایی قابل تخصیص',capital:'سرمایه قابل تخصیص این پروفایل، میلیارد تومان',certificate:'نوع گواهینامه یا مجوز',certificateNo:'شماره گواهینامه',issuer:'مرجع صادرکننده',expiry:'تاریخ اعتبار / انقضا، عین سند',validity:'وضعیت اعتبار طبق اعلام شما',references:'سوابق شاخص و تجربه مرتبط'};
const groups=[
 {title:'معرفی و نقش حرفه‌ای',keys:['name','entity','roles']},
 {title:'حوزه و توان اجرایی',keys:['province','specialty','capacity','capital']},
 {title:'گواهینامه یا صلاحیت مرتبط',keys:['certificate','certificateNo','issuer','expiry','validity'],optional:true},
 {title:'سوابق و تجربه',keys:['references']},
];
const required=['entity','roles'];

export function ProfessionalForm(){const identity=useStore(s=>s.user?.mobile);return <ProfessionalFields key={identity||'guest'}/>}

function ProfessionalFields(){
 const user=useStore(s=>s.user),{start}=useAuth();
 const [initialized,setInitialized]=useState(false),[values,setValues]=useState<Record<string,string>>({}),[roles,setRoles]=useState<string[]>([]),[error,setError]=useState(''),[notice,setNotice]=useState(''),[busy,setBusy]=useState(false);
 const {profile:professional,ready,error:loadError}=useProProfileState();
 const revision=useRef(0),dirty=useRef(false),base=useRef<typeof professional>(null),attempt=useRef<{payload:string;key:string}|null>(null),fieldRefs=useRef<Record<string,HTMLElement|null>>({});
 useEffect(()=>{if(ready&&!dirty.current){base.current=professional;setValues(Object.fromEntries(Object.entries(professional||{}).filter(([k,v])=>k!=='roles'&&(typeof v==='string'||typeof v==='number')).map(([k,v])=>[k,String(v)])));setRoles(professional?.roles??[]);setInitialized(true)}},[professional,ready]);
 const answered=(key:string)=>key==='roles'?roles.length>0:Boolean(values[key]);
 const done=required.filter(answered).length,percent=Math.round(done*100/required.length),next=required.find(k=>!answered(k));
 const change=()=>{revision.current++;dirty.current=true;setNotice('');setError('')};
 const jump=(key:string)=>{const el=fieldRefs.current[key];el?.scrollIntoView({block:'center',behavior:'smooth'});window.setTimeout(()=>el?.querySelector<HTMLElement>('input,select,textarea,button,[role=combobox]')?.focus({preventScroll:true}),350)};
 const save=async()=>{
  if(!user){setNotice('برای ذخیره سروری وارد شوید؛ ورودی فرم تا زمانی که این صفحه باز است حفظ می‌شود.');await start();return}
  if(!values.entity||!roles.length){setError('نوع فعالیت و دست‌کم یک نقش حرفه‌ای را انتخاب کنید.');jump(!values.entity?'entity':'roles');return}
  const submitted=revision.current;setBusy(true);setError('');setNotice('');
  try{const next={...values,roles},payload=JSON.stringify(next);if(attempt.current?.payload!==payload)attempt.current={payload,key:crypto.randomUUID()};await writeProProfile(next,base.current,attempt.current.key);base.current=next;attempt.current=null;dirty.current=revision.current!==submitted;setNotice('اطلاعات حرفه‌ای چندنقشی با رسید سرور ذخیره شد.')}
  catch(e){setError(e instanceof Error?e.message:'ذخیره انجام نشد.')}
  finally{setBusy(false)}
 };
 const options:Record<string,[string,string][]>=useMemo(()=>({
  entity:[['','انتخاب کنید'],['company','شخص حقوقی'],['individual','شخص حقیقی']],
  province:[['all','سراسر کشور'],...provinces.map(p=>[p,p] as [string,string])],
  validity:[['unknown','بررسی نشده'],['reported','معتبر طبق اعلام من، استعلام نشده'],['expired','منقضی یا نیازمند تمدید'],['none','فعلاً گواهینامه مرتبط ندارم']],
 }),[]);
 const inputClass='mt-2 block min-h-12 w-full min-w-0 rounded-2xl border border-border bg-white px-4 py-3 text-sm font-semibold text-ink outline-none focus:ring-2 focus:ring-primary';
 const download=()=>{
  const esc=(s:unknown)=>String(s??'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
  const choice=(key:string,value:string)=>options[key]?.find(x=>x[0]===value)?.[1]||value||'مشخص نشده';
  const rows=[['عنوان پروفایل',values.name||'پروفایل بدون نام'],['نوع فعالیت',choice('entity',values.entity)],['نقش‌ها',roles.map(r=>professionalRoles.find(x=>x[0]===r)?.[1]||r).join('، ')||'مشخص نشده'],['محدوده فعالیت',choice('province',values.province||'all')],['حوزه تخصص',values.specialty||'مشخص نشده'],['ظرفیت اعلامی',values.capacity||'مشخص نشده'],['سرمایه این پروفایل',values.capital?values.capital+' میلیارد تومان':'مشخص نشده'],['نوع و شماره گواهینامه',[values.certificate,values.certificateNo].filter(Boolean).join(' / ')||'مشخص نشده'],['مرجع صادرکننده',values.issuer||'مشخص نشده'],['تاریخ اعتبار اعلامی',values.expiry||'مشخص نشده'],['وضعیت اعتبار، استعلام نشده',choice('validity',values.validity||'unknown')],['سوابق',values.references||'ثبت نشده']];
  const html='<!doctype html><html lang="fa" dir="rtl"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>خلاصه پروفایل حرفه‌ای</title><style>*{box-sizing:border-box}body{max-width:860px;margin:32px auto;padding:28px;font:14px/2 Vazirmatn,Tahoma,Arial;color:#083b37;background:#f3f5f5}.sheet{background:white;border:1px solid #e4e9e8;border-radius:28px;overflow:hidden}header{padding:30px 38px;background:linear-gradient(135deg,#fff 55%,#eef6f4);border-top:4px solid #00adab}main{padding:18px 38px 32px}h1{margin:0;color:#083b37}p{color:#667473}dl{display:grid;grid-template-columns:1fr 1fr;gap:10px}dl div{border:1px solid #e4e9e8;border-radius:14px;padding:10px 14px}dt{font-size:12px;color:#667473}dd{margin:0;font-weight:800}@media(max-width:600px){body{margin:0;padding:0}.sheet{border-radius:0}header,main{padding-inline:22px}dl{grid-template-columns:1fr}}</style></head><body><div class="sheet"><header><p>پروفایل حرفه‌ای</p><h1>'+esc(values.name||'پروفایل حرفه‌ای من')+'</h1></header><main><p>این اطلاعات خوداظهاری است و مجوز یا اختیار حساب ایجاد نمی‌کند.</p><dl>'+rows.map(([k,v])=>'<div><dt>'+esc(k)+'</dt><dd>'+esc(v)+'</dd></div>').join('')+'</dl></main></div></body></html>';
  const url=URL.createObjectURL(new Blob([html],{type:'text/html;charset=utf-8'})),a=document.createElement('a');a.href=url;a.download='invest-professional-profile.html';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
 };
 if(!initialized)return <p role={loadError?'alert':'status'}>{loadError||'در حال دریافت اطلاعات حرفه‌ای…'}</p>;
 return <form className="professional-form space-y-6" onChange={change} onSubmit={e=>{e.preventDefault();void save()}}>
  <header className="space-y-5"><p className="text-xs font-extrabold text-primary-ink">از شناخت فرصت تا آمادگی ورود</p><h2 className="text-2xl font-black leading-relaxed text-ink">پرونده فرصت و خدمات تکمیلی</h2><p className="text-sm leading-7 text-muted-foreground">شرایط فراخوان، مدیریت اجاره و مشخصات حرفه‌ای خود را یکجا بررسی کنید. این ابزار به سامانه‌های رسمی متصل نیست و درخواست یا پیشنهاد رسمی ثبت نمی‌کند.</p><h3 className="border-r-4 border-primary pr-3 text-base font-extrabold text-ink">پروفایل حرفه‌ای سرمایه‌گذار یا سازنده</h3><p className="text-sm leading-7 text-muted-foreground">اطلاعات ثابت خود را به‌صورت اختیاری ثبت کنید. این پروفایل جایگزین ثبت‌نام یا احراز صلاحیت رسمی نیست.</p><p className="rounded-2xl bg-[#edf2f7] p-5 text-sm leading-7 text-muted-foreground">ذخیره فقط پس از تأیید سرور انجام می‌شود. ذخیره و دریافت فایل به معنی ارسال به دستگاه اجرایی یا تأیید صلاحیت نیست.</p></header>
  <div className="professional-progress sticky top-24 z-20 rounded-[1.5rem] border border-border bg-white/95 p-4 shadow-[0_18px_40px_-30px_rgb(22_32_48/0.45)] backdrop-blur">
   <div className="flex items-center gap-4"><span className="grid size-12 shrink-0 place-items-center rounded-full bg-ink/[0.06] text-[13px] font-black text-primary-ink">{faNumber(percent)}٪</span><div className="min-w-0 flex-1"><p className="text-sm font-extrabold text-ink">{faNumber(done)} از {faNumber(required.length)} پرسش ضروری پاسخ داده شده</p><p className="mt-0.5 text-xs font-semibold text-muted-foreground">{done===required.length?'می‌توانید اطلاعات را ذخیره کنید.':faNumber(required.length-done)+' پرسش مانده تا ادامه'}</p><div className="mt-2.5 h-1.5 overflow-hidden rounded-full bg-muted"><div className="h-full rounded-full bg-primary" style={{width:percent+'%'}}/></div></div>{next&&<button type="button" onClick={()=>jump(next)} className="inline-flex min-h-10 shrink-0 items-center gap-1.5 rounded-full border border-border bg-white px-4 text-[13px] font-extrabold">پرسش بعدی بی‌پاسخ<ArrowLeft size={15}/></button>}</div>
   <nav className="mt-3 flex flex-wrap gap-1.5 border-t border-border/70 pt-3" aria-label="بخش‌های پروفایل">{groups.map(g=>{const list=g.keys.filter(k=>required.includes(k)),complete=list.length>0&&list.every(answered);return <button key={g.title} type="button" onClick={()=>jump(g.keys[0])} className="flex min-h-8 items-center gap-1.5 rounded-full border border-border bg-white px-3 py-1 text-[12px] font-bold text-ink/70">{complete&&<TickCircle size={14} variant="Bold"/>}{g.title}<span className="text-[11px] text-muted-foreground">{list.length?(complete?'کامل':faNumber(list.filter(answered).length)+' از '+faNumber(list.length)):'اختیاری'}</span></button>})}</nav>
  </div>
  <fieldset disabled={!ready||busy} className="space-y-0">
   <legend className="sr-only">اطلاعات حرفه‌ای</legend>
   {groups.map((g,i)=>{const mandatory=g.keys.filter(k=>required.includes(k)),left=mandatory.filter(k=>!answered(k)).length;return <section key={g.title} className={(i?'border-t border-border pt-6 ':'')+'scroll-mt-48 pb-6'}>
    <header className="mb-5 flex min-h-7 items-center gap-3"><h4 className="text-base font-extrabold text-ink">{g.title}</h4>{g.optional&&<span className="rounded-full bg-muted px-2.5 py-0.5 text-[11px] font-bold text-muted-foreground">اختیاری</span>}{mandatory.length>0&&<span className="mr-auto rounded-full border border-border px-2.5 py-0.5 text-[11px] font-bold text-muted-foreground">{left?faNumber(left)+' پرسش مانده':'کامل'}</span>}</header>
    <div className="grid grid-cols-1 items-start gap-x-5 gap-y-5 sm:grid-cols-2">{g.keys.map(k=>k==='roles'?<div key={k} ref={el=>{fieldRefs.current[k]=el}} className="min-w-0 sm:col-span-2"><label className="mb-2 block text-sm font-bold text-ink">نقش‌های حرفه‌ای شما <span className="text-destructive" aria-label="ضروری">*</span></label><MultiDrop items={professionalRoles.map(([key,title])=>({key,title,checked:roles.includes(key),disabled:false}))} onToggle={key=>{change();setRoles(old=>old.includes(key)?old.filter(x=>x!==key):[...old,key])}}/></div>:<label key={k} ref={el=>{fieldRefs.current[k]=el}} className={(k==='references'?'sm:col-span-2 ':'')+'min-w-0 text-sm font-bold text-ink'}>{labels[k]}{required.includes(k)&&<span className="text-destructive" aria-label="ضروری"> *</span>}
     {options[k]?<select aria-label={k==='entity'?'نوع فعالیت':undefined} className={inputClass} value={values[k]||(k==='province'?'all':k==='validity'?'unknown':'')} onChange={e=>setValues(v=>({...v,[k]:e.target.value}))}>{options[k].map(([value,label])=><option key={value} value={value}>{label}</option>)}</select>:k==='references'?<textarea className={inputClass+' min-h-24'} value={values[k]||''} onChange={e=>setValues(v=>({...v,[k]:e.target.value}))}/>:<input aria-label={k==='name'?'نام':undefined} className={inputClass} inputMode={k==='capital'?'decimal':undefined} value={values[k]||''} onChange={e=>setValues(v=>({...v,[k]:k==='capital'?e.target.value.replace(/[^\d.۰-۹]/g,'').replace(/[۰-۹]/g,d=>String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))):e.target.value}))}/>} {k==='name'&&<small className="mt-1 block font-normal leading-6 text-muted-foreground">برای استفاده از راهنما نیازی به کد ملی، اطلاعات حساب بانکی یا بارگذاری مدارک نیست.</small>}{k==='capital'&&<small className="mt-1 block font-normal leading-6 text-muted-foreground">در سایر مسیرها خودکار جایگزین سرمایه یا بودجه پروژه نمی‌شود.</small>}</label>)}</div>
   </section>})}
  </fieldset>
  {loadError&&<p role="alert">{loadError}</p>}{error&&<p role="alert" className="rounded-2xl bg-red-50 p-4 text-sm text-red-800">{error}</p>}{notice&&<p role="status" className="text-sm text-teal-800">{notice}</p>}
  <div className="flex flex-wrap gap-3 border-t border-border pt-5"><button className="min-h-12 rounded-full bg-primary px-6 text-sm font-extrabold text-white disabled:opacity-50" disabled={busy||!ready}>{busy?'در حال ذخیره…':user?'ذخیره اطلاعات حرفه‌ای اختیاری':'ورود برای ذخیره اطلاعات حرفه‌ای'}</button><button className="min-h-12 rounded-full border border-border bg-white px-6 text-sm font-bold" type="button" onClick={download}>دریافت خلاصه خواندنی پروفایل</button></div>
  <p className="text-xs leading-6 text-muted-foreground">این تخصص‌ها خوداظهاری‌اند و هیچ نقش ادمین، کارشناس یا اختیار سازمانی ایجاد نمی‌کنند.</p>
 </form>;
}

export function ProfilePage(){return <CoreShell><Private><Content/></Private></CoreShell>}
