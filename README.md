# Dash Launcher Storage

Public version catalog and GitHub Actions deployment pipeline for Dash Launcher.

## Project status

The repository includes:
- A **public read-only web panel** in `web/`.
- A JSON catalog grouped into Stable, Beta, and Archived.
- A provider directory that links to external sources and labels what each source actually contains.
- GitHub Actions workflows for catalog validation and GitHub Pages deployment.

The panel does not host APKs, scrape provider sites, or contain administrator credentials.

## Web panel

The panel is designed for mobile and desktop and reads:
- `web/catalog.json` — generated during deployment from `catalog/catalog.json`.
- `web/providers.json` — curated external provider directory.
- `web/index.html`, `web/styles.css`, and `web/app.js` — interface and catalog viewer.

### Publish with GitHub Pages

1. Open **Settings → Pages** in this repository.
2. Under **Build and deployment**, select **GitHub Actions** as the source.
3. The workflow **Deploy Dash Launcher Storage panel** will publish the `web/` directory after a relevant push, or when run manually from Actions.

The panel URL will appear in the successful deployment under the `github-pages` environment.

## Version catalog

The public catalog is `catalog/catalog.json`:

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
- `source`: HTTPS source URL.
- `distribution_authorized`: must be `true`.
- `sha256`: recommended 64-character SHA-256 digest.
- `size_bytes`: recommended positive file size.

Only include an entry if the file is legally authorized for distribution. The validator rejects an entry unless `distribution_authorized` is explicitly `true`.

## Provider research

The panel's provider directory is a research aid, not an endorsement or an automated downloader.

Current findings:
- **Google Play:** official listing for the paid Geometry Dash app; not a historical APK archive.
- **Uptodown:** version history confirmed for Geometry Dash Lite and spin-offs; a matching archive for the paid full game was not confirmed.
- **APKMirror:** searchable listings confirmed for Geometry Dash Lite and spin-offs; the category reviewed did not confirm the paid full game.
- **APKPure:** a version history is available for Geometry Dash World; the paid full game was not confirmed.
- **APKCombo:** a legacy listing for package `com.robtopx.geometryjump` shows version `2.011` dated 2015; this is not a current archive.
- **Uoldown:** lists eight historical entries for Geometry Dash, but each file needs package, signature, and provenance verification.

Provider availability can change. Before using any file, check the exact package ID, publisher certificate/signature, Android architecture, minimum OS, SHA-256, and legal distribution rights. Do not treat a site listing, attribution, or disclaimer as proof of permission to redistribute Geometry Dash.

## Validation

The **Validate Dash Launcher catalog** workflow runs:

```bash
python scripts/validate_catalog.py
```

It checks the JSON structure, required fields, unique IDs, HTTPS URLs, optional SHA-256 values, file sizes, and explicit distribution authorization.

## Hybrid architecture

- **Public:** this repository's catalog and panel assets.
- **Private:** administrator-only configuration and credentials, kept in GitHub Actions secrets or a separate private repository.
- **Distribution:** authorized hosting or GitHub Releases where suitable. GitHub Actions artifacts are temporary workflow outputs, not permanent storage.

The Android launcher should consume only published catalog entries and verify downloaded files against their SHA-256 digest. Never put tokens, signing keys, passwords, or private administration data in this public repository.
