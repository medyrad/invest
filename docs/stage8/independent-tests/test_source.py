import json
from pathlib import Path
import pytest
from apps.services.advisories import CONFIGS,questions
SOURCE=json.loads(Path('/source/source-configs.json').read_text())
@pytest.mark.parametrize('source',SOURCE,ids=lambda c:c['id'])
def test_each_primary_source_configuration(source):
    actual=CONFIGS[source['id']]
    for key in ['group','name','context','baseChecks']:
        assert actual[key]==source[key],(source['id'],key)
    reduced=[{k:q.get(k,{} if k=='actions' else [] if k in ['review','block'] else '') for k in ['id','label','help','options','actions','review','block']} for q in actual['questions']]
    assert reduced==source['questions']
    for case in source['activation']:
        assert [q['id'] for q in questions(source['id'],case['answers'])]==case['active'],(source['id'],case['answers'])
