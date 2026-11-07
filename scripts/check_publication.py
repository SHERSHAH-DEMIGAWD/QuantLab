"""Read-only publication checks; findings omit matched values. No network or Git writes."""

import json
from pathlib import Path, PurePosixPath
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
PERSONAL = re.compile(r"(?:[A-Za-z]:[\\/](?:Users|Documents and Settings)[\\/][^\s\"'<>]+|/(?:home|Users)/[^/\s]+)", re.I)
TOKENS = re.compile(r"(?:AKIA[0-9A-Z]{16}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{30,}|sk-(?:proj-)?[A-Za-z0-9_-]{20,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)")
ASSIGNMENT = re.compile(r"(?i)(?:api[_-]?key|api[_-]?secret|password|access[_-]?token|client[_-]?secret)[\"']?\s*[:=]\s*[\"']([^\"'\n]{8,})[\"']")
SYNTHETIC_CSV = {"backend/tests/fixtures/synthetic_daily.csv", "frontend/public/examples/nine_sessions.csv"}
GENERATED = {".venv", "venv", "node_modules", "__pycache__", ".release-check", ".pytest_cache", "test-results", "playwright-report", "dist", "build", ".aws", ".ssh"}


def git(*args, data=None):
    return subprocess.run(["git", *args], cwd=ROOT, input=data, stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE, check=True).stdout


def inspect(name, body):
    path = PurePosixPath(name)
    findings = []
    if (GENERATED.intersection(path.parts) or path.suffix in {".db", ".sqlite", ".sqlite3", ".pyc", ".log", ".pem", ".key"}
            or name.endswith(("-wal", "-shm"))
            or (path.name.startswith(".env") and path.name != ".env.example")
            or (path.suffix == ".csv" and name not in SYNTHETIC_CSV)
            or (path.parts[0] == "data" and path.name != ".gitkeep")):
        findings.append({"path": name, "kind": "excluded_or_unreviewed_file"})
    if path.suffix == ".png":
        if not name.startswith("docs/images/") or not body.startswith(b"\x89PNG\r\n\x1a\n"):
            findings.append({"path": name, "kind": "unreviewed_binary"})
        # Playwright screenshots should contain no textual metadata/EXIF chunks.
        offset = 8
        while offset + 12 <= len(body):
            size = int.from_bytes(body[offset:offset + 4], "big")
            if body[offset + 4:offset + 8] in {b"tEXt", b"zTXt", b"iTXt", b"eXIf"}:
                findings.append({"path": name, "kind": "image_metadata_requires_review"})
            offset += size + 12
        return findings
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return findings + [{"path": name, "kind": "unreviewed_binary"}]
    for kind, pattern in (("personal_absolute_path", PERSONAL), ("credential_token_pattern", TOKENS)):
        for match in pattern.finditer(text):
            findings.append({"path": name, "line": text.count("\n", 0, match.start()) + 1, "kind": kind})
    for match in ASSIGNMENT.finditer(text):
        value = match.group(1)
        # Flag credential-like literals, not environment-variable names or prose.
        if len(value) >= 16 and re.search(r"[a-z]", value) and re.search(r"[A-Z0-9]", value) and not re.search(r"\s", value):
            findings.append({"path": name, "line": text.count("\n", 0, match.start()) + 1,
                             "kind": "credential_assignment_requires_review"})
    return findings


def tree_entries(revision):
    for record in git("ls-tree", "-rz", revision).split(b"\0"):
        if record:
            header, name = record.split(b"\t", 1)
            mode, kind, oid = header.decode().split()
            yield oid, name.decode(), kind, mode


def blobs(identifiers):
    identifiers = sorted(set(identifiers))
    if not identifiers:
        return {}
    output = git("cat-file", "--batch", data=("\n".join(identifiers) + "\n").encode())
    result, cursor = {}, 0
    for oid in identifiers:
        end = output.index(b"\n", cursor)
        header = output[cursor:end].decode().split()
        assert header[:2] == [oid, "blob"], header
        size = int(header[2])
        cursor = end + 1
        result[oid] = output[cursor:cursor + size]
        cursor += size + 1
    return result


def main():
    names = git("ls-files", "--cached", "--others", "--exclude-standard", "-z").decode().split("\0")[:-1]
    current = []
    for name in names:
        current.extend(inspect(name, (ROOT / name).read_bytes()))
    commits = git("rev-list", "--branches", "--tags").decode().splitlines()
    public_entries = {entry for commit in commits for entry in tree_entries(commit)}
    internal_refs = []
    for line in git("for-each-ref", "--format=%(refname) %(objecttype) %(objectname)").decode().splitlines():
        name, kind, oid = line.split()
        if not name.startswith(("refs/heads/", "refs/tags/", "refs/remotes/")):
            internal_refs.append((name, kind, oid))
    internal_entries = {entry for _, kind, oid in internal_refs if kind == "tree" for entry in tree_entries(oid)}
    contents = blobs(oid for oid, _, kind, _ in public_entries | internal_entries if kind == "blob")

    def scan(entries):
        found = []
        for oid, name, kind, mode in sorted(entries):
            if kind != "blob" or mode == "120000":
                found.append({"path": name, "kind": "nonregular_git_entry"})
            else:
                found.extend(inspect(name, contents[oid]))
        return found

    public, internal = scan(public_entries), scan(internal_entries)
    report = {
        "status": "PASS" if not current and not public else "REVIEW_REQUIRED",
        "candidate_files": len(names), "tracked_files": len(git("ls-files", "-z").split(b"\0")) - 1,
        "publication_commits": len(commits), "candidate_findings": current, "publication_history_findings": public,
        "internal_refs_not_for_publication": len(internal_refs), "internal_snapshot_findings": internal,
        "limits": "Pattern review is not an exhaustive secret detector. Internal tool refs are not publication branches; never mirror-push or distribute the working .git directory.",
    }
    print(json.dumps(report, indent=2))
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
