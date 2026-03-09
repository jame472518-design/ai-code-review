import pytest

from ai_code_review.commit_check import check_commit_message, CommitCheckResult


class TestValidMessages:
    @pytest.mark.parametrize("msg", [
        "[BSP-456] fix camera HAL crash on boot",
        "[KERN-1] update device tree",
        "[AUD-9999] resolve ALSA mixer issue",
        "[WIFI-12] add support for new chipset",
        "[fix] resolve camera crash",
        "[feat] add hand tracking support",
        "[BSP] fix camera crash",
        "[bsp-456] fix camera crash",
    ])
    def test_valid_format(self, msg):
        result = check_commit_message(msg)
        assert result.valid is True
        assert result.error is None


class TestInvalidMessages:
    def test_missing_prefix(self):
        result = check_commit_message("fix camera crash")
        assert result.valid is False
        assert "format" in result.error.lower()

    def test_missing_description(self):
        result = check_commit_message("[BSP-456]")
        assert result.valid is False

    def test_missing_space_after_bracket(self):
        result = check_commit_message("[BSP-456]fix camera crash")
        assert result.valid is False

    def test_empty_message(self):
        result = check_commit_message("")
        assert result.valid is False


class TestCustomPattern:
    def test_strict_pattern_rejects_lowercase(self):
        result = check_commit_message(
            "[bsp-456] fix crash",
            pattern=r"^\[[A-Z]+-\d+\] .+",
        )
        assert result.valid is False

    def test_strict_pattern_accepts_uppercase(self):
        result = check_commit_message(
            "[BSP-456] fix crash",
            pattern=r"^\[[A-Z]+-\d+\] .+",
        )
        assert result.valid is True

    def test_custom_hint_in_error(self):
        result = check_commit_message(
            "bad message",
            format_hint="Must start with [TAG]",
        )
        assert "Must start with [TAG]" in result.error


class TestCommitCheckResult:
    def test_result_contains_expected_format_hint(self):
        result = check_commit_message("bad message")
        assert "[tag]" in result.error.lower()
