"""Local trial probe. Print checks only, never credentials, OTP or cookie values."""
import http.cookiejar
import json
import subprocess
import urllib.error
import urllib.request
from pathlib import Path
from uuid import uuid4

origin = 'http://127.0.0.1:3108'
jar = http.cookiejar.CookieJar()
client = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))
flow = ''


def get(path):
    with client.open(origin + '/api/v1/auth/' + path, timeout=15) as response:
        assert 'no-store' in response.headers['Cache-Control']
        return json.load(response)


def post(path, body):
    token = get('csrf')['csrfToken']
    request = urllib.request.Request(origin + '/api/v1/auth/' + path, data=json.dumps(body).encode(), headers={'Content-Type': 'application/json', 'X-CSRFToken': token, 'X-Login-Flow': flow, 'Origin': origin}, method='POST')
    with client.open(request, timeout=15) as response:
        assert 'no-store' in response.headers['Cache-Control']
        return json.load(response)


flow = post('flows', {})['flow_token']
issued = post('issue', {'mobile': '09120000001', 'key': str(uuid4())})
code = issued['notification']['code']
assert post('verify', {'challenge_id': issued['challenge_id'], 'code': code})['authenticated']
assert get('me')['authenticated']
cookie = next(c.value for c in jar if c.name == 'invest_session')
compose = ['docker', 'compose', '--env-file', '.env', '-f', 'deploy/compose.yaml']
logs = subprocess.run(compose + ['logs', '--no-color', 'backend', 'web'], capture_output=True, check=True).stdout.decode()
assert all(secret not in logs for secret in (code, flow, cookie))
assert post('logout', {})['logged_out']
assert not get('me')['authenticated']
# Inspect stored fields in the same local project without dumping them.
inspection = '''
import json
from apps.identity.models import User,AuthSession,OTPChallenge,AuditEvent
u=User.objects.get(mobile='+989120000001')
assert u.mobile_verified_at is None
assert all(len(s.digest)==64 for s in AuthSession.objects.filter(user=u))
assert all(len(c.code_digest)==64 and len(c.nonce)==64 for c in OTPChallenge.objects.filter(user=u))
audit=list(AuditEvent.objects.filter(account_id=u.pk).values())
assert all(set(e)=={'id','kind','account_id','at'} for e in audit)
print('identity_storage_ok')
'''
result = subprocess.run(compose + ['exec', '-T', 'backend', '/app/.venv/bin/python', 'manage.py', 'shell', '-c', inspection], capture_output=True, check=True)
assert b'identity_storage_ok' in result.stdout
# Check actual configured secret values against public assets and deliverable documents/tests.
private = {}
for line in Path('.env').read_text().splitlines():
    if '=' in line and not line.startswith('#'):
        key, value = line.split('=', 1)
        private[key] = value
secrets_to_scan = [private[k].encode() for k in ('DJANGO_SECRET_KEY', 'POSTGRES_PASSWORD') if len(private.get(k, '')) >= 12]
scanned = 0
for directory in ('frontend/public', 'frontend/.next/static', 'backend/tests', 'docs', 'specs'):
    for path in Path(directory).rglob('*'):
        if path.is_file() and '__pycache__' not in path.parts:
            data = path.read_bytes()
            assert all(secret not in data for secret in secrets_to_scan), 'Private configuration found in deliverable'
            scanned += 1
report = {'journey_on_local_delivery': True, 'no_store': True, 'no_otp_flow_or_cookie_in_service_logs': True, 'hashed_storage_and_minimal_audit': True, 'trial_does_not_verify_mobile': True, 'logout_invalidates_session': True, 'private_configuration_not_in_public_assets_documents_or_tests': True, 'scanned_files': scanned, 'scope': 'local synthetic data only; public-mode policy covered separately by backend tests'}
Path('docs/stage3/evidence/security-probe.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
print(json.dumps(report, ensure_ascii=False))
