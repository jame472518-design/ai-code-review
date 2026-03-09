from __future__ import annotations

import re
from dataclasses import dataclass

from .config import DEFAULT_COMMIT_FORMAT_HINT, DEFAULT_COMMIT_PATTERN


@dataclass(frozen=True)
class CommitCheckResult:
    valid: bool
    error: str | None = None


def check_commit_message(
    message: str,
    pattern: str | None = None,
    format_hint: str | None = None,
) -> CommitCheckResult:
    pat = re.compile(pattern) if pattern else re.compile(DEFAULT_COMMIT_PATTERN)
    hint = format_hint or DEFAULT_COMMIT_FORMAT_HINT

    message = message.strip()
    if not message:
        return CommitCheckResult(valid=False, error=f"Commit message is empty. {hint}")
    if not pat.match(message):
        return CommitCheckResult(valid=False, error=f"Invalid commit message format. {hint}")
    return CommitCheckResult(valid=True)
