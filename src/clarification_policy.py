import json
from pathlib import Path


class ClarificationPolicy:
    """Load declarative validation rules for pending clarification responses."""

    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "clarification.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.rules = data

    def accepted_meanings(self, name):
        rule = self.rules.get(name, {})
        return rule.get("accepted_meanings", [])
