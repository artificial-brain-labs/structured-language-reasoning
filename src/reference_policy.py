import json
from pathlib import Path


class ReferencePolicyError(ValueError):
    """Raised when lexical or grammatical reference metadata is invalid."""


class ReferencePolicyValidator:
    """Validate declarative lexical and grammatical reference contracts."""

    def __init__(
        self,
        policy_path="knowledge/reference_policy.json",
        grammar_path="knowledge/grammar_foundation.json",
    ):
        with open(Path(policy_path), "r", encoding="utf-8") as file:
            data = json.load(file)
        with open(Path(grammar_path), "r", encoding="utf-8") as file:
            grammar = json.load(file)
        self.version = data.get("version")
        self.modes = data.get("reference_modes", {})
        self.grammar_productions = grammar.get("productions", [])

    def validate_lexicon(self, words):
        errors = []
        for word, entry in words.items():
            if not isinstance(entry, dict) or entry.get("pos") != "PRONOUN":
                continue
            reference = entry.get("reference")
            referent = entry.get("referent")
            if reference is not None and referent is not None:
                errors.append(f"{word}: reference and referent cannot both be declared")
                continue
            if reference is not None:
                if not isinstance(reference, dict):
                    errors.append(f"{word}: reference must be an object")
                    continue
                mode = reference.get("mode")
                if mode not in self.modes:
                    errors.append(f"{word}: unsupported reference mode {mode!r}")
                    continue
                policy = reference.get("policy", {})
                if not isinstance(policy, dict):
                    errors.append(f"{word}: reference policy must be an object")
                    continue
                for field in self.modes[mode].get("required_policy_fields", []):
                    if field not in policy:
                        errors.append(f"{word}: reference policy requires {field!r}")
                allowed_roles = policy.get("allowed_roles", [])
                if not isinstance(allowed_roles, list):
                    errors.append(f"{word}: allowed_roles must be a list")
                else:
                    allowed_values = set(self.modes[mode].get("allowed_role_values", []))
                    errors.extend(
                        f"{word}: unsupported role {role!r}"
                        for role in allowed_roles
                        if role not in allowed_values
                    )
                required_evidence = policy.get("required_evidence", [])
                if not isinstance(required_evidence, list):
                    errors.append(f"{word}: required_evidence must be a list")
                else:
                    evidence_values = set(self.modes[mode].get("evidence_values", []))
                    errors.extend(
                        f"{word}: unsupported evidence {kind!r}"
                        for kind in required_evidence
                        if kind not in evidence_values
                    )
            elif referent is None:
                errors.append(f"{word}: pronoun must declare reference or referent")
        if errors:
            raise ReferencePolicyError("\n".join(errors))
        return True

    def validate_grammar(self, words):
        errors = []
        for production in self.grammar_productions:
            roles = production.get("roles", {})
            reference_roles = production.get("reference_roles", {})
            for role in reference_roles:
                if role not in roles:
                    errors.append(
                        f"{production.get('name')}: reference role {role!r} "
                        "is not a declared grammatical role"
                    )
            for role, modes in reference_roles.items():
                if not isinstance(modes, list) or not modes:
                    errors.append(
                        f"{production.get('name')}: reference modes for {role!r} "
                        "must be a non-empty list"
                    )
                    continue
                errors.extend(
                    f"{production.get('name')}: unsupported reference mode {mode!r}"
                    for mode in modes
                    if mode not in self.modes
                )
        if errors:
            raise ReferencePolicyError("\n".join(errors))
        return True

    def validate(self, words):
        self.validate_lexicon(words)
        self.validate_grammar(words)
        return True
