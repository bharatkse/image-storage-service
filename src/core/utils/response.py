"""
Centralized API response builder for AWS Lambda / API Gateway.
"""

from __future__ import annotations

import base64
import json
from collections.abc import Callable
from functools import wraps
from http import HTTPStatus
from typing import Any, Protocol

from core.utils.time import utc_now_iso

JsonDict = dict[str, Any]


class LambdaHandler(Protocol):
    def __call__(
        self,
        event: Any,
        context: Any,
        *,
        cors_origin: str | None = None,
    ) -> JsonDict: ...


class ResponseBuilder:
    """Factory for API Gateway-compatible HTTP responses."""

    DEFAULT_HEADERS: dict[str, str] = {
        "Content-Type": "application/json",
    }

    CORS_HEADERS: dict[str, str] = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Api-Key",
        "Access-Control-Allow-Methods": "OPTIONS,GET,POST,PUT,DELETE",
    }

    @staticmethod
    def _build_headers(cors_origin: str | None = None) -> dict[str, str]:
        headers: dict[str, str] = dict(ResponseBuilder.DEFAULT_HEADERS)

        if cors_origin:
            headers.update(ResponseBuilder.CORS_HEADERS)
            headers["Access-Control-Allow-Origin"] = cors_origin

        return headers

    @staticmethod
    def _response(
        *,
        status: HTTPStatus,
        body: JsonDict | None = None,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        payload: JsonDict = {}

        if body:
            payload.update(body)

        if request_id:
            payload["request_id"] = request_id

        response: JsonDict = {
            "statusCode": status.value,
            "headers": ResponseBuilder._build_headers(cors_origin),
            "body": json.dumps(payload),
        }

        return response

    @staticmethod
    def ok(
        body: JsonDict,
        *,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder._response(
            status=HTTPStatus.OK,
            body=body,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def created(
        body: JsonDict,
        *,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder._response(
            status=HTTPStatus.CREATED,
            body=body,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def no_content(*, cors_origin: str | None = None) -> JsonDict:
        response: JsonDict = {
            "statusCode": HTTPStatus.NO_CONTENT.value,
            "headers": ResponseBuilder._build_headers(cors_origin),
            "body": "",
        }
        return response

    @staticmethod
    def error(
        *,
        status: HTTPStatus,
        message: str,
        error: str | None = None,
        details: JsonDict | None = None,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        payload: JsonDict = {
            "error": error or status.name,
            "message": message,
            "timestamp": utc_now_iso(),
        }

        if details:
            payload["details"] = details

        return ResponseBuilder._response(
            status=status,
            body=payload,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def bad_request(
        message: str,
        *,
        details: JsonDict | None = None,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder.error(
            status=HTTPStatus.BAD_REQUEST,
            message=message,
            details=details,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def validation_error(
        *,
        message: str,
        details: JsonDict | None = None,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        """422 Unprocessable Entity validation error."""
        return ResponseBuilder.error(
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            error="VALIDATION_ERROR",
            message=message,
            details=details,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def unauthorized(
        message: str = "Unauthorized",
        *,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder.error(
            status=HTTPStatus.UNAUTHORIZED,
            message=message,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def forbidden(
        message: str = "Forbidden",
        *,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder.error(
            status=HTTPStatus.FORBIDDEN,
            message=message,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def not_found(
        message: str = "Resource not found",
        *,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder.error(
            status=HTTPStatus.NOT_FOUND,
            message=message,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def internal_error(
        message: str = "Internal server error",
        *,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        return ResponseBuilder.error(
            status=HTTPStatus.INTERNAL_SERVER_ERROR,
            message=message,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def problem_detail(
        *,
        status: HTTPStatus,
        title: str,
        detail: str,
        instance: str | None = None,
        request_id: str | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        payload: JsonDict = {
            "type": f"https://httpstatuses.com/{status.value}",
            "title": title,
            "status": status.value,
            "detail": detail,
        }

        if instance:
            payload["instance"] = instance

        return ResponseBuilder._response(
            status=status,
            body=payload,
            request_id=request_id,
            cors_origin=cors_origin,
        )

    @staticmethod
    def binary_response(
        content: bytes,
        *,
        content_type: str,
        headers: dict[str, str] | None = None,
        cors_origin: str | None = None,
    ) -> JsonDict:
        response_headers: dict[str, str] = {
            "Content-Type": content_type,
            "Content-Length": str(len(content)),
        }

        if cors_origin:
            response_headers.update(ResponseBuilder.CORS_HEADERS)
            response_headers["Access-Control-Allow-Origin"] = cors_origin

        if headers:
            response_headers.update(headers)

        response: JsonDict = {
            "statusCode": HTTPStatus.OK.value,
            "headers": response_headers,
            "body": base64.b64encode(content).decode("utf-8"),
            "isBase64Encoded": True,
        }

        return response


def handle_exception(
    exc: Exception,
    *,
    request_id: str | None = None,
    cors_origin: str | None = None,
) -> JsonDict:
    if isinstance(exc, ValueError):
        return ResponseBuilder.bad_request(
            str(exc), request_id=request_id, cors_origin=cors_origin
        )

    if isinstance(exc, PermissionError):
        return ResponseBuilder.forbidden(
            str(exc), request_id=request_id, cors_origin=cors_origin
        )

    return ResponseBuilder.internal_error(
        str(exc), request_id=request_id, cors_origin=cors_origin
    )


def api_handler(func: LambdaHandler) -> Callable[..., JsonDict]:
    """Lambda handler decorator with exception handling and request_id injection."""

    @wraps(func)
    def wrapper(
        event: Any,
        context: Any,
        *,
        cors_origin: str | None = None,
    ) -> JsonDict:
        request_id = getattr(context, "aws_request_id", None)

        try:
            return func(event, context, cors_origin=cors_origin)
        except Exception as exc:  # noqa: BLE001
            return handle_exception(
                exc,
                request_id=request_id,
                cors_origin=cors_origin,
            )

    return wrapper
