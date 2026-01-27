"""
Lambda handler responsible for listing images with optional filtering and pagination.
"""

from typing import Any

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext

from core.models.image import ImageMetadata, ListImagesResponse
from core.models.pagination import PaginationInfo
from core.utils.response import ResponseBuilder
from core.utils.validators import validate_request

from .models import ListImagesRequest
from .service import ListService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> ResponseBuilder:
    """
    Handle requests to list images.

    Supports:
    - Filtering by creation date (DynamoDB-level)
    - Filtering by image name substring (in-memory)
    - Sorting and offset-based pagination
    """

    params = event.get("queryStringParameters") or {}

    is_valid, result = validate_request(ListImagesRequest, params)
    if not is_valid:
        return result

    request: ListImagesRequest = result
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
    except Exception as exc:
        logger.exception("Internal error listing images")
        return ResponseBuilder.internal_error(str(exc))

    images: list[dict[str, Any]] = []
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
                ).model_dump()
            )
        except Exception as exc:
            logger.warning("Skipping malformed item", exc_info=exc)

    response = ListImagesResponse(
        images=images,
        total_count=total_count,
        returned_count=len(images),
        pagination=PaginationInfo(
            limit=request.limit,
            offset=request.offset,
            has_more=has_more,
        ),
    )

    return ResponseBuilder.ok(response.model_dump())
