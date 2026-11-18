export async function core<T = unknown>(path: string, body?: unknown): Promise<T> {
  let headers: Record<string,string> = {};
  if (body !== undefined) {
    const c = await fetch('/api/v1/auth/csrf', { cache: 'no-store' });
    const csrf = await c.json(); headers = { 'Content-Type': 'application/json', 'X-CSRFToken': csrf.csrf_token || csrf.csrfToken || csrf.token };
  }
  const r = await fetch('/api/v1/core/'+path, { cache:'no-store', method:body === undefined ? 'GET':'POST', headers, ...(body === undefined ? {} : {body:JSON.stringify(body)}) });
  const result = await r.json();
  if (!r.ok) { const e = new Error(result.error?.message || 'ارتباط انجام نشد؛ تلاش دوباره کنید.'); Object.assign(e,{status:r.status}); throw e; }
  return result;
}
