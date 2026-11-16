#!/usr/bin/env python3
"""Validate the public Dash Launcher catalog and its launcher-facing indexes."""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

CATALOG = Path("catalog/catalog.json")
LAUNCHER_CATALOG = Path("catalog")
CHANNELS = ("stable", "beta", "archived")
ID_RE = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9._-]{0,95}$")
SHA_RE = re.compile(r"^[a-fA-F0-9]{64}$")
SUPPORTED_ABIS = {"arm64-v8a", "armeabi-v7a", "x86", "x86_64"}
ALLOWED_EXTERNAL_HOSTS = {
    "play.google.com",
    "uoldown.com",
    "www.uoldown.com",
    "apkcombo.com",
    "www.apkcombo.com",
}


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load_json(path: Path, label: str):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        fail(f"Missing {path} ({label})")
    except json.JSONDecodeError as exc:
        fail(f"Invalid JSON in {path}: {exc}")


def valid_https_url(value: object, allowed_hosts: set[str] | None = None) -> bool:
    if not isinstance(value, str) or not value.strip() or value != value.strip():
        return False
    parsed = urlparse(value)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        return False
    if allowed_hosts is not None and parsed.hostname.lower() not in allowed_hosts:
        return False
    return True


def validate_panel_catalog() -> None:
    data = load_json(CATALOG, "web panel catalog")
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        fail("catalog/catalog.json: schema_version must be 1")
    channels = data.get("channels")
    if not isinstance(channels, dict):
        fail("catalog/catalog.json: channels must be an object")

    seen: set[str] = set()
    for channel in CHANNELS:
        entries = channels.get(channel)
        if not isinstance(entries, list):
            fail(f"catalog/catalog.json: channels.{channel} must be an array")
        for index, item in enumerate(entries):
            prefix = f"catalog/catalog.json: channels.{channel}[{index}]"
            if not isinstance(item, dict):
                fail(f"{prefix} must be an object")
            for field in ("id", "version", "name", "source"):
                if not isinstance(item.get(field), str) or not item[field].strip():
                    fail(f"{prefix}.{field} must be a non-empty string")
            if not ID_RE.fullmatch(item["id"]):
                fail(f"{prefix}.id contains unsupported characters")
            if item["id"] in seen:
                fail(f"Duplicate panel catalog id: {item['id']}")
            seen.add(item["id"])

            if item.get("entry_type") == "external_reference":
                if item.get("distribution_authorized") is not False:
                    fail(f"{prefix} external_reference must set distribution_authorized to false")
                if item.get("download_enabled") is not False:
                    fail(f"{prefix} external_reference must set download_enabled to false")
                if "package_name" in item or "signing_certificate_sha256" in item:
                    fail(f"{prefix} external_reference cannot claim an unverified APK identity")
                if not valid_https_url(item["source"], ALLOWED_EXTERNAL_HOSTS):
                    fail(f"{prefix}.source must be HTTPS on an approved external provider domain")
            else:
                if not valid_https_url(item["source"]):
                    fail(f"{prefix}.source must use HTTPS")
                if item.get("distribution_authorized") is not True:
                    fail(f"{prefix} must explicitly set distribution_authorized to true")
                digest = item.get("sha256")
                if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                    fail(f"{prefix}.sha256 must contain exactly 64 hexadecimal characters")
                size = item.get("size_bytes")
                if not isinstance(size, int) or size <= 0:
                    fail(f"{prefix}.size_bytes must be a positive integer")
                if item.get("package_name") != "com.robtopx.geometryjump":
                    fail(f"{prefix}.package_name must be the official Geometry Dash package")
                signer = item.get("signing_certificate_sha256")
                if not isinstance(signer, str) or not SHA_RE.fullmatch(signer):
                    fail(f"{prefix}.signing_certificate_sha256 must be a verified 64-character SHA-256")


