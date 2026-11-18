"use client";
import {useSyncExternalStore,useEffect,useState} from 'react';
import type {FilterValue,SavedProfile,SearchCriteria} from '@/types';
import {core} from './core-api';
import {toast} from './toast';
import {clearRanking} from './match';
import {geoNames} from './public-values';
export const emptyCriteria:SearchCriteria={route:'investor',groups:[],provinces:[],amount:null,filters:{}};
type Pending = { type: "save-listing"; id: string } | { type: "save-criteria"; name?: string } | null;

interface State {
  user: { mobile: string } | null;
  saved: string[];
  profiles: SavedProfile[];
  criteria: SearchCriteria;
  /** آیا کاربر گام «اطلاعات پایه» را در صفحه پروژه‌ها گذرانده است */
  started: boolean;
  /** پروژه‌های انتخاب‌شده برای مقایسه (حداکثر چهار) */
  compare: string[];
  toggleCompare: (id: string) => void;
  /** جایگزینی کامل فهرست مقایسه (مثلاً «مقایسه علاقه‌مندی‌ها») */
  setCompare: (ids: string[]) => void;
  clearCompare: () => void;
  /** پروژه‌هایی که از صفحه جزئیات («دیدن پروژه‌های پیشنهادی») به صفحه پروژه‌ها فرستاده شده‌اند، بالای نتایج سنجاق می‌شوند */
  pinned: { from: string; ids: string[] } | null;
  setPinned: (p: { from: string; ids: string[] } | null) => void;
  setStarted: (v: boolean) => void;
  /** شروع تازه از یک دسته اصلی یا گروه، گام اطلاعات پایه دوباره نمایش داده می‌شود */
  begin: (c: Partial<SearchCriteria>) => void;
  applyProfile: (id: string) => void;
  loginOpen: boolean;
  pending: Pending;
  setCriteria: (c: Partial<SearchCriteria>) => void;
  setFilter: (id: string, v: FilterValue) => void;
  resetFilters: () => void;
  openLogin: (pending?: Pending) => void;
  closeLogin: () => void;
  login: (mobile: string) => Pending;
  logout: () => void;
  toggleSaved: (id: string) => void;
  saveProfile: (name: string) => void;
  /** افزودن جست‌وجوی تازه از صفحه علاقه‌مندی‌ها، بدون دست زدن به فیلترهای فعلی */
  addProfile: (name: string, criteria: SearchCriteria) => void;
  removeProfile: (id: string) => void;
  updateProfile: (id: string, patch: { name?: string; criteria?: SearchCriteria }) => void;
  touchProfile: (id: string) => void;
}


