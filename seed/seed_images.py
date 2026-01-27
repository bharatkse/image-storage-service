#!/usr/bin/env python3
"""
Seed script to populate the system via API endpoints.

Run:
    poetry run python seed/seed_images.py \
      --api-id <API-ID> \
      --api-key <API-KEY>
"""

import argparse
import base64
import json
from pathlib import Path
import sys
from typing import Any, cast

from aws_lambda_powertools import Logger
import requests

logger = Logger(service="seed")


UPLOAD_API_URL = "http://localhost:4566/restapis/{0}/snd/_user_request_/v1/images"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed images via Image Storage API")

    parser.add_argument(
        "--api-id",
        required=True,
        help="Base API ID (e.g. LocalStack API Gateway ID)",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="API key for x-api-key header (optional for local)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=4,
        help="Number of images to seed",
    )

    return parser.parse_args()


def load_sample_data() -> dict[str, Any]:
    data_file = Path(__file__).parent / "data" / "images.json"
    with open(data_file, encoding="utf-8") as f:
        return cast(dict[str, Any], json.load(f))


def seed_images() -> None:
    try:
        args = parse_args()
        data = load_sample_data()

        images_dir = Path(__file__).parent / "images"

        headers: dict[str, str] = {
            "Content-Type": "application/json",
        }
        if args.api_key:
            headers["x-api-key"] = args.api_key

        upload_url = UPLOAD_API_URL.format(args.api_id)

        logger.info(
            "Starting seeding process",
            extra={"api_base_url": upload_url},
        )

        for item in cast(list[dict[str, Any]], data.get("images", []))[: args.limit]:
            image_path = images_dir / item["image_name"]

            if not image_path.exists():
                logger.warning("Image file not found", extra={"path": str(image_path)})
                continue

            with open(image_path, "rb") as f:
                image_bytes = f.read()

            encoded_file = base64.b64encode(image_bytes).decode("utf-8")

            payload: dict[str, Any] = {
                "file": encoded_file,
                "user_id": item["user_id"],
                "image_name": item["image_name"],
                "description": item.get("description"),
                "tags": item.get("tags"),
            }

            response = requests.post(
                upload_url,
                headers=headers,
                json=payload,
                timeout=30,
            )

            response_json = cast(dict[str, Any], response.json())

            if response.status_code == 201:
                logger.info(
                    "Seeded image",
                    extra={
                        "image": item["image_name"],
                        "image_id": response_json.get("image_id"),
                    },
                )
            else:
                logger.error(
                    "Failed to seed image",
                    extra={
                        "image": item["image_name"],
                        "status": response.status_code,
                        "response": response_json,
                    },
                )

        logger.info("Seeding completed")

        first_user = cast(dict[str, Any], data["images"][0])["user_id"]
        list_url = UPLOAD_API_URL.format(args.api_id)

        list_response = requests.get(
            list_url,
            headers=headers,
            params={"user_id": first_user},
            timeout=30,
        )

        list_response_json = cast(dict[str, Any], list_response.json())

        logger.info(
            "List images response",
            extra={
                "status": list_response.status_code,
                "response": list_response_json if list_response.ok else list_response.text,
            },
        )

    except Exception as exc:
        logger.exception("Seeding failed", exc_info=exc)
        sys.exit(1)


if __name__ == "__main__":
    seed_images()
