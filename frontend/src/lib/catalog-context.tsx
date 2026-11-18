'use client';
import { createContext, useContext, useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { MotionConfig } from 'motion/react';
import {useStore} from "@/lib/store";
import {toListing,configureGeography} from '@/lib/public-values';
import type { Listing, ProjectGroup, SearchCriteria } from '@/types';

type City = { id: string; name: string };
type County = City & { cities: City[] };
type Province = City & { counties: County[] };
type Data = { groups: ProjectGroup[]; provinces: Province[]; listings: Listing[]; previewEnabled: boolean };
const empty: Data = { groups: [], provinces: [], listings: [], previewEnabled: false };
const initial: SearchCriteria = { route: 'investor', groups: [], provinces: [], amount: null, filters: {} };
const Context = createContext<null | (Data & {
  status: string; reload: () => Promise<void>; criteria: SearchCriteria;
  begin: (value: Partial<SearchCriteria>) => void;
  group: string; subtype: string; province: string; county: string; city: string;
  chooseSubtypeInGroup: (group: string, subtype: string) => void;
  chooseGroup: (v: string) => void; chooseSubtype: (v: string) => void;
  chooseProvince: (v: string) => void; chooseCounty: (v: string) => void; chooseCity: (v: string) => void; clear: () => void;
})>(null);
export function CatalogProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState(empty);
  const [status, setStatus] = useState('loading');
  const [criteria, setCriteria] = useState(initial);
  const [group, setGroup] = useState(''); const [subtype, setSubtype] = useState('');
  const [province, setProvince] = useState(''); const [county, setCounty] = useState(''); const [city, setCity] = useState('');
  const revision = useRef(0);
  const reload = useCallback(async () => {
    const id = ++revision.current; setStatus('loading');
    try {
      const [tax, geo, preview] = await Promise.all(['taxonomy', 'geography', 'published'].map(async name => {
        const response = await fetch(name === 'published' ? '/api/v1/core/opportunities' : '/api/v1/catalog/' + name, { cache: 'no-store', signal: AbortSignal.timeout(10000) });
        if (!response.ok) throw new Error('catalog unavailable');
        return response.json();
      }));
      if (id !== revision.current) return;
      if (!Array.isArray(tax.groups) || !Array.isArray(geo.provinces) || !Array.isArray(preview.items)) throw new Error('invalid catalog');
      configureGeography(geo);
      setData({ groups: tax.groups, provinces: geo.provinces, listings: preview.items.map(toListing), previewEnabled: preview.items.some((x:{synthetic:boolean})=>x.synthetic) });
      setStatus(tax.groups.length && geo.provinces.length ? 'ready' : 'empty');
    } catch { if (id === revision.current) { setData(empty); setStatus('error'); } }
  }, []);
  useEffect(() => { void reload(); return () => { ++revision.current; }; }, [reload]);
  const chooseGroup = (v: string) => { setGroup(data.groups.some(g => g.id === v) ? v : ''); setSubtype(''); };
  const chooseProvince = (v: string) => { setProvince(data.provinces.some(p => p.id === v) ? v : ''); setCounty(''); setCity(''); };
  const chooseCounty = (v: string) => { setCounty(data.provinces.find(p => p.id === province)?.counties.some(c => c.id === v) ? v : ''); setCity(''); };
  const chooseSubtype = (v: string) => setSubtype(data.groups.find(g => g.id === group)?.subtypes.some(s => s.id === v) ? v : '');
  const chooseCity = (v: string) => setCity(data.provinces.find(p => p.id === province)?.counties.find(c => c.id === county)?.cities.some(c => c.id === v) ? v : '');
  return <Context.Provider value={{ ...data, status, reload, criteria, begin: value => {setCriteria(c => ({ ...c, ...value }));useStore.getState().begin(value)}, group, subtype, province, county, city, chooseGroup, chooseSubtype, chooseProvince, chooseCounty, chooseCity, chooseSubtypeInGroup: (g, s) => { if (data.groups.find(x => x.id === g)?.subtypes.some(x => x.id === s)) { setGroup(g); setSubtype(s); } }, clear: () => { setGroup(''); setSubtype(''); setProvince(''); setCounty(''); setCity(''); } }}><MotionConfig reducedMotion="user">{children}</MotionConfig></Context.Provider>;
}
export function useCatalog() { const value = useContext(Context); if (!value) throw new Error('CatalogProvider required'); return value; }
export const useHomeSelection = useCatalog;
