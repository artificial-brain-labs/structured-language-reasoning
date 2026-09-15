class SemanticExecutor:
    """Execute declarative semantic operations without domain-specific rules."""

    def __init__(self, memory):
        self.memory = memory

    def execute(self, operation, source="USER", confidence=1.0):
        if operation is None:
            return None

        if operation.name == "ASSERT_STATE":
            return self.memory.add_memory(
                operation.subject,
                operation.predicate,
                operation.object,
                source,
                confidence,
            )

        if operation.name in {"ASSERT_RELATION", "ASSERT_CLASSIFICATION"}:
            schema = self.memory.relations.get(operation.predicate) or {}
            if schema.get("type") == "IDENTITY":
                return self.memory.add_identity(
                    operation.subject,
                    operation.object,
                    source,
                    confidence,
                )
            return self.memory.add_memory(
                operation.subject,
                operation.predicate,
                operation.object,
                source,
                confidence,
            )

        return None
