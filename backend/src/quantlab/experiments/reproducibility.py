"""Identify current local package source without fabricating a clean Git revision."""

from hashlib import sha256
from pathlib import Path
import platform

from quantlab.data.identity import canonical_json

from .models import ExperimentError, Reproducibility


def source_snapshot() -> Reproducibility:
    root = Path(__file__).resolve().parents[1]
    try:
        files = tuple((path.relative_to(root).as_posix(), sha256(path.read_bytes()).hexdigest())
                      for path in sorted(root.rglob("*.py")))
    except OSError as exc:
        raise ExperimentError(f"Cannot fingerprint local source: {exc}") from exc
    if not files:
        raise ExperimentError("Local Python package source is unavailable for fingerprinting.")
    return Reproducibility(
        sha256(canonical_json(files)).hexdigest(), files, platform.python_version(),
        "SHA-256 of sorted package-relative Python source paths/content hashes; no Git clean/revision claim. Retain these source bytes and original market inputs to reproduce; a fingerprint alone cannot restore them.",
    )
