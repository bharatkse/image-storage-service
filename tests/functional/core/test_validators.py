"""Unit tests for request validation utilities."""

from collections.abc import Mapping, Sequence
from typing import Any

from pydantic import BaseModel, ValidationError
import pytest

from core.utils.validators import sanitize_validation_errors, validate_request


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
        errors: Sequence[Mapping[str, Any]] = [
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
        errors: Sequence[Mapping[str, Any]] = [
            {
                "msg": "Invalid value",
            }
        ]

        result = sanitize_validation_errors(errors)

        assert result == [
            {
                "field": "body",
                "message": "Invalid value",
            }
        ]

    def test_removes_value_error_prefix(self) -> None:
        errors: Sequence[Mapping[str, Any]] = [
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
        errors: Sequence[Mapping[str, Any]] = [
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

        result = validate_request(SampleModel, data)

        assert isinstance(result, SampleModel)
        assert result.name == "John"
        assert result.age == 30

    def test_validate_request_missing_required_field(self) -> None:
        data: dict[str, Any] = {}

        with pytest.raises(ValidationError) as exc_info:
            validate_request(RequiredOnlyModel, data)

        errors = sanitize_validation_errors(exc_info.value.errors())

        assert errors == [
            {
                "field": "name",
                "message": "This field is required",
            }
        ]

    def test_validate_request_invalid_type(self) -> None:
        data: dict[str, Any] = {
            "name": "John",
            "age": "not-an-int",
        }

        with pytest.raises(ValidationError) as exc_info:
            validate_request(SampleModel, data)

        errors = sanitize_validation_errors(exc_info.value.errors())

        assert errors[0]["field"] == "age"
        assert "integer" in errors[0]["message"].lower()
