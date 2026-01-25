from datetime import datetime, timezone

from core.utils.time import utc_now_iso


class TestUtcNowIso:
    def test_returns_string(self) -> None:
        result = utc_now_iso()
        assert isinstance(result, str)

    def test_returns_valid_iso8601_datetime(self) -> None:
        result = utc_now_iso()
        parsed = datetime.fromisoformat(result)
        assert isinstance(parsed, datetime)

    def test_returns_utc_timezone(self) -> None:
        result = utc_now_iso()
        parsed = datetime.fromisoformat(result)
        assert parsed.tzinfo == timezone.utc

    def test_is_close_to_current_time(self) -> None:
        before = datetime.now(timezone.utc)
        result = utc_now_iso()
        after = datetime.now(timezone.utc)

        parsed = datetime.fromisoformat(result)
        assert before <= parsed <= after

    def test_iso_format_is_lexicographically_sortable(self) -> None:
        t1 = utc_now_iso()
        t2 = utc_now_iso()
        assert t1 <= t2
