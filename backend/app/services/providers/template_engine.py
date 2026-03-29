"""Deterministic fallback generator used for local development and tests."""

from __future__ import annotations

import re
from pathlib import Path

from app.schemas import (
    AssistantMessage,
    AssetReference,
    ComponentSpec,
    DesignPage,
    DesignPageSection,
    DesignSpec,
    PagePlan,
    RequirementBrief,
    RequirementInput,
    VisualDirection,
)


SECTION_ALIASES: dict[str, tuple[str, ...]] = {
    "hero": ("hero", "hero section", "above the fold"),
    "services": ("services", "offerings", "what we do"),
    "offer": ("offer", "offer section", "solution"),
    "proof": ("proof", "credibility", "social proof"),
    "testimonials": ("testimonials", "reviews", "client quotes"),
    "case studies": ("case studies", "case studies", "work samples"),
    "pricing": ("pricing", "plans", "packages"),
    "faq": ("faq", "frequently asked questions"),
    "about": ("about", "our story", "who we are"),
    "contact": ("contact", "get in touch", "reach out"),
}

TONE_KEYWORDS = (
    "bold",
    "editorial",
    "premium",
    "minimal",
    "modern",
    "clean",
    "playful",
    "warm",
    "luxury",
    "technical",
    "futuristic",
    "trustworthy",
)


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "page"


def _dedupe_keep_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        normalized = value.strip()
        key = normalized.lower()
        if not normalized or key in seen:
            continue
        seen.add(key)
        result.append(normalized)
    return result


def _extract_sections(text: str, fallback: list[str]) -> list[str]:
    lower_text = text.lower()
    requested: list[str] = []
    for canonical, aliases in SECTION_ALIASES.items():
        if any(alias in lower_text for alias in aliases):
            requested.append(canonical)
    return _dedupe_keep_order(requested or fallback)


def _extract_audiences(text: str, fallback: list[str]) -> list[str]:
    matches = re.findall(r"(?:audience|target(?:ing)?|for)\s+(?:is\s+|includes\s+|:)?([^.!\n]{5,80})", text, flags=re.IGNORECASE)
    extracted: list[str] = []
    for match in matches:
        candidates = re.split(r",|/| and ", match)
        for candidate in candidates:
            cleaned = candidate.strip(" .:-")
            if 2 <= len(cleaned.split()) <= 6:
                extracted.append(cleaned)
    return _dedupe_keep_order(extracted or fallback)


def _extract_brand_direction(text: str, fallback: str | None) -> str | None:
    tone_hits = [keyword for keyword in TONE_KEYWORDS if re.search(rf"\b{re.escape(keyword)}\b", text, flags=re.IGNORECASE)]
    if tone_hits:
        return ", ".join(_dedupe_keep_order([item.title() for item in tone_hits]))
    return fallback


def _extract_cta_goals(text: str, fallback: list[str]) -> list[str]:
    matches = re.findall(r"(?:cta|call to action|visitors? to|should (?:book|start|request|get|contact))([^.!\n]{0,80})", text, flags=re.IGNORECASE)
    extracted: list[str] = []
    for match in matches:
        cleaned = match.strip(" .:-")
        if cleaned:
            extracted.append(cleaned[0].upper() + cleaned[1:])
    return _dedupe_keep_order(extracted or fallback)


def _extract_business_type(text: str, fallback: str) -> str:
    match = re.search(r"(?:website|site|homepage|landing page)\s+for\s+([^.!\n]{4,80})", text, flags=re.IGNORECASE)
    if match:
        return match.group(1).strip(" .:-")
    return fallback


def _extract_value_propositions(prompt: str, fallback_cta: str) -> list[str]:
    snippets = re.split(r"[.\n]", prompt)
    extracted = [snippet.strip() for snippet in snippets if 4 <= len(snippet.strip().split()) <= 14]
    shortlisted = extracted[:2]
    values = shortlisted + [f"Drive visitors toward the primary CTA: {fallback_cta}."]
    return _dedupe_keep_order(values)


def _extract_open_questions(prompt: str) -> list[str]:
    questions = re.findall(r"([^?.!\n]{8,120}\?)", prompt)
    defaults = [
        "Which proof points or testimonials should replace the default placeholders?",
        "Should the final site include a lead form, email CTA, or outbound booking link?",
    ]
    return _dedupe_keep_order(questions + defaults)[:3]


