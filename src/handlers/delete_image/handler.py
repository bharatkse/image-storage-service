"""
Lambda handler responsible for deleting an image resource.
"""

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from core.models.errors import (
    ImageDeletionFailedError,
    MetadataOperationFailedError,
    NotFoundError,
)
from core.utils.response import ResponseBuilder
from core.utils.validators import validate_request

from .models import DeleteImageRequest, DeleteImageResponse
from .service import DeleteService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> ResponseBuilder:
    """
    Handle image deletion requests.

    This function:
    - Extracts the image identifier from API Gateway path parameters
    - Validates the incoming request payload
    - Delegates deletion to the service layer
    - Translates domain and runtime errors into HTTP responses

    Expected API Gateway event structure:
    {
        "pathParameters": {
            "image_id": "img_123..."
        }
    }

    Args:
        event: API Gateway Lambda proxy event
        context: AWS Lambda execution context

    Returns:
        API Gateway-compatible HTTP response dictionary
    """
    # Extract path parameters (API Gateway may pass None)
    path_params = event.get("pathParameters") or {}

    # Validate and hydrate request model
    is_valid, result = validate_request(
        DeleteImageRequest,
        {"image_id": path_params.get("image_id")},
    )
    if not is_valid:
        logger.error(
            "Request validation failed",
            extra={"validation_result": str(result)},
        )
        # Validation errors already return a formatted HTTP response
        return result

    request = result
    service = DeleteService()

    try:
        delete_result = service.delete_image(request.image_id)

    except NotFoundError:
        logger.exception(
            "Image not found during delete",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.not_found(f"Image not found: {request.image_id}")

    except (ImageDeletionFailedError, MetadataOperationFailedError) as exc:
        logger.exception(
            "Deletion failed",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.internal_error(exc.message)

    except Exception:
        logger.exception(
            "Unexpected delete error",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.internal_error("Failed to delete image")

    response = DeleteImageResponse(
        image_id=delete_result["image_id"],
        message="Image deleted successfully",
        deleted_at=delete_result["deleted_at"],
        s3_key=delete_result["s3_key"],
    )

    return ResponseBuilder.ok(response.model_dump())
