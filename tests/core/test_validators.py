"""Unit tests for request validation utilities."""

import json
from typing import Any

from pydantic import BaseModel

from core.utils.validators import (
    sanitize_validation_errors,
    validate_request,
)


class SampleModel(BaseModel):
    """Sample model for validation tests."""

    name: str
    age: int


class RequiredOnlyModel(BaseModel):
    """Model with a required field only."""

    name: str


class TestSanitizeValidationErrors:
    """Tests for sanitize_validation_errors."""

    def test_sanitizes_required_field(self) -> None:
        errors = [
            {
                "loc": ("name",),
                "msg": "Field required",
            }
        ]

        result = sanitize_validation_errors(errors)

        assert result == [
            {
                "field": "name",
                "message": "This field is required",
            }
        ]

    def test_defaults_field_to_body(self) -> None:
        errors = [{"msg": "Invalid value"}]

        result = sanitize_validation_errors(errors)

        assert result == [
            {
                "field": "body",
                "message": "Invalid value",
            }
        ]

    def test_removes_value_error_prefix(self) -> None:
        errors = [
            {
                "loc": ("age",),
                "msg": "Value error, must be positive",
            }
        ]

        result = sanitize_validation_errors(errors)

        assert result == [
            {
                "field": "age",
                "message": "must be positive",
            }
        ]

    def test_preserves_pydantic_type_message(self) -> None:
        """Pydantic v2 type errors are not rewritten."""
        errors = [
            {
                "loc": ("age",),
                "msg": "Input should be a valid integer",
            }
        ]

        result = sanitize_validation_errors(errors)

        assert result == [
            {
                "field": "age",
                "message": "Input should be a valid integer",
            }
        ]


class TestValidateRequest:
    """Tests for validate_request."""

    def test_validate_request_success(self) -> None:
        data: dict[str, Any] = {
            "name": "John",
            "age": 30,
        }

        is_valid, result = validate_request(SampleModel, data)

        assert is_valid is True
        assert isinstance(result, SampleModel)
        assert result.name == "John"
        assert result.age == 30

    def test_validate_request_missing_required_field(self) -> None:
        data: dict[str, Any] = {}

        is_valid, result = validate_request(
            RequiredOnlyModel,
            data,
            request_id="req-1",
            cors_origin="*",
        )

        assert is_valid is False
        assert result["statusCode"] == 422

        body = json.loads(result["body"])

        assert body["message"] == "Invalid request payload"
        assert body["request_id"] == "req-1"
        assert body["details"][0]["field"] == "name"
        assert body["details"][0]["message"] == "This field is required"

        assert result["headers"]["Access-Control-Allow-Origin"] == "*"

    def test_validate_request_invalid_type(self) -> None:
        data: dict[str, Any] = {
            "name": "John",
            "age": "not-an-int",
        }

        is_valid, result = validate_request(SampleModel, data)

        assert is_valid is False
        assert result["statusCode"] == 422

        body = json.loads(result["body"])

        detail = body["details"][0]
        assert detail["field"] == "age"
        assert detail["message"] == "Input should be a valid integer, unable to parse string as an integer"
