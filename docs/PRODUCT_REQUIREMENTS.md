# Product Requirements

## Product goal

Provide a single-team, admin-protected application that converts rough website requests into a production-ready static site export through a staged workflow:

1. collect and polish requirements
2. generate UX/UI design guidance
3. generate frontend code and downloadable artifacts

## Primary users

- internal operators building websites for themselves or clients
- small teams producing brochure, campaign, portfolio, or company sites

## Functional requirements

### Input Studio

- accept text prompt, business context, target audience, brand direction, required sections, CTA goals, notes, and uploaded images
- convert raw input into a normalized `RequirementBrief`
- keep requirement versions so operators can compare and regenerate
- support provider/model selection for the refinement stage

### Design Studio

- generate a structured `DesignSpec` from an approved requirement brief
- include sitemap, page structure, component inventory, content strategy, visual direction, and image plan
- require explicit approval before build generation
- preserve prior design versions

### Build Studio

- generate a static export from the approved design
- include HTML, CSS, optional JavaScript, uploaded assets, manifest, and README
- package the export as a ZIP
- preserve build versions and download history

### Provider support

- support OpenAI, Gemini, Claude, and DeepSeek behind one normalized orchestration layer
- keep provider credentials server-side only
- expose default models by stage
- record run metadata including provider, model, prompt template version, latency, and token usage

### Asset policy

- uploaded assets are reusable project resources and may be bundled into exports
- internet images are suggested only as metadata
- the system must not auto-download or redistribute arbitrary web images
- image generation is out of scope in v1

### Persistence

- projects are saved and reopenable
- requirement, design, and build artifacts are versioned independently
- uploads and ZIP builds are stored on the server filesystem

## Non-functional requirements

- operator UI should work on desktop and mobile
- backend should remain single-instance friendly in v1
- generated output should be deterministic enough for testing and artifact diffing
- stage transitions should use validated structured schemas

## Out of scope

- end-user account systems
- multi-tenant SaaS isolation
- CMS backends
- ecommerce flows
- dynamic app generation
- automatic stock image import
