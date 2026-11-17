#!/usr/bin/env python3
"""Arithmetic audit of matching policy D28, NOT invest matching implementation."""
import itertools
import json
from fractions import Fraction
from decimal import Decimal

WEIGHTS = [30, 20, 15, 20, 15, 15]

def proposed(weights, states):
    total = sum(weights)
    if not total:
        return None, None
    earned = sum(w for w, s in zip(weights, states) if s == 'met')
    known = sum(w for w, s in zip(weights, states) if s != 'unknown')
    return Fraction(100 * earned, total), Fraction(100 * known, total)

cases = [
    ('25-Tehran', ['met', 'met'], Fraction(100), Fraction(100)),
    ('40-Tehran', ['unmet', 'met'], Fraction(100, 3), Fraction(100)),
    ('25-Isfahan', ['met', 'unmet'], Fraction(200, 3), Fraction(100)),
    ('unknown-Tehran', ['unknown', 'met'], Fraction(100, 3), Fraction(100, 3)),
    ('all-unknown', ['unknown', 'unknown'], Fraction(0), Fraction(0)),
]
for name, states, score, coverage in cases:
    assert proposed([30, 15], states) == (score, coverage), name
assert proposed([], []) == (None, None)
checked = 0
for states in itertools.product(['met', 'unmet', 'unknown'], repeat=6):
    score, coverage = proposed(WEIGHTS, states)
    assert 0 <= score <= coverage <= 100
    for index, state in enumerate(states):
        if state == 'unknown':
            continue
        hidden = list(states)
        hidden[index] = 'unknown'
        after, after_coverage = proposed(WEIGHTS, hidden)
        assert after <= score, 'Hiding a field must not improve score'
        assert after_coverage < coverage
        checked += 1
# Same weighted item expressed in two subcriteria must not double the bucket.
assert proposed([30], ['met'])[0] == proposed([15, 15], ['met', 'met'])[0]
# Amount conversion examples only, not validation of monetary contracts.
assert Decimal('1.5') * Decimal(10**9) == Decimal('1500') * Decimal(10**6)
# Refundable deposit and rent expense remain separate quantities.
assert Decimal(10) * Decimal('200000000') == Decimal('2000000000')
assert Decimal(10) * Decimal('5000000') * Decimal(6) == Decimal('300000000')
old_before = Fraction(100 * 15, 45)
old_hidden = Fraction(100 * (15 + 15), 45)
assert old_hidden > old_before
print(json.dumps({
    'proposal':'P-B02-v1', 'approved':True, 'decision':'D28',
    'scope':'arithmetic and finite invariants only; no production code or real relevance evaluation',
    'passed':True, 'explicit_score_examples':len(cases), 'six_bucket_states':3**6,
    'hide_known_field_checks':checked,
    'source_counterexample':{'known_mismatch_score':float(old_before),'hidden_mismatch_score':float(old_hidden)},
    'cases':[{'name':n,'score':float(s),'coverage':float(c)} for n,_,s,c in cases],
    'unit_policy':{'package':'P-B04-v1','decision':'D29','approved':True},
    'unit_examples_scope':'D29 arithmetic examples only; not production parser, schema or financial calculations',
    'unit_examples':[
        {'inputs':['1.5 billion TOMAN','1500 million TOMAN'],'exact_toman':'1500000000'},
        {'households':10,'months':6,'deposit_per_household_toman':'200000000','monthly_rent_per_household_toman':'5000000','refundable_deposit_toman':'2000000000','rent_expense_toman':'300000000'}
    ],
    'limitations':['Not calibrated against customer/expert judgments','Not a test of production matching API','Does not validate all source financial or legal rules','Does not validate route-specific predicates or final B04 unit contracts']
},ensure_ascii=False,indent=2))
