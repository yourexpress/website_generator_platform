# Export Bundle Specification

## Purpose

Each generated build produces a filesystem directory and a downloadable ZIP archive containing the generated website and handoff metadata.

## Expected contents

- `index.html`
- additional page HTML files when the sitemap has multiple pages
- `styles.css`
- `app.js`
- `README.md`
- `manifest.json`
- `assets/` for uploaded project images

## Rules

- only explicitly uploaded project assets are bundled
- recommended internet images remain metadata only
- exported HTML must reference relative asset paths
- CSS should be shared across pages
- JavaScript should be minimal and optional

## Manifest fields

- `project_name`
- `build_id`
- `site_title`
- `generated_at`
- `provider`
- `model`
- `pages`
- `files`
- `assets`
- `notes`

## Production handoff expectations

The export is intended as a generated draft. Before launch, operators should:

- replace placeholder copy
- verify image licensing
- connect real CTAs, forms, or booking URLs
- review responsive spacing
- add analytics or deployment-specific scripts
