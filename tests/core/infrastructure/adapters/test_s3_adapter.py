import pytest
from botocore.exceptions import ClientError
from core.infrastructure.adapters.s3_adapter import S3Adapter
from core.utils.constants import ENV_IMAGE_S3_BUCKET_NAME


class TestS3Adapter:
    def test_init_missing_bucket_env(self, monkeypatch):
        monkeypatch.delenv(ENV_IMAGE_S3_BUCKET_NAME, raising=False)

        with pytest.raises(RuntimeError):
            S3Adapter()

    def test_put_and_get_object_success(
        self,
        s3_bucket,
        s3_get_object,
    ):
        adapter = S3Adapter()

        key = "images/user/img_1.jpg"
        data = b"image-bytes"

        adapter.put_object(
            key=key,
            body=data,
            content_type="image/jpeg",
            metadata={"image_id": "img_1"},
        )

        content = s3_get_object(key)

        assert content == data

    def test_get_object_missing_key_raises_client_error(
        self,
        s3_bucket,
    ):
        adapter = S3Adapter()

        with pytest.raises(ClientError) as exc:
            adapter.get_object(key="images/missing.jpg")

        assert exc.value.response["Error"]["Code"] == "NoSuchKey"

    def test_delete_object_success(
        self,
        s3_bucket,
        s3_put_object,
        s3_get_object,
    ):
        adapter = S3Adapter()

        key = "images/user/img_delete.jpg"
        s3_put_object(key, b"data", "image/jpeg")

        adapter.delete_object(key=key)

        with pytest.raises(ClientError) as exc:
            s3_get_object(key)

        assert exc.value.response["Error"]["Code"] == "NoSuchKey"

    def test_put_object_bubbles_client_error(self, monkeypatch, s3_bucket):
        adapter = S3Adapter()

        def raise_error(**_):
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "PutObject",
            )

        monkeypatch.setattr(adapter._client, "put_object", raise_error)

        with pytest.raises(ClientError):
            adapter.put_object(
                key="images/x.jpg",
                body=b"data",
                content_type="image/jpeg",
                metadata={},
            )

    def test_delete_object_bubbles_client_error(self, monkeypatch, s3_bucket):
        adapter = S3Adapter()

        def raise_error(**_):
            raise ClientError(
                {"Error": {"Code": "InternalError"}},
                "DeleteObject",
            )

        monkeypatch.setattr(adapter._client, "delete_object", raise_error)

        with pytest.raises(ClientError):
            adapter.delete_object(key="images/x.jpg")
