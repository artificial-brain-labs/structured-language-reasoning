import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReferenceResolution:
    status: str
    reference: str | None = None
    reason: str | None = None
    candidates: tuple[str, ...] = ()


class ReferenceResolver:
    """Declarative lexical-reference resolver."""

    def __init__(
        self,
        lexicon=None,
        user_memory=None,
        runtime_sources=None,
        contextual_memory=None,
        anchor_path="knowledge/reference_anchors.json",
    ):
        self.lexicon = lexicon
        self.user_memory = user_memory
        self.runtime_sources = runtime_sources or {}
        self.contextual_memory = contextual_memory
        with open(Path(anchor_path), "r", encoding="utf-8") as file:
            data = json.load(file)
        self.anchors = data.get("anchors", {})

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
            )
            if len(candidates) == 1:
                return ReferenceResolution(
                    "RESOLVED",
                    reference=candidates[0].entity_id,
                    reason="The contextual reference has exactly one evidence-supported antecedent.",
                )
            if len(candidates) > 1:
                return ReferenceResolution(
                    "AMBIGUOUS",
                    reason="Multiple evidence-supported antecedents remain.",
                    candidates=tuple(candidate.entity_id for candidate in candidates),
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
