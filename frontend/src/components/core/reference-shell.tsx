'use client';
import {createContext,useContext,useEffect,useState,useRef} from 'react';
import {useStore,toCriteria,fromCriteria} from '@/lib/store';
import {core} from '@/lib/core-api';
import {listings} from '@/lib/listings';
import {toListing, type PublicOpportunity} from '@/lib/public-values';
import {acceptRanking} from '@/lib/match';
import {usePathname} from 'next/navigation';
import {Header} from '@/components/site/header';
import Link from 'next/link';
import {documents,configureGeography} from '@/lib/public-values';
const Tick=createContext(0);export const usePublicTick=()=>useContext(Tick);
type Feed={items:PublicOpportunity[];next:string|null;criteria:Record<string,unknown>};
function Data({children,id}:{children:React.ReactNode;id?:string}){
 const c=useStore(s=>s.criteria),profiles=useStore(s=>s.profiles);const [ready,setReady]=useState(false),[error,setError]=useState(''),[tick,setTick]=useState(0);const path=usePathname();const initialURL=useRef(false);


 useEffect(()=>{let active=true;setError('');
 async function feed(criteria:Record<string,unknown>){let next:string|null=null;const all:PublicOpportunity[]=[];do{const q=new URLSearchParams({criteria:JSON.stringify(criteria),...(next?{cursor:next}:{})});const r:Feed=await core<Feed>('opportunities?'+q.toString());all.push(...r.items);next=r.next;}while(next&&active);return all;}
 async function load(){
 const geography=await fetch('/api/v1/catalog/geography',{cache:'no-store'}).then(r=>{if(!r.ok)throw Error('دریافت موقعیت‌ها انجام نشد.');return r.json()});configureGeography(geography);
 if(!initialURL.current){const params=new URLSearchParams(window.location.search);if(path==='/opportunities'&&params.has('criteria')){let raw;try{raw=JSON.parse(params.get('criteria')!)}catch{throw Error('پیوند جست‌وجو معتبر نیست.')}const checked=await core<Feed>('opportunities?criteria='+encodeURIComponent(JSON.stringify(raw)));if(active){initialURL.current=true;useStore.getState().setCriteria(fromCriteria(checked.criteria));}return;}if(path==='/compare'&&params.has('ids')){const ids=params.get('ids')!.split(',');await core('compare',{ids});if(!active)return;initialURL.current=true;useStore.getState().setCompare(ids)}else initialURL.current=true;}
 const base=await feed({});if(id&&!base.some(p=>p.id===id)){const one=await core<PublicOpportunity>('opportunities/'+id);base.push(one)}
 const ranked=await feed(toCriteria(c));if(!active)return;
 listings.splice(0,listings.length,...base.map(toListing));
 const maps=new Map(listings.map(l=>[l.id,l]));for(const p of ranked)documents.set(p.id,p);acceptRanking(c,ranked.map(p=>({listing:maps.get(p.id)||toListing(p),score:p.matching?.score===null?NaN:Number(p.matching?.score),reasons:p.matching?.checks.map(x=>({label:x.reason,status:x.state}))||[]})));
 for(const p of profiles){const ranked=await feed(toCriteria(p.criteria));if(!active)return;acceptRanking(p.criteria,ranked.map(p=>({listing:maps.get(p.id)||toListing(p),score:p.matching?.score===null?NaN:Number(p.matching?.score),reasons:p.matching?.checks.map(x=>({label:x.reason,status:x.state}))||[]})))}
 if(active){setReady(true);setTick(t=>t+1)}
 }
 void load().catch(e=>{if(active){setReady(false);setError(e.message)}});return()=>{active=false};
 },[c,id,path,profiles]);
 return <Tick.Provider value={tick}>{error?<><Header/><p role="alert" className="m-10">{error} <Link href="/opportunities">بازگشت به فرصت‌ها</Link></p></>:ready?children:<><Header/><p role="status" className="m-10">در حال دریافت داده معتبر سرور…</p></>}</Tick.Provider>
}
export default function ReferenceShell({children,id}:{children:React.ReactNode;id?:string}){return <><Data id={id}>{children}</Data></>}
