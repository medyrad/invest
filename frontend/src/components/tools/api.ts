import {Failure} from '@/components/workspace/api';
export async function services<T>(path:string, body?:object):Promise<T>{
 const headers:Record<string,string>={};
 if(body){const csrf=await fetch('/api/v1/auth/csrf',{cache:'no-store'});if(!csrf.ok)throw new Error('دریافت مجوز درخواست انجام نشد.');headers['X-CSRFToken']=(await csrf.json()).csrfToken;headers['Content-Type']='application/json'}
 const r=await fetch('/api/v1/services/'+path,{method:body?'POST':'GET',headers,body:body?JSON.stringify(body):undefined,cache:'no-store',signal:AbortSignal.timeout(35000)});
 const data=await r.json();if(!r.ok)throw new Failure(data.error?.message||'درخواست انجام نشد.',r.status,data.error?.fields,data.current);return data as T;
}
