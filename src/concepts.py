from dataclasses import dataclass

@dataclass
class Concept:
    name: str
    category: str

@dataclass
class Entity:
    entity_id: str
    concept: str
