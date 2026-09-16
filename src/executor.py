from .operation_registry import OperationRegistry
from .operations import OperationDefinitions


class SemanticExecutor:
    """Execute semantic operations through a mechanism registry."""

    def __init__(self, memory, registry=None, definitions=None):
        self.memory = memory
        self.registry = registry or OperationRegistry()
        self.definitions = definitions or OperationDefinitions()
        self._register_default_operations()

    def _register_default_operations(self):
        for operation_name in self.definitions.operations:
            self.registry.register(operation_name, self._execute_memory_operation)

    def _execute_memory_operation(self, operation, source="USER", confidence=1.0):
        return self.memory.apply_operation(operation, source, confidence)

    def execute(self, operation, source="USER", confidence=1.0):
        if operation is None:
            return None

        handler = self.registry.get(operation.name)
        if handler is None:
            return None

        return handler(operation, source, confidence)
