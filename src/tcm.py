from dataclasses import dataclass, field
from datetime import datetime, UTC


@dataclass(frozen=True)
class Communication:
    """Temporary raw communication retained during an interaction window."""

    content: str
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class TransientCommunicationMemory:
    """Bounded temporary store for raw communication.

    TCM answers: "What happened?"
    It does not define identity, assertions, or persistent knowledge.
    """

    def __init__(self, capacity=32):
        if not isinstance(capacity, int) or capacity <= 0:
            raise ValueError("TCM capacity must be a positive integer")
        self.capacity = capacity
        self.records = []

    def add(self, content):
        if not isinstance(content, str) or not content.strip():
            raise ValueError("TCM content must be a non-empty string")
        communication = Communication(content=content.strip())
        self.records.append(communication)
        if len(self.records) > self.capacity:
            self.records.pop(0)
        return communication

    def recent(self, limit=None):
        if limit is None:
            return list(self.records)
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("TCM limit must be a non-negative integer")
        return list(self.records[-limit:]) if limit else []

    def clear(self):
        self.records.clear()

    def __len__(self):
        return len(self.records)
