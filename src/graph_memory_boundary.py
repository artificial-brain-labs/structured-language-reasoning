from dataclasses import dataclass


@dataclass(frozen=True)
class PromotionResult:
    """Result of an explicit graph-to-memory promotion attempt."""

    status: str
    memory: object = None
    reason: str | None = None


class GraphMemoryBoundary:
    """Govern the boundary between transient semantic graphs and user memory.

    Graph projection is observational. This boundary is the only mechanism that
    can promote a graph edge into user memory, and promotion requires explicit
    confirmation plus explicit endpoint resolution. No graph edge is promoted
    automatically.
    """

    def __init__(self, user_memory, endpoint_resolver=None):
        self.user_memory = user_memory
        self.endpoint_resolver = endpoint_resolver

    def promote_edge(self, edge, confirmed=False, source="USER"):
        if edge is None:
            return PromotionResult("REJECTED", reason="missing_edge")
        if edge.status != "OBSERVED":
            return PromotionResult("REJECTED", reason="edge_not_observed")
        if not confirmed:
            return PromotionResult("PENDING_CONFIRMATION", reason="explicit_confirmation_required")
        if self.endpoint_resolver is None:
            return PromotionResult("REJECTED", reason="explicit_endpoint_resolution_required")

        subject = self.endpoint_resolver(edge.subject)
        object_ = self.endpoint_resolver(edge.object)
        if not subject or not object_:
            return PromotionResult("REJECTED", reason="unresolved_endpoint")

        memory = self.user_memory.add_memory(
            subject,
            edge.predicate,
            object_,
            source=source,
            confidence=edge.confidence,
        )
        return PromotionResult("PROMOTED", memory=memory)
