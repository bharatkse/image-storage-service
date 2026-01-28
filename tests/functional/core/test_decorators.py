import base64
import json
from http import HTTPStatus
from types import SimpleNamespace
from typing import Any, cast

from core.utils.decorators import api_gateway_handler
from core.utils.response import ResponseBuilder, JsonDict



def parse_body(resp: dict[str, Any]) -> dict[str, Any]:
    """Parse JSON body from API Gateway response."""
    body = resp.get("body")
    if not body:
        return {}
    return cast(dict[str, Any], json.loads(body))



def test_binary_response() -> None:
    """Binary responses are base64-encoded and preserve content."""
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


def test_api_handler_success() -> None:
    """Successful handler execution returns response unchanged."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        return ResponseBuilder.ok(
            {"msg": "ok"},
            request_id=context.aws_request_id,
            cors_origin="*",
        )

    context = SimpleNamespace(aws_request_id="req-ok")
    resp = handler({}, context)

    parsed = parse_body(resp)
    assert resp["statusCode"] == HTTPStatus.OK
    assert parsed["msg"] == "ok"
    assert parsed["request_id"] == "req-ok"


def test_api_handler_options_preflight() -> None:
    """OPTIONS request returns 204 with CORS headers."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:  # pragma: no cover
        raise AssertionError("Should not be called")

    resp = handler({"httpMethod": "OPTIONS"}, SimpleNamespace())

    assert resp["statusCode"] == HTTPStatus.NO_CONTENT
    assert resp["body"] == ""
    assert "Access-Control-Allow-Origin" in resp["headers"]



def test_value_error_returns_400() -> None:
    """ValueError returns 400 with user-friendly message."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise ValueError("Invalid input data")

    resp = handler({}, SimpleNamespace(aws_request_id="req-400"))
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.BAD_REQUEST
    assert parsed["message"] == "Invalid input data"
    assert parsed["request_id"] == "req-400"


def test_type_error_returns_400() -> None:
    """TypeError returns 400."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise TypeError("wrong type")

    resp = handler({}, SimpleNamespace())
    assert resp["statusCode"] == HTTPStatus.BAD_REQUEST


def test_permission_error_returns_403() -> None:
    """PermissionError returns 403."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise PermissionError("no access")

    resp = handler({}, SimpleNamespace(aws_request_id="req-403"))
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.FORBIDDEN
    assert parsed["message"] == "You don't have permission to perform this action."
    assert parsed["request_id"] == "req-403"


def test_lookup_error_returns_404() -> None:
    """LookupError returns 404."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise LookupError("not found")

    resp = handler({}, SimpleNamespace())
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.NOT_FOUND
    assert parsed["message"] == "The requested resource was not found."


def test_file_not_found_returns_404() -> None:
    """FileNotFoundError returns 404."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise FileNotFoundError("missing")

    resp = handler({}, SimpleNamespace())
    assert resp["statusCode"] == HTTPStatus.NOT_FOUND



def test_memory_error_returns_413() -> None:
    """MemoryError maps to 413 Payload Too Large."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise MemoryError("too big")

    resp = handler({}, SimpleNamespace())
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.REQUEST_ENTITY_TOO_LARGE
    assert "too large" in parsed["message"].lower()


def test_timeout_error_returns_504() -> None:
    """TimeoutError returns 504 Gateway Timeout."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise TimeoutError("timeout")

    resp = handler({}, SimpleNamespace())
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.GATEWAY_TIMEOUT
    assert "too long" in parsed["message"].lower()


def test_connection_error_returns_503() -> None:
    """ConnectionError returns 503 Service Unavailable."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise ConnectionError("db down")

    resp = handler({}, SimpleNamespace())
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.SERVICE_UNAVAILABLE
    assert "unable to connect" in parsed["message"].lower()


def test_unexpected_exception_returns_500() -> None:
    """Unhandled exception returns generic 500."""

    @api_gateway_handler
    def handler(event: Any, context: Any) -> JsonDict:
        raise RuntimeError("boom")

    resp = handler({}, SimpleNamespace(aws_request_id="req-500"))
    parsed = parse_body(resp)

    assert resp["statusCode"] == HTTPStatus.INTERNAL_SERVER_ERROR
    assert parsed["message"] == (
        "We're experiencing technical difficulties. Please try again in a few moments."
    )
    assert parsed["request_id"] == "req-500"
