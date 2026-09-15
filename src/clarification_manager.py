from dataclasses import dataclass


@dataclass
class ClarificationRequest:
    """A pending clarification required before reasoning can continue."""

    entity_id: str
    question: str
    original_operation: object = None
    original_context: object = None


class ClarificationManager:
    """Manage unresolved clarification state without guessing.

    The manager records what remains unresolved and recognizes an explicit
    classification response for the pending entity. It never invents a type.
    """

    def __init__(self, memory):
        self.memory = memory
        self.pending = None

    def request_entity_identity(self, entity_id, operation=None, context=None):
        if entity_id not in self.memory.entities:
            return None

        name = self.memory.entities[entity_id]["name"]
        question = f"Who is {name.title()}? I don't know enough about this entity yet."
        self.pending = ClarificationRequest(
            entity_id=entity_id,
            question=question,
            original_operation=operation,
            original_context=context,
        )
        return self.pending

    def has_pending(self):
        return self.pending is not None

    def current(self):
        return self.pending

    def matches_entity(self, entity_id):
        return self.pending is not None and self.pending.entity_id == entity_id

    def clear(self):
        pending = self.pending
        self.pending = None
        return pending
