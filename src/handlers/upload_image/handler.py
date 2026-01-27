"""
Lambda handler responsible for image upload and metadata creation.
"""

from http import HTTPStatus
import json
from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError as PydanticValidationError

from core.models.errors import (
    DuplicateImageError,
    MetadataOperationFailedError,
    S3Error,
    ValidationError,
)
from core.utils.response import ResponseBuilder
from core.utils.validators import sanitize_validation_errors, validate_request

from .models import ImageUploadRequest, ImageUploadResponse
from .service import UploadService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handle image upload requests.

    The handler decodes base64-encoded image data, validates the incoming
    payload, uploads the image to storage, and returns metadata describing
    the newly created image resource.

    Expected API Gateway event structure:
    {
        "body": "{...}",           # JSON string containing upload data
        "isBase64Encoded": false
    }

    Args:
        event: API Gateway Lambda proxy event containing the upload payload
        context: AWS Lambda execution context

    Returns:
        API Gateway-compatible HTTP response containing created image metadata
    """

    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError as exc:
        logger.exception("Invalid JSON body received", exc_info=exc)
        return ResponseBuilder.validation_error(message="Invalid JSON body")

    try:
        request = validate_request(ImageUploadRequest, body)
    except PydanticValidationError as exc:
        logger.error(
            "Request validation failed",
            extra={"errors": exc.errors()},
        )
        return ResponseBuilder.validation_error(
            message="Invalid request params",
            details={"errors": sanitize_validation_errors(exc.errors())},
        )

    try:
        file_data = UploadService.decode_file(request.file)
        service = UploadService()

        metadata = service.upload_image(
            user_id=request.user_id,
            image_name=request.image_name,
            file_data=file_data,
            description=request.description,
            tags=request.tags,
        )

    except ValidationError as exc:
        logger.exception(
            "Validation error during image upload",
            extra={"user_id": request.user_id},
        )
        return ResponseBuilder.validation_error(message=exc.message)

    except DuplicateImageError as exc:
        logger.exception(
            "Duplicate image upload attempted",
            extra={"user_id": request.user_id},
        )
        return ResponseBuilder.error(
            status=HTTPStatus.UNPROCESSABLE_ENTITY,
            error=exc.error_code,
            message=exc.message,
        )

    except (S3Error, MetadataOperationFailedError) as exc:
        logger.exception(
            "Infrastructure error during image upload",
            extra={"user_id": request.user_id},
        )
        return ResponseBuilder.internal_error(exc.message)

    except Exception:
        logger.exception(
            "Unexpected error occurred while uploading image",
            extra={"user_id": request.user_id},
        )
        return ResponseBuilder.internal_error("Unexpected error occurred while uploading image")

    response = ImageUploadResponse(
        image_id=metadata["image_id"],
        user_id=metadata["user_id"],
        image_name=metadata["image_name"],
        description=metadata.get("description"),
        created_at=metadata["created_at"],
        s3_key=metadata["s3_key"],
        message="Image uploaded successfully",
    )

    return ResponseBuilder.created(response.model_dump())
