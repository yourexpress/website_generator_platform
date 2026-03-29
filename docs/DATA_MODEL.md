# Data Model

## Project

- `id`
- `name`
- `summary`
- `created_at`
- `updated_at`
- `active_requirement_version_id`
- `active_design_version_id`
- `active_build_version_id`

## UploadedAsset

- `id`
- `project_id`
- `filename`
- `content_type`
- `size_bytes`
- `storage_path`
- `created_at`

## RequirementVersion

- `id`
- `project_id`
- `version_number`
- `status`
- `provider`
- `model`
- `source_input_json`
- `brief_json`
- `approved`
- `created_at`
- `approved_at`

## DesignVersion

- `id`
- `project_id`
- `requirement_version_id`
- `version_number`
- `status`
- `provider`
- `model`
- `design_json`
- `approved`
- `created_at`
- `approved_at`

## BuildVersion

- `id`
- `project_id`
- `design_version_id`
- `version_number`
- `status`
- `provider`
- `model`
- `manifest_json`
- `export_root_path`
- `export_zip_path`
- `created_at`
- `completed_at`

## GenerationRun

- `id`
- `project_id`
- `stage`
- `provider`
- `model`
- `prompt_version`
- `status`
- `latency_ms`
- `token_usage_json`
- `error_message`
- `output_ref_id`
- `created_at`
- `completed_at`

## Structured contracts

### `RequirementBrief`

- project identity and website type
- business context
- target audiences
- value propositions
- recommended tone
- required pages and sections
- content requirements
- asset requirements
- assumptions and open questions

### `DesignSpec`

- sitemap
- page definitions
- visual direction
- component inventory
- image plan
- content strategy
- implementation notes

### `BuildManifest`

- build id
- project and site title
- provider and model metadata
- generated timestamps
- files included in export
- asset references
- notes and production handoff reminders
