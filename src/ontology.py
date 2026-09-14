import json

class Ontology:
    def __init__(self, path="knowledge/ontology.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.classes = json.load(f)["classes"]

    def parent(self, concept):
        node = self.classes.get(concept)
        return node.get("parent") if node else None

    def ancestors(self, concept):
        result = []
        current = concept
        while current:
            current = self.parent(current)
            if current:
                result.append(current)
        return result

    def is_a(self, concept, target):
        return concept == target or target in self.ancestors(concept)

    def properties(self, concept):
        result = {}
        chain = list(reversed(self.ancestors(concept))) + [concept]
        for node in chain:
            result.update(self.classes.get(node, {}).get("properties", {}))
        return result
