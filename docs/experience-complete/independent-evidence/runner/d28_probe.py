import json
from pathlib import Path
from apps.core import discovery
inputs=json.loads(Path('/app/tests/fixtures/core/d28-human-review-inputs.json').read_text())
out=[]
for scenario in inputs['scenarios']:
    actual=discovery.listing(scenario['criteria'])
    out.append({'id':scenario['id'],'cohort':scenario['cohort'],'criteria':scenario['criteria'],'total':actual['total'],'items':actual['items'][:5]})
Path('/evidence/d28-fresh-output.json').write_text(json.dumps(out,ensure_ascii=False,indent=2))
print({'count':len(out),'nonempty':sum(bool(x['items']) for x in out),'labels_generated':False})
