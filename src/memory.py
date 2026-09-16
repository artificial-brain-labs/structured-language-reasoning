from dataclasses import dataclass, field
from datetime import datetime, UTC

from .relations import RelationSchema


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
    def __init__(self, relation_schema=None):
        self.entities = {}
        self.memories = []
        self.relations = relation_schema or RelationSchema()

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

    def apply_operation(self, operation, source="USER", confidence=1.0):
        """Apply a declaratively defined memory operation.

        The operation supplies the requested execution mechanism while the
        relation schema supplies relation-specific memory semantics.
        Undefined relations are stored as ordinary relations rather than
        being rejected or guessed.
        """
        schema = self.relations.get(operation.predicate) or {}
        if schema.get("role") == "identity":
            return self.add_identity(
                operation.subject,
                operation.object,
                source,
                confidence,
            )
        return self.add_memory(
            operation.subject,
            operation.predicate,
            operation.object,
            source,
            confidence,
        )

    def add_memory(self, subject, predicate, object_, source="USER", confidence=1.0):
        subject = self.canonical_entity(subject)
        identity_predicate = self._identity_predicate()
        if predicate != identity_predicate and object_ in self.entities:
            object_ = self.canonical_entity(object_)

        for memory in self.memories:
            if memory.subject == subject and memory.predicate == predicate and memory.object == object_:
                return memory

        opposite = self.opposite(predicate)
        if opposite:
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
        schema = self.relations.get(predicate) or {}
        return schema.get("opposite")

    def _identity_neighbors(self, entity_id):
        neighbors = set()
        identity_predicate = self._identity_predicate()
        for memory in self.memories:
            if memory.status == "CONFLICTED" or memory.predicate != identity_predicate:
                continue
            if memory.subject == entity_id:
                neighbors.add(memory.object)
            if memory.object == entity_id:
                neighbors.add(memory.subject)
        return neighbors

    def _identity_predicate(self):
        for predicate, schema in self.relations.schemas.items():
            if schema.get("role") == "identity":
                return predicate
        return None

    def canonical_entity(self, entity_id):
        """Derive a stable identity representative from explicit identity data."""
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
        identity_predicate = self._identity_predicate()
        if not identity_predicate or subject not in self.entities or object_ not in self.entities:
            return None
        if subject == object_:
            return None
        memory = self.add_memory(subject, identity_predicate, object_, source, confidence)
        schema = self.relations.get(identity_predicate) or {}
        if schema.get("symmetric"):
            self.add_memory(object_, identity_predicate, subject, source, confidence)
        return memory

    def query(self, subject=None, predicate=None, object_=None):
        subject = self.canonical_entity(subject) if subject else None
        if object_ in self.entities:
            object_ = self.canonical_entity(object_)
        return [m for m in self.memories if
                (subject is None or self.canonical_entity(m.subject) == subject) and
                (predicate is None or m.predicate == predicate) and
                (object_ is None or self.canonical_entity(m.object) == object_)]
