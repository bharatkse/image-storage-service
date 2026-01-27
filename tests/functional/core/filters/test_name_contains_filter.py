from core.filters.name_contains_filter import NameContainsFilter


class TestNameContainsFilter:
    def test_filter_by_name(self) -> None:
        items = [
            {"image_name": "sunset.jpg"},
            {"image_name": "sunrise.jpg"},
            {"image_name": "landscape.jpg"},
        ]

        result = NameContainsFilter.apply(items, "sun")

        assert len(result) == 2
        assert {item["image_name"] for item in result} == {
            "sunset.jpg",
            "sunrise.jpg",
        }

    def test_filter_by_name_case_insensitive(self) -> None:
        items = [
            {"image_name": "Sunset.jpg"},
            {"image_name": "SUNRISE.jpg"},
            {"image_name": "landscape.jpg"},
        ]

        result = NameContainsFilter.apply(items, "SUN")

        assert len(result) == 2

    def test_filter_with_empty_search_term_returns_all(self) -> None:
        items = [
            {"image_name": "sunset.jpg"},
            {"image_name": "sunrise.jpg"},
        ]

        result = NameContainsFilter.apply(items, "")

        assert result == items

    def test_filter_with_whitespace_search_term_returns_all(self) -> None:
        items = [
            {"image_name": "sunset.jpg"},
            {"image_name": "sunrise.jpg"},
        ]

        result = NameContainsFilter.apply(items, "   ")

        assert result == items

    def test_filter_handles_missing_field_gracefully(self) -> None:
        items = [
            {"image_name": "sunset.jpg"},
            {"other_field": "no-name"},
        ]

        result = NameContainsFilter.apply(items, "sun")

        assert len(result) == 1
        assert result[0]["image_name"] == "sunset.jpg"

    def test_validate_returns_true_for_valid_term(self) -> None:
        assert NameContainsFilter.validate("sun") is True

    def test_validate_returns_false_for_invalid_term(self) -> None:
        assert NameContainsFilter.validate("") is False
        assert NameContainsFilter.validate("   ") is False
