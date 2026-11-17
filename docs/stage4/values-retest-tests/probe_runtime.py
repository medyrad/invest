"""Stateless local HTTP probes; evidence excludes CSRF/cookies."""
import copy
import http.cookiejar
import json
import urllib.error
import urllib.request
from pathlib import Path

BASE = 'http://127.0.0.1:3108'
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
csrf = json.load(client.open(BASE + '/api/v1/auth/csrf'))['csrfToken']
body = {'field': {'namespace': 'invest.opportunity.project', 'key': 'min_capital', 'version': 1},
        'unit': {'code': 'BILLION_TOMAN', 'version': 1}, 'status': 'known', 'source_value': '۱٫۵', 'basis': None}
ret = copy.deepcopy(body)
ret['field']['key'] = 'irr'
ret['unit']['code'] = 'PERCENT'
ret['basis'] = {'version': 1, 'metric_type': 'irr', 'period': 'annual', 'horizon': {'value': '۵', 'unit': {'code': 'YEAR', 'version': 1}}, 'basis_date': '2024-02-29', 'price_basis': 'nominal', 'scope': 'investor', 'observation': 'claimed', 'source': 'منبع مصنوعی معتبر 🌱'}
duration = copy.deepcopy(body)
duration['field']['key'] = 'execution_months'
duration['unit']['code'] = 'MONTH'
duration['basis'] = {'start_basis': 'آغاز قرارداد 🌱'}
cases = [('valid-persian-money', body, 200, None, None), ('valid-unicode-return', ret, 200, None, None), ('valid-unicode-duration', duration, 200, None, None)]
paths = [(body, 'field.namespace'), (body, 'field.key'), (body, 'unit.code'), (ret, 'basis.horizon.unit.code'), (ret, 'basis.source'), (duration, 'basis.start_basis')]
for original, path in paths:
    for char, code in [('\x00', 'nul_not_allowed'), ('\ud800', 'invalid_text')]:
        item = copy.deepcopy(original)
        node = item
        parts = path.split('.')
        for key in parts[:-1]:
            node = node[key]
        node[parts[-1]] += char
        cases.append((code + '-' + path, item, 400, code, path))
results = []
for name, data, expected, code, field in cases:
    request = urllib.request.Request(BASE + '/api/v1/catalog/values/normalize', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json', 'X-CSRFToken': csrf, 'Origin': BASE})
    try:
        response = client.open(request)
    except urllib.error.HTTPError as error:
        response = error
    result = json.load(response)
    passed = response.status == expected
    if code:
        passed = passed and result['error']['code'] == code and field in result['error']['fields'] and any('\u0600' <= c <= '\u06ff' for c in result['error']['message'])
    if name == 'valid-persian-money':
        passed = passed and result['value'] == '1500000000'
    results.append({'case': name, 'status': response.status, 'passed': passed, 'response': result})
Path('docs/stage4/values-retest-evidence/runtime-http.json').write_text(json.dumps(results, ensure_ascii=False, indent=2) + '\n')
print(f'{sum(r["passed"] for r in results)}/{len(results)} passed')
assert all(r['passed'] for r in results)
