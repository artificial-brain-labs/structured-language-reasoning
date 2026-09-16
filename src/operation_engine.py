from .execution_policy import ExecutionPolicies
from .statement_router import StatementResult


class OperationEngine:
    """Execute declarative operations through reusable execution mechanisms.

    Domain knowledge lives in operation, relation, ontology, and execution
    policy data. This class provides mechanisms for resolving, validating,
    clarifying, and executing those data-driven instructions.
    """

    def __init__(
        self,
        definitions,
        resolver,
        reasoner,
        executor,
        memory,
        lexicon,
        clarification,
        policies=None,
    ):
        self.definitions = definitions
        self.resolver = resolver
        self.reasoner = reasoner
        self.executor = executor
        self.memory = memory
        self.lexicon = lexicon
        self.clarification = clarification
        self.policies = policies or ExecutionPolicies()
        self._handlers = {
            "CLASSIFICATION": self._classification,
            "RELATION": self._relation,
            "FACT": self._fact,
        }

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
        operation.subject = self.resolver.resolve_canonical(
            self._surface(parsed, "subject")
        )
        return self.resolver.concept(operation.subject)

    def _should_clarify_unknown_subject(self, policy, relation_schema, subject_concept):
        if subject_concept != "UNKNOWN":
            return False
        if not policy.get("clarify_unknown_subject", False):
            return False
        # Relations may explicitly permit an unknown subject. This is useful
        # for identity-like relations without encoding a relation name here.
        if relation_schema.get("allow_unknown_subject", False):
            return False
        return True

    def _request_clarification(self, operation, parsed):
        request = self.clarification.request_entity_identity(
            operation.subject, operation, parsed
        )
        return request.question if request else None

    def _resolve_object(self, operation, parsed, policy):
        mode = policy.get("resolve_object")
        if mode == "literal":
            return operation.object
        if mode == "entity":n            return self.resolver.resolve_canonical(
                self._surface(parsed, "object")
            ) if self._surface(parsed, "object") else None
        if mode == "ontology_class" and parsed.object_word:
            resolved_type = self.resolver.resolve_type(parsed.object_word)
            return resolved_type
        return None

    def _classification(self, operation, parsed):
        policy = self._policy(operation)
        self._resolve_subject(operation, parsed)
        resolved_type = self._resolve_object(operation, parsed, policy)
        if not resolved_type:
            return StatementResult(operation=operation)

        concept, type_entity = resolved_type
        operation.object = type_entity
        result = self.executor.execute(operation)
        if result is not None and policy.get("update_subject_concept", False):
            self.memory.set_entity_concept(operation.subject, concept)
        return StatementResult(result=result, operation=operation)

    def _relation(self, operation, parsed):
        policy = self._policy(operation)
        subject_concept = self._resolve_subject(operation, parsed)
        relation_schema = self.memory.relations.get(operation.predicate) or {}

        if self._should_clarify_unknown_subject(policy, relation_schema, subject_concept):
            return StatementResult(
                clarification=self._request_clarification(operation, parsed),
                operation=operation,
            )

        operation.object = self._resolve_object(operation, parsed, policy)
        if operation.object is None:
            return StatementResult(operation=operation)

        if policy.get("validate_relation", False):
            if not self.reasoner.validate_relation(
                operation.subject, operation.predicate, operation.object
            ):
                return StatementResult(operation=operation)

        result = self.executor.execute(operation)
        return StatementResult(result=result, operation=operation)

    def _fact(self, operation, parsed):
        policy = self._policy(operation)
        subject_concept = self._resolve_subject(operation, parsed)
        operation.object = self._resolve_object(operation, parsed, policy)
        result = self.executor.execute(operation)

        relation_schema = self.memory.relations.get(operation.predicate) or {}
        if result is not None and self._should_clarify_unknown_subject(
            policy, relation_schema, subject_concept
        ):
            return StatementResult(
                result=result,
                clarification=self._request_clarification(operation, parsed),
                operation=operation,
            )
        return StatementResult(result=result, operation=operation)
