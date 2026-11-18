'use client';

import {bindAccount,clearPrivateAccount} from '@/lib/store';
import { createContext, useContext, useCallback, useEffect, useRef, useState, type ReactNode, type RefObject } from 'react';
import Image from 'next/image';

type Account = { id: string; mobile: string; role: string };
type Receipt = { challenge_id: string; state: string; expires_at: string; resend_at: string; delivery: string; notification?: { code: string } };
type Reply = Receipt & { authenticated?: boolean; user?: Account; flow_token?: string; csrfToken?: string; recovered?: boolean; error?: { code: string; message: string }; retry_after?: number };
const messageOf = (error: unknown) => error instanceof Error && /[\u0600-\u06ff]/.test(error.message) ? error.message : 'پاسخ سرور دریافت نشد؛ وضعیت اتصال را بررسی و دوباره تلاش کنید.';
class PostFailure extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}
const fa = (s: string | number) => String(s).replace(/\d/g, d => '۰۱۲۳۴۵۶۷۸۹'[Number(d)]);
const en = (s: string) => s.replace(/[۰-۹]/g, d => String('۰۱۲۳۴۵۶۷۸۹'.indexOf(d))).replace(/[٠-٩]/g, d => String('٠١٢٣٤٥٦٧٨٩'.indexOf(d)));
const photos = ['office.jpg', 'towers.jpg', 'heritage.webp', 'construction.jpg', 'field.jpg'];
const perks = ['پروژه‌ها و جست‌وجوهایتان می‌مانند', 'اطلاعات را یک بار وارد می‌کنید', 'پروژه‌های تازه را زودتر می‌بینید'];

function Icon({ name, size = 24 }: { name: string; size?: number }) {
  return <span aria-hidden className="auth-icon" style={{ width: size, height: size, maskImage: `url(/icons/auth/${name}.svg)`, WebkitMaskImage: `url(/icons/auth/${name}.svg)` }} />;
}

export function Logo({ light = false }: { light?: boolean }) {
  return <span className={`brand ${light ? 'brand-light' : ''}`}><span className="brand-mark"><svg viewBox="150 60 800 380" fill="none" stroke="currentColor" strokeWidth="34" strokeLinecap="round" strokeLinejoin="round" aria-hidden><path d="M232 248C302 248 332 292 360 342C386 386 414 393 440 390C466 387 490 372 502 357L703 92V395M585 250H703M703 395C703 300 742 250 880 250" /></svg></span><span>سرمایه‌گزین</span></span>;
}

function Visual() {
  const [photo, setPhoto] = useState(0);
  useEffect(() => { const timer = setInterval(() => setPhoto(i => (i + 1) % photos.length), 5000); return () => clearInterval(timer); }, []);
  return <div className="login-visual">
    {photos.map((src, i) => <Image key={src} src={`/images/hero/${src}`} fill unoptimized sizes="400px" alt="" priority={i === 0} className={`visual-photo ${i === photo ? 'visible' : ''}`} />)}
    <div className="visual-base-shade" />
    <svg aria-hidden className="visual-pattern"><defs><pattern id="login-pattern" width="176" height="132" patternUnits="userSpaceOnUse" patternTransform="scale(.55)"><g fill="none" stroke="currentColor"><path d="M0 40H320M0 95H160M0 180H295M0 235H320M30 40V235M80 0V240M160 0V240M245 40V240M80 235L200 115A45 45 0 0 1 277 147V180M30 180A50 50 0 0 0 115 215L245 85A42 42 0 0 1 320 110M40 0A45 45 0 0 0 130 0" /></g><g fill="currentColor">{[[160,40],[30,95],[245,95],[160,180],[295,180],[80,235]].map(([cx,cy])=><circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="4" />)}</g><g fill="currentColor">{[[80,95],[160,95],[30,180],[80,180],[30,235],[245,235]].map(([cx,cy])=><circle key={`${cx}-${cy}`} cx={cx} cy={cy} r="2" />)}</g></pattern></defs><rect width="100%" height="100%" fill="url(#login-pattern)" /></svg>
    <div className="visual-shade" />
    <div className="visual-top"><Logo light /><span className="photo-dots">{photos.map((_, i) => <span key={i} className={i === photo ? 'active' : ''} />)}</span></div>
    <div className="visual-copy"><p className="visual-title">سرمایه‌گزین، فرصت‌های سرمایه‌گذاری ایران را یک‌جا جلوی شما می‌گذارد.</p><p className="visual-description">شرایط و بودجه‌تان را می‌گویید، پروژه‌های سرمایه‌گذاری، مشارکت و اجرای سراسر کشور با درصد تطابق و دلیلش پیشنهاد می‌شوند.</p><ul>{perks.map((text, i) => <li key={text}><span className="perk-icon"><Icon name={['ArchiveTick', 'UserEdit', 'Notification'][i]} size={18} /></span>{text}</li>)}</ul></div>
  </div>;
}

