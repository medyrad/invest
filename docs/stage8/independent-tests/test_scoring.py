from decimal import Decimal
from types import SimpleNamespace
from apps.core.discovery import score

def test_advisory_block_does_not_change_independently_calculated_d28_score():
    # D28: دسته ۲۰ (مطابق)، موقعیت ۱۵ (نامعلوم)، ریسک ۱۵ (نامنطبق).
    # امتیاز=۲۰/۵۰*۱۰۰=۴۰؛ پوشش=(۲۰+۱۵)/۵۰*۱۰۰=۷۰.
    revision=SimpleNamespace(kind='project',snapshot={'group':'transport','province':'unknown','risk':'low'})
    criteria={'route':'investor','group':['transport'],'province':['تهران'],'risk':['high']}
    expected=score(revision,criteria)
    assert Decimal(expected['score'])==40 and Decimal(expected['coverage'])==70
    assert score(revision,{**criteria,'preferences':{'adv:roads:revenue':'user','adv:roads:toll':'notallowed'}})==expected
