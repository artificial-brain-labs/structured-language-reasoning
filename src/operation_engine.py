from .execution_policy import ExecutionPolicies
from .statement_router import StatementResult


class OperationEngine:
    """Execute declarative operations through reusable execution mechanisms.

    Domain knowledge lives in operation, relation, ontology, and execution
    policy data. Python supplies reusable mechanisms; policy data selects
    which mechanism handles each operation kind.

    Asserted knowledge learned from the current user is executed against the
    supplied user-memory store. System knowledge is never mutated here.
    """

    def __init__(self, definitions, resolver, reasoner, executor, memory, lexicon, clarification, policies=None):
        self.definitions = definitions
        self.resolver = resolver
        self.reasoner = reasoner
        self.executor = executor
        self.memory = memory
        self.lexicon = lexicon
        self.clarification = clarification
        self.policies = policies or ExecutionPolicies()
        self._handlers = self._build_handlers()

    def _build_handlers(self):
        handlers = {}
        for mechanism, policy in self.policies.mechanisms.items():
            handler_name = policy.get("handler")
            handler = getattr(self, f"_{handler_name}", None) if handler_name else None
            if handler is not None:
                handlers[mechanism] = handler
        return handlers

    def execute(self, operation, parsed):
        definition = self.definitions.get(operation.name)
        if definition is None:
            return StatementResult(operation=operation)
        mechanism = definition.get("kind")
        handler = self._handlers.get(mechanism)
        if handler is None:
            return StatementResult(operation=operation)
        return handler(operation, parsed)

    def _policy(self, operation):
        definition = self.definitions.get(operation.name) or {}
        return self.policies.get(definition.get("kind"))

    def _surface(self, parsed, slot):
        return getattr(parsed, f"{slot}_surface_word", None) or getattr(parsed, f"{slot}_word", None)

    def _resolve_subject(self, operation, parsed):
        # An operation may already be explicitly bound to a USER MEMORY
        # entity, for example when a pending clarification is resumed. In
        # that case preserve the binding instead of resolving the surface
        # word again and potentially creating a different semantic path.
        if operation.subject in self.memory.entities:
            explicit_types = self.reasoner.explicit_types(operation.subject)
            if explicit_types:
                # Explicit user-memory classification is sufficient to treat
                # the entity as known for this operation. Do not change the
                # entity's cached concept: UNKNOWN remains UNKNOWN unless the
                # system lexicon originally assigned its concept.
                return explicit_types[0]
            return self.resolver.concept(operation.subject)
        operation.subject = self.resolver.resolve_canonical(self._surface(parsed, "subject"))
        explicit_types = self.reasoner.explicit_types(operation.subject)
        if explicit_types:
            return explicit_types[0]
        return self.resolver.concept(operation.subject)

    def _should_clarify_unknown_subject(self, policy, relation_schema, subject_concept):
        if subject_concept != "UNKNOWN":
            return False
        if not policy.get("clarify_unknown_subject", False):
            return False
        if relation_schema.get("allow_unknown_subject", False):
            return False
        return True

    def _request_clarification(self, operation, parsed):
        request = self.clarification.request_entity_identity(operation.subject, operation, parsed)
        return request.question if request else None

    def _resolve_object(self, operation, parsed, policy):
        mode = policy.get("resolve_object")
        if mode == "literal":
            return operation.object
        if mode == "entity":
            object_word = self._surface(parsed, "object")
            return self.resolver.resolve_canonical(object_word) if object_word else None
        if mode == "ontology_class" and parsed.object_word:
            return self.resolver.resolve_type(parsed.object_word)
        return None

    def _classification(self, operation, parsed):
        policy = self._policy(operation)
        self._resolve_subject(operation, parsed)
        resolved_type = self._resolve_object(operation, parsed, policy)
        if not resolved_type:
            return StatementResult(operation=operation)

        _, type_entity = resolved_type
        operation.object = type_entity

        # Classification is explicit user knowledge. Store the IS_A relation
        # in USER MEMORY; never mutate the entity's cached concept and never
        # write user-specific knowledge into the system/main memory.
        result = self.executor.execute(operation, source="USER")
        return StatementResult(result=result, operation=operation)

    def _relation(self, operation, parsed):
        policy = self._policy(operation)
        subject_concept = self._resolve_subject(operation, parsed)
        relation_schema = self.memory.relations.get(operation.predicate) or {}
        if self._should_clarify_unknown_subject(policy, relation_schema, subject_concept):
            return StatementResult(clarification=self._request_clarification(operation, parsed), operation=operation)
        operation.object = self._resolve_object(operation, parsed, policy)
        if operation.object is None:
            return StatementResult(operation=operation)
        if policy.get("validate_relation", False) and not self.reasoner.validate_relation(operation.subject, operation.predicate, operation.object):
            return StatementResult(operation=operation)
        result = self.executor.execute(operation, source="USER")
        return StatementResult(result=result, operation=operation)

    def _fact(self, operation, parsed):
        policy = self._policy(operation)
        subject_concept = self._resolve_subject(operation, parsed)
        operation.object = self._resolve_object(operation, parsed, policy)
        result = self.executor.execute(operation, source="USER")
        relation_schema = self.memory.relations.get(operation.predicate) or {}
        if result is not None and self._should_clarify_unknown_subject(policy, relation_schema, subject_concept):
            return StatementResult(result=result, clarification=self._request_clarification(operation, parsed), operation=operation)
        return StatementResult(result=result, operation=operation)