type AuthValue = { account: Account | null; busy: boolean; ready: boolean; notice: string; start: () => Promise<void>; logout: () => Promise<void>; activity: () => Promise<void>; triggerRef: RefObject<HTMLButtonElement | null> };
const AuthContext = createContext<AuthValue | null>(null);
export function useAuth() { const value = useContext(AuthContext); if (!value) throw new Error('Auth provider required'); return value; }
function AccountBridge(){const {account,start,logout}=useAuth();const actions=useRef({start,logout});actions.current={start,logout};useEffect(()=>{bindAccount(account,()=>void actions.current.start(),()=>void actions.current.logout());return()=>bindAccount(null,()=>{},()=>{})},[account?.id]);return null;}
export default function LoginShell({ children }: { children?: ReactNode }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const opener = useRef<HTMLButtonElement>(null);
  const mobileInput = useRef<HTMLInputElement>(null);
  const codeInput = useRef<HTMLInputElement>(null);
  const csrf = useRef('');
  const flow = useRef('');
  const issueKey = useRef('');
  const issuedMobile = useRef('');
  const issueInFlight = useRef(false);
  const meVersion = useRef(0);
  const authChannel = useRef<BroadcastChannel | null>(null);
  const [open, setOpen] = useState(false);
  const [mobile, setMobile] = useState('');
  const [code, setCode] = useState('');
  const [step, setStep] = useState<'mobile' | 'code'>('mobile');
  const [issueUncertain, setIssueUncertain] = useState(false);
  const [receipt, setReceipt] = useState<Receipt | null>(null);
  const [notice, setNotice] = useState('');
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [waitUntil, setWaitUntil] = useState(0);
  const [clock, setClock] = useState(0);
  const [account, setAccount] = useState<Account | null>(null);
  const [ready, setReady] = useState(false);

  const bootstrap = useCallback(async () => {
    const response = await fetch('/api/v1/auth/csrf', { cache: 'no-store', signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error('ارتباط با سرور برقرار نشد.');
    csrf.current = (await response.json()).csrfToken;
  }, []);
  const post = useCallback(async (action: string, body = {}, useFlow = true): Promise<Reply> => {
    await bootstrap();
    const response = await fetch(`/api/v1/auth/${action}`, { method: 'POST', cache: 'no-store', signal: AbortSignal.timeout(10000), headers: { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.current, ...(useFlow ? { 'X-Login-Flow': flow.current } : {}) }, body: JSON.stringify(body) });
    const result = await response.json();
    if (!response.ok) {
      if (result.retry_after) setWaitUntil(Date.now() + result.retry_after * 1000);
      throw new PostFailure(result.error?.message || 'ارتباط با سرور برقرار نشد.', response.status);
    }
    return result;
  }, [bootstrap]);
  const refresh = useCallback(async () => {
    const version = ++meVersion.current;
    const response = await fetch('/api/v1/auth/me', { cache: 'no-store', signal: AbortSignal.timeout(10000) });
    if (!response.ok) throw new Error('وضعیت ورود دریافت نشد.');
    const result = await response.json();
    if (version !== meVersion.current) return null;
    if(!result.authenticated)clearPrivateAccount();
    setAccount(result.authenticated ? result.user : null);
    return result.authenticated ? result.user as Account : null;
  }, []);
  useEffect(() => { refresh().catch(() => setNotice('ارتباط با سرور برقرار نشد؛ دوباره تلاش کنید.')).finally(() => setReady(true)); }, [refresh]);
  const clearIdentity = useCallback(() => { ++meVersion.current; clearPrivateAccount(); setAccount(null); }, []);
  useEffect(() => {
    const recheck = () => { void refresh().catch(clearIdentity); };
    const visible = () => { if (document.visibilityState === 'visible') recheck(); };
    const channel = typeof window.BroadcastChannel === 'function'
      ? new window.BroadcastChannel('invest-auth-events-v1') : null;
    authChannel.current = channel;
    if (channel) channel.onmessage = ({ data }) => {
      if (data?.type === 'session-invalidated') { clearIdentity(); recheck(); }
    };
    window.addEventListener('focus', recheck);
    document.addEventListener('visibilitychange', visible);
    window.addEventListener('pageshow', recheck);
    return () => {
      ++meVersion.current;
      window.removeEventListener('focus', recheck);
      document.removeEventListener('visibilitychange', visible);
      window.removeEventListener('pageshow', recheck);
      channel?.close();
      authChannel.current = null;
    };
  }, [refresh, clearIdentity]);
  useEffect(() => { if (!open) return; const timer = setInterval(() => setClock(Date.now()), 1000); return () => clearInterval(timer); }, [open]);
  useEffect(() => {
    if (!open) return;
    if (busy) { dialog.current?.focus(); return; }
    if (document.activeElement === dialog.current || !dialog.current?.contains(document.activeElement)) {
      if (step === 'code') codeInput.current?.focus(); else mobileInput.current?.focus();
    }
  }, [open, step, busy]);

  const start = async () => {
    setError(''); setNotice(''); setBusy(true);
    try {
      const result = await post('flows', {}, false);
      flow.current = result.flow_token!;
      issueKey.current = ''; issuedMobile.current = ''; setIssueUncertain(false);
      setStep('mobile'); setCode(''); setReceipt(null); setWaitUntil(0); setClock(Date.now());
      setOpen(true); dialog.current?.showModal();
    } catch (e) { setNotice(messageOf(e)); } finally { setBusy(false); }
  };
  const close = async () => {
    if (busy) return;
    try { if (flow.current) await post('intent/cancel'); } catch { /* Flow expiry also ends any pending intent. */ }
    dialog.current?.close(); setOpen(false); setCode(''); setReceipt(null); flow.current = ''; setError(''); setIssueUncertain(false);
    opener.current?.focus();
  };
  const requestCode = async (fresh = false) => {
    if (issueInFlight.current || busy || (fresh && issueUncertain)) return;
    issueInFlight.current = true;
    if (fresh) issueKey.current = '';
    setError(''); setBusy(true); setClock(Date.now()); setIssueUncertain(true); setCode('');
    if (!issueKey.current || issuedMobile.current !== mobile) {
      issueKey.current = crypto.randomUUID(); issuedMobile.current = mobile;
    }
    try {
      const result = await post('issue', { mobile: issuedMobile.current, key: issueKey.current });
      setReceipt(result); setIssueUncertain(false); setStep('code'); setClock(Date.now());
      if (result.state !== 'active') {
        setError('این کد دیگر فعال نیست؛ کد تازه بگیرید.'); return;
      }
      if (result.delivery === 'unknown') setError('وضعیت تحویل نامشخص است؛ ارسال دوباره انجام نشده است. پس از پایان انتظار می‌توانید کد تازه درخواست کنید.');
    } catch (e) {
      // An unknown response keeps this operation's immutable key and payload for recovery.
      setIssueUncertain(!(e instanceof PostFailure && e.status >= 400 && e.status < 500 && e.status !== 408));
      setError(messageOf(e));
    } finally { issueInFlight.current = false; setBusy(false); }
  };
  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (step === 'mobile') { await requestCode(); return; }
    if (!receipt || issueUncertain) return;
    setBusy(true); setError('');
    try {
      await post('verify', { challenge_id: receipt.challenge_id, code });
      await refresh(); setNotice('خوش آمدید. ورود آزمایشی انجام شد؛ مالکیت واقعی شماره احراز نشده است.');
      dialog.current?.close(); setOpen(false); setCode(''); setReceipt(null); flow.current = ''; opener.current?.focus();
    } catch (e) {
      // A lost verify response may still have delivered Set-Cookie. Never replay to mint a session.
      const recovered = await refresh().catch(() => null);
      const canonical = en(mobile).replace(/[ -]/g, '').replace(/^0098/, '+98').replace(/^09/, '+989');
      if (recovered && recovered.mobile === canonical) { dialog.current?.close(); setOpen(false); setCode(''); setReceipt(null); flow.current = ''; setNotice('وضعیت ورود از سرور بازیابی شد.'); }
      else setError(messageOf(e));
    } finally { setBusy(false); }
  };
  const edit = async () => {
    setBusy(true); setError('');
    try { await post('edit'); setStep('mobile'); setCode(''); setReceipt(null); issueKey.current = ''; setIssueUncertain(false); } catch (e) { setError(messageOf(e)); } finally { setBusy(false); }
  };
  const logout = async () => {
    setBusy(true);
    try { await post('logout', {}, false); clearIdentity(); authChannel.current?.postMessage({ type: 'session-invalidated' }); setNotice('از حساب خارج شدید.'); } catch (e) { setNotice(messageOf(e)); } finally { setBusy(false); }
  };
  const remaining = receipt ? Math.max(0, Math.ceil((Date.parse(receipt.expires_at) - clock) / 1000)) : 0;
  const resend = receipt ? Math.max(0, Math.ceil((Math.max(Date.parse(receipt.resend_at), waitUntil) - clock) / 1000)) : 0;
  const limited = waitUntil > clock;
  return <AuthContext.Provider value={{ account, busy, ready, notice, start, logout, triggerRef: opener, activity: async () => { try { await post('activity', {}, false); setNotice('نشست فعال است.'); } catch { await refresh(); setNotice('نشست پایان یافته است؛ دوباره وارد شوید.'); } } }}>
    <AccountBridge />
    {children ?? <>
    <header className="shell-header"><Logo /><button ref={opener} disabled={!ready || busy} className="primary-button shell-login" onClick={account ? logout : start}>{account ? 'خروج' : 'ورود به حساب'}</button></header>
    <main className="auth-legacy"><h1>سرمایه‌گزین</h1><p>فرصت‌های سرمایه‌گذاری ایران</p><p className="trial-caption">محیط آزمایشی ورود؛ پیامک واقعی ارسال نمی‌شود.</p>
      {account && <section className="account-status" aria-label="وضعیت ورود"><strong>وارد شده‌اید</strong><p dir="ltr">{fa(account.mobile)}</p><p>احراز آزمایشی؛ مالکیت شماره تأیید نشده است.</p><button className="text-button" onClick={async () => { try { await post('activity', {}, false); setNotice('نشست فعال است.'); } catch { await refresh(); setNotice('نشست پایان یافته است؛ دوباره وارد شوید.'); } }}>بررسی و تمدید نشست</button></section>}
      {notice && <p role="status" className="shell-notice">{notice}</p>}
    </main></>}
    <dialog ref={dialog} tabIndex={-1} className="login-dialog" aria-labelledby="login-title" aria-describedby="login-description" onKeyDown={e => {
      if (e.key !== 'Tab') return;
      const focusable = Array.from(dialog.current?.querySelectorAll<HTMLElement>('button:not(:disabled), input:not(:disabled), [tabindex="0"]') || []);
      if (!focusable.length) { e.preventDefault(); dialog.current?.focus(); return; }
      const first = focusable[0], last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last?.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first?.focus(); }
    }} onCancel={e => { e.preventDefault(); void close(); }} onClick={e => { if (e.target === dialog.current) void close(); }}>
      {open && <div className="login-grid"><Visual /><div className="login-form-panel">
        <button type="button" className="dialog-close" aria-label="بستن پنجره ورود" disabled={busy} onClick={close}><Icon name="Add" size={20} /></button>
        <span className="form-emblem"><Icon name={step === 'mobile' ? 'Mobile' : 'ShieldTick'} /></span>
        <h2 id="login-title">{step === 'mobile' ? 'ورود با شماره موبایل' : 'کد تایید را وارد کنید'}</h2>
        <p id="login-description">{step === 'mobile' ? 'برای ورود آزمایشی فقط شماره موبایل لازم است، نام و رمز نمی‌خواهیم.' : issueUncertain ? 'نتیجه درخواست کد مشخص نیست؛ برای دریافت نتیجه همان درخواست دوباره تلاش کنید.' : receipt?.delivery === 'unknown' ? 'وضعیت تحویل کد نامشخص است؛ ادعای ارسال یا تحویل نداریم.' : `کد شش‌رقمی آزمایشی برای ${fa(mobile)} در اعلان همین صفحه نمایش داده شد؛ پیامکی ارسال نشد.`}</p>
        <form onSubmit={submit} aria-busy={busy}>
          {step === 'mobile' ? <label><span className="input-label">شماره موبایل</span><input ref={mobileInput} autoFocus dir="ltr" inputMode="tel" autoComplete="tel" placeholder="09xx xxx xxxx" value={mobile} onChange={e => { setMobile(e.target.value); setError(''); }} aria-label="شماره موبایل" aria-invalid={!!error} aria-describedby={error ? 'auth-error' : undefined} disabled={busy || issueUncertain} /></label> : <div className="code-boxes" dir="ltr"><div className="code-cells" aria-hidden>{Array.from({ length: 6 }, (_, i) => <span key={i} className={i === Math.min(code.length, 5) ? 'code-active' : ''}>{fa(en(code)[i] || '')}</span>)}</div><input ref={codeInput} autoFocus inputMode="numeric" autoComplete="one-time-code" value={code} onChange={e => setCode(en(e.target.value))} aria-label="کد تایید" aria-invalid={!!error} aria-describedby={error ? 'auth-error' : undefined} disabled={busy} /></div>}
          <button className="primary-button" type="submit" disabled={busy || limited || (step === 'mobile' ? !mobile : issueUncertain || !/^[0-9]{6}$/.test(code) || remaining === 0)}>{busy ? 'در حال بررسی…' : step === 'mobile' ? 'دریافت کد' : 'ورود'}</button>
          {step === 'code' && <><button type="button" className="text-button" disabled={busy} onClick={edit}>ویرایش شماره</button><div className="code-timing" aria-live="polite"><span>{issueUncertain ? 'نتیجه درخواست مشخص نیست.' : remaining > 0 ? `اعتبار کد: ${fa(remaining)} ثانیه` : 'اعتبار کد تمام شده است.'}</span><button type="button" className="text-button" disabled={busy || (!issueUncertain && resend > 0)} onClick={() => { void requestCode(!issueUncertain); }}>{issueUncertain ? 'تلاش دوباره برای دریافت نتیجه' : resend > 0 ? `ارسال مجدد در ${fa(resend)} ثانیه` : 'دریافت کد تازه'}</button></div></>}
          {issueUncertain && !busy && <p role="status">تلاش دوباره فقط نتیجه همان درخواست را دریافت می‌کند؛ کد تازه‌ای صادر نمی‌کند.</p>}
          {limited && <p role="status">تلاش دوباره در {fa(Math.max(0, Math.ceil((waitUntil - clock) / 1000)))} ثانیه</p>}
          {error && <p id="auth-error" role="alert" className="auth-error">{error}</p>}
        </form>
        <p className="privacy-note"><Icon name="Lock1" size={15} />شماره شما برای ورود استفاده می‌شود؛ اشتراک آن برای پیگیری فرصت فقط با رضایت شما و برای گیرندهٔ مشخص انجام می‌شود.</p>
        {receipt?.notification && receipt.state === 'active' && !issueUncertain && remaining > 0 && <aside role="status" className="test-notification"><strong>اعلان آزمایشی — پیامکی ارسال نشد</strong><p>کد ورود: <b dir="ltr" data-testid="trial-code">{receipt.notification.code}</b></p><small>این روش مالکیت واقعی شماره را تأیید نمی‌کند.</small></aside>}
      </div></div>}
    </dialog>
  </AuthContext.Provider>;
}
