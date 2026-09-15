import json
from pathlib import Path


class QueryPolicy:
    """Load declarative query behavior from knowledge data."""

    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "query_policy.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.types = data.get("question_types", {})

    def get(self, question_type):
        return self.types.get(question_type)

    def all(self):
        return self.types
