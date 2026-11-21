"""Content-free, process-safe budget guard for controlled S09 live evaluation."""

from __future__ import annotations

import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .quota import PRICE_VERSION

SCHEMA_VERSION = "invest-s09-campaign-ledger-v1"
MAX_CAMPAIGN_USD = Decimal("2.00")
SERVICE_TIER = "standard"
PRICES_PER_MILLION = {
    "gpt-6.2-sol": {"input": Decimal("2"), "output": Decimal("10")},
    "gpt-6-luna": {"input": Decimal("0.10"), "output": Decimal("0.50")},
}


class CampaignBudgetError(Exception):
    pass


def money(value: object) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CampaignBudgetError("invalid_campaign_budget") from exc
    if not parsed.is_finite():
        raise CampaignBudgetError("invalid_campaign_budget")
    return parsed


def cost_usd(model: str, input_tokens: int, output_tokens: int) -> Decimal:
    if model not in PRICES_PER_MILLION:
        raise CampaignBudgetError("unknown_model_price")
    if type(input_tokens) is not int or type(output_tokens) is not int:
        raise CampaignBudgetError("missing_or_invalid_usage")
    if input_tokens < 0 or output_tokens < 0:
        raise CampaignBudgetError("missing_or_invalid_usage")
    price = PRICES_PER_MILLION[model]
    return (
        Decimal(input_tokens) * price["input"]
        + Decimal(output_tokens) * price["output"]
    ) / Decimal(1_000_000)


def conservative_reservation_usd(model: str, policy) -> Decimal:
    """Reserve every possible call at the full per-call token bounds."""
    per_call = cost_usd(model, policy.max_input_tokens, policy.max_output_tokens)
    return per_call * Decimal(policy.max_provider_calls)


