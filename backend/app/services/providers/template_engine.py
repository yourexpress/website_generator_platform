"""Deterministic fallback generator used for local development and tests."""

from __future__ import annotations

import re
from pathlib import Path

from app.schemas import (
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


def _slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "page"


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
        value_propositions=[
            "Clarify the offer quickly above the fold.",
            "Build trust through proof, process, and visual consistency.",
            f"Drive visitors toward the primary CTA: {ctas[0]}.",
        ],
        recommended_tone=["confident", "clear", "helpful", "modern"],
        required_pages=required_pages,
        content_requirements=[
            "Write concise headline and subhead copy for every hero section.",
            "Translate raw notes into scannable sections with strong hierarchy.",
            "Add proof blocks such as testimonials, metrics, or logos where appropriate.",
        ],
        asset_requirements=asset_notes,
        assumptions=assumptions,
        open_questions=[
            "Which proof points or testimonials should replace the default placeholders?",
            "Should the final site include a lead form, email CTA, or outbound booking link?",
        ],
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
            mood="Bold, editorial, and trustworthy with high contrast",
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
