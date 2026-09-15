import json
from pathlib import Path


class ResponsePolicy:
    """Render operation and system outcomes from declarative response metadata."""

    def __init__(self, definitions, path=None):
        self.definitions = definitions
        path = path or Path(__file__).resolve().parent.parent / "knowledge" / "responses.json"
        with open(path, "r", encoding="utf-8") as file:
            data = json.load(file)
        self.system_responses = data.get("system", {})

    def _template(self, operation, outcome):
        definition = self.definitions.get(operation.name) or {}
        responses = definition.get("responses", {})
        return responses.get(outcome)

    def render(self, operation, outcome, context=None):
        template = self._template(operation, outcome)
        if template is None:
            return None

        context = context or {}
        try:
            return template.format(**context)
        except (KeyError, ValueError):
            return None

    def system(self, outcome, context=None):
        template = self.system_responses.get(outcome)
        if template is None:
            return None

        context = context or {}
        try:
            return template.format(**context)
        except (KeyError, ValueError):
            return None
