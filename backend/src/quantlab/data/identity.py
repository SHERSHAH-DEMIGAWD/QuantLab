"""Identity of exact CSV bytes and effective metadata, independent of paths."""

from dataclasses import asdict
from hashlib import sha256
import json

from .models import Metadata


def canonical_json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def fingerprints(source_bytes: bytes, metadata: Metadata) -> tuple[str, str, str]:
    """Return source SHA-256, effective metadata SHA-256, and dataset ID."""
    source_hash = sha256(source_bytes).hexdigest()
    metadata_hash = sha256(canonical_json(asdict(metadata))).hexdigest()
    dataset_id = sha256(canonical_json({
        "contract_version": metadata.contract_version,
        "source_sha256": source_hash,
        "metadata_sha256": metadata_hash,
    })).hexdigest()
    return source_hash, metadata_hash, dataset_id