def build_requirement_brief(project_name: str, payload: RequirementInput, asset_filenames: list[str]) -> RequirementBrief:
    business_type = payload.business_type or "small business"
    audience = payload.target_audience or ["prospective customers", "partners"]
    sections = payload.required_sections or [
        "hero",
        "services",
        "proof",
        "about",
        "contact",
    ]
    ctas = payload.cta_goals or ["Book a consultation", "Start a conversation"]
    page_count = payload.preferred_page_count
    page_titles = ["Home", "About", "Services", "Contact", "Work"]
    required_pages: list[PagePlan] = []
    for index in range(page_count):
        title = page_titles[index]
        slug = "index" if index == 0 else _slugify(title)
        required_pages.append(
            PagePlan(
                slug=slug,
                title=title,
                goal=f"Guide visitors through the core offer and drive {ctas[0].lower()}.",
                sections=sections if index == 0 else ["hero", "content", "cta"],
            )
        )
    if page_count > 1:
        required_pages[-1] = PagePlan(
            slug="contact",
            title="Contact",
            goal=f"Make it frictionless to {ctas[0].lower()}.",
            sections=["hero", "contact-methods", "faq", "cta"],
        )
    asset_notes = [f"Reuse uploaded asset: {name}" for name in asset_filenames]
    if not asset_notes:
        asset_notes = [
            "Recommend a hero image from a licensed source if the user does not upload one.",
            "Use graphic placeholders where a custom brand asset is still missing.",
        ]

    assumptions = [
        "The first release targets a static brochure-style site with concise persuasive copy.",
        "The user wants a polished layout with mobile-first responsiveness.",
    ]
    if payload.brand_direction:
        assumptions.append(f"Visual direction should reflect: {payload.brand_direction}.")
    return RequirementBrief(
        project_name=project_name,
        project_type=payload.site_type,
        summary=payload.prompt.strip(),
        business_context=f"{payload.business_name or project_name} is presented as a {business_type} website.",
        target_audience=audience,
        value_propositions=_extract_value_propositions(payload.prompt, ctas[0]),
        recommended_tone=_dedupe_keep_order(
            [item.lower() for item in (payload.brand_direction or "confident, clear, helpful, modern").replace("/", ",").split(",")]
        ),
        required_pages=required_pages,
        content_requirements=[
            "Write concise headline and subhead copy for every hero section.",
            "Translate raw notes into scannable sections with strong hierarchy.",
            "Add proof blocks such as testimonials, metrics, or logos where appropriate.",
        ],
        asset_requirements=asset_notes,
        assumptions=assumptions,
        open_questions=_extract_open_questions(payload.prompt),
    )


def build_design_spec(brief: RequirementBrief, asset_filenames: list[str]) -> DesignSpec:
    colors = ["#0E1C36", "#2A6F97", "#F4F1DE", "#E36414", "#F7B267"]
    typography = "Space Grotesk for UI with Fraunces-style editorial headlines"
    pages: list[DesignPage] = []
    components: list[ComponentSpec] = []
    image_plan: list[AssetReference] = []

    for page in brief.required_pages:
        sections: list[DesignPageSection] = []
        for section_name in page.sections:
            sections.append(
                DesignPageSection(
                    name=section_name.title().replace("-", " "),
                    purpose=f"Advance the page goal through the {section_name} section.",
                    layout="responsive grid with strong vertical rhythm",
                    content_items=[
                        "headline",
                        "supporting copy",
                        "visual or illustration",
                        "call to action" if section_name in {"hero", "cta"} else "supporting detail",
                    ],
                    cta="Start your project" if section_name in {"hero", "cta"} else None,
                )
            )
        pages.append(
            DesignPage(
                slug=page.slug,
                title=page.title,
                hero_message=f"{brief.project_name}: a clear, high-trust digital front door.",
                sections=sections,
            )
        )
        components.extend(
            [
                ComponentSpec(
                    name="Hero Banner",
                    purpose="Frame the offer quickly with a strong headline and primary CTA.",
                    page_slug=page.slug,
                    notes="Use a two-column composition on desktop and a single-column stack on mobile.",
                ),
                ComponentSpec(
                    name="Trust Strip",
                    purpose="Surface outcomes, credentials, or client proof.",
                    page_slug=page.slug,
                    notes="Keep the proof compact and scannable.",
                ),
            ]
        )

    for filename in asset_filenames:
        image_plan.append(
            AssetReference(
                kind="uploaded",
                label=filename,
                source_type="project-upload",
                page_slug="index",
                section="Hero",
                alt_text=f"{brief.project_name} uploaded visual",
                notes="Prefer this asset before suggesting a licensed stock image.",
            )
        )
    if not image_plan:
        image_plan.append(
            AssetReference(
                kind="placeholder",
                label="Licensed hero image placeholder",
                source_type="placeholder",
                page_slug="index",
                section="Hero",
                alt_text="Placeholder hero visual",
                notes="Replace with an uploaded image or licensed image recommendation before final handoff.",
            )
        )

    return DesignSpec(
        project_name=brief.project_name,
        sitemap=[page.slug for page in brief.required_pages],
        pages=pages,
        visual_direction=VisualDirection(
            mood=", ".join(word.title() for word in brief.recommended_tone[:3]) or "Bold, editorial, and trustworthy",
            colors=colors,
            typography=typography,
            layout_keywords=["editorial hero", "asymmetric cards", "scannable rhythm", "mobile-first"],
        ),
        components=components,
        image_plan=image_plan,
        content_strategy=[
            "Lead with outcome language before process language.",
            "Keep paragraphs short and pair each major claim with a visual or proof element.",
            "Use one dominant CTA per page with lighter secondary actions.",
        ],
        implementation_notes=[
            "Generate semantic HTML sections per page and a shared stylesheet.",
            "Use CSS custom properties for palette, spacing, and type scale.",
            "Keep JavaScript minimal and only for navigation or small interactions.",
        ],
    )


