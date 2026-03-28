from __future__ import annotations

import pytest

from fastai.prompting import PROMPT_SECTION_ORDER, assemble_prompt


def test_assemble_prompt_includes_expected_sections_in_fixed_order() -> None:
    result = assemble_prompt(
        user_query="What is FastAI?",
        retrieved_context="FastAI is a framework.",
        system_instructions="Answer clearly.",
        route_instructions="Use concise style.",
    )

    section_names = tuple(section.name for section in result.sections)
    assert section_names == PROMPT_SECTION_ORDER

    expected_prompt = (
        "[system_instructions]\nAnswer clearly.\n\n"
        "[route_instructions]\nUse concise style.\n\n"
        "[retrieved_context]\nFastAI is a framework.\n\n"
        "[user_query]\nWhat is FastAI?"
    )
    assert result.final_prompt == expected_prompt


def test_assemble_prompt_is_deterministic_for_same_inputs() -> None:
    first = assemble_prompt(
        user_query="Q",
        retrieved_context="C",
        system_instructions="S",
        route_instructions="R",
    )
    second = assemble_prompt(
        user_query="Q",
        retrieved_context="C",
        system_instructions="S",
        route_instructions="R",
    )

    assert first == second


def test_assemble_prompt_normalizes_optional_values() -> None:
    result = assemble_prompt(
        user_query="  query  ",
        retrieved_context="  context  ",
        system_instructions="   ",
        route_instructions=None,
    )

    assert result.sections[0].content == ""
    assert result.sections[1].content == ""
    assert result.sections[2].content == "context"
    assert result.sections[3].content == "query"


def test_assemble_prompt_rejects_empty_user_query() -> None:
    with pytest.raises(ValueError, match="user_query"):
        assemble_prompt(user_query="   ", retrieved_context="context")
