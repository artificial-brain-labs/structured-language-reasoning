import json
from pathlib import Path


class InferenceRules:
    """Load declarative inference rules from knowledge data."""

    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "inference_rules.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.rules = data.get("rules", [])

    def all(self):
        return list(self.rules)

    def enabled(self):
        return [rule for rule in self.rules if rule.get("enabled", True)]
