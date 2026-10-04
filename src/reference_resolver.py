import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ReferenceResolution:
    """Evidence-backed binding of a lexical reference to an entity."""

    status: str
    reference: str | None = None
    reason: str | None = None


class ReferenceResolver:
    """Resolve lexical references using declarative anchor metadata.

    Lexical entries name a reference anchor. The anchor policy declares which
    runtime context supplies the referent. No individual pronoun spelling or
    anchor meaning is encoded here.
    """

    def __init__(
        self,
        lexicon=None,
        user_memory=None,
        user_profile=None,
        anchor_path="knowledge/reference_anchors.json",
    ):
        self.lexicon = lexicon
        self.user_memory = user_memory
        self.user_profile = user_profile
        with open(Path(anchor_path), "r", encoding="utf-8") as file:
            data = json.load(file)
        self.anchors = data.get("anchors", {})

    def _source(self, source):
        sources = {
            "USER_PROFILE": self.user_profile,
        }
        return sources.get(source)

    def resolve(self, word):
        if not word or self.lexicon is None:
            return ReferenceResolution("UNKNOWN", reason="No lexical reference was supplied.")

        entry = self.lexicon.words.get(word.lower(), {})
        if entry.get("pos") != "PRONOUN":
            return ReferenceResolution(
                "UNKNOWN",
                reason="The lexical entry is not classified as a pronoun.",
            )

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

        source = self._source(anchor.get("source"))
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
