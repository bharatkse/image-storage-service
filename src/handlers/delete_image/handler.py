"""
Lambda handler responsible for deleting an image resource.
"""

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError

from core.models.errors import (
    MetadataOperationFailedError,
    NotFoundError,
    S3Error,
)
from core.utils.decorators import api_gateway_handler
from core.utils.response import ResponseBuilder
from core.utils.validators import sanitize_validation_errors, validate_request

from .models import DeleteImageRequest, DeleteImageResponse
from .service import DeleteService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@api_gateway_handler
@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handle image deletion requests.

    This function:
    - Extracts the image identifier from API Gateway path parameters
    - Validates the incoming request payload
    - Delegates deletion to the service layer
    - Translates domain and runtime errors into HTTP responses

    Args:
        event: API Gateway Lambda proxy event
        context: AWS Lambda execution context

    Returns:
        API Gateway-compatible HTTP response
    """
    logger.info(
        "Received image delete request",
        extra={
            "http_method": event.get("httpMethod"),
            "path": event.get("path"),
            "query_params": event.get("queryStringParameters"),
            "request_id": getattr(context, "aws_request_id", None),
            "function_name": getattr(context, "function_name", None),
            "remaining_time_ms": context.get_remaining_time_in_millis()
            if hasattr(context, "get_remaining_time_in_millis")
            else None,
        },
    )

    path_params = event.get("pathParameters") or {}

    try:
        request = validate_request(
            DeleteImageRequest,
            {"image_id": path_params.get("image_id")},
        )
    except ValidationError as exc:
        logger.error(
            "Request validation failed",
            extra={"errors": exc.errors()},
        )
        return ResponseBuilder.bad_request(
            message="Invalid request payload",
            details={"errors": sanitize_validation_errors([err for err in exc.errors()])},
        )

    service = DeleteService()

    try:
        delete_result = service.delete_image(request.image_id)

    except NotFoundError:
        logger.exception(
            "Image not found during delete",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.not_found(f"Image not found: {request.image_id}")

    except (S3Error, MetadataOperationFailedError) as exc:
        logger.exception(
            "Deletion failed",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.internal_error(exc.message)

    response = DeleteImageResponse(
        image_id=delete_result["image_id"],
        message="Image deleted successfully",
        deleted_at=delete_result["deleted_at"],
        s3_key=delete_result["s3_key"],
    )

    return ResponseBuilder.ok(response.model_dump())
