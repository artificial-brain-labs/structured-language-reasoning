from .statement_router import StatementResult


class OperationEngine:
    """Execute operation kinds through generic mechanism handlers.

    Operation names and domain relations remain declarative. The engine only
    provides reusable execution mechanisms selected by the operation's
    declarative kind.
    """

    def __init__(self, definitions, resolver, reasoner, executor, memory, lexicon, clarification):
        self.definitions = definitions
        self.resolver = resolver
        self.reasoner = reasoner
        self.executor = executor
        self.memory = memory
        self.lexicon = lexicon
        self.clarification = clarification
        self._handlers = {
            "CLASSIFICATION": self._classification,
            "RELATION": self._relation,
            "FACT": self._fact,
        }

    def execute(self, operation, parsed):
        definition = self.definitions.get(operation.name)
        if definition is None:
            return StatementResult(operation=operation)

        handler = self._handlers.get(definition.get("kind"))
        if handler is None:
            return StatementResult(operation=operation)
        return handler(operation, parsed)

    def _resolve_subject(self, operation, parsed):
        operation.subject = self.resolver.resolve_canonical(parsed.subject_word)
        return self.resolver.concept(operation.subject)

    def _classification(self, operation, parsed):
        self._resolve_subject(operation, parsed)
        resolved_type = self.resolver.resolve_type(parsed.object_word)
        if resolved_type is None:
            return StatementResult(operation=operation)

        concept, type_entity = resolved_type
        operation.object = type_entity
        result = self.executor.execute(operation)
        if result is not None:
            self.memory.set_entity_concept(operation.subject, concept)
        return StatementResult(result=result, operation=operation)

    def _relation(self, operation, parsed):
        subject_concept = self._resolve_subject(operation, parsed)
        relation_schema = self.memory.relations.get(operation.predicate) or {}

        if relation_schema.get("type") == "IDENTITY":
            operation.object = self.resolver.resolve_canonical(parsed.object_word)
            result = self.executor.execute(operation)
            return StatementResult(result=result, operation=operation)

        if subject_concept == "UNKNOWN":
            request = self.clarification.request_entity_identity(
                operation.subject, operation, parsed
            )
            return StatementResult(
                clarification=request.question if request else None,
                operation=operation,
            )

        object_concept = self.lexicon.concept(parsed.object_word) if parsed.object_word else None
        if not object_concept:
            return StatementResult(operation=operation)

        object_entity = self.resolver.resolve_canonical(parsed.object_word)
        if not self.reasoner.validate_relation(
            operation.subject, operation.predicate, object_entity
        ):
            return StatementResult(operation=operation)

        operation.object = object_entity
        result = self.executor.execute(operation)
        return StatementResult(result=result, operation=operation)

    def _fact(self, operation, parsed):
        subject_concept = self._resolve_subject(operation, parsed)
        result = self.executor.execute(operation)
        if result is not None and subject_concept == "UNKNOWN":
            request = self.clarification.request_entity_identity(
                operation.subject, operation, parsed
            )
            return StatementResult(
                result=result,
                clarification=request.question if request else None,
                operation=operation,
            )
        return StatementResult(result=result, operation=operation)
