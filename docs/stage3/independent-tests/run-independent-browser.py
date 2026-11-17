"""Reset only invest_browser, then run the independent browser journeys."""
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[3]
base = ['docker', 'compose', '--env-file', '.env', '-f', 'deploy/compose.yaml']
check = subprocess.check_output(base + ['run', '--rm', 'browser-api', '/app/.venv/bin/python', '-c',
    'import os;from config.env import read_environment;c=read_environment(os.environ);assert c["mode"]=="test" and c["database"]["NAME"]=="invest_browser";print("isolated invest_browser confirmed")'], cwd=root, text=True)
print(check, flush=True)
for args in [['stop','browser-api'], ['run','--rm','browser-api','/app/.venv/bin/python','-m','tests.prepare_browser_db'], ['run','--rm','browser-api','/app/.venv/bin/python','manage.py','migrate','--noinput'], ['up','-d','browser-api']]:
    subprocess.run(base + args, cwd=root, check=True)
subprocess.run([str(root / '.tools/runtimes/node-v24.22.3-linux-x64/bin/node'),
    str(root / 'docs/stage3/independent-tests/browser-independent.cjs')], cwd=root, check=True)
