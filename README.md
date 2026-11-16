# Dash Launcher Storage

Public version catalog and GitHub Actions deployment pipeline for Dash Launcher.

## Project status

The repository contains:
- A public, read-only web panel in `web/`.
- A version catalog grouped into Stable, Beta, and Archived.
- A curated directory of external providers.
- GitHub Actions workflows for catalog validation and GitHub Pages deployment.

The panel does not host APKs, scrape provider sites, or contain administrator credentials.

## Web panel

The mobile-friendly panel reads:
- `web/catalog.json` — generated during deployment from `catalog/catalog.json`.
- `web/providers.json` — curated external provider directory.
- `web/index.html`, `web/styles.css`, and `web/app.js` — interface and catalog viewer.

To publish it, open **Settings → Pages**, select **GitHub Actions** as the source, and run or trigger **Deploy Dash Launcher Storage panel**. The resulting URL appears in the successful deployment under the `github-pages` environment.

## Version catalog

The public panel catalog is `catalog/catalog.json`. The Android client reads the separate manifest at `catalog/manifest.json`, the indexes in `catalog/versions/`, and per-version records in `catalog/metadata/`.

Current state:
- **Stable:** an external Google Play reference for Geometry Dash. The catalog tracks the Android patch as 2.2091; the official Play listing records an update on 19 October 2026 and displays the 2.209 feature notes. Confirm the exact version shown by the store on the target device.
- **Archived:** external Uoldown and APKCombo references. Uoldown lists eight entries under the title Geometry Dash; the package ID, signing certificate, ABI, and provenance of those files have not been verified by Dash Launcher.
- **Beta:** empty until a public beta for the full game can be verified.

An external reference always has `entry_type: "external_reference"`, `distribution_authorized: false`, and `download_enabled: false`. It only opens the provider's page. It is not an APK download and is not a claim that the file is authentic or safe.

## Direct APK release requirements

A direct APK entry must not be published until all of the following are verified from an authorized source:

1. Permission to distribute the file.
2. Exact package ID: `com.robtopx.geometryjump`.
3. SHA-256 fingerprint of the APK's signing certificate, not just a checksum copied from a download page.
4. The set of native ABIs actually present inside the APK.
5. Exact file size and SHA-256 digest of the APK.
6. HTTPS download URL and a successful validation/test on a compatible Android device.

The metadata uses `artifact.packageName`, `artifact.signingCertificateSha256`, root-level `supportedAbis`, `artifact.sizeBytes`, and `artifact.sha256`. The validator rejects incomplete direct artifacts and prevents external-page records from claiming APK identity or integrity values.

The Android launcher checks file size and SHA-256, parses the APK package, checks the signing certificate fingerprint, and inspects the ABI libraries before marking a file as verified. The current flow downloads and verifies the file; it does **not** silently install it.

## Updates and multiple installations

Android treats an APK with the same package ID and compatible signing certificate as an update to the existing app. That is the normal path for preserving the existing app's private data; the APK must also satisfy Android's version/update rules. A different package ID is a separate app installation with separate app data. Dash Launcher must not rewrite or re-sign Geometry Dash packages to create parallel copies.

## Provider research

The provider directory is a research aid, not an endorsement or an automated downloader.

- **Google Play:** official paid Geometry Dash listing by RobTop Games; current store reference, not an archive of older APKs.
- **Uptodown:** the history reviewed belongs to Geometry Dash Lite and spin-offs; a matching archive for the paid full game was not confirmed.
- **APKMirror:** searchable listings reviewed included Lite and spin-offs; a matching archive for the paid full game was not confirmed.
- **APKPure:** a version history was found for Geometry Dash World; the paid full game was not confirmed.
- **APKCombo:** a legacy listing for package `com.robtopx.geometryjump` shows version 2.011 from 2015; the downloaded APK itself has not been authenticated.
- **Uoldown:** shows eight historical versions under the Geometry Dash title. Package identity and signing details are still unverified.

Provider availability and store versions can change. Re-check the exact page, package, signing certificate, ABI, minimum Android version, SHA-256, and legal distribution rights before promoting any external listing to a direct artifact. A listing, attribution, or disclaimer is not permission to redistribute Geometry Dash.

## Validation

The **Validate Dash Launcher catalog** workflow runs:

```bash
python scripts/validate_catalog.py
```

It validates both the public panel catalog and the Android manifest, channel indexes, and per-version metadata. Direct artifacts must have a verified package ID, signer fingerprint, ABI list, file size, and SHA-256. External references must remain explicitly non-downloadable.

## Hybrid architecture

- **Public:** this repository's catalog and panel assets.
- **Private:** administrator-only configuration and credentials, kept in GitHub Actions secrets or a separate private repository.
- **Distribution:** authorized hosting or GitHub Releases where suitable. GitHub Actions artifacts are temporary workflow outputs, not permanent storage.

Never put tokens, signing keys, passwords, or private administration data in this public repository.
