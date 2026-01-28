"""Request validation utilities."""

from collections.abc import Mapping, Sequence
from typing import Any, TypeVar

from pydantic import BaseModel

ModelT = TypeVar("ModelT", bound=BaseModel)


def sanitize_validation_errors(
    errors: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Sanitize Pydantic validation errors for API responses.

    Removes sensitive/internal fields and rewrites messages
    into user-friendly validation errors.
    """
    sanitized: list[dict[str, Any]] = []

    for err in errors:
        field = ".".join(str(x) for x in err.get("loc", [])) or "body"
        raw_msg = err.get("msg", "Invalid value")

        msg = raw_msg.replace("Value error,", "").strip()
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
) -> ModelT:
    """Validate request data against a Pydantic model.

    Args:
        model: Pydantic model class
        data: Input data to validate

    Returns:
        Validated Pydantic model instance

    Raises:
        ValidationError: If validation fails
    """
    instance: ModelT = model(**data)
    return instance
