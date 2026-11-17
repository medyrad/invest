import json
from pathlib import Path

import pytest
from jsonschema import validate
from openapi_spec_validator import validate as validate_openapi
from rest_framework.exceptions import ValidationError

from config.protocol import parse_version, validate_idempotency_key


def test_openapi_and_actual_responses(client):
    contract = json.loads(Path("/contracts/openapi.yaml").read_text())
    validate_openapi(contract)
    assert client.get("/api/v1/schema").json() == contract
    for path, name in [("health/live", "Health"), ("auth/csrf", "Csrf"), ("missing", "Error")]:
        validate(client.get("/api/v1/" + path).json(), contract["components"]["schemas"][name])


def test_concurrency_headers():
    assert parse_version('"12"') == 12
    assert parse_version(None) is None
    assert validate_idempotency_key("request_1:retry-2") == "request_1:retry-2"
    assert validate_idempotency_key(None) is None


@pytest.mark.parametrize(
    ("name", "helper", "valid", "invalid"),
    [
        ("VersionHeader", parse_version, '"999999999999999999"', '"1000000000000000000"'),
        ("VersionHeader", parse_version, '"1"', '"1"\n'),
        ("IdempotencyKey", validate_idempotency_key, "x" * 128, "x" * 129),
        ("IdempotencyKey", validate_idempotency_key, "key:1", "key:1\n"),
    ],
)
def test_header_contract_and_runtime_agree(name, helper, valid, invalid):
    from jsonschema.exceptions import ValidationError as SchemaError

    contract = json.loads(Path("/contracts/openapi.yaml").read_text())
    schema = contract["components"]["schemas"][name]
    validate(valid, schema)
    helper(valid)
    with pytest.raises(SchemaError):
        validate(invalid, schema)
    with pytest.raises(ValidationError):
        helper(invalid)


@pytest.mark.parametrize("value", ['W/"1"', '"0"', '"-1"', "1", '"01"', '"۱"', '"1"\n'])
def test_invalid_versions(value):
    with pytest.raises(ValidationError):
        parse_version(value)


@pytest.mark.parametrize("value", ["", "الف", "a b", "a\n", "x" * 129])
def test_invalid_idempotency(value):
    with pytest.raises(ValidationError):
        validate_idempotency_key(value)


@pytest.mark.urls("tests.urls")
@pytest.mark.parametrize(
    ("header", "value", "code"),
    [
        ("HTTP_IF_MATCH", "1", "invalid_version"),
        ("HTTP_IDEMPOTENCY_KEY", "bad key", "invalid_idempotency_key"),
    ],
)
def test_header_errors_keep_stable_api_code(client, header, value, code):
    token = client.get("/api/v1/auth/csrf").json()["csrfToken"]
    response = client.post("/api/v1/_test/probe", HTTP_X_CSRFTOKEN=token, **{header: value})
    assert response.status_code == 400
    assert response.json()["error"]["code"] == code
    assert response.json()["error"]["request_id"] == response["X-Request-ID"]
