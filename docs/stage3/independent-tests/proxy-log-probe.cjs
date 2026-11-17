const path=require('node:path'),fs=require('node:fs'),{spawnSync}=require('node:child_process');
const root=path.resolve(__dirname,'../../..');const {request}=require(path.join(root,'frontend/node_modules/@playwright/test'));
const compose=['compose','--env-file','.env','-f','deploy/compose.yaml'];
const since=new Date().toISOString();
(async()=>{
 const clients=[];const secrets=[];const rows=[];
 for(const [mobile,xff] of [['09178009992','198.51.100.201'],['09178009993','203.0.113.202']]){
  const client=await request.newContext({baseURL:'http://127.0.0.1:3108'});clients.push(client);
  const csrf=(await(await client.get('/api/v1/auth/csrf')).json()).csrfToken;
  const flow=(await(await client.post('/api/v1/auth/flows',{headers:{'X-CSRFToken':csrf},data:{}})).json()).flow_token;
  const r=await client.post('/api/v1/auth/issue',{headers:{'X-CSRFToken':csrf,'X-Login-Flow':flow,'X-Forwarded-For':xff},data:{mobile,key:require('node:crypto').randomUUID()}});
  const body=await r.json();rows.push({client:rows.length+1,issue_status:r.status()});
  if(r.status()===200){
   secrets.push(flow,body.notification.code,csrf);
   const v=await client.post('/api/v1/auth/verify',{headers:{'X-CSRFToken':csrf,'X-Login-Flow':flow},data:{challenge_id:body.challenge_id,code:body.notification.code}});
   rows.at(-1).verify_status=v.status();
   const cookies=(await client.storageState()).cookies;const cookie=cookies.find(x=>x.name==='invest_session');if(cookie)secrets.push(cookie.value);
   const fresh=(await(await client.get('/api/v1/auth/csrf')).json()).csrfToken;
   await client.post('/api/v1/auth/logout',{headers:{'X-CSRFToken':fresh},data:{}});
  }
 }
 const code='import json;from apps.identity.models import IssueEvent;from apps.identity.otp import digest;q=IssueEvent.objects.filter(user__mobile__in=["+989178009992","+989178009993"]);v=list(q.values_list("ip_digest",flat=True));print(json.dumps({"events":len(v),"distinct_observed_ip":len(set(v)),"spoofed_ip_accepted":any(x in [digest("ip:198.51.100.201"),digest("ip:203.0.113.202")] for x in v)}))';
 const db=spawnSync('docker',[...compose,'exec','-T','backend','/app/.venv/bin/python','manage.py','shell','-c',code],{cwd:root,encoding:'utf8'});const match=db.stdout.match(/\{"events"[^\n]+/);const ip=match?JSON.parse(match[0]):{error:'Could not read scoped synthetic events'};
 const logs=spawnSync('docker',[...compose,'logs','--since',since,'--no-color','backend','web'],{cwd:root,encoding:'utf8'});
 const output={origin:'http://127.0.0.1:3108',clients:rows,ip,log_scan:{secret_values_checked:secrets.length,leaks:secrets.filter(s=>logs.stdout.includes(s)).length,raw_logs_saved:false}};
 fs.writeFileSync(path.join(root,'docs/stage3/independent-evidence/proxy-log-probe.json'),JSON.stringify(output,null,2));console.log(JSON.stringify(output));
 for(const c of clients)await c.dispose();
})().catch(e=>{console.error(e.message);process.exitCode=1;});
