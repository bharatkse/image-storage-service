"""Unit tests for S3ImageStorage."""

from typing import Any

from botocore.exceptions import ClientError
import pytest

from core.infrastructure.aws.s3_image_storage import S3ImageStorage
from core.models.errors import (
    NotFoundError,
    S3Error,
)


class DummyBody:
    """Dummy streaming body returned by S3 get_object."""

    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self) -> bytes:
        return self._data


class DummyS3Adapter:
    """Configurable S3 adapter test double (mypy-safe)."""

    def __init__(
        self,
        *,
        put_exc: Exception | None = None,
        get_exc: Exception | None = None,
        delete_exc: Exception | None = None,
        get_response: dict[str, Any] | None = None,
        presigned_url: str = "https://example.com/presigned",
    ) -> None:
        self._put_exc = put_exc
        self._get_exc = get_exc
        self._delete_exc = delete_exc
        self._get_response = get_response or {}
        self._presigned_url = presigned_url

    def put_object(self, **_: Any) -> None:
        if self._put_exc:
            raise self._put_exc

    def get_object(self, **_: Any) -> dict[str, Any]:
        if self._get_exc:
            raise self._get_exc
        return self._get_response

    def delete_object(self, **_: Any) -> None:
        if self._delete_exc:
            raise self._delete_exc

    def generate_presigned_url(
        self,
        *,
        method: str,
        params: dict[str, Any],
        expires_in: int,
    ) -> str:
        return self._presigned_url


class TestS3ImageStorage:
    def test_upload_image_success(self) -> None:
        storage = S3ImageStorage(DummyS3Adapter())

        key = storage.upload_image(
            image_id="img_123",
            user_id="user_456",
            file_data=b"image-bytes",
            mime_type="image/jpeg",
        )
        assert key == "images/user_456/img_123.jpg"

    def test_upload_image_client_error(self) -> None:
        adapter = DummyS3Adapter(
            put_exc=ClientError(
                {"Error": {"Code": "AccessDenied"}},
                "PutObject",
            )
        )
        storage = S3ImageStorage(adapter)

        with pytest.raises(S3Error):
            storage.upload_image(
                image_id="img_1",
                user_id="user_1",
                file_data=b"data",
                mime_type="image/png",
            )

    def test_upload_image_unexpected_exception(self) -> None:
        adapter = DummyS3Adapter(put_exc=Exception("boom"))
        storage = S3ImageStorage(adapter)

        with pytest.raises(S3Error):
            storage.upload_image(
                image_id="img_1",
                user_id="user_1",
                file_data=b"data",
                mime_type="image/png",
            )

    def test_upload_image_unknown_mime_type_uses_bin_extension(self) -> None:
        storage = S3ImageStorage(DummyS3Adapter())

        key = storage.upload_image(
            image_id="img_bin",
            user_id="user_x",
            file_data=b"bytes",
            mime_type="application/unknown",
        )

        assert key == "images/user_x/img_bin.bin"

    def test_download_image_success(self) -> None:
        adapter = DummyS3Adapter(
            get_response={
                "Body": DummyBody(b"image-bytes"),
                "ContentType": "image/png",
                "ContentLength": 11,
            }
        )
        storage = S3ImageStorage(adapter)

        body, content_type, length = storage.download_image(key="images/u/img.png")

        assert body == b"image-bytes"
        assert content_type == "image/png"
        assert length == 11

    def test_download_image_defaults_when_headers_missing(self) -> None:
        adapter = DummyS3Adapter(
            get_response={
                "Body": DummyBody(b"abc"),
            }
        )
        storage = S3ImageStorage(adapter)

        body, content_type, length = storage.download_image(key="images/u/img.bin")

        assert body == b"abc"
        assert content_type == "application/octet-stream"
        assert length == 3

    def test_download_image_not_found(self) -> None:
        adapter = DummyS3Adapter(
            get_exc=ClientError(
                {"Error": {"Code": "NoSuchKey"}},
                "GetObject",
            )
        )
        storage = S3ImageStorage(adapter)

        with pytest.raises(NotFoundError):
            storage.download_image(key="images/missing.png")

    def test_download_image_client_error(self) -> None:
        adapter = DummyS3Adapter(
            get_exc=ClientError(
                {"Error": {"Code": "InternalError"}},
                "GetObject",
            )
        )
        storage = S3ImageStorage(adapter)

        with pytest.raises(S3Error):
            storage.download_image(key="images/broken.png")

    def test_download_image_unexpected_exception(self) -> None:
        adapter = DummyS3Adapter(get_exc=Exception("boom"))
        storage = S3ImageStorage(adapter)

        with pytest.raises(S3Error):
            storage.download_image(key="images/crash.png")

    def test_remove_image_success(self) -> None:
        storage = S3ImageStorage(DummyS3Adapter())

        storage.remove_image(key="images/u/img.jpg")

    def test_remove_image_client_error(self) -> None:
        adapter = DummyS3Adapter(
            delete_exc=ClientError(
                {"Error": {"Code": "AccessDenied"}},
                "DeleteObject",
            )
        )
        storage = S3ImageStorage(adapter)

        with pytest.raises(S3Error):
            storage.remove_image(key="images/u/img.jpg")

    def test_remove_image_unexpected_exception(self) -> None:
        adapter = DummyS3Adapter(delete_exc=Exception("boom"))
        storage = S3ImageStorage(adapter)

        with pytest.raises(S3Error):
            storage.remove_image(key="images/u/img.jpg")