def content_free_request_hash(*, case_id: str, model: str, purpose: str, manifest: dict) -> str:
    identity = {
        "case_id": case_id,
        "model": model,
        "purpose": purpose,
        "oracle_sha256": manifest["oracle_sha256"],
        "held_out_sha256": manifest["held_out_sha256"],
        "context_sha256": manifest["context_sha256"],
        "source_commit": manifest["commit"],
        "versions": manifest["product_prompt_tool_schema_router_versions"],
    }
    encoded = json.dumps(identity, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


class CampaignLedger:
    def __init__(self, path: Path, cap_usd: object, manifest: dict):
        self.path = Path(path)
        self.lock_path = self.path.with_suffix(self.path.suffix + ".lock")
        self.cap = money(cap_usd)
        if self.cap <= 0 or self.cap > MAX_CAMPAIGN_USD:
            raise CampaignBudgetError("campaign_budget_out_of_range")
        self.identity = {
            "schema_version": SCHEMA_VERSION,
            "cap_usd": str(self.cap),
            "price_version": PRICE_VERSION,
            "service_tier": SERVICE_TIER,
            "oracle_sha256": manifest["oracle_sha256"],
            "held_out_sha256": manifest["held_out_sha256"],
            "context_sha256": manifest["context_sha256"],
            "source_commit": manifest["commit"],
            "versions": manifest["product_prompt_tool_schema_router_versions"],
        }
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._locked() as data:
            if data is None:
                self._write({**self.identity, "entries": {}})
            else:
                self._assert_compatible(data)

    @contextmanager
    def _locked(self):
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        descriptor = os.open(self.lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        try:
            with os.fdopen(descriptor, "r+") as lock:
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
                data = None
                if self.path.exists():
                    try:
                        data = json.loads(self.path.read_text())
                    except (OSError, ValueError) as exc:
                        raise CampaignBudgetError("invalid_campaign_ledger") from exc
                yield data
        finally:
            # fdopen owns the descriptor; this is only reached after the lock is released.
            pass

    def _write(self, data: dict) -> None:
        encoded = json.dumps(data, sort_keys=True, separators=(",", ":"))
        descriptor, temporary = tempfile.mkstemp(
            prefix=self.path.name + ".", dir=self.path.parent
        )
        try:
            os.fchmod(descriptor, 0o600)
            with os.fdopen(descriptor, "w") as handle:
                handle.write(encoded)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)

    def _assert_compatible(self, data: dict) -> None:
        if any(data.get(key) != value for key, value in self.identity.items()):
            raise CampaignBudgetError("campaign_ledger_mismatch")
        if not isinstance(data.get("entries"), dict):
            raise CampaignBudgetError("invalid_campaign_ledger")

    @staticmethod
    def _exposure(entries: dict) -> Decimal:
        total = Decimal("0")
        for entry in entries.values():
            status = entry.get("status")
            if status == "completed":
                total += money(entry.get("actual_usd"))
            elif status in {"reserved", "unknown"}:
                total += money(entry.get("reserved_usd"))
            elif status != "cancelled":
                raise CampaignBudgetError("invalid_campaign_ledger")
        return total

    def reserve(
        self,
        request_hash: str,
        *,
        case_id: str,
        model: str,
        purpose: str,
        reserved_usd: Decimal,
    ) -> None:
        if model not in PRICES_PER_MILLION or purpose not in {"smoke", "eval"}:
            raise CampaignBudgetError("invalid_campaign_reservation")
        if (
            type(reserved_usd) is not Decimal
            or not reserved_usd.is_finite()
            or reserved_usd <= 0
        ):
            raise CampaignBudgetError("invalid_campaign_reservation")
        if not isinstance(request_hash, str) or len(request_hash) != 64:
            raise CampaignBudgetError("invalid_campaign_reservation")
        with self._locked() as data:
            self._assert_compatible(data)
            entries = data["entries"]
            if request_hash in entries:
                raise CampaignBudgetError("campaign_request_already_recorded")
            if self._exposure(entries) + reserved_usd > self.cap:
                raise CampaignBudgetError("campaign_budget_exhausted")
            entries[request_hash] = {
                "case_id": case_id,
                "model_requested": model,
                "purpose": purpose,
                "request_hash": request_hash,
                "price_version": PRICE_VERSION,
                "service_tier": SERVICE_TIER,
                "reserved_usd": str(reserved_usd),
                "actual_usd": None,
                "status": "reserved",
                "usage": None,
                "model_returned": None,
            }
            self._write(data)

    def cancel_before_call(self, request_hash: str) -> None:
        with self._locked() as data:
            self._assert_compatible(data)
            entry = data["entries"].get(request_hash)
            if not entry or entry.get("status") != "reserved":
                raise CampaignBudgetError("campaign_reservation_not_open")
            entry["status"] = "cancelled"
            self._write(data)

    def hold_unknown(
        self,
        request_hash: str,
        *,
        calls: int,
        failure_code: str,
        model_returned: str = "",
        usage: dict | None = None,
    ) -> None:
        with self._locked() as data:
            self._assert_compatible(data)
            entry = data["entries"].get(request_hash)
            if not entry or entry.get("status") != "reserved":
                raise CampaignBudgetError("campaign_reservation_not_open")
            safe_usage = {"calls": calls}
            if isinstance(usage, dict):
                for name in ("input_tokens", "output_tokens"):
                    if type(usage.get(name)) is int and usage[name] >= 0:
                        safe_usage[name] = usage[name]
            entry.update(
                status="unknown",
                usage=safe_usage,
                failure_code=failure_code,
                model_returned=model_returned or None,
            )
            self._write(data)

    def entry(self, request_hash: str) -> dict | None:
        with self._locked() as data:
            self._assert_compatible(data)
            value = data["entries"].get(request_hash)
            return json.loads(json.dumps(value)) if value else None

    def settle(
        self,
        request_hash: str,
        *,
        model_returned: str,
        usage: dict,
        outcome: dict | None = None,
    ) -> Decimal:
        with self._locked() as data:
            self._assert_compatible(data)
            entry = data["entries"].get(request_hash)
            if not entry or entry.get("status") != "reserved":
                raise CampaignBudgetError("campaign_reservation_not_open")
            required = {"input_tokens", "output_tokens", "calls"}
            if not isinstance(usage, dict) or not required.issubset(usage):
                entry.update(status="unknown", failure_code="missing_or_invalid_usage")
                self._write(data)
                raise CampaignBudgetError("missing_or_invalid_usage")
            if model_returned != entry["model_requested"]:
                entry.update(
                    status="unknown",
                    model_returned=model_returned,
                    failure_code="model_mismatch",
                )
                self._write(data)
                raise CampaignBudgetError("model_mismatch")
            calls = usage["calls"]
            if type(calls) is not int or calls < 1:
                entry.update(status="unknown", failure_code="missing_or_invalid_usage")
                self._write(data)
                raise CampaignBudgetError("missing_or_invalid_usage")
            actual = cost_usd(
                model_returned, usage["input_tokens"], usage["output_tokens"]
            )
            if actual > money(entry["reserved_usd"]):
                entry.update(status="unknown", failure_code="reservation_underflow")
                self._write(data)
                raise CampaignBudgetError("reservation_underflow")
            entry.update(
                status="completed",
                actual_usd=str(actual),
                model_returned=model_returned,
                usage={
                    "input_tokens": usage["input_tokens"],
                    "output_tokens": usage["output_tokens"],
                    "calls": calls,
                },
                outcome=outcome,
            )
            self._write(data)
            return actual

    def summary(self) -> dict:
        with self._locked() as data:
            self._assert_compatible(data)
            totals = {
                "reserved_usd": Decimal("0"),
                "actual_usd": Decimal("0"),
                "unknown_usd": Decimal("0"),
            }
            for entry in data["entries"].values():
                if entry["status"] == "reserved":
                    totals["reserved_usd"] += money(entry["reserved_usd"])
                elif entry["status"] == "unknown":
                    totals["unknown_usd"] += money(entry["reserved_usd"])
                elif entry["status"] == "completed":
                    totals["actual_usd"] += money(entry["actual_usd"])
            digest = hashlib.sha256(
                json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
            ).hexdigest()
            return {
                "schema_version": SCHEMA_VERSION,
                "cap_usd": str(self.cap),
                "price_version": PRICE_VERSION,
                "service_tier": SERVICE_TIER,
                **{key: str(value) for key, value in totals.items()},
                "exposure_usd": str(self._exposure(data["entries"])),
                "ledger_sha256": digest,
            }
