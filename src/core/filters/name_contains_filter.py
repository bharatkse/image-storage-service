"""Name-based filtering for images."""

from typing import Any


class NameContainsFilter:
    """Filter images by name using case-insensitive substring search.

    Provides functionality to search for images by name with flexible
    matching criteria. The search is case-insensitive and matches
    any image where the name contains the search term.

    This is useful for users searching for specific images without
    needing to remember exact naming conventions.
    """

    @staticmethod
    def apply(
        items: list[dict[str, Any]],
        search_term: str,
        field_name: str = "image_name",
    ) -> list[dict[str, Any]]:
        """Apply name filter to items.

        Performs case-insensitive substring search on the specified field.
        Returns all items where the field contains the search term.
        """
        if not search_term or not search_term.strip():
            return items

        search_lower = search_term.lower()
        return [
            item for item in items if search_lower in item.get(field_name, "").lower()
        ]

    @staticmethod
    def validate(search_term: str) -> bool:
        """Validate name filter search term."""
        return bool(search_term and search_term.strip())
