'use client';
import type { Basis, Field, Numeric, RefOption, Value } from './types';
const states = [['known', 'معلوم'], ['unknown', 'نامعلوم'], ['not_applicable', 'نامربوط']];
export const unitLabels: Record<string, string> = { TOMAN: 'تومان', MILLION_TOMAN: 'میلیون تومان', BILLION_TOMAN: 'میلیارد تومان', MONTH: 'ماه', YEAR: 'سال', DAY: 'روز', SHARE_PERCENT: 'درصد سهم', PERCENT: 'درصد IRR', ITEM: 'عدد', KILOGRAM: 'کیلوگرم', SQUARE_METRE: 'مترمربع' };
export function active(f: Field, routes: string[], heritage: boolean, values: Record<string, Value>) {
  const participation = routes.includes('investor') || (routes.includes('heritage') && !heritage);
  const c: Record<string, boolean> = { always: true, participation, execution: participation || routes.includes('contractor'), duration: routes.some(r => ['investor', 'lessee', 'heritage'].includes(r)), rights: routes.some(r => ['buyer', 'lessee'].includes(r)), heritage: routes.includes('heritage') && heritage, heritage_years: routes.includes('heritage') && heritage && JSON.stringify(values.heritage_returns) !== '["fee"]' };
  return c[f.when] ?? routes.includes(f.when);
}
export function requiredForRoutes(f: Field, routes: string[]) { return f.required || (f.required_routes?.some(r => routes.includes(r)) ?? false); }
export function initialNumber(f: Field): Numeric { return { field: { namespace: 'invest.opportunity.project', key: f.key, version: f.version || 1 }, unit: { code: f.unit!, version: 1 }, status: 'known', source_value: '', basis: ['MONTH', 'YEAR', 'DAY'].includes(f.unit!) ? { start_basis: '' } : null }; }
export function FieldControl({ field: f, value, change, options, error, completionRequired = f.required }: { field: Field; value: Value | undefined; change: (v: Value) => void; options?: RefOption[]; error?: string; completionRequired?: boolean }) {
  const id = `field-${f.key}`;
  const title = <span className="workspace-label">{f.label}{completionRequired && <small> · برای تکمیل اطلاعات</small>}</span>;
  if (f.unit) {
    const n = value && typeof value === 'object' && !Array.isArray(value) ? value : initialNumber(f);
    const set = (patch: Partial<Numeric>) => change({ ...n, field: initialNumber(f).field, ...patch });
    const basis = n.basis || {};
    const setBasis = (patch: Partial<Basis>) => set({ basis: { ...basis, ...patch } });
    const units = f.unit_options ? Object.keys(f.unit_options) : f.kind === 'money' ? ['TOMAN', 'MILLION_TOMAN', 'BILLION_TOMAN'] : f.key === 'metric_quantity' ? ['ITEM', 'KILOGRAM', 'SQUARE_METRE'] : [f.unit];
    return <fieldset className="workspace-field"><legend>{title}</legend><div className="workspace-inline">
      <select aria-label={`${f.label} — وضعیت`} value={value ? n.status : ''} onChange={e => e.target.value ? set({ status: e.target.value, source_value: e.target.value === 'known' ? '' : null, basis: f.kind === 'return' ? null : n.basis }) : change(null)}><option value="">هنوز وارد نشده</option>{states.map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select>
      <select aria-label={`${f.label} — واحد`} value={n.unit.code} onChange={e => set({ unit: { code: e.target.value, version: 1 } })}>{units.map(u => <option key={u} value={u}>{f.unit_options?.[u] || unitLabels[u]}</option>)}</select>
      {n.status === 'known' && <input id={id} aria-label={f.label} inputMode="decimal" dir="ltr" value={n.source_value || ''} onChange={e => set({ source_value: e.target.value })} placeholder="مثلاً ۱٫۵" />}
    </div>
      {['MONTH', 'YEAR', 'DAY'].includes(f.unit) && <label>مبنای شروع مدت<input aria-label={`${f.label} — مبنای شروع`} value={basis.start_basis || ''} onChange={e => setBasis({ start_basis: e.target.value })} placeholder="مثلاً تحویل؛ اگر نامعلوم است unspecified" /></label>}
      {f.kind === 'return' && n.status === 'known' && <div className="workspace-basis"><p>IRR محاسبه یا تأیید نمی‌شود؛ مبنای کامل ادعای خود را وارد کنید.</p>
        <label>نوع نرخ<select value={basis.metric_type || ''} onChange={e => setBasis({ version: 1, metric_type: e.target.value })}><option value="">انتخاب کنید</option><option value="irr">IRR</option></select></label>
        {([['period', 'دوره', { annual: 'سالانه', monthly: 'ماهانه', total: 'کل' }], ['price_basis', 'مبنای قیمت', { nominal: 'اسمی', real: 'واقعی' }], ['scope', 'سطح', { project: 'پروژه', investor: 'سرمایه‌گذار' }], ['observation', 'ماهیت', { forecast: 'پیش‌بینی', observed: 'عملکرد', claimed: 'ادعایی' }]] as [keyof Basis, string, Record<string, string>][]).map(([key, label, opts]) => <label key={key}>{label}<select value={String(basis[key] || '')} onChange={e => setBasis({ [key]: e.target.value })}><option value="">انتخاب کنید</option>{Object.entries(opts).map(([k, l]) => <option key={k} value={k}>{l}</option>)}</select></label>)}
        <label>افق زمانی<input inputMode="decimal" value={basis.horizon?.value || ''} onChange={e => setBasis({ horizon: { value: e.target.value, unit: basis.horizon?.unit || { code: 'YEAR', version: 1 } } })} /></label>
        <label>واحد افق<select value={basis.horizon?.unit.code || 'YEAR'} onChange={e => setBasis({ horizon: { value: basis.horizon?.value || '', unit: { code: e.target.value, version: 1 } } })}>{['DAY', 'MONTH', 'YEAR'].map(u => <option key={u} value={u}>{f.unit_options?.[u] || unitLabels[u]}</option>)}</select></label>
        <label>تاریخ مبنا (میلادی)<input type="date" value={basis.basis_date || ''} onChange={e => setBasis({ basis_date: e.target.value })} /></label>
        <label>منبع ادعا<textarea value={basis.source || ''} onChange={e => setBasis({ source: e.target.value })} /></label>
      </div>}{error && <p className="workspace-error" role="alert">{error}</p>}</fieldset>;
  }
  const choices = options ? Object.fromEntries(options.map(o => [o.id, o.name])) : f.options;
  return <div className="workspace-field"><label htmlFor={id}>{title}</label>
    {f.kind === 'multi' && choices ? <fieldset id={id}><legend className="sr-only">{f.label}</legend>{Object.entries(choices).map(([k, l]) => <label className="workspace-check" key={k}><input type="checkbox" checked={Array.isArray(value) && value.includes(k)} onChange={e => { const old = Array.isArray(value) ? value : []; const next = e.target.checked ? [...old, k] : old.filter(x => x !== k); change(next.length ? next : null); }} />{l}</label>)}<select aria-label={`${f.label} — وضعیت`} value={typeof value === 'string' ? value : ''} onChange={e => change(e.target.value || null)}><option value="">گزینه‌های بالا</option><option value="unknown">نامعلوم</option><option value="not_applicable">نامربوط</option></select></fieldset>
      : choices ? <select id={id} aria-label={f.label} value={typeof value === 'string' ? value : ''} onChange={e => change(e.target.value || null)}><option value="">هنوز وارد نشده</option>{Object.entries(choices).map(([k, l]) => <option key={k} value={k}>{l}</option>)}<option value="unknown">نامعلوم</option><option value="not_applicable">نامربوط</option></select>
        : <><textarea id={id} aria-label={f.label} value={Array.isArray(value) ? value.join('\n') : typeof value === 'string' ? ({ unknown: 'نامعلوم', not_applicable: 'نامربوط' }[value] || value) : ''} maxLength={4000} onChange={e => change(e.target.value ? f.kind === 'lines' ? e.target.value.split('\n') : e.target.value : null)} rows={f.key === 'description' ? 4 : 2} /><div className="workspace-inline"><button type="button" onClick={() => change('unknown')}>نامعلوم</button><button type="button" onClick={() => change('not_applicable')}>نامربوط</button><button type="button" onClick={() => change(null)}>پاک‌کردن مقدار</button></div></>}
    {f.key === 'city' && options?.length === 0 && <p>فهرست شهرهای این شهرستان فعلاً در دسترس نیست؛ انتخاب شهرستان شما حفظ شده است.</p>}
    {error && <p className="workspace-error" role="alert">{error}</p>}
  </div>;
}
