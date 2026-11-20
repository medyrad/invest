from dataclasses import dataclass

ROUTER_VERSION = "assistant-router-v1"
LUNA = "gpt-6-luna"
SOL = "gpt-6.2-sol"


@dataclass(frozen=True)
class RouteDecision:
    model: str
    code: str
    reason: str
    version: str = ROUTER_VERSION


def choose_model(*, normalized, opportunity_ids, history, message=""):
    """Choose once, before provider dispatch, without calling another model."""
    criteria = normalized.get("criteria") or {}
    questions = normalized.get("questions") or []
    ids = opportunity_ids or []
    conflict_words = ("متناقض", "همزمان", "هم‌زمان", "به جز", "اما", "یا ")
    conflict = len(questions) > 1 or any(word in message for word in conflict_words)
    basis_count = sum(
        key in criteria
        for key in ("budget_min", "budget_max", "province", "city", "risk", "return")
    )
    if conflict:
        return RouteDecision(SOL, "complex_constraints", "multiple_or_conflicting_constraints")
    if len(ids) >= 3 and (basis_count >= 2 or len(history or []) >= 2):
        return RouteDecision(SOL, "complex_comparison", "three_or_four_items_with_multiple_bases")
    if len(ids) >= 3:
        return RouteDecision(SOL, "multi_item_comparison", "three_or_four_items")
    if normalized.get("needs_clarification"):
        return RouteDecision(LUNA, "clarification", "ambiguous_request_requires_question")
    if len(ids) == 2:
        return RouteDecision(LUNA, "simple_comparison", "two_same_kind_items")
    if ids:
        return RouteDecision(LUNA, "simple_explanation", "single_public_item")
    return RouteDecision(LUNA, "simple_search", "bounded_public_search")
