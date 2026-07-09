# tests/test_prompts.py
# Gatekeeper tests for the system prompt: catch persona regressions,
# perspective-rule deletions, and structural drift before deploy.

import re
import src.prompts as prompts


def _msg():
    return prompts.system_message


# ---------- existence & basic shape ----------

def test_system_message_exists_and_is_substantial():
    msg = _msg()
    assert isinstance(msg, str)
    assert len(msg) > 1000, "system_message suspiciously short — truncated edit?"


def test_no_leftover_persona_voice_rules_variable():
    """PERSONA_VOICE_RULES was merged into system_message; it must not return."""
    assert not hasattr(prompts, "PERSONA_VOICE_RULES"), (
        "PERSONA_VOICE_RULES exists again — merge it into system_message "
        "or it will conflict/be forgotten at concatenation time."
    )


# ---------- required sections ----------

REQUIRED_SECTIONS = [
    "VOICE AND PERSPECTIVE",
    "ANSWER LENGTH",
    "CONVERSATIONAL INTEGRITY",
    "PROFESSIONAL QUESTIONS",
    "RECRUITER MODE",
    "CASUAL QUESTIONS",
    "TRUTHFULNESS",
    "MESSAGING MAMTA",
    "OVERALL GOAL",
]


def test_all_required_sections_present():
    msg = _msg()
    missing = [s for s in REQUIRED_SECTIONS if s not in msg]
    assert not missing, f"Missing prompt sections: {missing}"


# ---------- voice / perspective invariants ----------

def test_first_person_default_rule_present():
    msg = _msg()
    assert "FIRST PERSON" in msg
    assert "Speak AS Mamta" in msg


def test_third_person_exception_rule_present():
    msg = _msg()
    assert "THIRD PERSON" in msg
    assert "subject" in msg.lower(), (
        "Third-person exception should be scoped to questions treating "
        "Mamta as a subject being evaluated."
    )


def test_no_perspective_mixing_rule_present():
    assert "NEVER mix perspectives" in _msg()


def test_old_twin_voice_rule_removed():
    """The old rule made the twin a separate entity talking ABOUT Mamta."""
    msg = _msg()
    assert "She built me" not in msg, (
        "Old twin-voice example is back — conflicts with first-person default."
    )
    assert "AS the twin, ABOUT Mamta" not in msg


# ---------- policy invariants ----------

def test_years_of_experience_policy_present():
    msg = _msg()
    assert "years of experience" in msg, "Years-avoidance policy missing."
    assert "never explain this policy" in msg.lower() or "never mention" in msg.lower()


def test_no_actual_year_counts_in_prompt():
    """The prompt must not itself leak a tenure figure (e.g. '15 years')."""
    leaks = re.findall(r"\b\d{1,2}\+?\s*years?\b", _msg(), flags=re.IGNORECASE)
    assert not leaks, f"Prompt contains explicit year counts: {leaks}"


def test_truthfulness_hard_constraint_present():
    msg = _msg()
    assert "HARD CONSTRAINT" in msg
    assert "Never" in msg and "fabricate" in msg


def test_no_followup_questions_rule_present():
    assert "Never ask follow-up questions" in _msg()


# ---------- recruiter mode invariants ----------

def test_recruiter_mode_uses_third_person():
    msg = _msg()
    recruiter = msg.split("RECRUITER MODE", 1)[1].split("CASUAL QUESTIONS", 1)[0]
    assert "third person" in recruiter.lower()
    assert "senior technical IC" in recruiter


def test_recruiter_example_is_third_person():
    msg = _msg()
    recruiter = msg.split("RECRUITER MODE", 1)[1].split("CASUAL QUESTIONS", 1)[0]
    assert "Mamta's career highlights" in recruiter
    # Example must not have drifted into first person
    assert "My career highlights" not in recruiter