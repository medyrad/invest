'use client';
import { useCallback, useEffect, useRef, useState } from 'react';
import { Direction } from 'radix-ui';
import LoginShell, { useAuth } from '@/components/auth/login-dialog';
import { Header } from '@/components/site/header';
import { AlgoField } from '@/components/brand/algo-field';
import { api, Failure, message } from './api';
import { active, FieldControl } from './field';
import { FilesPanel } from './files-panel';
import type { Application, Draft, Group, Province, Schema, Values } from './types';
import './workspace.css';

function PrivateWorkspace() {
  const { start } = useAuth();
  const [schema, setSchema] = useState<Schema | null>(null); const [drafts, setDrafts] = useState<Draft[]>([]); const [apps, setApps] = useState<Application[]>([]);
  const [groups, setGroups] = useState<Group[]>([]); const [provinces, setProvinces] = useState<Province[]>([]);
  const [selected, setSelected] = useState<Draft | null>(null); const [values, setValues] = useState<Values>({}); const [routes, setRoutes] = useState<string[]>([]); const [heritage, setHeritage] = useState(false);
  const [owner, setOwner] = useState('personal'); const [trash, setTrash] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState(''); const [notice, setNotice] = useState(''); const [errors, setErrors] = useState<Record<string, string>>({}); const [conflict, setConflict] = useState<Draft | null>(null);
  const loadVersion = useRef(0);
  const pending = useRef<{ path: string; body: object } | null>(null); const alive = useRef(true); const [orgOpen, setOrgOpen] = useState(false);
  const [editingApplication, setEditingApplication] = useState<Application | null>(null);
  const [details, setDetails] = useState<Record<string, string | boolean | null>>({ name: '', country: '', organization_type: '', registration: '', signatory: '', representative_name: '', scope: '', starts_on: '', ends_on: null, no_expiry: true });
  const load = useCallback(async () => {
    const version = ++loadVersion.current;
    const [d, o] = await Promise.all([api<{ drafts: Draft[] }>('drafts' + (trash ? '?trash=1' : '')), api<{ applications: Application[] }>('owners')]);
    if (alive.current && version === loadVersion.current) { setDrafts(d.drafts); setApps(o.applications); }
  }, [trash]);
  useEffect(() => { alive.current = true; void Promise.all([api<Schema>('schema'), fetch('/api/v1/catalog/taxonomy').then(r => r.json()), fetch('/api/v1/catalog/geography').then(r => r.json())]).then(([s, t, g]) => { if (alive.current) { setSchema(s); setGroups(t.groups); setProvinces(g.provinces); } }).catch(e => { if (alive.current) setError(message(e)); }); return () => { alive.current = false; }; }, []);
  useEffect(() => { void load().catch(e => { if (alive.current) setError(message(e)); }); }, [load]);
  function open(d: Draft) { setSelected(d); setValues(d.raw); setRoutes(d.routes); setHeritage(d.heritage_enabled); setConflict(null); setNotice(''); setError(''); }
  const refreshFiles = async () => { await load(); if (selected) { const d = await api<Draft>('drafts/' + selected.id); if (alive.current) setSelected(old => old?.id === d.id ? { ...old, files: d.files } : old); } };
  useEffect(() => { const timer = setInterval(() => { if (selected?.files.some(f => f.status === 'pending_check' && f.received) || apps.some(a => a.files.some(f => f.status === 'pending_check' && f.received))) void refreshFiles().catch(() => {}); }, 5000); return () => clearInterval(timer); });
  async function execute(path?: string, body?: object) {
    if (!pending.current && path && body) pending.current = { path, body };
    const p = pending.current; if (!p) return;
    setBusy(true); setError(''); setErrors({}); setNotice('');
    try {
      const d = await api<Draft>(p.path, p.body); pending.current = null;
      if (!alive.current) return;
      if (d.id && d.raw) { open(d); setNotice(`ذخیره شد — شناسه ${d.id} — نسخه ${d.version}`); }
      if (!(d.id && d.raw)) { setNotice('درخواست با رسید سرور ذخیره شد.'); setOrgOpen(false); setEditingApplication(null); }
      await load();
    } catch (e) {
      if (!alive.current) return;
      setError(message(e));
      if (e instanceof Failure) { pending.current = null; setErrors(e.fields); if (e.status === 409 && e.current) setConflict(e.current as Draft); }
    } finally { if (alive.current) setBusy(false); }
  }
  useEffect(() => {
    const protect = (event: BeforeUnloadEvent) => { if (selected && (JSON.stringify(values) !== JSON.stringify(selected.raw) || JSON.stringify(routes) !== JSON.stringify(selected.routes) || heritage !== selected.heritage_enabled || pending.current)) { event.preventDefault(); } };
    window.addEventListener('beforeunload', protect); return () => window.removeEventListener('beforeunload', protect);
  }, [selected, values, routes, heritage]);
  function changeRoutes(next: string[], h = heritage) {
    if (!window.confirm('اطلاعات فیلدهای غیرفعال خصوصی حفظ می‌شوند و در نتیجه مؤثر نیستند؛ با بازگشت مسیر بازیابی می‌شوند. ادامه می‌دهید؟')) return;
    setRoutes(next); setHeritage(h);
  }
  const disabled = busy || !!pending.current;
  return <main className="workspace-page"><AlgoField className="text-ink/[0.04]" /><div className="workspace-container"><div className="workspace-heading"><div><p>فضای خصوصی مالک · ورود آزمایشی</p><h1>پیش‌نویس‌های من</h1></div><button disabled={disabled} onClick={() => { setTrash(t => !t); setSelected(null); }}>{trash ? 'پیش‌نویس‌های فعال' : 'سطل حذف'}</button></div>
    <p>پیش‌نویس، ارسال رسمی یا تأیید فرصت نیست. در این محیط فقط دادهٔ مصنوعی ثبت کنید.</p>
    {error && <div role="alert" className="workspace-error">{error}<button onClick={() => void start()}>ورود دوباره</button></div>}{notice && <p role="status" className="workspace-notice">{notice}</p>}
    {pending.current && <p role="status">نتیجه نامعلوم است؛ ورودی عملیات ثابت مانده است. <button disabled={busy} onClick={() => void execute()}>دریافت نتیجه همان عملیات</button></p>}
    {conflict && <section className="workspace-section"><h2>تعارض نسخه</h2><p>نسخه سرور: {conflict.version}؛ ورودی فعلی شما حفظ شده است.</p><pre>{JSON.stringify(conflict.raw, null, 2)}</pre><button onClick={() => { setSelected(conflict); setConflict(null); setNotice('نسخه سرور بازبینی شد؛ ورودی خود را بررسی و سپس ذخیره کنید.'); }}>حفظ ورودی من با نسخهٔ بازبینی‌شده</button><button onClick={() => open(conflict)}>بارگیری دادهٔ سرور</button></section>}
    {!selected && <><section className="workspace-section"><h2>پروژه تازه</h2><label>مالک<select aria-label="مالک" value={owner} onChange={e => setOwner(e.target.value)}><option value="personal">مالک فردی — خودم</option>{apps.map(a => <option key={a.id} value={a.id}>{String(a.details.name)} — {a.active ? 'اختیار فعال' : 'درخواست خودم، تأییدنشده'}</option>)}</select></label><p>صندوق و فروش در این مرحله هنوز قابل ثبت نیستند؛ اطلاعات پروژه با انتخاب آن‌ها حذف نمی‌شود.</p><button disabled={disabled || trash} onClick={() => void execute('drafts', { key: crypto.randomUUID(), kind: 'project', schema_version: 1, owner: owner === 'personal' ? { kind: 'personal' } : { kind: 'organization', request_id: owner } })}>ایجاد پیش‌نویس پروژه</button><button onClick={() => { setEditingApplication(null); setOrgOpen(x => !x); }}>درخواست نمایندگی سازمان</button></section>
      {orgOpen && <section className="workspace-section"><h2>مشخصات درخواست نمایندگی</h2><p>ثبت درخواست، اختیار سازمانی یا احراز نمایندگی ایجاد نمی‌کند؛ مدارک ثبت رسمی، اختیار امضا و معرفی‌نامه را جداگانه بارگذاری کنید.</p><div className="workspace-grid">{Object.entries({ name: 'نام رسمی', country: 'کشور', organization_type: 'نوع سازمان', registration: 'شناسه ثبت', signatory: 'اختیار امضای جاری', representative_name: 'نام نماینده', scope: 'حدود اختیار', starts_on: 'شروع اعتبار (میلادی)' }).map(([k, l]) => <label key={k}>{l}<input type={k === 'starts_on' ? 'date' : 'text'} value={String(details[k] || '')} onChange={e => setDetails(d => ({ ...d, [k]: e.target.value }))} /></label>)}<label className="workspace-check"><input type="checkbox" checked={!!details.no_expiry} onChange={e => setDetails(d => ({ ...d, no_expiry: e.target.checked, ends_on: e.target.checked ? null : '' }))} />پایان اعتبار در مدرک درج نشده است</label>{!details.no_expiry && <label>پایان اعتبار<input type="date" onChange={e => setDetails(d => ({ ...d, ends_on: e.target.value }))} /></label>}</div><button disabled={disabled} onClick={() => void execute(editingApplication ? `organizations/${editingApplication.id}` : 'organizations', { key: crypto.randomUUID(), ...(editingApplication ? { version: editingApplication.version } : {}), details })}>ذخیره درخواست</button></section>}
      {apps.map(a => <details className="workspace-section" key={a.id}><summary>{String(a.details.name)} — {a.active ? 'اختیار فعال' : 'تأییدنشده'}</summary><p>وضعیت درخواست: {a.status}</p>{a.status !== 'approved' && <button onClick={() => { setDetails(a.details); setEditingApplication(a); setOrgOpen(true); window.scrollTo({ top: 0, behavior: 'smooth' }); }}>تکمیل مشخصات درخواست</button>}<FilesPanel targetType="request" targetId={a.id} files={a.files} reload={load} /></details>)}
      <section className="workspace-section"><h2>{trash ? 'پیش‌نویس‌های حذف‌شده' : 'ادامه پیش‌نویس'}</h2>{drafts.length === 0 && <p>هنوز موردی در این فهرست نیست.</p>}<ul>{drafts.map(d => <li key={d.id}><strong>{String(d.raw.title || 'پروژه بدون عنوان')}</strong><p>{d.owner_label} · نسخه {d.version}</p>{trash ? <button disabled={disabled} onClick={() => void execute(`drafts/${d.id}/restore`, { key: crypto.randomUUID(), version: d.version })}>بازیابی پیش‌نویس</button> : <button onClick={() => open(d)}>ادامه ویرایش</button>}</li>)}</ul></section></>}
    {selected && schema && <><div className="workspace-section"><h2>{String(selected.raw.title || 'پروژه بدون عنوان')}</h2><p>{selected.owner_label} · نسخه {selected.version}</p><button disabled={disabled} onClick={() => { if (window.confirm('ورودی ذخیره‌نشده کنار گذاشته شود؟')) setSelected(null); }}>بازگشت به فهرست</button><button disabled={disabled} onClick={() => { if (window.confirm('پیش‌نویس به سطل حذف منتقل شود؟')) void execute(`drafts/${selected.id}/delete`, { key: crypto.randomUUID(), version: selected.version }); }}>حذف پیش‌نویس</button></div>
      {!selected.deleted && <><fieldset className="workspace-section" disabled={disabled}><legend>مسیرهای پروژه</legend>{Object.entries(schema.routes).map(([k, l]) => <label className="workspace-check" key={k}><input type="checkbox" checked={routes.includes(k)} onChange={e => changeRoutes(e.target.checked ? [...routes, k] : routes.filter(x => x !== k))} />{l}</label>)}{routes.includes('heritage') && <label className="workspace-check"><input type="checkbox" checked={heritage} onChange={e => changeRoutes(routes, e.target.checked)} />ترتیبات اختصاصی مرمت و بهره‌برداری دارد</label>}</fieldset>
      <form onSubmit={e => { e.preventDefault(); const visible = Object.fromEntries(schema.fields.filter(f => active(f, routes, heritage, values)).map(f => [f.key, values[f.key] ?? null])); void execute(`drafts/${selected.id}`, { key: crypto.randomUUID(), version: selected.version, routes, heritage_enabled: heritage, values: visible }); }}>
        <fieldset disabled={disabled} className="workspace-form">{Object.entries({ general: 'مشخصات عمومی و موقعیت', money: 'مبلغ و زمان', terms: 'شرایط همکاری', rights: 'حقوق و اسناد' }).map(([section, label]) => <section className="workspace-section" key={section}><h2>{label}</h2><div className="workspace-grid">{schema.fields.filter(f => f.section === section && active(f, routes, heritage, values)).map(f => {
          const province = provinces.find(p => p.id === values.province); const county = province?.counties.find(c => c.id === values.county); const group = groups.find(g => g.id === values.group);
          const options = f.key === 'province' ? provinces : f.key === 'county' ? province?.counties || [] : f.key === 'city' ? county?.cities || [] : f.key === 'group' ? groups : f.key === 'subtype' ? (group?.subtypes || []).map(s => ({ ...s, id: `${group?.id}.${s.id}` })) : undefined;
          return <FieldControl key={f.key} field={f} value={values[f.key]} options={options} error={Object.entries(errors).find(([k]) => k === f.key || k.startsWith(f.key + '.'))?.[1]} change={v => setValues(old => ({ ...old, [f.key]: v, ...(f.key === 'province' ? { county: null, city: null } : f.key === 'county' ? { city: null } : f.key === 'group' ? { subtype: null } : {}) }))} />;
        })}</div></section>)}</fieldset><div className="workspace-save"><button type="submit" disabled={disabled}>ذخیره پیش‌نویس</button><span>ذخیره صریح با رسید سرور؛ انتشار انجام نمی‌شود.</span></div>
      </form><section className="workspace-section"><h2>نقص‌های اطلاعات ذخیره‌شده</h2><p>این فهرست فقط راهنمای تکمیل است؛ آمادگی ارسال رسمی را تأیید نمی‌کند.</p><p>{selected.missing.map(k => schema.fields.find(f => f.key === k)?.label || k).join('، ') || 'فیلد اجباری خالی در مجموعه جاری نیست.'}</p><p>فیلدهای خصوصی غیرفعال: {selected.inactive.map(k => schema.fields.find(f => f.key === k)?.label).join('، ') || 'ندارد'}</p></section><FilesPanel key={selected.id} targetType="draft" targetId={selected.id} files={selected.files} reload={refreshFiles} /></>}
    </>}
  </div></main>;
}
function Content() {
  const { account, ready, start } = useAuth();
  const [retainedAccount, setRetainedAccount] = useState<string | null>(null);
  useEffect(() => { if (account) setRetainedAccount(account.id); }, [account]);
  return <><Header />{retainedAccount && (!account || account.id === retainedAccount) && <div hidden={!account}><PrivateWorkspace key={retainedAccount} /></div>}{!account && <main className="workspace-container"><h1>پیش‌نویس‌های من</h1><p>برای دسترسی خصوصی وارد شوید. ورودی همین حساب تا باز بودن این صفحه فقط در حافظه می‌ماند؛ با ورود حساب دیگر پاک می‌شود.</p><button disabled={!ready} onClick={() => void start()}>ورود و ادامه</button></main>}</>;
}
export default function Workspace() { return <Direction.Provider dir="rtl"><LoginShell><Content /></LoginShell></Direction.Provider>; }
