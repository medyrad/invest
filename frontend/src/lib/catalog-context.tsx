'use client';
import { createContext, useContext, useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { MotionConfig } from 'motion/react';
import {useStore} from "@/lib/store";
import {toListing,configureGeography} from '@/lib/public-values';
import type { Listing, ProjectGroup, SearchCriteria } from '@/types';

type City = { id: string; name: string };
type County = City & { cities: City[] };
type Province = City & { counties: County[] };
type Data = { groups: ProjectGroup[]; provinces: Province[]; listings: Listing[]; hasSynthetic: boolean };
const empty: Data = { groups: [], provinces: [], listings: [], hasSynthetic: false };
const initial: SearchCriteria = { route: 'investor', groups: [], provinces: [], amount: null, filters: {} };
const Context = createContext<null | (Data & {
  status: 'loading' | 'ready' | 'empty' | 'error'; error: string; reload: () => Promise<void>; criteria: SearchCriteria;
  begin: (value: Partial<SearchCriteria>) => void;
  group: string; subtype: string; province: string; county: string; city: string;
  chooseSubtypeInGroup: (group: string, subtype: string) => void;
  chooseGroup: (v: string) => void; chooseSubtype: (v: string) => void;
  chooseProvince: (v: string) => void; chooseCounty: (v: string) => void; chooseCity: (v: string) => void; clear: () => void;
})>(null);
export function CatalogProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState(empty);
  const [status, setStatus] = useState<'loading' | 'ready' | 'empty' | 'error'>('loading');
  const [error, setError] = useState('');
  const [criteria, setCriteria] = useState(initial);
  const [group, setGroup] = useState(''); const [subtype, setSubtype] = useState('');
  const [province, setProvince] = useState(''); const [county, setCounty] = useState(''); const [city, setCity] = useState('');
  const revision = useRef(0);
  const reload = useCallback(async () => {
    const id = ++revision.current; setStatus('loading'); setError('');
    try {
      const [tax, geo, published] = await Promise.all(['taxonomy', 'geography', 'published'].map(async name => {
        const response = await fetch(name === 'published' ? '/api/v1/core/opportunities' : '/api/v1/catalog/' + name, { cache: 'no-store', signal: AbortSignal.timeout(10000) });
        if (!response.ok) throw new Error('دریافت داده معتبر سرور انجام نشد.');
        return response.json();
      }));
      if (id !== revision.current) return;
      if (!Array.isArray(tax.groups) || !Array.isArray(geo.provinces) || !Array.isArray(published.items)) throw new Error('پاسخ کاتالوگ معتبر نیست.');
      configureGeography(geo);
      setData({ groups: tax.groups, provinces: geo.provinces, listings: published.items.map(toListing), hasSynthetic: published.items.some((x:{synthetic:boolean})=>x.synthetic) });
      setStatus(tax.groups.length && geo.provinces.length ? 'ready' : 'empty');
    } catch (cause) { if (id === revision.current) { setData(empty); setError(cause instanceof Error ? cause.message : 'دریافت کاتالوگ انجام نشد.'); setStatus('error'); } }
  }, []);
  useEffect(() => { void reload(); return () => { ++revision.current; }; }, [reload]);
  const chooseGroup = (v: string) => { setGroup(data.groups.some(g => g.id === v) ? v : ''); setSubtype(''); };
  const chooseProvince = (v: string) => { setProvince(data.provinces.some(p => p.id === v) ? v : ''); setCounty(''); setCity(''); };
  const chooseCounty = (v: string) => { setCounty(data.provinces.find(p => p.id === province)?.counties.some(c => c.id === v) ? v : ''); setCity(''); };
  const chooseSubtype = (v: string) => setSubtype(data.groups.find(g => g.id === group)?.subtypes.some(s => s.id === v) ? v : '');
  const chooseCity = (v: string) => setCity(data.provinces.find(p => p.id === province)?.counties.find(c => c.id === county)?.cities.some(c => c.id === v) ? v : '');
  return <Context.Provider value={{ ...data, status, error, reload, criteria, begin: value => {setCriteria(c => ({ ...c, ...value }));useStore.getState().begin(value)}, group, subtype, province, county, city, chooseGroup, chooseSubtype, chooseProvince, chooseCounty, chooseCity, chooseSubtypeInGroup: (g, s) => { if (data.groups.find(x => x.id === g)?.subtypes.some(x => x.id === s)) { setGroup(g); setSubtype(s); } }, clear: () => { setGroup(''); setSubtype(''); setProvince(''); setCounty(''); setCity(''); } }}><MotionConfig reducedMotion="user">{children}</MotionConfig></Context.Provider>;
}
export function useCatalog() { const value = useContext(Context); if (!value) throw new Error('CatalogProvider required'); return value; }
export const useHomeSelection = useCatalog;
