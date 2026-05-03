"""
Prompt Builder — Role-aware system prompts for ElectIQ AI chat.

Constructs context-specific system prompts for the Google Gemini API
based on the user's selected persona. Each role receives tailored
instructions that shape the AI's response style and content focus.
"""

from __future__ import annotations

__all__ = [
    "build_system_prompt",
    "get_suggested_questions",
    "BASE_SYSTEM_PROMPT",
    "ROLE_CONTEXT",
    "SUGGESTED_QUESTIONS",
]

BASE_SYSTEM_PROMPT: str = """
You are ElectIQ, a friendly and authoritative election education assistant.
Your role: Help citizens understand the election process in a clear,
non-partisan, factual way.

Rules:
1. NEVER express political opinions or favor any party/candidate
2. Always cite an official source at the end of your answer
3. Use simple language; avoid jargon unless explaining the term
4. Be encouraging — democracy works when citizens are informed
5. If unsure, say so and direct to the official Election Commission website
6. Keep answers under 200 words unless the user asks for detail
7. Use bullet points for steps/processes
8. When mentioning technical terms (EVM, VVPAT, NOTA, etc.), briefly explain them
9. Focus on Indian elections unless the user specifies another country
"""

ROLE_CONTEXT: dict[str, str] = {
    "voter": (
        "The user is a voter (possibly first-time). Focus on registration, "
        "polling booth location, ID required, how to vote, what to expect "
        "on voting day. Be encouraging and break processes into simple steps."
    ),
    "candidate": (
        "The user is a candidate or interested in standing for election. "
        "Focus on nomination, eligibility criteria, campaign rules, spending "
        "limits, code of conduct. Be precise about legal requirements."
    ),
    "journalist": (
        "The user is a journalist or researcher. Focus on electoral "
        "regulations, campaign finance laws, media guidelines, exit poll "
        "rules. Provide detailed, well-sourced answers."
    ),
    "student": (
        "The user is a student learning civics. Use analogies, keep it "
        "simple, make it engaging and educational. Use examples and "
        "comparisons to explain complex concepts."
    ),
}

SUGGESTED_QUESTIONS: dict[str, list[str]] = {
    "voter": [
        "How do I check if I'm registered to vote?",
        "What ID do I need to bring on election day?",
        "What happens inside a polling booth?",
        "Can I vote if I moved recently?",
    ],
    "candidate": [
        "What are the eligibility criteria to stand for election?",
        "How much can I spend on my campaign?",
        "What is the Model Code of Conduct?",
        "How do I file my nomination papers?",
    ],
    "journalist": [
        "What are the exit poll broadcasting rules?",
        "How is campaign expenditure monitored?",
        "What media restrictions apply during election period?",
        "How does the EVM counting process work?",
    ],
    "student": [
        "Explain First Past The Post vs Proportional Representation",
        "What is the Electoral College?",
        "How does vote counting work?",
        "Why do we have elections?",
    ],
}


def build_system_prompt(role: str) -> str:
    """
    Build a complete system prompt based on the user's selected role.

    Combines the base system prompt with role-specific context to
    guide the Google Gemini model's response style and content focus.

    Args:
        role: The user's selected persona (voter, candidate, journalist, student).

    Returns:
        Complete system prompt string for the Gemini API.
    """
    role_key = role.lower() if role else "voter"
    role_context = ROLE_CONTEXT.get(role_key, ROLE_CONTEXT["voter"])
    return f"{BASE_SYSTEM_PROMPT.strip()}\n\nUser Context: {role_context}"


def get_suggested_questions(role: str) -> list[str]:
    """
    Get role-specific suggested starter questions.

    Returns a curated list of questions tailored to the user's
    selected persona to help them begin their education journey.

    Args:
        role: The user's selected persona.

    Returns:
        List of suggested question strings.
    """
    role_key = role.lower() if role else "voter"
    return SUGGESTED_QUESTIONS.get(role_key, SUGGESTED_QUESTIONS["voter"])
