# Dash Launcher Storage

Public version catalog and GitHub Actions validation pipeline for Dash Launcher.

## Current status

This repository currently provides the **public metadata catalog** and an automated validation workflow. It is not an APK mirror or an unlimited file-storage service.

## Repository layout

- `catalog/catalog.json` — public version catalog, grouped by Stable, Beta, and Archived.
- `scripts/validate_catalog.py` — validates catalog structure, unique IDs, HTTPS sources, optional SHA-256 values, and explicit distribution authorization.
- `.github/workflows/validate-catalog.yml` — runs validation on relevant pushes, pull requests, and manual dispatch.

## Catalog format

The initial catalog is intentionally empty:

```json
{
  "schema_version": 1,
  "updated_at": null,
  "channels": {
    "stable": [],
    "beta": [],
    "archived": []
  }
}
```

A published entry must include:

- `id`: unique identifier.
- `version`: version label.
- `name`: display name.
- `source`: HTTPS download URL from an authorized source.
- `distribution_authorized`: must be `true`.
- `sha256`: recommended 64-character SHA-256 digest.
- `size_bytes`: recommended positive file size.

Never add credentials, private tokens, signing keys, or unpublished administrative information to this public repository.

## Validation

GitHub Actions runs:

```bash
python scripts/validate_catalog.py
```

You can also run it manually from the Actions tab using **Validate Dash Launcher catalog**.

## Hybrid architecture

- **Public:** this repository's catalog and public website assets.
- **Private:** administrator-only configuration and secrets, kept in GitHub Actions secrets or a separate private repository.
- **Distribution:** authorized external hosting or GitHub Releases where appropriate. GitHub Actions artifacts are temporary workflow outputs, not permanent storage.

The Android launcher should consume only published catalog entries and verify downloaded files against their SHA-256 digest.

## Distribution and rights

Only list files that you are legally authorized to distribute. A disclaimer or attribution does not grant redistribution rights. Do not upload Geometry Dash APKs unless you have permission to distribute them.
