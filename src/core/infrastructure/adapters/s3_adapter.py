"""Thin adapter for interacting with Amazon S3."""

from collections.abc import Mapping
import os
from typing import Any, Protocol

import boto3

from core.utils.constants import (
    ENV_AWS_ENDPOINT_URL,
    ENV_AWS_REGION,
    ENV_IMAGE_S3_BUCKET_NAME,
)


class _Boto3S3Client(Protocol):
    """Internal typing for boto3 S3 client (AWS-facing only)."""

    def put_object(
        self,
        *,
        Bucket: str,
        Key: str,
        Body: bytes,
        ContentType: str,
        Metadata: Mapping[str, str],
    ) -> Any: ...

    def get_object(
        self,
        *,
        Bucket: str,
        Key: str,
    ) -> Mapping[str, Any]: ...

    def delete_object(
        self,
        *,
        Bucket: str,
        Key: str,
    ) -> Any: ...

    def generate_presigned_url(
        self,
        ClientMethod: str,
        Params: Mapping[str, Any],
        ExpiresIn: int,
    ) -> str: ...


class S3AdapterProtocol(Protocol):
    """Minimal S3 adapter protocol (repository-facing)."""

    def put_object(
        self,
        *,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None: ...

    def get_object(self, *, key: str) -> Mapping[str, Any]: ...

    def delete_object(self, *, key: str) -> None: ...

    def generate_presigned_url(
        self,
        *,
        method: str,
        params: dict[str, Any],
        expires_in: int,
    ) -> str: ...


class S3Adapter:
    """Low-level S3 operations (mechanical, no error handling).

    This adapter:
    - Wraps boto3 S3 client
    - Does NOT handle errors (lets them bubble up)
    - Domain implementations catch and translate errors
    """

    def __init__(self) -> None:
        """Create S3 client from environment configuration."""
        bucket_name = os.getenv(ENV_IMAGE_S3_BUCKET_NAME)
        if not bucket_name:
            raise RuntimeError(f"{ENV_IMAGE_S3_BUCKET_NAME} environment variable is not set")

        self._bucket = bucket_name
        self._client: _Boto3S3Client = boto3.client(
            "s3",
            endpoint_url=os.getenv(ENV_AWS_ENDPOINT_URL),
            region_name=os.getenv(ENV_AWS_REGION),
        )

    def put_object(
        self,
        *,
        key: str,
        body: bytes,
        content_type: str,
        metadata: dict[str, str],
    ) -> None:
        """Store object in S3.
        Raises boto3 exceptions - caught by domain implementation.
        """
        self._client.put_object(
            Bucket=self._bucket,
            Key=key,
            Body=body,
            ContentType=content_type,
            Metadata=metadata,
        )

    def get_object(self, *, key: str) -> Mapping[str, Any]:
        """Fetch object from S3.
        Raises boto3 exceptions - caught by domain implementation.
        """
        response = self._client.get_object(
            Bucket=self._bucket,
            Key=key,
        )
        return response

    def delete_object(self, *, key: str) -> None:
        """Delete object from S3.
        Raises boto3 exceptions - caught by domain implementation.
        """
        self._client.delete_object(
            Bucket=self._bucket,
            Key=key,
        )

    def generate_presigned_url(
        self,
        *,
        method: str,
        params: dict[str, Any],
        expires_in: int,
    ) -> str:
        """Generate a pre-signed S3 URL."""
        return self._client.generate_presigned_url(
            ClientMethod=method,
            Params={**params, "Bucket": self._bucket},
            ExpiresIn=expires_in,
        )
