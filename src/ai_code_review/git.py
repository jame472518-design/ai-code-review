from __future__ import annotations

import subprocess


class GitError(Exception):
    pass


def _run_git(*args: str) -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="replace",
        )
    except subprocess.CalledProcessError as e:
        raise GitError(f"git {' '.join(args)} failed: {e.stderr.strip()}") from e
    except FileNotFoundError:
        raise GitError("git is not installed or not in PATH")
    return result.stdout


def get_staged_diff(extensions: list[str] | None = None) -> str:
    args = ["diff", "--cached"]
    if extensions:
        args.append("--")
        args.extend(f"*.{ext.lstrip('.')}" for ext in extensions)
    return _run_git(*args).strip()


def get_staged_diff_stat(extensions: list[str] | None = None) -> str:
    """Return file change summary (git diff --cached --stat)."""
    args = ["diff", "--cached", "--stat"]
    if extensions:
        args.append("--")
        args.extend(f"*.{ext.lstrip('.')}" for ext in extensions)
    return _run_git(*args).strip()


def get_recent_commits(count: int = 5) -> str:
    """Return recent commit oneline summaries."""
    return _run_git("log", f"--oneline", f"-{count}").strip()


def get_unstaged_diff() -> str:
    return _run_git("diff").strip()


def get_commit_diff(from_ref: str, to_ref: str, extensions: list[str] | None = None) -> str:
    args = ["diff", from_ref, to_ref]
    if extensions:
        args.append("--")
        args.extend(f"*.{ext.lstrip('.')}" for ext in extensions)
    return _run_git(*args).strip()


def split_diff_by_extension(diff: str) -> dict[str, str]:
    """Split a unified diff into groups keyed by file extension.

    Returns a dict like {"c": "diff --git ...", "py": "diff --git ..."}
    Files without an extension are grouped under "".
    """
    import os
    groups: dict[str, list[str]] = {}
    current_ext = ""
    current_lines: list[str] = []

    for line in diff.split("\n"):
        if line.startswith("diff --git "):
            # Flush previous file
            if current_lines:
                groups.setdefault(current_ext, []).extend(current_lines)
            # Parse extension from "diff --git a/path/file.ext b/path/file.ext"
            parts = line.split()
            if len(parts) >= 4:
                filepath = parts[3]  # b/path/file.ext
                if filepath.startswith("b/"):
                    filepath = filepath[2:]
                _, ext = os.path.splitext(filepath)
                current_ext = ext.lstrip(".").lower()
            else:
                current_ext = ""
            current_lines = [line]
        else:
            current_lines.append(line)

    # Flush last file
    if current_lines:
        groups.setdefault(current_ext, []).extend(current_lines)

    return {ext: "\n".join(lines) for ext, lines in groups.items()}


_ZERO_SHA = "0" * 40


def get_push_diff(local_sha: str, remote_sha: str, extensions: list[str] | None = None) -> str:
    """Get diff for commits being pushed.

    Args:
        local_sha: The local commit SHA being pushed.
        remote_sha: The remote commit SHA (current tip of the remote branch).
        extensions: Optional list of file extensions to filter the diff.

    Returns:
        The diff string, or empty string if the branch is being deleted
        or no base can be determined.
    """
    if local_sha == _ZERO_SHA:
        return ""  # Branch being deleted
    if remote_sha == _ZERO_SHA:
        # New branch — try to find merge base with main/master
        for base_ref in ["origin/main", "origin/master", "main", "master"]:
            try:
                merge_base = _run_git("merge-base", local_sha, base_ref).strip()
                return get_commit_diff(merge_base, local_sha, extensions)
            except GitError:
                continue
        return ""  # Can't determine base
    return get_commit_diff(remote_sha, local_sha, extensions)
