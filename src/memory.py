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
        subject = self.canonical_entity(subject)
        if predicate != "SAME_AS" and object_ in self.entities:
            object_ = self.canonical_entity(object_)
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
        if predicate == "EATS":
            return "NOT_EATS"
        if predicate == "NOT_EATS":
            return "EATS"
        return f"NOT_{predicate}"

    def _identity_neighbors(self, entity_id):
        neighbors = set()
        for memory in self.memories:
            if memory.status == "CONFLICTED" or memory.predicate != "SAME_AS":
                continue
            if memory.subject == entity_id:
                neighbors.add(memory.object)
            if memory.object == entity_id:
                neighbors.add(memory.subject)
        return neighbors

    def canonical_entity(self, entity_id):
        """Resolve an explicit SAME_AS connected component deterministically.

        Identity remains represented as graph data. This method only derives a
        stable representative from that graph; it does not contain entity
        knowledge or special cases.
        """
        if entity_id not in self.entities:
            return entity_id

        component = set()
        frontier = [entity_id]
        while frontier:
            current = frontier.pop()
            if current in component:
                continue
            component.add(current)
            frontier.extend(self._identity_neighbors(current) - component)

        return min(component)

    def add_identity(self, subject, object_, source="USER", confidence=1.0):
        """Store an explicit identity assertion and make it bidirectional."""
        if subject not in self.entities or object_ not in self.entities:
            return None
        if subject == object_:
            return None
        memory = self.add_memory(subject, "SAME_AS", object_, source, confidence)
        self.add_memory(object_, "SAME_AS", subject, source, confidence)
        return memory

    def query(self, subject=None, predicate=None, object_=None):
        subject = self.canonical_entity(subject) if subject else None
        if object_ in self.entities:
            object_ = self.canonical_entity(object_)
        return [m for m in self.memories if
                (subject is None or self.canonical_entity(m.subject) == subject) and
                (predicate is None or m.predicate == predicate) and
                (object_ is None or self.canonical_entity(m.object) == object_)]
