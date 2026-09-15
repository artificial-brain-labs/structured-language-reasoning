from dataclasses import dataclass


@dataclass(frozen=True)
class Edge:
    subject: str
    predicate: str
    object: str
    source: str = "USER"
    status: str = "ASSERTED"


class KnowledgeGraph:
    """Explicit graph memory. Derived relationships are queried, not stored."""

    def __init__(self):
        self.entities = {}
        self.edges = []

    def add_entity(self, entity_id, entity_type=None):
        self.entities.setdefault(entity_id, {"type": entity_type})
        if entity_type is not None:
            self.entities[entity_id]["type"] = entity_type

    def add_edge(self, subject, predicate, object_, source="USER", status="ASSERTED"):
        edge = Edge(subject, predicate, object_, source, status)
        if edge not in self.edges:
            self.edges.append(edge)
        return edge

    def has_edge(self, subject, predicate, object_=None):
        return any(
            e.subject == subject
            and e.predicate == predicate
            and (object_ is None or e.object == object_)
            for e in self.edges
        )

    def query(self, subject=None, predicate=None, object_=None):
        return [
            e for e in self.edges
            if (subject is None or e.subject == subject)
            and (predicate is None or e.predicate == predicate)
            and (object_ is None or e.object == object_)
        ]
