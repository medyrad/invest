export class Failure extends Error {
  constructor(message: string, readonly status: number, readonly fields: Record<string, string> = {}, readonly current?: unknown) { super(message); }
}
export async function api<T>(path: string, body?: object, method = 'POST'): Promise<T> {
  const headers: Record<string, string> = {};
  if (body) {
    const csrf = await fetch('/api/v1/auth/csrf', { cache: 'no-store', signal: AbortSignal.timeout(10000) });
    if (!csrf.ok) throw new Error('دریافت مجوز درخواست ممکن نشد.');
    headers['X-CSRFToken'] = (await csrf.json()).csrfToken;
    headers['Content-Type'] = 'application/json';
  }
  const response = await fetch('/api/v1/workspace/' + path, { method: body ? method : 'GET', headers, body: body ? JSON.stringify(body) : undefined, cache: 'no-store', signal: AbortSignal.timeout(35000) });
  const data = await response.json();
  if (!response.ok) throw new Failure(data.error?.message || 'درخواست انجام نشد.', response.status, data.error?.fields, data.current);
  return data as T;
}
export function message(error: unknown) { return error instanceof Error && /[\u0600-\u06ff]/.test(error.message) ? error.message : 'پاسخ دریافت نشد؛ نتیجه نامعلوم است. همان عملیات را دوباره بررسی کنید.'; }
