import json


class Ontology:
    """Class hierarchy and inherited property lookup."""

    def __init__(self, path="knowledge/ontology.json"):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.classes = data["classes"]
        self.principles = data.get("principles", {})

    def parent(self, concept):
        node = self.classes.get(concept)
        return node.get("parent") if node else None

    def ancestors(self, concept):
        result = []
        current = concept
        seen = set()
        while current:
            if current in seen:
                raise ValueError(f"Cycle detected in ontology at {current}")
            seen.add(current)
            current = self.parent(current)
            if current:
                result.append(current)
        return result

    def is_a(self, concept, target):
        return concept == target or target in self.ancestors(concept)

    def properties(self, concept):
        """Return properties inherited from ancestors, with child overrides."""
        result = {}
        chain = list(reversed(self.ancestors(concept))) + [concept]
        for node in chain:
            result.update(self.classes.get(node, {}).get("properties", {}))
        return result

    def class_exists(self, concept):
        return concept in self.classes
