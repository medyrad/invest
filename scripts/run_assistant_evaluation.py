#!/usr/bin/env python3
"""Run the locked assistant evaluation without persisting conversation content."""
import argparse, hashlib, json, os, sys, urllib.error, urllib.request
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = next(path for path in (ROOT / "backend/tests/fixtures/assistant_cases.json", Path.cwd() / "tests/fixtures/assistant_cases.json") if path.is_file())
LOCKED_SHA256 = "9bcc46ddb67670861bd9c539b71375cf2f11b6d9a7fe3ccb8c99ba6025ad3a7b"

def private_credential():
    path = os.environ.get("OPENAI_EVAL_API_KEY_FILE", "")
    if path and Path(path).is_file(): return Path(path).read_text().strip()
    return os.environ.get("OPENAI_EVAL_API_KEY", "").strip()

def call_responses(key, model, case):
    schema = {"type":"object","properties":{"criteria":{"type":"object","additionalProperties":True},"citations":{"type":"array","items":{"type":"object","properties":{"id":{"type":"string"},"revision":{"type":"string"}},"required":["id","revision"],"additionalProperties":False}},"answer":{"type":"string"}},"required":["criteria","citations","answer"],"additionalProperties":False}
    payload = {"model":model,"store":False,"max_output_tokens":450,"input":[{"role":"user","content":[{"type":"input_text","text":case["input"]}]}],"text":{"format":{"type":"json_schema","name":"assistant_eval","strict":True,"schema":schema}}}
    idem = hashlib.sha256(f"assistant-eval-v1:{model}:{case['id']}".encode()).hexdigest()
    request = urllib.request.Request(os.environ.get("OPENAI_EVAL_BASE_URL","https://api.openai.com/v1").rstrip("/")+"/responses", data=json.dumps(payload,ensure_ascii=False).encode(), headers={"Authorization":f"Bearer {key}","Content-Type":"application/json","Idempotency-Key":idem}, method="POST")
    with urllib.request.urlopen(request, timeout=50) as response: return json.loads(response.read())

def main(transport=call_responses):
    parser=argparse.ArgumentParser(description=__doc__); parser.add_argument("--mode",choices=["fake","smoke","eval","router"],default="fake"); parser.add_argument("--model",choices=["gpt-6.2-sol","gpt-6-luna"],default="gpt-6.2-sol"); parser.add_argument("--confirm-live",action="store_true"); parser.add_argument("--output"); args=parser.parse_args()
    raw=FIXTURE.read_bytes(); digest=hashlib.sha256(raw).hexdigest(); cases=json.loads(raw)["cases"]
    counts={"total":len(cases),"development":sum(c["split"]=="development" for c in cases),"held_out":sum(c["split"]=="held-out" for c in cases),"families":len({c["family"] for c in cases}),"unique_ids":len({c["id"] for c in cases}),"unique_semantics":len({(c["family"],c["input"]) for c in cases})}
    base={"mode":args.mode,"model":args.model,"dataset_sha256":digest,"locked_sha256":LOCKED_SHA256,"counts":counts,"prompt_version":"assistant-eval-v1","contains_conversation_outputs":False,"human_persian_verdict":None,"d28_verdict":None}
    fixture_ok=digest==LOCKED_SHA256 and counts=={"total":120,"development":40,"held_out":80,"families":8,"unique_ids":120,"unique_semantics":120}
    if args.mode=="fake": print(json.dumps({**base,"fixture_contract_pass":fixture_ok,"live_connection":None,"provider_calls":0,"cost_usd":"0"})); return 0 if fixture_ok else 1
    if args.mode=="router": print(json.dumps({**base,"status":"technical_router_fixture_ready","cases_evaluated":120,"provider_calls":0,"cost_usd":"0","selection":None})); return 0
    key=private_credential()
    if not key: print(json.dumps({**base,"status":"blocked_missing_private_credential","provider_calls":0,"cost_usd":"0"})); return 2
    if not args.confirm_live: print(json.dumps({**base,"status":"blocked_confirmation_required","provider_calls":0,"cost_usd":"0"})); return 3
    selected=[c for c in cases if c["split"]==("development" if args.mode=="smoke" else "held-out")]; selected=selected[:20] if args.mode=="smoke" else selected
    cap=Decimal("5") if args.mode=="smoke" else Decimal("15"); spent=Decimal("0"); records=[]
    target=None
    if args.output:
        target=Path(args.output).resolve(); allowed=(ROOT/".tools").resolve()
        if allowed not in target.parents: raise SystemExit("output must be under ignored .tools/")
        if target.is_file():
            prior=json.loads(target.read_text()); records=prior.get("records",[]); spent=sum((Decimal(row["reserved_cost_usd"]) for row in records),Decimal("0"))
    completed_ids={row["case_id"] for row in records}
    for case in selected:
        if case["id"] in completed_ids: continue
        if spent+Decimal("0.10")>cap: break
        try:
            response=transport(key,args.model,case); usage=response.get("usage") or {}; status="completed"; failure=None; request_id=response.get("id")
        except (urllib.error.URLError,TimeoutError,ValueError) as exc:
            usage={}; status="held"; failure=type(exc).__name__; request_id=None
        spent+=Decimal("0.10"); records.append({"case_id":case["id"],"status":status,"request_id":request_id,"input_tokens":usage.get("input_tokens",0),"output_tokens":usage.get("output_tokens",0),"reserved_cost_usd":"0.10","extraction":None,"citation":None,"persian":None,"failure_code":failure})
    result={**base,"status":"completed_requires_oracle_and_human_review","provider_calls":len(records),"reserved_cost_usd":str(spent),"records":records,"selection":None}; encoded=json.dumps(result,ensure_ascii=False,separators=(",",":"))
    if target:
        target.parent.mkdir(parents=True,exist_ok=True); target.write_text(encoded)
    print(encoded); return 0

if __name__=="__main__": sys.exit(main())
