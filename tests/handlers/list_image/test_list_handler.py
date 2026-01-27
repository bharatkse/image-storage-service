import json

from handlers.list_image.handler import handler


class TestListImageHandler:
    def test_list_all_images_for_user(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {"queryStringParameters": {"user_id": "john"}}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["total_count"] == 2
        assert body["returned_count"] == 2
        assert {img["user_id"] for img in body["images"]} == {"john"}

    def test_list_with_name_filter(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "name_contains": "sunset",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["total_count"] == 1
        assert body["images"][0]["image_name"] == "sunset.jpg"

    def test_list_with_date_filter(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "start_date": "2024-01-04",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["total_count"] == 1
        assert body["images"][0]["image_id"] == "img_4"

    def test_list_with_date_range_filter(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "start_date": "2024-01-01",
                "end_date": "2024-01-04",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["total_count"] == 2
        assert {img["image_id"] for img in body["images"]} == {"img_2", "img_4"}

    def test_list_with_pagination(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "limit": "1",
                "offset": "0",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["returned_count"] == 1
        assert body["pagination"]["has_more"] is True

    def test_list_offset_beyond_range(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "offset": "10",
                "limit": "5",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["returned_count"] == 0
        assert body["images"] == []

    def test_list_user_isolation(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {"queryStringParameters": {"user_id": "alice"}}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])

        assert body["total_count"] == 1
        assert body["images"][0]["user_id"] == "alice"

    def test_list_invalid_date_format(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "start_date": "2024/01/04",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422
        body = json.loads(response["body"])
        assert body["error"] == "VALIDATION_FAILED"

    def test_list_missing_user_id(
        self,
        lambda_context,
    ) -> None:
        event: dict = {"queryStringParameters": {}}

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422

    def test_list_invalid_limit_type(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "limit": "abc",
            }
        }

        response = handler(event, lambda_context)

        assert response["statusCode"] == 422

    def test_list_default_sorting_created_at_desc(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {"queryStringParameters": {"user_id": "john"}}

        response = handler(event, lambda_context)

        body = json.loads(response["body"])
        image_ids = [img["image_id"] for img in body["images"]]

        assert image_ids == ["img_4", "img_2"]

    def test_list_sort_by_image_name_asc(
        self,
        lambda_context,
        dynamodb_with_multiple_items,
    ) -> None:
        event = {
            "queryStringParameters": {
                "user_id": "john",
                "sort_by": "image_name",
                "sort_order": "asc",
            }
        }

        response = handler(event, lambda_context)

        body = json.loads(response["body"])
        image_names = [img["image_name"] for img in body["images"]]

        assert image_names == ["b.png", "sunset.jpg"]
