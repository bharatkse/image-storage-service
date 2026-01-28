""" """

import logging

import boto3
from botocore.exceptions import ClientError
import pytest

from .e2e_api_client import E2EAPIClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

S3_IMAGE_BUCKET_NAME = "image-storage-images-snd"
DYNAMODB_TABLE_NAME = "image-storage-metadata-snd"
ENDPOINT_BASE_URL = "http://localhost:4566"

# ============================================================================
# API Details Fixture
# ============================================================================


@pytest.fixture(scope="session")
def api_details():
    """Get API Gateway details from LocalStack"""
    try:
        apigateway = boto3.client("apigateway", endpoint_url=ENDPOINT_BASE_URL)

        apis = apigateway.get_rest_apis()
        api = next(api for api in apis["items"] if "image-storage" in api["name"])
        api_id = api["id"]

        keys = apigateway.get_api_keys(includeValues=True)
        api_key = keys["items"][0]["value"] if keys["items"] else "test-key"

        endpoint = f"{ENDPOINT_BASE_URL}/restapis/{api_id}/snd/_user_request_"

        return {"api_id": api_id, "api_key": api_key, "endpoint": endpoint, "stage": "snd"}
    except Exception as e:
        logger.warning(f"Could not get API details from LocalStack: {e}")
        pytest.skip(f"Could not get API details from LocalStack: {e}")


# ============================================================================
# API Headers Fixture
# ============================================================================


@pytest.fixture(scope="session")
def api_headers(api_details):
    """Default HTTP headers for API requests"""
    return {"Content-Type": "application/json", "x-api-key": api_details["api_key"]}


# ============================================================================
# API Client Fixture
# ============================================================================


@pytest.fixture
def api_client(api_details, api_headers):
    """HTTP client wrapper for E2E API testing"""
    _client = E2EAPIClient(api_details["endpoint"], api_headers)
    yield _client


@pytest.fixture(scope="function", autouse=True)
def cleanup_storage_after_each_test():
    """Clean S3 and DynamoDB to prevent test data leakage."""
    _cleanup_s3()
    _cleanup_dynamodb()


def _cleanup_s3():
    """Clean all objects from S3 bucket"""
    logger.info("Cleaning S3 bucket: %s", S3_IMAGE_BUCKET_NAME)

    s3_client = boto3.client("s3", endpoint_url=ENDPOINT_BASE_URL)

    try:
        response = s3_client.list_objects_v2(Bucket=S3_IMAGE_BUCKET_NAME)
        objects = response.get("Contents", [])

        if not objects:
            logger.info("S3 bucket is already empty")
            return

        for obj in objects:
            s3_client.delete_object(Bucket=S3_IMAGE_BUCKET_NAME, Key=obj["Key"])

        logger.info("Deleted %d objects from S3 bucket", len(objects))

    except ClientError as err:
        logger.error("Failed to cleanup S3 bucket: %s", S3_IMAGE_BUCKET_NAME, exc_info=err)


def _cleanup_dynamodb():
    """Delete all items from the DynamoDB metadata table using allowed IAM permissions."""
    logger.info("Cleaning DynamoDB table: %s", DYNAMODB_TABLE_NAME)

    dynamodb = boto3.resource("dynamodb", endpoint_url=ENDPOINT_BASE_URL)
    table = dynamodb.Table(DYNAMODB_TABLE_NAME)

    try:
        deleted = 0
        start_key = None

        while True:
            scan_kwargs = {
                "ProjectionExpression": "image_id",
            }
            if start_key:
                scan_kwargs["ExclusiveStartKey"] = start_key

            response = table.scan(**scan_kwargs)
            items = response.get("Items", [])

            for item in items:
                table.delete_item(Key={"image_id": item["image_id"]})
                deleted += 1

            start_key = response.get("LastEvaluatedKey")
            if not start_key:
                break

        logger.info("Deleted %d items from DynamoDB table", deleted)

    except ClientError as err:
        logger.error(
            "Failed to cleanup DynamoDB table: %s",
            DYNAMODB_TABLE_NAME,
            exc_info=err,
        )


# ============================================================================
# Test User IDs
# ============================================================================


@pytest.fixture
def test_user_id():
    """Default test user ID"""
    return "test-user-default"


@pytest.fixture
def test_user_ids():
    """Collection of test user IDs"""
    return {
        "upload": "e2e-upload-user",
        "list": "e2e-list-user",
        "get": "e2e-get-user",
        "delete": "e2e-delete-user",
        "lifecycle": "e2e-lifecycle-user",
        "auth": "e2e-auth-user",
        "error": "e2e-error-user",
    }


# ============================================================================
# Sample Image Data
# ============================================================================

SAMPLE_JPEG_BASE64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8VAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwCwAA8A/9k="


@pytest.fixture
def upload_valid_payload() -> dict:
    return {
        "user_id": "test-user-123",
        "image_name": "sample.jpg",
        "description": "Sample test image",
        "tags": ["test", "sample"],
        "file": SAMPLE_JPEG_BASE64,
    }
