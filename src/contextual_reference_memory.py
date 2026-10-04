from dataclasses import dataclass


@dataclass(frozen=True)
class ReferenceEvidence:
    kind: str
    detail: str


@dataclass(frozen=True)
class ReferenceMention:
    """Ephemeral structured mention used only for contextual reference resolution."""

    entity_id: str
    surface: str
    role: str
    concepts: tuple[str, ...] = ()
    evidence: tuple[ReferenceEvidence, ...] = ()


class ContextualReferenceMemory:
    """Bounded discourse context for previously established entity mentions.

    This is not persistent knowledge and does not assert facts. It stores only
    structured mention bindings needed to resolve later references.
    """

    def __init__(self, capacity=16):
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("Contextual reference capacity must be a positive integer")
        self.capacity = capacity
        self.mentions = []

    def add(self, entity_id, surface, role, concepts=()):
        if not entity_id or not surface or not role:
            return None
        evidence = (
            ReferenceEvidence("PRIOR_MENTION", "Entity was established by a prior successful operation."),
            ReferenceEvidence("ROLE", f"Prior mention role: {role}."),
        )
        mention = ReferenceMention(entity_id, surface, role, tuple(concepts), evidence)
        self.mentions.append(mention)
        if len(self.mentions) > self.capacity:
            self.mentions.pop(0)
        return mention

    def candidates(self, allowed_roles=(), concepts=(), required_evidence=()):
        roles = set(allowed_roles)
        required = set(concepts)
        evidence_types = set(required_evidence)
        result = []
        seen = set()
        for mention in reversed(self.mentions):
            if roles and mention.role not in roles:
                continue
            if required and not required.intersection(mention.concepts):
                continue
            if evidence_types and not evidence_types.issubset({item.kind for item in mention.evidence}):
                continue
            if mention.entity_id in seen:
                continue
            seen.add(mention.entity_id)
            result.append(mention)
        return result

    def clear(self):
        self.mentions.clear()

    def __len__(self):
        return len(self.mentions)