const listeners=new Set<()=>void>();
let open:()=>void=()=>{};let close:()=>void=()=>{};let logout:()=>void=()=>{};let generation=0;
function set(p:Partial<State>){state={...state,...p};for(const fn of listeners)fn();}
const stateActions={
 setPinned:(pinned:State['pinned'])=>set({pinned}),toggleCompare:(id:string)=>set({compare:state.compare.includes(id)?state.compare.filter(x=>x!==id):state.compare.length<4?[...state.compare,id]:state.compare}),setCompare:(compare:string[])=>set({compare:[...new Set(compare)].slice(0,4)}),clearCompare:()=>set({compare:[]}),setStarted:(started:boolean)=>set({started}),begin:(c:Partial<SearchCriteria>)=>set({criteria:{...emptyCriteria,...c},started:true}),setCriteria:(c:Partial<SearchCriteria>)=>set({criteria:{...state.criteria,...c}}),setFilter:(id:string,v:FilterValue)=>{const filters={...state.criteria.filters};if(v===undefined||v===''||v===false||(Array.isArray(v)&&!v.length))delete filters[id];else filters[id]=v;set({criteria:{...state.criteria,filters}})},resetFilters:()=>set({criteria:{...emptyCriteria,route:state.criteria.route}}),openLogin:(pending:Pending=null)=>{set({pending});open()},closeLogin:()=>close(),login:()=>null,logout:()=>logout(),toggleSaved:(id:string)=>{if(!state.user)return open();void mutation('save',id,!state.saved.includes(id))},saveProfile:(name:string)=>{void state.addProfile(name,state.criteria)},addProfile:(name:string,c:SearchCriteria)=>{void mutation('search',null,{name,criteria:toCriteria(c)})},removeProfile:(id:string)=>{void mutation('search_delete',id,null)},updateProfile:(id:string,patch:{name?:string;criteria?:SearchCriteria})=>{const p=state.profiles.find(p=>p.id===id);if(p){void mutation('search_delete',id,null).then(()=>mutation('search',null,{name:patch.name||p.name,criteria:toCriteria(patch.criteria||p.criteria)}))}},touchProfile:(id:string)=>{void mutation('search_seen',id,null)},applyProfile:(id:string)=>{const p=state.profiles.find(p=>p.id===id);if(p){set({criteria:p.criteria,started:true});state.touchProfile(id)}}
};
let state:State={user:null,saved:[],profiles:[],criteria:emptyCriteria,started:true,loginOpen:false,pending:null,compare:[],pinned:null,...stateActions};
const initial=state;
export const useStore=Object.assign(function useStore<T=State>(selector:(s:State)=>T=((s:State)=>s as unknown as T)){const s=useSyncExternalStore(cb=>{listeners.add(cb);return()=>listeners.delete(cb)},()=>state,()=>initial);return selector(s)},{getState:()=>state});
export function useHydrated(){const [ready,setReady]=useState(false);useEffect(()=>setReady(true),[]);return ready;}
export type PersonalState={profile:Record<string,string>;saved:{id:string}[];searches:{id:string;name:string;criteria:Record<string,unknown>;last_seen:string}[]};
export async function refreshPersonal(){const g=generation;if(!state.user)return;const p=await core<PersonalState>('personal');if(g===generation)accept(p);}
function accept(p:PersonalState){set({saved:p.saved.map(x=>x.id),profiles:p.searches.map(s=>({id:s.id,name:s.name,criteria:fromCriteria(s.criteria),createdAt:s.last_seen,lastSeenAt:s.last_seen}))});}
async function mutation(action:string,id:string|null,value:unknown){const g=generation;try{const p=await core<PersonalState>('personal',{key:crypto.randomUUID(),action,id,value});if(g===generation){accept(p);toast('تغییر با رسید سرور ذخیره شد.')}}catch(e){if(g===generation)toast(e instanceof Error?e.message:'ذخیره انجام نشد.');return;}}
export function bindAccount(account:{id:string;mobile:string}|null,login:()=>void,leave:()=>void){generation++;const hadIdentity=!!state.user;if(state.user){clearRanking();set({criteria:emptyCriteria})}open=login;logout=leave;close=()=>{};set({user:account?{mobile:account.mobile}:null,saved:[],profiles:[],compare:hadIdentity?[]:state.compare,pending:null});if(account)void refreshPersonal().catch(e=>toast(e.message));}
export function toCriteria(c:SearchCriteria):Record<string,unknown>{
 const kind=c.route==='fund'?'fund':c.route==='buyer'?undefined:'project';const f=c.filters;const result:Record<string,unknown>={...(kind?{kind}:{}),route:c.route};if(typeof f._query==='string'&&f._query)result.q=f._query;if(typeof f._sort==='string')result.sort=f._sort;if(c.amount){const factor=c.route==='fund'?1000000:1000000000;result.budget_min=scaleDecimal(String(c.amount[0]),factor===1000000?6:9);result.budget_max=scaleDecimal(String(c.amount[1]),factor===1000000?6:9)}if(c.provinces.length)result.province=c.provinces;if(c.groups.length)result.group=c.groups;
 if(Array.isArray(f.cities)&&f.cities.length)result.city=f.cities;if(Array.isArray(f.counties)&&f.counties.length)result.county=f.counties;
 if(Array.isArray(f.risk)&&f.risk.length)result.risk=f.risk;
 if(Array.isArray(f._important))result.important=f._important;
 const preferences=Object.fromEntries(Object.entries(f).filter(([k,v])=>!k.startsWith('_')&&!['strictLocation','cities','counties'].includes(k)&&v!==undefined));if(Object.keys(preferences).length)result.preferences=preferences;return result;
}
export function fromCriteria(c:Record<string,unknown>):SearchCriteria{const factor=c.kind==='fund'?1e6:1e9;return {route:(c.route||'investor') as SearchCriteria['route'],groups:(c.group||[]) as string[],provinces:((c.province||[]) as string[]).map(x=>geoNames.get(x)||x),amount:c.budget_max?[Number(c.budget_min||0)/factor,Number(c.budget_max)/factor]:null,filters:{...((c.preferences||c.conditions||{}) as SearchCriteria['filters']),...(c.important?{_important:c.important as string[]}:{}),...(c.city?{cities:c.city as string[]}:{}),...(c.county?{counties:c.county as string[]}:{}),...(c.q?{_query:String(c.q)}:{}),...(c.sort?{_sort:String(c.sort)}:{})}};}

function scaleDecimal(value:string,places:number){const [whole,fraction='']=value.split('.');const joined=whole+fraction.padEnd(places,'0');const extra=fraction.length>places?fraction.slice(places):'';return extra?BigInt(joined.slice(0,joined.length-extra.length)).toString()+'.'+extra:BigInt(joined).toString();}

export function clearPrivateAccount(){if(!state.user)return;generation++;clearRanking();set({user:null,saved:[],profiles:[],compare:[],criteria:emptyCriteria,pending:null,pinned:null});}
