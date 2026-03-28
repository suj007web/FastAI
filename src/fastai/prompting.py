"""Prompt construction utilities for deterministic sectioned templates.

Template variables (fixed order):
1. system_instructions
2. route_instructions
3. retrieved_context
4. user_query
"""

from __future__ import annotations

from dataclasses import dataclass

PromptSectionName = str
PROMPT_SECTION_ORDER: tuple[PromptSectionName, ...] = (
    "system_instructions",
    "route_instructions",
    "retrieved_context",
    "user_query",
)


@dataclass(frozen=True)
class PromptSection:
    """One named prompt section in final assembly order."""

    name: str
    content: str


@dataclass(frozen=True)
class PromptBuildResult:
    """Deterministic prompt assembly result."""

    final_prompt: str
    sections: tuple[PromptSection, ...]


def assemble_prompt(
    *,
    user_query: str,
    retrieved_context: str,
    system_instructions: str | None = None,
    route_instructions: str | None = None,
) -> PromptBuildResult:
    """Assemble final prompt in deterministic section order.

    Section order is fixed by PROMPT_SECTION_ORDER and cannot vary by input.
    """
    normalized_query = user_query.strip()
    if not normalized_query:
        raise ValueError("user_query must not be empty for prompt assembly.")

    sections = (
        PromptSection("system_instructions", _normalize_optional(system_instructions)),
        PromptSection("route_instructions", _normalize_optional(route_instructions)),
        PromptSection("retrieved_context", retrieved_context.strip()),
        PromptSection("user_query", normalized_query),
    )

    rendered = "\n\n".join(_render_section(section) for section in sections)
    return PromptBuildResult(final_prompt=rendered, sections=sections)


def _normalize_optional(value: str | None) -> str:
    if value is None:
        return ""
    return value.strip()


def _render_section(section: PromptSection) -> str:
    return f"[{section.name}]\n{section.content}"