def validate_launcher_indexes() -> None:
    manifest_path = LAUNCHER_CATALOG / "manifest.json"
    manifest = load_json(manifest_path, "launcher manifest")
    if not isinstance(manifest, dict) or manifest.get("catalogVersion") != 1:
        fail("catalog/manifest.json: catalogVersion must be 1")
    version_files = manifest.get("versionFiles")
    if not isinstance(version_files, dict):
        fail("catalog/manifest.json: versionFiles must be an object")

    all_ids: set[str] = set()
    for channel in CHANNELS:
        relative_index = version_files.get(channel)
        if not isinstance(relative_index, str) or not relative_index:
            fail(f"catalog/manifest.json: missing versionFiles.{channel}")
        index_path = LAUNCHER_CATALOG / relative_index
        index = load_json(index_path, f"{channel} index")
        if not isinstance(index, list):
            fail(f"{index_path}: channel index must be an array")

        for position, item in enumerate(index):
            prefix = f"{index_path}[{position}]"
            if not isinstance(item, dict):
                fail(f"{prefix} must be an object")
            required = ("id", "displayName", "version", "channel", "platform", "minAndroidApi", "metadata")
            for field in required:
                if field not in item:
                    fail(f"{prefix}.{field} is required")
            version_id = item["id"]
            if not isinstance(version_id, str) or not ID_RE.fullmatch(version_id):
                fail(f"{prefix}.id is invalid")
            if version_id in all_ids:
                fail(f"Duplicate launcher catalog id: {version_id}")
            all_ids.add(version_id)
            if item["channel"] != channel:
                fail(f"{prefix}.channel must be {channel}")
            if item["platform"] != "android":
                fail(f"{prefix}.platform must be android")
            if not isinstance(item["minAndroidApi"], int) or item["minAndroidApi"] < 26:
                fail(f"{prefix}.minAndroidApi must be at least 26 (launcher minimum)")
            if not isinstance(item["metadata"], str) or not item["metadata"]:
                fail(f"{prefix}.metadata must be a relative path")

            metadata_path = (index_path.parent / item["metadata"]).resolve()
            try:
                metadata_path.relative_to(LAUNCHER_CATALOG.resolve())
            except ValueError:
                fail(f"{prefix}.metadata escapes the catalog directory")
            metadata = load_json(metadata_path, f"metadata for {version_id}")
            if not isinstance(metadata, dict):
                fail(f"{metadata_path}: metadata must be an object")
            if metadata.get("id") != version_id:
                fail(f"{metadata_path}: metadata id does not match index id")
            if metadata.get("platform") != "android":
                fail(f"{metadata_path}: platform must be android")
            if metadata.get("minAndroidApi") != item["minAndroidApi"]:
                fail(f"{metadata_path}: minAndroidApi must match its index entry")
            abis = metadata.get("supportedAbis")
            if not isinstance(abis, list) or any(abi not in SUPPORTED_ABIS for abi in abis):
                fail(f"{metadata_path}: supportedAbis contains an unsupported value")
            artifact = metadata.get("artifact")
            if artifact is None:
                continue
            if not isinstance(artifact, dict):
                fail(f"{metadata_path}: artifact must be an object or null")

            provider = artifact.get("provider")
            if provider == "external-page":
                if not isinstance(artifact.get("providerName"), str) or not artifact["providerName"].strip():
                    fail(f"{metadata_path}: external-page requires providerName")
                if not valid_https_url(artifact.get("url"), ALLOWED_EXTERNAL_HOSTS):
                    fail(f"{metadata_path}: external-page URL is not an approved HTTPS provider page")
                if abis:
                    # ABI details must only be populated when verified.
                    fail(f"{metadata_path}: external-page references must not claim unverified ABIs")
                if artifact.get("packageName") is not None or artifact.get("signingCertificateSha256") is not None:
                    fail(f"{metadata_path}: external-page references cannot claim an unverified APK identity")
                if artifact.get("sizeBytes") is not None or artifact.get("sha256") is not None:
                    fail(f"{metadata_path}: external-page references cannot claim APK size or SHA-256")
            elif provider == "direct":
                if not abis:
                    fail(f"{metadata_path}: direct APK entries require at least one verified ABI")
                if not valid_https_url(artifact.get("url")):
                    fail(f"{metadata_path}: direct artifact requires an HTTPS URL")
                size = artifact.get("sizeBytes")
                digest = artifact.get("sha256")
                if not isinstance(size, int) or size <= 0:
                    fail(f"{metadata_path}: direct artifact requires a positive sizeBytes")
                if not isinstance(digest, str) or not SHA_RE.fullmatch(digest):
                    fail(f"{metadata_path}: direct artifact requires a valid SHA-256")
                if artifact.get("packageName") != "com.robtopx.geometryjump":
                    fail(f"{metadata_path}: direct artifact must declare the official Geometry Dash package")
                signer = artifact.get("signingCertificateSha256")
                if not isinstance(signer, str) or not SHA_RE.fullmatch(signer):
                    fail(f"{metadata_path}: direct artifact requires a verified signer certificate SHA-256")
            else:
                fail(f"{metadata_path}: unsupported provider '{provider}'")


def main() -> None:
    validate_panel_catalog()
    validate_launcher_indexes()
    print("Catalog validation passed (panel references and launcher indexes).")


if __name__ == "__main__":
    main()
