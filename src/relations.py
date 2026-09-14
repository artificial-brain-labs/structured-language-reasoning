import json
from dataclasses import dataclass

@dataclass
class Relation:
    subject: str
    predicate: str
    object: str
    negated: bool = False

class RelationSchema:
    def __init__(self, path="knowledge/relations.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.schemas = json.load(f)

    def get(self, predicate):
        return self.schemas.get(predicate)
