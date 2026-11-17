'use client';
import { useRef, useState } from 'react';
import { api, message } from './api';
import type { FileRow } from './types';
export function FilesPanel({ targetType, targetId, files, reload }: { targetType: string; targetId: string; files: FileRow[]; reload: () => Promise<void> }) {
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false); const [kind, setKind] = useState('document'); const [replace, setReplace] = useState('');
  const pending = useRef<{ file: File; body: object; id?: string } | null>(null);
  async function upload() {
    if (!pending.current) return;
    setBusy(true); setError('');
    try {
      const p = pending.current;
      if (!p.id) p.id = (await api<FileRow>('files/reserve', p.body)).id;
      const csrf = await (await fetch('/api/v1/auth/csrf', { cache: 'no-store' })).json();
      const response = await fetch(`/api/v1/workspace/files/${p.id}/content`, { method: 'PUT', headers: { 'Content-Type': 'application/octet-stream', 'X-CSRFToken': csrf.csrfToken }, body: p.file, signal: AbortSignal.timeout(35000) });
      if (!response.ok) { const r = await response.json(); throw new Error(r.error?.message || 'دریافت فایل انجام نشد.'); }
      pending.current = null; await reload();
    } catch (e) { setError(message(e)); } finally { setBusy(false); }
  }
  return <section className="workspace-section"><h3>فایل‌های خصوصی</h3><p>تا پایان بررسی، دریافت ممکن نیست. مدرک PDF/JPEG/PNG تا۲۰MiB؛ تصویر JPEG/PNG/WebP تا۱۰MiB.</p>
    <label>نوع فایل<select aria-label="نوع فایل" value={kind} onChange={e => setKind(e.target.value)}><option value="document">مدرک / راهنمای خصوصی</option>{targetType === 'draft' && <option value="image">تصویر معرفی</option>}</select></label>
    <label>جایگزینی<select aria-label="جایگزینی" value={replace} onChange={e => setReplace(e.target.value)}><option value="">فایل تازه</option>{files.filter(f => f.attached && !f.deleted && f.kind === kind).map(f => <option key={f.id} value={f.id}>{f.name}</option>)}</select></label>
    <label>انتخاب فایل<input type="file" disabled={busy || !!pending.current} accept={kind === 'image' ? '.jpg,.jpeg,.png,.webp' : '.pdf,.jpg,.jpeg,.png'} onChange={async e => {
      const file = e.target.files?.[0]; if (!file) return;
      if (file.size > (kind === 'image' ? 10 : 20) * 1048576) { setError('فایل بیش از سقف مجاز است.'); return; }
      const hash = [...new Uint8Array(await crypto.subtle.digest('SHA-256', await file.arrayBuffer()))].map(x => x.toString(16).padStart(2, '0')).join('');
      pending.current = { file, body: { key: crypto.randomUUID(), target_type: targetType, target_id: targetId, kind, name: file.name, size: file.size, sha256: hash, replaces: replace || null } }; await upload();
    }} /></label>
    {pending.current && <button disabled={busy} onClick={() => void upload()}>تلاش دوباره همان دریافت</button>}{error && <p role="alert" className="workspace-error">{error}</p>}
    <ul>{files.map(f => <li key={f.id}><strong>{f.name}</strong> — {{ pending_check: 'در انتظار بررسی', clean: 'بررسی موفق', rejected: 'ردشده', quarantined: 'قرنطینه' }[f.status] || f.status}{f.deleted ? ' — حذف‌شده' : ''}{f.replaced ? ' — جایگزین‌شده' : ''}<p>{f.reason}</p>
      {f.status === 'clean' && f.attached && !f.deleted && <a href={`/api/v1/workspace/files/${f.id}/download`}>دریافت خصوصی</a>}
      {f.status === 'pending_check' && f.received && !f.deleted && <button disabled={busy} onClick={async () => { try { await api(`files/${f.id}/retry`, {}); await reload(); } catch (e) { setError(message(e)); } }}>بررسی دوباره</button>}
      {!f.replaced && <button disabled={busy} onClick={async () => { setBusy(true); try { await api(`files/${f.id}/${f.deleted ? 'restore' : 'delete'}`, {}); await reload(); } catch (e) { setError(message(e)); } finally { setBusy(false); } }}>{f.deleted ? 'بازیابی فایل' : 'حذف فایل'}</button>}
    </li>)}</ul>
  </section>;
}
