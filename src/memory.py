from dataclasses import dataclass, field
from datetime import datetime, UTC

@dataclass
class Memory:
    subject: str
    predicate: str
    object: str
    status: str = "ASSERTED"
    confidence: float = 1.0
    source: str = "USER"
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    support: list = field(default_factory=list)
    contradictions: list = field(default_factory=list)

class DynamicMemory:
    def __init__(self):
        self.entities = {}
        self.memories = []

    def create_entity(self, concept, name=None):
        base = (name or concept).lower().replace(" ", "_")
        entity_id = f"{base}_{len(self.entities) + 1:03d}"
        self.entities[entity_id] = {"concept": concept, "name": name or concept}
        return entity_id

    def find_entity(self, concept):
        for entity_id, data in self.entities.items():
            if data["concept"] == concept and data.get("name") == concept:
                return entity_id
        return self.create_entity(concept)

    def find_named_entity(self, name):
        name = name.strip().lower()
        for entity_id, data in self.entities.items():
            if data.get("name", "").lower() == name:
                return entity_id
        return None

    def create_named_entity(self, name):
        return self.find_named_entity(name) or self.create_entity("UNKNOWN", name=name)

    def set_entity_concept(self, entity_id, concept):
        self.entities[entity_id]["concept"] = concept

    def add_memory(self, subject, predicate, object_, source="USER", confidence=1.0):
        for memory in self.memories:
            if memory.subject == subject and memory.predicate == predicate and memory.object == object_:
                return memory
        opposite = self.opposite(predicate)
        for memory in self.memories:
            if memory.subject == subject and memory.predicate == opposite and memory.object == object_:
                memory.status = "CONFLICTED"
                new_memory = Memory(subject, predicate, object_, "CONFLICTED", confidence, source)
                memory.contradictions.append(len(self.memories))
                self.memories.append(new_memory)
                return new_memory
        new_memory = Memory(subject, predicate, object_, "ASSERTED", confidence, source)
        self.memories.append(new_memory)
        return new_memory

    def opposite(self, predicate):
        if predicate == "EATS": return "NOT_EATS"
        if predicate == "NOT_EATS": return "EATS"
        return f"NOT_{predicate}"

    def canonical_entity(self, entity_id):
        """Resolve identity through explicit SAME_AS links only."""
        visited = set()
        current = entity_id
        while current not in visited:
            visited.add(current)
            links = [m for m in self.memories
                     if m.subject == current and m.predicate == "SAME_AS"
                     and m.status != "CONFLICTED"]
            if not links:
                return current
            current = links[0].object
        return current

    def add_identity(self, subject, object_, source="USER", confidence=1.0):
        """Store an explicit identity assertion and make it bidirectional."""
        subject = self.canonical_entity(subject)
        object_ = self.canonical_entity(object_)
        if subject == object_:
            return None
        memory = self.add_memory(subject, "SAME_AS", object_, source, confidence)
        self.add_memory(object_, "SAME_AS", subject, source, confidence)
        return memory

    def query(self, subject=None, predicate=None, object_=None):
        return [m for m in self.memories if
                (subject is None or m.subject == subject) and
                (predicate is None or m.predicate == predicate) and
                (object_ is None or m.object == object_)]
