class ResponsePolicy:
    """Render operation outcomes from declarative response metadata."""

    def __init__(self, definitions):
        self.definitions = definitions

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
