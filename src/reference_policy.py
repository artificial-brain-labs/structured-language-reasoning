import json
from pathlib import Path


class ReferencePolicyError(ValueError):
    """Raised when lexical reference metadata violates the declarative contract."""


class ReferencePolicyValidator:
    """Validate lexical reference metadata against the declarative policy contract."""

    def __init__(self, policy_path="knowledge/reference_policy.json"):
        with open(Path(policy_path), "r", encoding="utf-8") as file:
            data = json.load(file)
        self.version = data.get("version")
        self.modes = data.get("reference_modes", {})

    def validate_lexicon(self, words):
        errors = []
        for word, entry in words.items():
            if not isinstance(entry, dict):
                continue
            if entry.get("pos") != "PRONOUN":
                continue

            reference = entry.get("reference")
            referent = entry.get("referent")

            if reference is not None and referent is not None:
                errors.append(
                    f"{word}: reference and referent cannot both be declared"
                )
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

                required_fields = self.modes[mode].get("required_policy_fields", [])
                for field in required_fields:
                    if field not in policy:
                        errors.append(
                            f"{word}: reference policy requires {field!r}"
                        )

                allowed_roles = policy.get("allowed_roles", [])
                if not isinstance(allowed_roles, list):
                    errors.append(f"{word}: allowed_roles must be a list")
                else:
                    allowed_values = set(
                        self.modes[mode].get("allowed_role_values", [])
                    )
                    errors.extend(
                        f"{word}: unsupported role {role!r}"
                        for role in allowed_roles
                        if role not in allowed_values
                    )

                required_evidence = policy.get("required_evidence", [])
                if not isinstance(required_evidence, list):
                    errors.append(f"{word}: required_evidence must be a list")
                else:
                    evidence_values = set(
                        self.modes[mode].get("evidence_values", [])
                    )
                    errors.extend(
                        f"{word}: unsupported evidence {kind!r}"
                        for kind in required_evidence
                        if kind not in evidence_values
                    )

            elif referent is None:
                errors.append(
                    f"{word}: pronoun must declare reference or referent"
                )

        if errors:
            raise ReferencePolicyError("\n".join(errors))
        return True
