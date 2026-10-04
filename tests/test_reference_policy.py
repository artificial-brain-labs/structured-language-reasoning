import pytest

from src.reference_policy import ReferencePolicyError, ReferencePolicyValidator


def test_reference_policy_accepts_current_lexicon_and_grammar():
    validator = ReferencePolicyValidator()
    assert validator.validate({
        "it": {
            "concept": "REFERENCE",
            "pos": "PRONOUN",
            "reference": {
                "mode": "CONTEXTUAL",
                "policy": {
                    "allowed_roles": ["subject", "object"],
                    "required_evidence": ["PRIOR_MENTION"],
                },
            },
        },
        "i": {
            "concept": "SELF",
            "pos": "PRONOUN",
            "referent": "USER",
        },
    })


def test_grammar_reference_role_must_be_a_declared_role():
    validator = ReferencePolicyValidator()
    validator.grammar_productions = [{
        "name": "bad",
        "roles": {"subject": [0, "head"]},
        "reference_roles": {"object": ["CONTEXTUAL"]},
    }]
    with pytest.raises(ReferencePolicyError, match="not a declared grammatical role"):
        validator.validate_grammar({})


def test_grammar_reference_mode_must_be_declared():
    validator = ReferencePolicyValidator()
    validator.grammar_productions = [{
        "name": "bad",
        "roles": {"subject": [0, "head"]},
        "reference_roles": {"subject": ["UNSUPPORTED"]},
    }]
    with pytest.raises(ReferencePolicyError, match="unsupported reference mode"):
        validator.validate_grammar({})


def test_grammar_reference_role_requires_non_empty_modes():
    validator = ReferencePolicyValidator()
    validator.grammar_productions = [{
        "name": "bad",
        "roles": {"subject": [0, "head"]},
        "reference_roles": {"subject": []},
    }]
    with pytest.raises(ReferencePolicyError, match="non-empty list"):
        validator.validate_grammar({})
