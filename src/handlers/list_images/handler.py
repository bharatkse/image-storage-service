"""
Lambda handler responsible for listing images with optional filtering and pagination.
"""

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from pydantic import ValidationError

from core.models.image import ImageMetadata, ListImagesResponse
from core.models.pagination import PaginationInfo
from core.utils.decorators import api_gateway_handler
from core.utils.response import ResponseBuilder
from core.utils.validators import sanitize_validation_errors, validate_request

from .models import ListImagesRequest
from .service import ListService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@api_gateway_handler
@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """
    Handle requests to list images.

    Supports:
    - Filtering by creation date (DynamoDB-level)
    - Filtering by image name substring (in-memory)
    - Sorting and offset-based pagination

    Args:
        event: API Gateway Lambda proxy event
        context: AWS Lambda execution context

    Returns:
        API Gateway-compatible HTTP response

    """
    logger.info(
        "Received image list request",
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

    params = event.get("queryStringParameters") or {}

    try:
        request = validate_request(
            ListImagesRequest,
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

    service = ListService()

    try:
        items, total_count, has_more = service.list_images(
            user_id=request.user_id,
            name_contains=request.name_contains,
            start_date=request.start_date,
            end_date=request.end_date,
            offset=request.offset,
            limit=request.limit,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
        )
    except ValueError as exc:
        logger.exception("Error listing images")
        return ResponseBuilder.bad_request(str(exc))

    images: list[ImageMetadata] = []

    for item in items:
        try:
            images.append(
                ImageMetadata(
                    image_id=item["image_id"],
                    user_id=item["user_id"],
                    image_name=item["image_name"],
                    description=item.get("description"),
                    tags=item.get("tags"),
                    created_at=item["created_at"],
                    updated_at=item.get("updated_at"),
                    s3_key=item["s3_key"],
                    file_size=int(item["file_size"]),
                    mime_type=item["mime_type"],
                )
            )
        except Exception as exc:
            logger.warning("Skipping malformed item", exc_info=exc)

    next_offset = request.offset + len(images) if has_more else None

    response = ListImagesResponse(
        images=images,
        total_count=total_count,
        returned_count=len(images),
        pagination=PaginationInfo(
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
            next_offset=next_offset,
        ),
    )

    return ResponseBuilder.ok(response.model_dump())
