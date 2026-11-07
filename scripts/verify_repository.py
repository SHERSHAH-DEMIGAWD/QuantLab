"""Offline source/document release checks; no staging, network or financial changes."""

import ast
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import re
from statistics import median
import subprocess
import tomllib
from urllib.parse import unquote


ROOT = Path(__file__).resolve().parents[1]


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True)


def main():
    files = [Path(name) for name in git("ls-files", "--cached", "--others", "--exclude-standard").splitlines()]
    assert files and len(files) == len(set(files))
    texts = {}
    counts = {"files": len(files), "python_ast": 0, "json": 0, "markdown_links": 0}
    secret_patterns = (r"AKIA[A-Z0-9]{16}", r"gh[pousr]_[A-Za-z0-9]{20,}", r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")
    for path in files:
        assert not {"node_modules", "dist", "__pycache__", ".venv", ".release-check", "test-results"}.intersection(path.parts), path
        assert path.suffix not in (".db", ".sqlite3", ".pyc") and path.name != ".env", path
        source = (ROOT / path).read_bytes()
        if path.suffix == ".png":
            assert path.parts[:2] == ("docs", "images") and source.startswith(b"\x89PNG\r\n\x1a\n"), path
            continue
        assert not source.startswith(b"\xef\xbb\xbf"), f"BOM: {path}"
        text = source.decode("utf-8")
        assert "\r" not in text and (not text or text.endswith("\n")), f"Line endings: {path}"
        assert not re.search(r"[ \t]+$", text, re.M), f"Trailing spaces: {path}"
        assert not any(re.search(pattern, text) for pattern in secret_patterns), f"Potential secret pattern: {path}"
        texts[path] = text
        if path.suffix == ".py":
            ast.parse(text, filename=str(path))
            counts["python_ast"] += 1
        if path.suffix == ".json":
            json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
            counts["json"] += 1
    for path, text in texts.items():
        if path.suffix != ".md":
            continue
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", text):
            link = link.strip().split(' "')[0].strip("<>")
            if re.match(r"[a-zA-Z][a-zA-Z0-9+.-]*:", link) or link.startswith("//"):
                continue
            target, _, anchor = link.partition("#")
            destination = ROOT / (path.parent / unquote(target) if target else path)
            assert destination.is_file(), f"Missing link: {path}: {link}"
            if anchor and destination.suffix == ".md":
                headings = re.findall(r"^#{1,6} +(.+)$", destination.read_text(encoding="utf-8"), re.M)
                slugs = [re.sub(r"[^\w\- ]", "", heading.lower()).replace(" ", "-") for heading in headings]
                assert unquote(anchor) in slugs, f"Missing anchor: {path}: {link}"
            counts["markdown_links"] += 1

    def whitespace(path):
        result = subprocess.run(["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf", "diff", "--no-index", "--check", "--", "/dev/null", str(path)], cwd=ROOT, text=True, capture_output=True)
        assert result.returncode in (0, 1) and not result.stdout and not result.stderr, f"Whitespace: {path}: {result.stdout}{result.stderr}"

    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(whitespace, files))
    package = json.loads(texts[Path("frontend/package.json")])
    lock = json.loads(texts[Path("frontend/package-lock.json")])
    for section in ("dependencies", "devDependencies"):
        assert package[section] == lock["packages"][""][section]
        assert all(re.fullmatch(r"\d+\.\d+\.\d+", version) for version in package[section].values())
    python = tomllib.loads(texts[Path("pyproject.toml")])["project"]
    assert python["dependencies"] == ["fastapi==0.162.0", "pydantic==2.14.2", "starlette==1.10.0", "uvicorn==0.54.0"]
    assert python["optional-dependencies"]["test"] == ["pytest==9.2.0", "httpx2==2.16.0"]
    baseline = json.loads(texts[Path("frontend/src/test/fixtures/backtest.json")])["implementation"]["source"]
    backend = ROOT / "backend/src/quantlab"
    actual = {path.relative_to(backend).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in backend.rglob("*.py")}
    assert actual == dict(baseline["source_files"]), "Production backend differs from verified baseline"
    core = [path for path in backend.rglob("*.py") if path.relative_to(backend).parts[0] in ("data", "execution", "strategies", "analytics", "audit", "experiments")]
    for path in core:
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
            names = [name.name for name in node.names] if isinstance(node, ast.Import) else [node.module or ""] if isinstance(node, ast.ImportFrom) else []
            assert not any(re.match(r"^(fastapi|pydantic|starlette|uvicorn|sqlite3|httpx2?|requests|quantlab\.(api|persistence|application))(\.|$)", name) for name in names), path
    for path, text in texts.items():
        if path.parts[:2] == ("frontend", "src") and "test" not in path.parts and path.suffix in (".ts", ".tsx"):
            assert not re.search(r"(?:from|import)\s*['\"][^'\"]*(?:fixtures|test-results)[^'\"]*['\"]", text), path
    for folder in ("data/raw", "data/processed"):
        assert [path.name for path in (ROOT / folder).iterdir()] == [".gitkeep"]
    latest = max(path for path in texts if path.parent == Path("docs/session-reports"))
    report = texts[latest]
    assert re.findall(r"^## ([A-L])\.", report, re.M) == list("ABCDEFGHIJKL")
    technical = report.split("Five technical questions:")[1].split("Three financial questions:")[0]
    finance = report.split("Three financial questions:")[1].split("Independent exercise:")[0]
    assert len(re.findall(r"^\d\. ", technical, re.M)) == 5
    assert len(re.findall(r"^\d\. ", finance, re.M)) == 3
    rows = re.findall(r"^\| (\d+) \| [^|]+ \| ([^|]+) \|", texts[Path("docs/ROADMAP.md")], re.M)
    assert len(rows) == 11 and all(status.strip().startswith("COMPLETE") for _, status in rows)
    assert "**Current phase:** 10" in texts[Path("docs/PROJECT_STATUS.md")]
    evidence = json.loads(texts[Path("docs/benchmark-results/phase10.json")])
    assert evidence["script_sha256"] == hashlib.sha256((ROOT / "scripts/benchmark.py").read_bytes()).hexdigest()
    assert evidence["source_snapshot_sha256"] == baseline["source_snapshot_sha256"]
    assert [result["bars"] for result in evidence["results"]] == [250, 1000, 5000]
    for result in evidence["results"]:
        assert len(result["operations"]) == 5
        for measured in result["operations"].values():
            assert len(measured["samples_ns"]) == evidence["repeats"] == 5
            assert all(value > 0 for value in measured["samples_ns"])
            assert measured["median_ms"] == median(measured["samples_ns"]) / 1e6
    staged_count = len(git("diff", "--cached", "--name-only").splitlines())
    print(json.dumps({"status": "PASS", **counts, "git_whitespace_files": len(files), "backend_hashes_unchanged": len(actual),
                      "independent_core_modules": len(core), "benchmark_samples": 75, "phases_complete": "0-10", "staged_files": staged_count,
                      "latest_report": latest.name}, indent=2))


if __name__ == "__main__":
    main()
