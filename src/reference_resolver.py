from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceResolution:
    """Evidence-backed binding of a lexical reference to an entity."""

    status: str
    reference: str | None = None
    reason: str | None = None


class ReferenceResolver:
    """Resolve lexical references using declarative lexicon metadata.

    The resolver contains no knowledge of individual pronoun spellings.
    Lexical entries declare how a reference is anchored; runtime context
    supplies the entity that satisfies that anchor.
    """

    def __init__(self, lexicon=None, user_memory=None, user_profile=None):
        self.lexicon = lexicon
        self.user_memory = user_memory
        self.user_profile = user_profile

    def resolve(self, word):
        if not word or self.lexicon is None:
            return ReferenceResolution("UNKNOWN", reason="No lexical reference was supplied.")

        entry = self.lexicon.words.get(word.lower(), {})
        if entry.get("pos") != "PRONOUN":
            return ReferenceResolution(
                "UNKNOWN",
                reason="The lexical entry is not classified as a pronoun.",
            )

        referent = entry.get("referent")
        if not referent:
            return ReferenceResolution(
                "UNKNOWN",
                reason="The pronoun has no declarative reference anchor.",
            )

        if referent == "USER":
            if self.user_profile is None or self.user_memory is None:
                return ReferenceResolution(
                    "UNKNOWN",
                    reason="No user identity context is available.",
                )
            name = self.user_profile.display_name
            entity_id = self.user_memory.find_named_entity(name)
            if entity_id is None:
                entity_id = self.user_memory.create_named_entity(name)
            return ReferenceResolution(
                "RESOLVED",
                reference=entity_id,
                reason="Lexicon-declared USER reference resolved through the active user identity.",
            )

        return ReferenceResolution(
            "UNKNOWN",
            reason="The declared reference anchor has no active runtime binding.",
        )
