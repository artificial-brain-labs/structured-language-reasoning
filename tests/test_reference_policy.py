import pytest

from src.reference_policy import ReferencePolicyError, ReferencePolicyValidator


def test_reference_policy_accepts_current_lexicon():
    validator = ReferencePolicyValidator()
    assert validator.validate_lexicon({
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


def test_contextual_reference_requires_declared_policy_fields():
    validator = ReferencePolicyValidator()
    with pytest.raises(ReferencePolicyError, match="allowed_roles"):
        validator.validate_lexicon({
            "it": {
                "pos": "PRONOUN",
                "reference": {
                    "mode": "CONTEXTUAL",
                    "policy": {
                        "required_evidence": ["PRIOR_MENTION"],
                    },
                },
            }
        })


def test_reference_policy_rejects_unsupported_evidence():
    validator = ReferencePolicyValidator()
    with pytest.raises(ReferencePolicyError, match="UNSUPPORTED"):
        validator.validate_lexicon({
            "it": {
                "pos": "PRONOUN",
                "reference": {
                    "mode": "CONTEXTUAL",
                    "policy": {
                        "allowed_roles": ["subject"],
                        "required_evidence": ["UNSUPPORTED"],
                    },
                },
            }
        })


def test_reference_policy_rejects_mixed_reference_declarations():
    validator = ReferencePolicyValidator()
    with pytest.raises(ReferencePolicyError, match="both"):
        validator.validate_lexicon({
            "it": {
                "pos": "PRONOUN",
                "referent": "USER",
                "reference": {
                    "mode": "CONTEXTUAL",
                    "policy": {
                        "allowed_roles": ["subject"],
                        "required_evidence": ["PRIOR_MENTION"],
                    },
                },
            }
        })


def test_pronoun_without_reference_metadata_is_rejected():
    validator = ReferencePolicyValidator()
    with pytest.raises(ReferencePolicyError, match="reference or referent"):
        validator.validate_lexicon({
            "it": {
                "pos": "PRONOUN"
            }
        })
