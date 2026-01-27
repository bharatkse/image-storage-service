import base64
import json
from http import HTTPStatus
from types import SimpleNamespace
from typing import Any, cast

import pytest

from core.utils.response import JsonDict, ResponseBuilder, api_handler, handle_exception


def parse_body(resp: dict[str, Any]) -> dict[str, Any]:
    body = resp.get("body")
    if not body:
        return {}

    return cast(dict[str, Any], json.loads(body))


def test_ok_response() -> None:
    resp = ResponseBuilder.ok({"foo": "bar"}, request_id="req-1", cors_origin="*")
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.OK
    assert parsed["foo"] == "bar"
    assert parsed["request_id"] == "req-1"
    assert resp["headers"]["Access-Control-Allow-Origin"] == "*"


def test_created_response() -> None:
    resp = ResponseBuilder.created({"id": 1})
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.CREATED
    assert parsed["id"] == 1


def test_no_content_response() -> None:
    resp = ResponseBuilder.no_content(cors_origin="https://example.com")

    assert resp["statusCode"] == HTTPStatus.NO_CONTENT
    assert resp["body"] == ""
    assert resp["headers"]["Access-Control-Allow-Origin"] == "https://example.com"


@pytest.mark.parametrize(
    "func,status,error_name",
    [
        (ResponseBuilder.bad_request, HTTPStatus.BAD_REQUEST, "BAD_REQUEST"),
        (ResponseBuilder.unauthorized, HTTPStatus.UNAUTHORIZED, "UNAUTHORIZED"),
        (ResponseBuilder.forbidden, HTTPStatus.FORBIDDEN, "FORBIDDEN"),
        (ResponseBuilder.not_found, HTTPStatus.NOT_FOUND, "NOT_FOUND"),
        (
            ResponseBuilder.internal_error,
            HTTPStatus.INTERNAL_SERVER_ERROR,
            "INTERNAL_SERVER_ERROR",
        ),
    ],
)
def test_error_responses_use_explicit_message(func, status, error_name) -> None:
    resp = func("bad", request_id="req-x", cors_origin="*")
    parsed = parse_body(resp)

    assert resp["statusCode"] == status
    assert parsed["error"] == error_name
    assert parsed["message"] == "bad"
    assert parsed["request_id"] == "req-x"
    assert "timestamp" in parsed


def test_default_error_messages() -> None:
    assert parse_body(ResponseBuilder.unauthorized())["message"] == "Unauthorized"
    assert parse_body(ResponseBuilder.forbidden())["message"] == "Forbidden"
    assert parse_body(ResponseBuilder.not_found())["message"] == "Resource not found"
    assert (
        parse_body(ResponseBuilder.internal_error())["message"]
        == "Internal server error"
    )


def test_validation_error() -> None:
    resp = ResponseBuilder.validation_error(
        message="Invalid input",
        details={"field": "name"},
        request_id="req-val",
    )
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.UNPROCESSABLE_ENTITY
    assert parsed["error"] == "VALIDATION_FAILED"
    assert parsed["message"] == "Invalid input"
    assert parsed["details"]["field"] == "name"
    assert parsed["request_id"] == "req-val"


def test_binary_response() -> None:
    content = b"binary-data"

    resp = ResponseBuilder.binary_response(
        content,
        content_type="image/png",
        cors_origin="*",
    )

    assert resp["statusCode"] == HTTPStatus.OK
    assert resp["isBase64Encoded"] is True
    assert base64.b64decode(resp["body"]) == content
    assert resp["headers"]["Content-Type"] == "image/png"


def test_handle_exception_value_error() -> None:
    resp = handle_exception(ValueError("bad"), request_id="req-1")
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.BAD_REQUEST
    assert parsed["message"] == "bad"


def test_handle_exception_permission_error() -> None:
    resp = handle_exception(PermissionError("denied"), request_id="req-2")
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.FORBIDDEN
    assert parsed["message"] == "denied"


def test_handle_exception_generic() -> None:
    resp = handle_exception(RuntimeError("boom"))
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert parsed["message"] == "boom"


def test_api_handler_success() -> None:
    @api_handler
    def handler(
        event: Any,
        context: Any,
        *,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder.ok(
            {"msg": "ok"},
            request_id=context.aws_request_id,
            cors_origin=cors_origin,
        )

    context = SimpleNamespace(aws_request_id="req-ok")
    resp = handler({}, context, cors_origin="*")

    parsed = parse_body(resp)
    assert parsed["msg"] == "ok"
    assert parsed["request_id"] == "req-ok"


def test_api_handler_catches_exception() -> None:
    @api_handler
    def handler(
        event: Any,
        context: Any,
        *,
        cors_origin: str | None = None,
    ) -> JsonDict:
        raise ValueError("Bad input")

    context = SimpleNamespace(aws_request_id="req-err")
    resp = handler({}, context)

    parsed = parse_body(resp)
    assert parsed["message"] == "Bad input"
    assert parsed["request_id"] == "req-err"
