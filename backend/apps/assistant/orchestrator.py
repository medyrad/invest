"""Shared, server-authoritative preparation for product and evaluation turns."""

from dataclasses import dataclass

from . import tools
from .routing import RouteDecision, choose_model


@dataclass(frozen=True)
class PreparedTurn:
    message: str
    history: list[dict]
    opportunity_ids: list[str]
    normalized: dict
    decision: RouteDecision
    server_result: dict | None


def prepare_turn(*, message, criteria=None, opportunity_ids=None, history=None):
    """Run the exact product parser, router and read-only public tools once."""
    ids = list(opportunity_ids or [])
    turns = list(history or [])
    supplied = dict(criteria or {})
    selected_result = None
    if len(ids) == 1:
        selected_result = {
            "items": [tools.run("get_public_opportunity", {"id": ids[0]})],
            "total": 1,
        }
    elif ids:
        selected_result = tools.run("compare_same_kind", {"ids": ids})
    if selected_result and not supplied.get("route"):
        items = selected_result.get("items") or []
        common_routes = set(items[0].get("routes") or []) if items else set()
        for item in items[1:]:
            common_routes &= set(item.get("routes") or [])
        if len(common_routes) == 1:
            supplied["route"] = next(iter(common_routes))
        kinds = {item.get("kind") for item in items}
        if len(kinds) == 1:
            supplied["kind"] = next(iter(kinds))
    normalized = tools.normalize(message, supplied or None)
    if selected_result is not None and "مقایسه" in message:
        normalized["questions"] = [
            question for question in normalized["questions"] if "بازده" not in question
        ]
        normalized["needs_clarification"] = bool(normalized["questions"])
    decision = choose_model(
        normalized=normalized,
        opportunity_ids=ids,
        history=turns,
        message=message,
    )
    if selected_result is not None:
        server_result = selected_result
    elif normalized["needs_clarification"]:
        server_result = None
    else:
        server_result = tools.run(
            "search_public_opportunities", {"criteria": normalized["criteria"]}
        )
    return PreparedTurn(message, turns, ids, normalized, decision, server_result)


def provider_context(prepared, claim_call):
    return {
        "message": prepared.message,
        "normalized": prepared.normalized,
        "server_result": prepared.server_result or {"items": []},
        "history": prepared.history,
        "claim_call": claim_call,
        "clarification_only": prepared.server_result is None,
    }


def product_tool_runner(prepared):
    """Keep model tool calls behind the same server validators as the public API."""

    def execute(name, arguments):
        if prepared.server_result is None and name != "normalize_criteria":
            from apps.workspace.schema import Fault

            raise Fault("تا رفع ابهام فقط ابزار برداشت نیاز مجاز است.", 409)
        return tools.run(
            name,
            arguments,
            fallback_text=prepared.message,
            fallback_criteria=prepared.normalized["criteria"],
        )

    return execute
