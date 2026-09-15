class SemanticExecutor:
    """Execute declarative semantic operations without domain-specific rules.

    The executor understands operation mechanics only. Concepts, predicates,
    ontology rules, and relation behavior remain data-driven.
    """

    def __init__(self, memory):
        self.memory = memory

    def execute(self, operation, source="USER", confidence=1.0):
        if operation is None:
            return None

        if operation.name == "ASSERT_STATE":
            return self.memory.add_memory(
                operation.subject,
                operation.predicate,
                None,
                source,
                confidence,
            )

        if operation.name == "ASSERT_RELATION":
            return self.memory.add_memory(
                operation.subject,
                operation.predicate,
                operation.object,
                source,
                confidence,
            )

        if operation.name == "ASSERT_CLASSIFICATION":
            return self.memory.add_memory(
                operation.subject,
                operation.predicate,
                operation.object,
                source,
                confidence,
            )

        return None
