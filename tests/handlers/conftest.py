import base64
import json
from types import SimpleNamespace
from typing import Any

import pytest


@pytest.fixture
def lambda_context(monkeypatch):
    context = SimpleNamespace(
        aws_request_id="test-request-id",
        function_name="test-function",
        memory_limit_in_mb=256,
        invoked_function_arn="arn:aws:lambda:us-east-1:000000000000:function:test",
        log_group_name="/aws/lambda/test-function",
        log_stream_name="2024/01/01/[$LATEST]test",
    )

    monkeypatch.setattr(
        "aws_lambda_powertools.utilities.typing.LambdaContext",
        lambda: context,
        raising=False,
    )

    return context


@pytest.fixture
def get_image_event() -> dict[str, Any]:
    return {
        "pathParameters": {"image_id": "img_abc123"},
        "queryStringParameters": {"metadata": "false"},
        "headers": {"x-api-key": "test-api-key"},
    }


@pytest.fixture
def get_image_event_with_metadata() -> dict[str, Any]:
    return {
        "pathParameters": {"image_id": "img_abc123"},
        "queryStringParameters": {"metadata": "true"},
        "headers": {"x-api-key": "test-api-key"},
    }


@pytest.fixture
def list_images_event() -> dict[str, Any]:
    return {
        "queryStringParameters": {
            "user_id": "john",
            "limit": "20",
            "offset": "0",
        },
        "headers": {"x-api-key": "test-api-key"},
    }


@pytest.fixture
def delete_image_event() -> dict[str, Any]:
    return {
        "pathParameters": {"image_id": "img_abc123"},
        "headers": {"x-api-key": "test-api-key"},
    }


@pytest.fixture
def upload_image_event(sample_image_binary) -> dict[str, Any]:
    return {
        "body": json.dumps(
            {
                "file": base64.b64encode(sample_image_binary).decode("utf-8"),
                "user_id": "john",
                "image_name": "test_upload.png",
                "description": "Test upload",
                "tags": "test,upload",
            }
        ),
        "headers": {
            "Content-Type": "application/json",
            "x-api-key": "test-api-key",
        },
    }
