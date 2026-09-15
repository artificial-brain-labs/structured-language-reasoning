class StatementRouter:
    """Route structured statements to mechanism-level handlers.

    Domain knowledge remains in the lexicon, ontology, grammar, and relation
    schema. This router only connects semantic operation names to handlers.
    """

    def __init__(self):
        self._handlers = {}

    def register(self, operation_name, handler):
        self._handlers[operation_name] = handler

    def dispatch(self, operation, context=None):
        if operation is None:
            return None

        handler = self._handlers.get(operation.name)
        if handler is None:
            return None

        return handler(operation, context)
