# Dash Launcher Android catalog

This directory exposes the read-only JSON format consumed by the Android launcher. The manifest and channel indexes are deployed with the Dash Launcher Storage Pages site. Version indexes remain empty until entries with verified metadata and legally authorized distribution sources are added.

Each index entry points to a metadata JSON document relative to its channel index. Direct APK downloads must include a verified HTTPS URL, exact byte size, and SHA-256. External provider references are not treated as direct APK downloads.
