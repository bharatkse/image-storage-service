"""
Common decorators and helpers for API Gateway Lambda handlers.
"""

from __future__ import annotations

import traceback
from collections.abc import Callable
from functools import wraps
from http import HTTPStatus
from typing import Any, Protocol
from aws_lambda_powertools import Logger

from core.utils.response import ResponseBuilder

logger = Logger(service="api-gateway-handler", UTC=True)

JsonDict = dict[str, Any]


class ApiGatewayHandlerProtocol(Protocol):
    """Protocol for API Gateway Lambda handler functions."""

    def __call__(
        self,
        event: Any,
        context: Any,
        *,
        cors_origin: str | None = None,
    ) -> JsonDict: ...


def _get_user_friendly_message(exc: Exception) -> str:
    """
    Convert technical exception messages into user-friendly ones.
    
    Preserves specific validation messages while making generic errors friendly.
    """
    exc_str = str(exc)
    
    # If the exception message is already user-friendly (starts with common phrases),
    # keep it as is
    friendly_prefixes = (
        "Invalid",
        "Missing",
        "Required",
        "Must",
        "Cannot",
        "Unable to",
        "Failed to",
        "Image",
        "File",
        "User",
    )
    
    if exc_str and any(exc_str.startswith(prefix) for prefix in friendly_prefixes):
        return exc_str
    
    # Default friendly messages by exception type
    if isinstance(exc, ValueError):
        return "The provided data is invalid. Please check your input and try again."
    
    if isinstance(exc, (KeyError, AttributeError)):
        return "A required field is missing. Please ensure all required fields are provided."
    
    if isinstance(exc, TypeError):
        return "The data format is incorrect. Please check the request format."
    
    if isinstance(exc, (UnicodeDecodeError, UnicodeEncodeError)):
        return "The file contains invalid characters or encoding. Please check the file format."
    
    if isinstance(exc, MemoryError):
        return "The file is too large to process. Please use a smaller file."
    
    if isinstance(exc, TimeoutError):
        return "The request took too long to process. Please try again with a smaller file or simpler request."
    
    # For other exceptions with no context, use generic message
    return "We encountered an issue processing your request. Please try again."


def _log_error(
    message: str,
    *,
    handler_name: str,
    request_id: str | None,
    exc: Exception,
    level: str = "warning",
) -> None:
    """
    Log error with consistent structure and full context.
    
    Args:
        message: Log message
        handler_name: Name of the handler function
        request_id: AWS request ID
        exc: Exception that was raised
        level: Log level ('warning' or 'exception')
    """
    log_extra = {
        "handler": handler_name,
        "request_id": request_id,
        "error": str(exc),
        "error_type": type(exc).__name__,
    }
    
    if level == "exception":
        # logger.exception automatically includes traceback
        logger.exception(message, extra=log_extra)
    else:
        # For warnings, manually add traceback
        log_extra["traceback"] = traceback.format_exc()
        logger.warning(message, extra=log_extra)


def api_gateway_handler(
    func: Callable[..., JsonDict],
) -> Callable[..., JsonDict]:
    """
    Decorator for API Gateway Lambda handlers.
    
    Provides:
    - Automatic CORS preflight (OPTIONS) handling
    - Centralized exception handling and error responses
    - Request ID tracking and structured logging
    - User-friendly error messages
    - Full traceback logging for monitoring
    
    Example:
        @api_gateway_handler
        def lambda_handler(event, context):
            return {"statusCode": 200, "body": "Success"}
    """

    @wraps(func)
    def wrapper(
        event: Any,
        context: Any,
        *,
        cors_origin: str | None = None,
    ) -> JsonDict:
        # Handle CORS preflight requests
        if event.get("httpMethod") == "OPTIONS":
            return {
                "statusCode": HTTPStatus.NO_CONTENT.value,
                "headers": ResponseBuilder._build_headers(cors_origin),
                "body": "",
            }

        request_id = getattr(context, "aws_request_id", None)

        try:
            return func(event, context)
            
        # Client errors (4xx) - Bad Request
        except (
            ValueError,           # Invalid values, validation errors
            KeyError,             # Missing required fields in dicts
            TypeError,            # Wrong data types
            AttributeError,       # Missing attributes on objects
            UnicodeDecodeError,   # Invalid file encoding
            UnicodeEncodeError,   # Cannot encode response
        ) as exc:
            _log_error(
                "Validation error in handler",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
            )
            return ResponseBuilder.bad_request(
                _get_user_friendly_message(exc),
                request_id=request_id,
                cors_origin=cors_origin,
            )

        # Client errors (4xx) - Unauthorized/Forbidden
        except PermissionError as exc:
            _log_error(
                "Permission denied in handler",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
            )
            return ResponseBuilder.forbidden(
                "You don't have permission to perform this action.",
                request_id=request_id,
                cors_origin=cors_origin,
            )

        # Client errors (4xx) - Not Found
        except (FileNotFoundError, LookupError) as exc:
            _log_error(
                "Resource not found",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
            )
            return ResponseBuilder.not_found(
                "The requested resource was not found.",
                request_id=request_id,
                cors_origin=cors_origin,
            )

        # Client errors (4xx) - Payload Too Large
        except MemoryError as exc:
            _log_error(
                "Memory error - payload too large",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
            )
            return ResponseBuilder.error(
                message="The file is too large to process. Maximum size is 10MB.",
                status=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                request_id=request_id,
                cors_origin=cors_origin,
            )

        # Server errors (5xx) - Timeout
        except TimeoutError as exc:
            _log_error(
                "Request timeout",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
                level="exception",
            )
            return ResponseBuilder.error(
                message="The request took too long to process. Please try again.",
                status=HTTPStatus.GATEWAY_TIMEOUT,
                request_id=request_id,
                cors_origin=cors_origin,
            )

        # Server errors (5xx) - Connection/Network issues
        except (ConnectionError, OSError) as exc:
            _log_error(
                "Connection error",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
                level="exception",
            )
            return ResponseBuilder.error(
                message="Unable to connect to required services. Please try again later.",
                status=HTTPStatus.SERVICE_UNAVAILABLE,
                request_id=request_id,
                cors_origin=cors_origin,
            )

        # Catch-all for unexpected errors
        except Exception as exc:
            _log_error(
                "Unexpected error in handler",
                handler_name=func.__name__,
                request_id=request_id,
                exc=exc,
                level="exception",
            )
            return ResponseBuilder.internal_error(
                "We're experiencing technical difficulties. Please try again in a few moments.",
                request_id=request_id,
                cors_origin=cors_origin,
            )

    return wrapper