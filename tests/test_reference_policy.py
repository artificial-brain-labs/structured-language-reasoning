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


def test_agreement_contract_is_declarative_only():
    validator = ReferencePolicyValidator()
    assert "number" in validator.agreement_dimensions
    assert "person" in validator.agreement_dimensions
    assert "gender" in validator.agreement_dimensions


def test_unsupported_agreement_dimension_is_rejected():
    validator = ReferencePolicyValidator()
    validator.modes["CONTEXTUAL"]["agreement"]["dimensions"] = ["unsupported"]
    with pytest.raises(ReferencePolicyError, match="unsupported agreement dimension"):
        validator.validate_lexicon({
            "it": {
                "pos": "PRONOUN",
                "reference": {
                    "mode": "CONTEXTUAL",
                    "policy": {
                        "allowed_roles": ["subject"],
                        "required_evidence": ["PRIOR_MENTION"]
                    }
                }
            }
        })


def test_non_declarative_agreement_enforcement_is_rejected():
    validator = ReferencePolicyValidator()
    validator.modes["CONTEXTUAL"]["agreement"]["enforcement"] = "HEURISTIC"
    with pytest.raises(ReferencePolicyError, match="unsupported agreement enforcement"):
        validator.validate_lexicon({
            "it": {
                "pos": "PRONOUN",
                "reference": {
                    "mode": "CONTEXTUAL",
                    "policy": {
                        "allowed_roles": ["subject"],
                        "required_evidence": ["PRIOR_MENTION"]
                    }
                }
            }
        })
