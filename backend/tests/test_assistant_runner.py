import importlib.util
import json
import sys
from pathlib import Path


SCRIPT = Path("/scripts/run_assistant_evaluation.py") if Path("/scripts/run_assistant_evaluation.py").exists() else Path(__file__).resolve().parents[2] / "scripts/run_assistant_evaluation.py"


def module():
    spec = importlib.util.spec_from_file_location("assistant_eval_runner", SCRIPT)
    value = importlib.util.module_from_spec(spec); spec.loader.exec_module(value)
    return value


def test_live_runner_fails_fast_without_credential(monkeypatch, capsys):
    runner = module(); monkeypatch.delenv("OPENAI_EVAL_API_KEY", raising=False); monkeypatch.delenv("OPENAI_EVAL_API_KEY_FILE", raising=False); monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--mode", "smoke", "--confirm-live"])
    assert runner.main() == 2
    value = json.loads(capsys.readouterr().out)
    assert value["provider_calls"] == 0 and value["cost_usd"] == "0"


def test_live_runner_uses_injected_transport_and_persists_no_content(monkeypatch, capsys):
    runner = module(); monkeypatch.setenv("OPENAI_EVAL_API_KEY", "private-test-only"); monkeypatch.setattr(sys, "argv", [str(SCRIPT), "--mode", "smoke", "--confirm-live"])
    calls=[]
    def transport(key, model, case):
        calls.append(case["id"]); return {"id": "opaque-" + case["id"], "usage": {"input_tokens": 2, "output_tokens": 3}}
    assert runner.main(transport=transport) == 0 and len(calls) == 20
    value=json.loads(capsys.readouterr().out)
    assert value["provider_calls"] == 20 and value["human_persian_verdict"] is None
    encoded=json.dumps(value, ensure_ascii=False)
    assert "private-test-only" not in encoded and "input" not in value["records"][0] and "response" not in value["records"][0]
