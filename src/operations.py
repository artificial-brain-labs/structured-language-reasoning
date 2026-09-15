import json
from pathlib import Path


class OperationDefinitions:
    """Load operation metadata from declarative knowledge data."""

    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "operations.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.operations = data.get("operations", {})

    def get(self, name):
        return self.operations.get(name)

    def requires(self, name):
        definition = self.get(name) or {}
        return definition.get("requires", [])
