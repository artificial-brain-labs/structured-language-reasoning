import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReferenceResolution:
    status: str
    reference: str | None = None
    reason: str | None = None
    candidates: tuple[str, ...] = ()
    evidence: tuple[tuple[str, tuple[str, ...]], ...] = ()


class ReferenceResolver:
    """Declarative lexical-reference resolver."""

    @staticmethod
    def _default_agreement_compatibility(reference):
        agreement = reference.get("agreement", {})
        dimensions = agreement.get("dimensions", [])
        return {dimension: "EXACT" for dimension in dimensions}

    @staticmethod
    def _agreement_compatibility(reference_agreement, candidate_agreement, compatibility):
        for dimension, rule in compatibility.items():
            reference_value = reference_agreement.get(dimension)
            candidate_value = candidate_agreement.get(dimension)
            if reference_value is None or candidate_value is None:
                continue
            if rule == "EXACT" and reference_value != candidate_value:
                return "INCOMPATIBLE", dimension
        return "COMPATIBLE", None

    def __init__(
        self,
        lexicon=None,
        user_memory=None,
        runtime_sources=None,
        contextual_memory=None,
        anchor_path="knowledge/reference_anchors.json",
        reference_policy_path="knowledge/reference_policy.json",
    ):
        self.lexicon = lexicon
        self.user_memory = user_memory
        self.runtime_sources = runtime_sources or {}
        self.contextual_memory = contextual_memory
        with open(Path(anchor_path), "r", encoding="utf-8") as file:
            data = json.load(file)
        self.anchors = data.get("anchors", {})
        policy_file = Path(reference_policy_path)
        with open(policy_file, "r", encoding="utf-8") as file:
            policy_data = json.load(file)
        self.reference_modes = policy_data.get("reference_modes", {})

    def resolve(self, word):
        if not word or self.lexicon is None:
            return ReferenceResolution("UNKNOWN", reason="No lexical reference was supplied.")

        entry = self.lexicon.words.get(word.lower(), {})
        if entry.get("pos") != "PRONOUN":
            return ReferenceResolution(
                "UNKNOWN",
                reason="The lexical entry is not classified as a pronoun.",
            )

        reference = entry.get("reference", {})
        if reference.get("mode") == "CONTEXTUAL":
            if self.contextual_memory is None:
                return ReferenceResolution("UNKNOWN", reason="No contextual reference memory is available.")
            policy = reference.get("policy", {})
            candidates = self.contextual_memory.candidates(
                allowed_roles=policy.get("allowed_roles", []),
                concepts=policy.get("concepts", []),
                required_evidence=policy.get("required_evidence", []),
            )
            reference_agreement = entry.get("agreement", {})
            mode_policy = self.reference_modes.get(reference.get("mode"), {})
            agreement_policy = reference.get("agreement", {})
            compatibility = agreement_policy.get(
                "compatibility",
                mode_policy.get("agreement", {}).get(
                    "compatibility",
                    self._default_agreement_compatibility(reference),
                ),
            )
            compatible = []
            evidence = []
            rejected = []
            for candidate in candidates:
                status, dimension = self._agreement_compatibility(
                    reference_agreement,
                    dict(candidate.agreement),
                    compatibility,
                )
                candidate_evidence = tuple(item.kind for item in candidate.evidence)
                if status == "COMPATIBLE":
                    compatible.append(candidate)
                    evidence.append((candidate.entity_id, candidate_evidence + ("AGREEMENT_COMPATIBLE",)))
                else:
                    rejected.append((candidate.entity_id, dimension))
                    evidence.append((candidate.entity_id, candidate_evidence + ("AGREEMENT_INCOMPATIBLE",)))
            if len(compatible) == 1:
                return ReferenceResolution(
                    "RESOLVED",
                    reference=compatible[0].entity_id,
                    reason="Exactly one evidence-supported antecedent remains after declarative agreement compatibility.",
                    evidence=tuple(evidence),
                )
            if len(compatible) > 1:
                return ReferenceResolution(
                    "AMBIGUOUS",
                    reason="Multiple evidence-supported antecedents remain after declarative agreement compatibility.",
                    candidates=tuple(candidate.entity_id for candidate in compatible),
                    evidence=tuple(evidence),
                )
            if candidates and rejected:
                return ReferenceResolution(
                    "UNKNOWN",
                    reason="Evidence-supported antecedents were incompatible with explicit agreement.",
                    evidence=tuple(evidence),
                )
            return ReferenceResolution("UNKNOWN", reason="No evidence-supported antecedent exists.")

        anchor_name = entry.get("referent")
        if not anchor_name:
            return ReferenceResolution(
                "UNKNOWN",
                reason="The pronoun has no declarative reference anchor.",
            )

        anchor = self.anchors.get(anchor_name)
        if not anchor:
            return ReferenceResolution(
                "UNKNOWN",
                reason="The declared reference anchor has no policy.",
            )

        source = self.runtime_sources.get(anchor.get("source"))
        field = anchor.get("field")
        if source is None or not field:
            return ReferenceResolution(
                "UNKNOWN",
                reason="The reference anchor has no active runtime source.",
            )

        value = getattr(source, field, None)
        if not value:
            return ReferenceResolution(
                "UNKNOWN",
                reason="The active reference source has no bound value.",
            )

        if self.user_memory is None:
            return ReferenceResolution(
                "UNKNOWN",
                reason="No entity context is available for the reference.",
            )

        entity_id = self.user_memory.find_named_entity(value)
        if entity_id is None:
            entity_id = self.user_memory.create_named_entity(value)

        return ReferenceResolution(
            "RESOLVED",
            reference=entity_id,
            reason="The declarative reference anchor resolved through active runtime context.",
        )
