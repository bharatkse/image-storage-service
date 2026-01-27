#!/usr/bin/env python3
"""
Cleanup script to remove seeded images via API endpoints.

Run:
    poetry run python seed/cleanup_images.py \
      --api-id <API-ID> \
      --api-key <API-KEY> \
      --user-id <USER-ID>
"""

import argparse
import sys
from typing import Any, cast

from aws_lambda_powertools import Logger
import requests

logger = Logger(service="cleanup")

BASE_API_URL = "http://localhost:4566/restapis/{0}/snd/_user_request_/v1/images"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Cleanup seeded images via Image Storage API")

    parser.add_argument(
        "--api-id",
        required=True,
        help="API Gateway ID (LocalStack)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for x-api-key header (optional for local)",
    )
    parser.add_argument(
        "--user-id",
        required=True,
        help="User ID whose images should be deleted",
    )

    return parser.parse_args()


def cleanup_images() -> None:
    try:
        args = parse_args()

        headers: dict[str, str] = {}
        if args.api_key:
            headers["x-api-key"] = args.api_key

        base_url = BASE_API_URL.format(args.api_id)

        logger.info(
            "Starting cleanup process",
            extra={"api_base_url": base_url, "user_id": args.user_id},
        )

        # List images for user
        response = requests.get(
            base_url,
            headers=headers,
            params={"user_id": args.user_id},
            timeout=30,
        )

        if not response.ok:
            logger.error(
                "Failed to list images",
                extra={"status": response.status_code, "response": response.text},
            )
            sys.exit(1)

        response_json = cast(dict[str, Any], response.json())
        images = cast(list[dict[str, Any]], response_json.get("images", []))

        if not images:
            logger.info("No images found for cleanup")
            return

        for image in images:
            image_id = image["image_id"]
            delete_url = f"{base_url}/{image_id}"

            delete_resp = requests.delete(
                delete_url,
                headers=headers,
                timeout=30,
            )

            if delete_resp.ok:
                logger.info("Deleted image", extra={"image_id": image_id})
            else:
                logger.error(
                    "Failed to delete image",
                    extra={
                        "image_id": image_id,
                        "status": delete_resp.status_code,
                        "response": delete_resp.text,
                    },
                )

        logger.info("Cleanup completed successfully")

    except Exception as exc:
        logger.exception("Cleanup failed", exc_info=exc)
        sys.exit(1)


if __name__ == "__main__":
    cleanup_images()
