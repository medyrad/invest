// Share only an in-flight bootstrap; never retain a token across session changes.
let pendingCsrf: Promise<string> | null = null;
function csrfToken() {
  if (!pendingCsrf) pendingCsrf = fetch('/api/v1/auth/csrf', {cache:'no-store'}).then(async r => {
    if (!r.ok) throw new Error('دریافت مجوز درخواست انجام نشد.');
    return (await r.json()).csrfToken as string;
  }).finally(() => { pendingCsrf = null; });
  return pendingCsrf;
}
export async function core<T = unknown>(path: string, body?: unknown): Promise<T> {
  let headers: Record<string,string> = {};
  if (body !== undefined) {
    headers = { 'Content-Type': 'application/json', 'X-CSRFToken': await csrfToken() };
  }
  const r = await fetch('/api/v1/core/'+path, { cache:'no-store', method:body === undefined ? 'GET':'POST', headers, ...(body === undefined ? {} : {body:JSON.stringify(body)}) });
  const result = await r.json();
  if (!r.ok) { const e = new Error(result.error?.message || 'ارتباط انجام نشد؛ تلاش دوباره کنید.'); Object.assign(e,{status:r.status}); throw e; }
  return result;
}
