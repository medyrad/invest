#!/usr/bin/env python3
"""Validate planning traceability and evidence integrity, not product behavior."""
import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FEATURE = ROOT / 'specs/001-business-baseline'
errors = []
checks = {}

def require(condition, message):
    if not condition:
        errors.append(message)

def read_json(path):
    return json.loads((ROOT / path).read_text())

spec = (FEATURE / 'spec.md').read_text()
tasks_text = (FEATURE / 'tasks.md').read_text()
requirements = re.findall(r'^\| ((?:FR|SC)-\d{3}) \|', spec, re.M)
stories = re.findall(r'^### (US\d+) \(P[123]\)', spec, re.M)
task_records = re.findall(r'^- \[([ xX])\] (T\d{3}) (.+)$', tasks_text, re.M)
task_lines = [(tid, body) for _, tid, body in task_records]
completed_tasks = [tid for mark, tid, _ in task_records if mark.lower() == 'x']
task_ids = [tid for tid, _ in task_lines]
require(len(task_ids) == len(set(task_ids)), 'duplicate task IDs')
require(task_ids == [f'T{i:03}' for i in range(1, len(task_ids) + 1)], 'non-sequential task IDs')
require(len(requirements) == len(set(requirements)), 'duplicate FR/SC IDs')
require(len(stories) == 6, 'expected six prioritized user stories')
require(len(task_lines) == len(re.findall(r'^- \[', tasks_text, re.M)), 'invalid task checklist line')
status = read_json('docs/stage-status.json')
allowed_completed = {'T002'}
if status.get('foundation', {}).get('status') == 'complete':
    allowed_completed.update(f'T{i:03}' for i in range(3, 9))
if status.get('identity', {}).get('status') in {'technical-pass', 'complete'}:
    allowed_completed.update(f'T{i:03}' for i in range(13, 17))
require(set(completed_tasks) <= allowed_completed, 'completed task exceeds verified stage scope')
for tid, body in task_lines:
    require(bool(re.search(r'[\w.-]+/(?:[^\s؛،]+)', body)), f'{tid}: missing concrete path')
    for story in re.findall(r'\[(US\d+)\]', body):
        require(story in stories, f'{tid}: unknown story {story}')
    for req in re.findall(r'\b(?:FR|SC)-\d{3}\b', body):
        require(req in requirements, f'{tid}: unknown requirement {req}')
coverage = {req: [tid for tid, body in task_lines if req in body] for req in requirements}
for req, tids in coverage.items():
    require(bool(tids), f'{req}: no planned task')
trace = read_json('docs/catalogs/implementation-traceability.json')
require([t['id'] for t in trace['tasks']] == task_ids, 'trace/task order differs')
for record, (tid, body) in zip(trace['tasks'], task_lines):
    require(record['description'] in body, f'{tid}: stale trace description')
    require(set(record['requirements']) == set(re.findall(r'\b(?:FR|SC)-\d{3}\b', body)), f'{tid}: stale trace requirements')
features = list(csv.DictReader((ROOT / 'docs/catalogs/feature-coverage.csv').open()))
require(len({f['id'] for f in features}) == 44, 'feature registry count/uniqueness')
require({f['feature'] for f in trace['features']} == {f['id'] for f in features}, 'feature trace missing/extra')
for f in trace['features']:
    require(bool(f['tasks']) and set(f['tasks']) <= set(task_ids), f"{f['feature']}: missing task mapping")
    expected = [r['id'] for r in trace['tasks'] if f['package'] in r['packages']]
    require(expected == f['tasks'], f"{f['feature']}: stale package/task mapping")

manifest = read_json('docs/stage1/evidence/manifest.json')
require(len(manifest['cases']) == 46, 'expected 46 reference captures')
for case in manifest['cases']:
    require(case.get('status') == 200 and not case.get('capture_error'), f"capture failed: {case['id']}")
    path = ROOT / 'docs/stage1/evidence' / case.get('file', 'missing')
    require(path.is_file(), f"missing screenshot: {case['id']}")
    if path.is_file():
        require(hashlib.sha256(path.read_bytes()).hexdigest() == case['sha256'], f"changed screenshot: {case['id']}")
