"""Small, declarative visibility predicates for this fixed S08 contract (no eval)."""

from apps.workspace.schema import Fault


def matches(condition, raw):
    if not condition:
        return True
    if "all" in condition:
        return all(matches(c, raw) for c in condition["all"])
    if "any" in condition:
        return any(matches(c, raw) for c in condition["any"])
    value = raw.get(condition.get("field"))
    op = condition.get("op", "eq")
    target = condition.get("value")
    if op == "eq":
        return value == target
    if op == "ne":
        return value != target
    if op == "in":
        return value in condition["values"]
    if op == "contains":
        return isinstance(value, list) and target in value
    raise Fault("شرط این نسخه پشتیبانی نمی‌شود.", field="schema")
