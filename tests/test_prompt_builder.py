"""
Prompt Builder Tests for ElectIQ.

Tests role-aware system prompt construction and
suggested question retrieval for all personas.
"""

import pytest

from backend.services.prompt_builder import (
    build_system_prompt,
    get_suggested_questions,
    BASE_SYSTEM_PROMPT,
    ROLE_CONTEXT,
    SUGGESTED_QUESTIONS,
)


class TestBuildSystemPrompt:
    """System prompt construction tests."""

    def test_includes_base_prompt(self):
        prompt = build_system_prompt("voter")
        assert "ElectIQ" in prompt
        assert "non-partisan" in prompt

    def test_includes_role_context(self):
        prompt = build_system_prompt("voter")
        assert "voter" in prompt.lower() or "registration" in prompt.lower()

    def test_candidate_context(self):
        prompt = build_system_prompt("candidate")
        assert "candidate" in prompt.lower() or "nomination" in prompt.lower()

    def test_journalist_context(self):
        prompt = build_system_prompt("journalist")
        assert "journalist" in prompt.lower() or "media" in prompt.lower()

    def test_student_context(self):
        prompt = build_system_prompt("student")
        assert "student" in prompt.lower() or "educational" in prompt.lower()

    def test_invalid_role_defaults_to_voter(self):
        prompt = build_system_prompt("hacker")
        voter_prompt = build_system_prompt("voter")
        assert prompt == voter_prompt

    def test_none_role_defaults_to_voter(self):
        prompt = build_system_prompt(None)
        voter_prompt = build_system_prompt("voter")
        assert prompt == voter_prompt

    def test_empty_role_defaults_to_voter(self):
        prompt = build_system_prompt("")
        voter_prompt = build_system_prompt("voter")
        assert prompt == voter_prompt

    def test_case_insensitive(self):
        prompt1 = build_system_prompt("VOTER")
        prompt2 = build_system_prompt("voter")
        assert prompt1 == prompt2

    def test_prompt_has_rules(self):
        prompt = build_system_prompt("voter")
        assert "NEVER express political opinions" in prompt
        assert "cite an official source" in prompt

    def test_prompt_not_too_short(self):
        prompt = build_system_prompt("voter")
        assert len(prompt) > 200, "System prompt should be comprehensive"


class TestSuggestedQuestions:
    """Suggested questions retrieval tests."""

    def test_voter_has_suggestions(self):
        questions = get_suggested_questions("voter")
        assert len(questions) >= 3
        assert all(isinstance(q, str) for q in questions)

    def test_candidate_has_suggestions(self):
        questions = get_suggested_questions("candidate")
        assert len(questions) >= 3

    def test_journalist_has_suggestions(self):
        questions = get_suggested_questions("journalist")
        assert len(questions) >= 3

    def test_student_has_suggestions(self):
        questions = get_suggested_questions("student")
        assert len(questions) >= 3

    def test_invalid_role_defaults_to_voter(self):
        questions = get_suggested_questions("invalid")
        voter_questions = get_suggested_questions("voter")
        assert questions == voter_questions

    def test_suggestions_are_meaningful(self):
        """Suggestions should be non-trivial text."""
        for role in ["voter", "candidate", "journalist", "student"]:
            questions = get_suggested_questions(role)
            for q in questions:
                assert len(q) >= 15, \
                    f"Suggestion too short: {q}"

    def test_all_roles_covered(self):
        assert set(SUGGESTED_QUESTIONS.keys()) == set(ROLE_CONTEXT.keys())


class TestConstants:
    """Test module-level constants."""

    def test_base_prompt_not_empty(self):
        assert len(BASE_SYSTEM_PROMPT.strip()) > 100

    def test_all_roles_have_context(self):
        expected_roles = {"voter", "candidate", "journalist", "student"}
        assert set(ROLE_CONTEXT.keys()) == expected_roles

    def test_all_roles_have_suggestions(self):
        expected_roles = {"voter", "candidate", "journalist", "student"}
        assert set(SUGGESTED_QUESTIONS.keys()) == expected_roles
