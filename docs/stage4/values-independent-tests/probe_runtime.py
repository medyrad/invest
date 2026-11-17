"""Read-only definitions and stateless normalize probes; never stores tokens in evidence."""
import copy
import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path

base='http://127.0.0.1:3108'
client=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf=json.load(client.open(base+'/api/v1/auth/csrf'))['csrfToken']
with client.open(base+'/api/v1/catalog/value-definitions') as response:
    definitions=json.load(response)
body={'field':{'namespace':'invest.opportunity.project','key':'min_capital','version':1},
      'unit':{'code':'BILLION_TOMAN','version':1},'status':'known','source_value':'۱٫۵','basis':None}
results=[]
for name,payload in [('valid',body)]+[(f'nul-{ref}-{key}',copy.deepcopy(body)) for ref,key in [('field','namespace'),('field','key'),('unit','code')]]:
    if name.startswith('nul-'):
        _,ref,key=name.split('-');payload[ref][key]+='\x00'
    request=urllib.request.Request(base+'/api/v1/catalog/values/normalize',data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','X-CSRFToken':csrf,'Origin':base})
    try:
        response=client.open(request)
    except urllib.error.HTTPError as error:
        response=error
    results.append({'case':name,'status':response.status,'response':json.load(response)})
output={'definitions':definitions,'normalize':results}
Path('docs/stage4/values-independent-evidence/runtime-http.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print([(r['case'],r['status']) for r in results])
