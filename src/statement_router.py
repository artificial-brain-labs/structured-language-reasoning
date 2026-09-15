from dataclasses import dataclass


@dataclass
class StatementResult:
    """Result of routing and executing one structured statement."""

    result: object = None
    clarification: str | None = None
    operation: object = None


class StatementRouter:
    """Route semantic operations through registered mechanism handlers.

    Operation names and domain knowledge remain in declarative knowledge.
    The router only maps operation names to execution mechanisms and carries
    the parsed statement context into those mechanisms.
    """

    def __init__(self):
        self._handlers = {}

    def register(self, operation_name, handler):
        self._handlers[operation_name] = handler

    def register_all(self, operation_names, handler):
        for operation_name in operation_names:
            self.register(operation_name, handler)

    def dispatch(self, operation, context=None):
        if operation is None:
            return StatementResult()

        handler = self._handlers.get(operation.name)
        if handler is None:
            return StatementResult(operation=operation)

        result = handler(operation, context)
        if isinstance(result, StatementResult):
            return result
        return StatementResult(result=result, operation=operation)