def make_index_filename(slug: str) -> str:
    return "index.html" if slug == "index" else f"{slug}.html"


def infer_image_label(asset_path: str) -> str:
    return Path(asset_path).name


def build_requirement_input_from_conversation(
    *,
    project_name: str,
    project_summary: str | None,
    messages: list[str],
    site_type: str,
    preferred_page_count: int,
    uploaded_asset_ids: list[str],
    previous_input: RequirementInput | None,
) -> RequirementInput:
    trimmed_messages = [message.strip() for message in messages if message.strip()]
    combined_prompt = "\n\n".join(trimmed_messages)
    last_message = trimmed_messages[-1] if trimmed_messages else ""
    summary_seed = project_summary or "business website"
    previous = previous_input or RequirementInput(
        prompt=combined_prompt or f"Build a polished website for {project_name}.",
        business_name=project_name,
    )
    inferred_sections = _extract_sections(combined_prompt, previous.required_sections or ["hero", "offer", "proof", "about", "contact"])
    inferred_audience = _extract_audiences(combined_prompt, previous.target_audience or ["prospective customers", "decision-makers"])
    inferred_brand = _extract_brand_direction(combined_prompt, previous.brand_direction or "confident, modern, conversion-focused")
    inferred_cta = _extract_cta_goals(combined_prompt, previous.cta_goals or ["Start a conversation", "Request a proposal"])
    return RequirementInput(
        prompt=combined_prompt or previous.prompt,
        business_name=previous.business_name or project_name,
        business_type=_extract_business_type(combined_prompt, previous.business_type or summary_seed),
        site_type=site_type,  # type: ignore[arg-type]
        target_audience=inferred_audience,
        brand_direction=inferred_brand,
        required_sections=inferred_sections,
        cta_goals=inferred_cta,
        reference_notes="\n\n".join(filter(None, [previous.reference_notes, last_message])) or None,
        preferred_page_count=preferred_page_count,
        uploaded_asset_ids=uploaded_asset_ids,
    )


def build_assistant_reply(
    *,
    brief: RequirementBrief,
    design: DesignSpec,
    message_count: int,
) -> str:
    focus_page = brief.required_pages[0].title if brief.required_pages else "the homepage"
    next_question = brief.open_questions[0] if brief.open_questions else "What proof points should the homepage emphasize next?"
    preserved_points = _dedupe_keep_order(
        [
            f"{len(design.pages)} page layout",
            f"sections: {', '.join(brief.required_pages[0].sections[:4])}" if brief.required_pages else "",
            f"tone: {', '.join(brief.recommended_tone[:3])}",
            f"CTA: {brief.value_propositions[-1]}" if brief.value_propositions else "",
        ]
    )
    return (
        f"I updated the concept after message {message_count} using the full session context. "
        f"The current direction is a {brief.project_type} site for {', '.join(brief.target_audience[:2])} "
        f"with {len(design.pages)} page(s), led by {focus_page}. "
        f"I kept these requirements in view: {'; '.join(preserved_points[:3])}. "
        f"The preview now reflects a {design.visual_direction.mood.lower()} visual system. "
        f"Next useful detail: {next_question}"
    )
