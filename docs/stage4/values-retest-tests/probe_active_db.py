"""Only SELECT on active DB; normalize API is stateless. No environment values emitted."""
import http.cookiejar
import json
import subprocess
import urllib.request
from pathlib import Path

container = json.loads(Path('docs/stage4/values-retest-evidence/version.json').read_text())['runtime']['backend']['container']
script = '''import os,json;os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings')
import django;django.setup()
from django.db import connection
with connection.cursor() as c:
    counts={}
    for table in ['catalog_moneyvalue','catalog_quantity','catalog_returnmetric']:
        c.execute('SELECT count(*) FROM '+table);counts[table]=c.fetchone()[0]
    c.execute("SELECT name FROM django_migrations WHERE app='catalog' ORDER BY name")
    migrations=[r[0] for r in c.fetchall()]
    c.execute("SELECT tgname,tgenabled FROM pg_trigger WHERE NOT tgisinternal AND tgname IN ('money_basis_guard','quantity_basis_guard','return_basis_guard') ORDER BY tgname")
    triggers=c.fetchall()
print(json.dumps({'counts':counts,'catalog_migrations':migrations,'basis_triggers':triggers}))'''
def read():
    return json.loads(subprocess.check_output(['docker', 'exec', container, '/app/.venv/bin/python', '-c', script], text=True))
before = read()
base = 'http://127.0.0.1:3108'
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf = json.load(client.open(base + '/api/v1/auth/csrf'))['csrfToken']
payload = {'field': {'namespace': 'invest.opportunity.project', 'key': 'min_capital', 'version': 1}, 'unit': {'code': 'MILLION_TOMAN', 'version': 1}, 'status': 'known', 'source_value': '۱۵۰۰', 'basis': None}
request = urllib.request.Request(base + '/api/v1/catalog/values/normalize', data=json.dumps(payload).encode(), headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf, 'Origin': base})
with client.open(request) as response:
    result = json.load(response)
    status = response.status
after = read()
assert before == after
assert '0004_basis_integrity' in after['catalog_migrations']
assert len(after['basis_triggers']) == 3 and all(t[1] == 'O' for t in after['basis_triggers'])
assert status == 200 and result['value'] == '1500000000'
Path('docs/stage4/values-retest-evidence/active-db-readonly.json').write_text(json.dumps({'before': before, 'after': after, 'http_status': status, 'value': result['value'], 'unchanged': True}, indent=2) + '\n')
print('Active migration installed; three enabled guards; normalize count unchanged')
