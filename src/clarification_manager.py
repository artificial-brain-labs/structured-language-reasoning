from dataclasses import dataclass


@dataclass
class ClarificationRequest:
    """A pending clarification required before reasoning can continue."""

    entity_id: str
    question: str
    original_operation: object = None


class ClarificationManager:
    """Manage clarification state without embedding domain knowledge.

    The manager records what remains unresolved. It does not infer an entity
    type or manufacture an answer. Knowledge enters the system only through
    an explicit user response that is subsequently validated by the caller.
    """

    def __init__(self, memory):
        self.memory = memory
        self.pending = None

    def request_entity_identity(self, entity_id, operation=None):
        if entity_id not in self.memory.entities:
            return None

        name = self.memory.entities[entity_id]["name"]
        question = f"Who is {name.title()}? I don't know enough about this entity yet."
        self.pending = ClarificationRequest(
            entity_id=entity_id,
            question=question,
            original_operation=operation,
        )
        return self.pending

    def has_pending(self):
        return self.pending is not None

    def current(self):
        return self.pending

    def clear(self):
        pending = self.pending
        self.pending = None
        return pending
