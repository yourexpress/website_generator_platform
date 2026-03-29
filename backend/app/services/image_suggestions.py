"""Metadata-only image suggestion service."""

from __future__ import annotations

from urllib.parse import quote_plus

from app.schemas import ImageSuggestion, RequirementBrief


def build_image_suggestions(project_id: str, brief: RequirementBrief) -> list[ImageSuggestion]:
    base_terms = [
        brief.project_type,
        *brief.target_audience[:2],
        *brief.value_propositions[:1],
    ]
    query = " ".join(item for item in base_terms if item)
    encoded = quote_plus(query)
    return [
        ImageSuggestion(
            source_name="Unsplash",
            url=f"https://unsplash.com/s/photos/{encoded}",
            licensing_note="Review Unsplash license and attribution requirements before use.",
            intended_use="Hero image reference",
            query=query,
        ),
        ImageSuggestion(
            source_name="Pexels",
            url=f"https://www.pexels.com/search/{encoded}/",
            licensing_note="Review Pexels license before downloading or redistributing.",
            intended_use="Supporting section imagery",
            query=query,
        ),
        ImageSuggestion(
            source_name="unDraw",
            url="https://undraw.co/illustrations",
            licensing_note="Review unDraw terms for commercial use.",
            intended_use="Illustrative placeholder option",
            query=query,
        ),
    ]
