"""Run unchanged delivered browser tests with isolated evidence paths."""
import os
import pathlib
import subprocess

root = pathlib.Path(__file__).resolve().parents[3]
evidence = root / 'docs/stage3/independent-evidence'
env = dict(os.environ)
env['PATH'] = str(root / '.tools/runtimes/node-v24.22.3-linux-x64/bin') + ':' + env['PATH']
env['PLAYWRIGHT_CHROMIUM_EXECUTABLE'] = '/usr/bin/google-chrome'
env['PLAYWRIGHT_JSON_OUTPUT_FILE'] = str(evidence / 'existing-browser-results.json')
compose = ['docker', 'compose', '--env-file', '.env', '-f', 'deploy/compose.yaml']
commands = [
    (compose + ['stop', 'browser-api'], root),
    (compose + ['run', '--rm', 'browser-api', '/app/.venv/bin/python', '-m', 'tests.prepare_browser_db'], root),
    (compose + ['run', '--rm', 'browser-api', '/app/.venv/bin/python', 'manage.py', 'migrate', '--noinput'], root),
    (compose + ['up', '-d', 'browser-api'], root),
    (['npm', 'run', 'build'], root / 'frontend'),
]
run_dir = root / '.tools/test-s03-02/existing/frontend'
run_dir.mkdir(parents=True, exist_ok=True)
for command, cwd in commands:
    print('COMMAND:', ' '.join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=env, check=True)
subprocess.run([
    str(root / '.tools/runtimes/node-v24.22.3-linux-x64/bin/node'),
    str(root / 'frontend/node_modules/@playwright/test/cli.js'), 'test',
    '--config', str(root / 'frontend/playwright.config.ts'),
    '--output', str(root / '.tools/test-s03-02/existing-results'),
], cwd=run_dir, env=env, check=True)
