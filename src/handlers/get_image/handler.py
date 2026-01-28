"""
Lambda handler responsible for image retrieval and download.
"""

from typing import Any, Literal

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

from .models import GetImageRequest, ImageMetadataHeader
from .service import GetService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@api_gateway_handler
@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handle image view or download requests.

    This function:
     - Default: return view URL
        - download=true: return download URL
        - metadata=true: include metadata in response
    Args:
        event: API Gateway event payload.
        context: AWS Lambda runtime context.

    Returns:
        API Gateway-compatible response dictionary.
    """
    logger.info(
        "Received image view/download request",
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
    query_params = event.get("queryStringParameters") or {}

    params = {
        "image_id": path_params.get("image_id"),
        "metadata": query_params.get("metadata", "false").lower() == "true",
        "download": query_params.get("download", "false").lower() == "true",
    }

    try:
        request = validate_request(
            GetImageRequest,
            params,
        )
    except ValidationError as exc:
        logger.error(
            "Request validation failed",
            extra={"errors": exc.errors()},
        )
        return ResponseBuilder.bad_request(
            message="Invalid request params",
            details={"errors": sanitize_validation_errors([err for err in exc.errors()])},
        )

    service = GetService()

    mode: Literal["view", "download"] = "download" if request.download else "view"

    try:
        url, metadata = service.generate_image_url(
            request.image_id,
            mode=mode,
        )
    except NotFoundError:
        logger.exception(
            "Image not found during delete",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.not_found(f"Image not found: {request.image_id}")

    except (S3Error, MetadataOperationFailedError) as exc:
        logger.exception(
            "Get Image failed",
            extra={"image_id": request.image_id},
        )
        return ResponseBuilder.internal_error(exc.message)

    response_body: dict[str, Any] = {
        "image_id": request.image_id,
        "mode": mode,
        "url": url,
    }

    if request.metadata:
        response_body["metadata"] = ImageMetadataHeader(
            image_id=metadata["image_id"],
            user_id=metadata["user_id"],
            image_name=metadata["image_name"],
            description=metadata.get("description"),
            tags=metadata.get("tags"),
            created_at=metadata["created_at"],
            file_size=metadata["file_size"],
            mime_type=metadata["mime_type"],
        ).model_dump()

    return ResponseBuilder.ok(response_body)
