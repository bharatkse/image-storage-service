"""Request validation utilities."""

from typing import Any, TypeVar

from pydantic import BaseModel, ValidationError

from core.utils.response import ResponseBuilder

ModelT = TypeVar("ModelT", bound=BaseModel)


def sanitize_validation_errors(errors: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Sanitize Pydantic validation errors for API responses.

    Removes sensitive/internal fields like:
    - url
    - ctx
    - input
    - internal exception details
    """
    sanitized: list[dict[str, str]] = []

    for err in errors:
        field = ".".join(str(x) for x in err.get("loc", [])) or "body"
        raw_msg = err.get("msg", "Invalid value")

        # Remove noisy prefixes
        msg = raw_msg.replace("Value error,", "").strip()

        # Friendly rewrites for common cases
        msg_lower = msg.lower()
        if "base64" in msg_lower:
            msg = "File must be a valid Base64-encoded string"
        elif "field required" in msg_lower:
            msg = "This field is required"
        elif "type" in msg_lower:
            msg = "Invalid value type"

        sanitized.append(
            {
                "field": field,
                "message": msg,
            }
        )

    return sanitized


def validate_request(
    model: type[ModelT],
    data: dict[str, Any],
    *,
    request_id: str | None = None,
    cors_origin: str | None = None,
) -> tuple[bool, ModelT | dict[str, Any]]:
    """Validate request data against a Pydantic model.

    Args:
        model: Pydantic model class
        data: Input data to validate
        request_id: Optional request ID for tracing
        cors_origin: Optional CORS origin

    Returns:
        (True, validated_model) on success
        (False, error_response) on validation failure
    """
    try:
        validated = model(**data)
        return True, validated

    except ValidationError as exc:
        sanitized_errors = sanitize_validation_errors(exc.errors())
        return (
            False,
            ResponseBuilder.validation_error(
                message="Invalid request payload",
                details=sanitized_errors,
                request_id=request_id,
                cors_origin=cors_origin,
            ),
        )
