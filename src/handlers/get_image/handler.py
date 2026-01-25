"""
Lambda handler responsible for image retrieval and download.
"""

from typing import Any, Literal

from aws_lambda_powertools import Logger, Metrics, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from core.utils.response import ResponseBuilder
from core.utils.validators import validate_request

from .models import GetImageRequest, ImageMetadataHeader
from .service import GetService

logger = Logger(UTC=True)
tracer = Tracer()
metrics = Metrics()


@tracer.capture_lambda_handler
@metrics.log_metrics()
def handler(event: dict[str, Any], context: LambdaContext) -> ResponseBuilder:
    """
    Handle image view or download requests.

    - Default: return view URL
    - download=true: return download URL
    - metadata=true: include metadata in response
    """

    path_params = event.get("pathParameters") or {}
    query_params = event.get("queryStringParameters") or {}

    params = {
        "image_id": path_params.get("image_id"),
        "metadata": query_params.get("metadata", "false").lower() == "true",
        "download": query_params.get("download", "false").lower() == "true",
    }

    is_valid, result = validate_request(GetImageRequest, params)
    if not is_valid:
        logger.error("Validation error: %s", result)
        return result

    request = result
    service = GetService()

    mode: Literal["view", "download"] = "download" if request.download else "view"

    try:
        url, metadata = service.generate_image_url(
            request.image_id,
            mode=mode,
        )
    except Exception as exc:
        logger.exception("Failed to generate image URL")
        return ResponseBuilder.internal_error(str(exc))

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
