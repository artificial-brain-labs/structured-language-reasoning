from dataclasses import dataclass, field
from datetime import datetime, UTC


class EvidenceKind:
    OBSERVATION = "OBSERVATION"
    INTERPRETATION = "INTERPRETATION"
    ASSERTION = "ASSERTION"
    DERIVATION = "DERIVATION"
    HYPOTHESIS = "HYPOTHESIS"


@dataclass(frozen=True)
class Evidence:
    """Epistemic record describing how a piece of information is held.

    Evidence is deliberately separate from truth. A record can describe an
    observation or hypothesis without granting it asserted status.
    """

    kind: str
    subject: str | None = None
    predicate: str | None = None
    object: str | None = None
    source: str = "USER"
    confirmed: bool = False
    support: tuple = ()
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())


class EvidenceState:
    """Small data-independent guard for epistemic state transitions."""

    VALID_KINDS = frozenset(
        {
            EvidenceKind.OBSERVATION,
            EvidenceKind.INTERPRETATION,
            EvidenceKind.ASSERTION,
            EvidenceKind.DERIVATION,
            EvidenceKind.HYPOTHESIS,
        }
    )

    @classmethod
    def validate(cls, evidence):
        if evidence.kind not in cls.VALID_KINDS:
            raise ValueError(f"Unknown evidence kind: {evidence.kind}")
        if evidence.kind == EvidenceKind.ASSERTION and not evidence.confirmed:
            raise ValueError("ASSERTION requires explicit confirmation")
        if evidence.kind in {EvidenceKind.DERIVATION, EvidenceKind.HYPOTHESIS}:
            if evidence.confirmed:
                raise ValueError(f"{evidence.kind} cannot be asserted by confirmation")
        return evidence


class EvidenceStore:
    """Append-only epistemic record; promotion requires explicit confirmation."""

    def __init__(self):
        self.records = []

    def record(self, evidence):
        EvidenceState.validate(evidence)
        self.records.append(evidence)
        return evidence

    def observe(self, subject=None, predicate=None, object=None, source="USER"):
        return self.record(
            Evidence(
                EvidenceKind.OBSERVATION,
                subject,
                predicate,
                object,
                source=source,
            )
        )

    def interpret(self, subject=None, predicate=None, object=None, support=(), source="SYSTEM"):
        return self.record(
            Evidence(
                EvidenceKind.INTERPRETATION,
                subject,
                predicate,
                object,
                source=source,
                support=tuple(support),
            )
        )

    def assert_explicit(self, subject=None, predicate=None, object=None, source="USER", support=()):
        return self.record(
            Evidence(
                EvidenceKind.ASSERTION,
                subject,
                predicate,
                object,
                source=source,
                confirmed=True,
                support=tuple(support),
            )
        )

    def derive(self, subject=None, predicate=None, object=None, support=(), source="REASONER"):
        return self.record(
            Evidence(
                EvidenceKind.DERIVATION,
                subject,
                predicate,
                object,
                source=source,
                support=tuple(support),
            )
        )

    def hypothesize(self, subject=None, predicate=None, object=None, support=(), source="REASONER"):
        return self.record(
            Evidence(
                EvidenceKind.HYPOTHESIS,
                subject,
                predicate,
                object,
                source=source,
                support=tuple(support),
            )
        )
