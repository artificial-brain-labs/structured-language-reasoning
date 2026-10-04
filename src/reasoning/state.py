"""Core SRST reasoning-state data structures.

The reasoning state is transient working state. It is deliberately separate
from SLR's DynamicMemory, which remains the durable world/user memory layer.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ValidationStatus(str, Enum):
    OBSERVED = "observed"
    DERIVED = "derived"
    SUPPORTED = "supported"
    CONTRADICTED = "contradicted"
    UNKNOWN = "unknown"
    AMBIGUOUS = "ambiguous"


class GoalStatus(str, Enum):
    OPEN = "open"
    SATISFIED = "satisfied"
    BLOCKED = "blocked"
    FAILED = "failed"


@dataclass
class Goal:
    id: str
    target: str
    constraints: list[str] = field(default_factory=list)
    status: GoalStatus = GoalStatus.OPEN
    priority: float = 1.0


@dataclass
class Claim:
    id: str
    subject: str
    predicate: str
    object: Any = None
    source: str | None = None
    status: ValidationStatus = ValidationStatus.UNKNOWN
    confidence: float = 0.0
    dependencies: list[str] = field(default_factory=list)


@dataclass
class Evidence:
    id: str
    source: str
    content: str
    evidence_type: str
    reliability: float = 0.0
    supports: list[str] = field(default_factory=list)
    contradicts: list[str] = field(default_factory=list)


@dataclass
class Conflict:
    id: str
    claim_a: str
    claim_b: str
    reason: str
    resolved: bool = False


@dataclass
class ReasoningState:
    goal: Goal
    claims: dict[str, Claim] = field(default_factory=dict)
    evidence: dict[str, Evidence] = field(default_factory=dict)
    relations: list[tuple[str, str, str]] = field(default_factory=list)
    assumptions: list[str] = field(default_factory=list)
    proof: "ProofGraph | None" = None
    conflicts: dict[str, Conflict] = field(default_factory=dict)
    validation: dict[str, ValidationStatus] = field(default_factory=dict)
    history: list[str] = field(default_factory=list)
    step: int = 0

    def __post_init__(self) -> None:
        # Avoid a circular import at module load time while guaranteeing that
        # every reasoning state has an explicit proof graph.
        if self.proof is None:
            from .proof import ProofGraph
            self.proof = ProofGraph()

    def add_claim(self, claim: Claim) -> None:
        self.claims[claim.id] = claim
        self.validation[claim.id] = claim.status

    def add_conflict(self, conflict: Conflict) -> None:
        self.conflicts[conflict.id] = conflict

    def unresolved_conflicts(self) -> list[Conflict]:
        return [conflict for conflict in self.conflicts.values() if not conflict.resolved]

    def unresolved_claims(self) -> list[Claim]:
        return [
            claim
            for claim in self.claims.values()
            if claim.status in {
                ValidationStatus.UNKNOWN,
                ValidationStatus.AMBIGUOUS,
                ValidationStatus.CONTRADICTED,
            }
        ]
