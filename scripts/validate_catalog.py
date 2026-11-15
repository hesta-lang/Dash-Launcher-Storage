#!/usr/bin/env python3
"""Validate the public Dash Launcher Storage catalog."""
import json
import re
import sys
from pathlib import Path

CATALOG = Path("catalog/catalog.json")
CHANNELS = ("stable", "beta", "archived")
ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}$")
SHA_RE = re.compile(r"^[a-fA-F0-9]{64}$")

def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)

def main() -> None:
    try:
        data = json.loads(CATALOG.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing {CATALOG}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON: {exc}")

    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("schema_version must be 1")
    channels = data.get("channels")
    if not isinstance(channels, dict):
        fail("channels must be an object")

    seen = set()
    for channel in CHANNELS:
        entries = channels.get(channel)
        if not isinstance(entries, list):
            fail(f"channels.{channel} must be an array")
        for index, item in enumerate(entries):
            prefix = f"channels.{channel}[{index}]"
            if not isinstance(item, dict):
                fail(f"{prefix} must be an object")
            for field in ("id", "version", "name", "source"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    fail(f"{prefix}.{field} must be a non-empty string")
            if not ID_RE.fullmatch(item["id"]):
                fail(f"{prefix}.id contains unsupported characters")
            if item["id"] in seen:
                fail(f"Duplicate version id: {item['id']}")
            seen.add(item["id"])
            url = item["source"]
            if not url.startswith("https://"):
                fail(f"{prefix}.source must use HTTPS")
            digest = item.get("sha256")
            if digest is not None and (not isinstance(digest, str) or not SHA_RE.fullmatch(digest)):
                fail(f"{prefix}.sha256 must contain exactly 64 hexadecimal characters")
            size = item.get("size_bytes")
            if size is not None and (not isinstance(size, int) or size <= 0):
                fail(f"{prefix}.size_bytes must be a positive integer")
            if item.get("distribution_authorized") is not True:
                fail(f"{prefix} must explicitly set distribution_authorized to true")

    print("Catalog validation passed.")

if __name__ == "__main__":
    main()
