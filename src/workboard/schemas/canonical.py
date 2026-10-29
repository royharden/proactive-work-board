"""Canonical P01 UTF-8 JSON. No database, provider or credential discovery."""
from __future__ import annotations

import hashlib
import json
from typing import Any


def _check(value: Any) -> None:
    if value is None or type(value) in (str, int, bool):
        return
    if isinstance(value, list):
        for item in value:
            _check(item)
        return
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        for item in value.values():
            _check(item)
        return
    raise ValueError("canonical JSON requires string keys, integer numbers and JSON values")


def canonical_json(value: Any) -> str:
    _check(value)
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def proposal_digest(proposal: dict) -> str:
    return digest_json({key: value for key, value in proposal.items() if key != "digest"})
