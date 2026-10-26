from main import app

import pytest
from fastapi.testclient import TestClient


client = TestClient(app)


@pytest.mark.parametrize(
    ("body", "expected_body"),
    [
        (
            {"amount": 5000},
            {"amount": 5000, "discount": 0, "payable": 5000},
        ),
        (
            {"amount": 20000},
            {"amount": 20000, "discount": 1000, "payable": 19000},
        ),
        (
            {"amount": 1},
            {"amount": 1, "discount": 0, "payable": 1},
        ),
        (
            {"amount": 100000},
            {"amount": 100000, "discount": 1000, "payable": 99000},
        ),
        (
            {"amount": 9999},
            {"amount": 9999, "discount": 0, "payable": 9999},
        ),
        (
            {"amount": 10000},
            {"amount": 10000, "discount": 1000, "payable": 9000},
        ),
        (
            {"amount": 10001},
            {"amount": 10001, "discount": 1000, "payable": 9001},
        ),
    ],
    ids=[
        "normal-below-discount-threshold",
        "normal-above-discount-threshold",
        "allowed-minimum",
        "allowed-maximum",
        "discount-boundary-minus-one",
        "discount-boundary-core-regression",
        "discount-boundary-plus-one",
    ],
)
def test_quote_success_contract(body, expected_body):
    response = client.post("/quotes", json=body)

    assert response.status_code == 200
    assert response.json() == expected_body


@pytest.mark.parametrize(
    "body",
    [
        {"amount": 0},
        {"amount": 100001},
        {},
        {"amount": "10000"},
        {"amount": True},
        {"amount": 10000.0},
    ],
    ids=[
        "below-allowed-minimum",
        "above-allowed-maximum",
        "required-amount-missing",
        "string-is-not-a-strict-integer",
        "boolean-is-not-a-strict-integer",
        "float-is-not-a-strict-integer",
    ],
)
def test_quote_invalid_input_contract(body):
    response = client.post("/quotes", json=body)

    assert response.status_code == 422