require(len({c['id'] for c in manifest['cases']}) == len(manifest['cases']), 'duplicate capture ID')

local_links = 0
for path in [ROOT / 'README.md', *sorted((ROOT / 'docs').rglob('*.md')), *sorted((ROOT / 'specs').rglob('*.md'))]:
    content = path.read_text()
    for target in re.findall(r'\[[^\]\n]+\]\(([^)\n]+)\)', content):
        target = target.strip('<>').split('#')[0]
        if not target or re.match(r'\w+://', target) or target.startswith('mailto:'):
            continue
        local_links += 1
        require((path.parent / target).resolve().exists(), f'{path.relative_to(ROOT)}: broken link {target}')
    if path.parent == FEATURE:
        require(not re.search(r'\[FEATURE\]|\[DATE\]|\[###-feature|ACTION REQUIRED', content), f'{path.name}: unfilled template')
for checklist in (FEATURE / 'checklists').glob('*.md'):
    require('- [x]' not in checklist.read_text().lower(), 'reviewer checklist auto-completed')

status = read_json('docs/stage-status.json')
acceptance_ids = re.findall(r'^\| (AC-D\d+-\d+) \|', (ROOT / 'docs/03-decisions.md').read_text(), re.M)
clarifications = re.findall(r'^- Q:.*?\((Q-[\w-]+)\)', spec, re.M)
require(len(acceptance_ids) == len(set(acceptance_ids)), 'duplicate acceptance scenario IDs')
require(len(acceptance_ids) == status['business_specification']['decision_acceptance_scenarios'], 'acceptance scenario count/status differs')
require(len(clarifications) == len(set(clarifications)), 'duplicate clarification answers')
require(len(clarifications) == status.get('clarification_step', status['active_step'])['accepted_answers'], 'clarification answer count/status differs')
require(len(clarifications) <= status.get('clarification_step', status['active_step'])['asked_questions'] <= status.get('clarification_step', status['active_step'])['question_limit'], 'clarification session limit exceeded')
require(sum(r.startswith('FR') for r in requirements) == status['business_specification']['functional_requirements'], 'functional requirement count/status differs')
require(status['speckit_initialized'], 'SpecKit status stale')
if status['speckit']['final_plan_gate_passed']:
    require(bool(status['speckit'].get('gate_scope')), 'passed plan gate must name its limited scope')
    require('کل محصول' not in status['speckit']['gate_scope'], 'open product gates must not be represented as passed')
if status['application_implemented'] or status['runtime_verified']:
    require(bool(status.get('application_implementation_scope')), 'implemented runtime must state its bounded scope')
    require(
        any(marker in status['application_implementation_scope'] for marker in ('باز', 'شروع نشده', 'پذیرش')),
        'implemented runtime must preserve open product gates',
    )
for file in ['plan.md', 'research.md', 'data-model.md', 'contracts/api.md', 'quickstart.md', 'test-plan.md', 'tasks.md']:
    require((FEATURE / file).is_file(), f'missing design artifact {file}')

checks.update(requirements=len(requirements), functional_requirements=sum(r.startswith('FR') for r in requirements), success_criteria=sum(r.startswith('SC') for r in requirements), stories=len(stories), tasks=len(task_ids), features=len(features), local_markdown_links=local_links, reference_screenshots=len(manifest['cases']), reference_page_error_cases=sum(bool(c['page_errors']) for c in manifest['cases']), reviewer_checklist_items=len(re.findall(r'^- \[ \] CHK\d+', (FEATURE / 'checklists/business-ui-quality.md').read_text(), re.M)))
checks.update(completed_baseline_tasks=completed_tasks, pending_tasks=len(task_ids)-len(completed_tasks), decision_acceptance_scenarios=len(acceptance_ids), clarification_answers=len(clarifications))
result = {'scope': 'planning structure and evidence integrity only', 'passed': not errors, 'checks': checks, 'requirement_task_coverage': coverage, 'errors': errors, 'not_proven': ['semantic completeness', 'all source states covered', 'visual parity of invest', 'runtime health by this planning validator', 'live OpenAI or SMS', 'reviewer approval']}
print(json.dumps(result, ensure_ascii=False, indent=2))
sys.exit(bool(errors))
