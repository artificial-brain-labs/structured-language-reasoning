import json
from pathlib import Path


class ExecutionPolicies:
    """Load generic execution behavior from declarative knowledge data."""

    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "execution_policies.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.mechanisms = data.get("mechanisms", {})

    def get(self, kind):
        return self.mechanisms.get(kind, {})

    def value(self, kind, name, default=None):
        return self.get(kind).get(name, default)
