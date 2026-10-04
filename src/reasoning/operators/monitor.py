"""MONITOR: validate claims against explicit evidence."""

from ..controller import CognitiveOperator
from ..evidence import EvidencePolicy
from ..state import GoalStatus, ReasoningState, ValidationStatus
from ._utils import transition


class Monitor(CognitiveOperator):
    name = "MONITOR"

    def __init__(self, policy=None):
        self.policy = policy or EvidencePolicy()

    def _needs_monitoring(self, state):
        return any(
            claim.status in (ValidationStatus.UNKNOWN, ValidationStatus.AMBIGUOUS)
            for claim in state.claims.values()
        )

    def applicable(self, state):
        return state.goal.status == GoalStatus.OPEN and self._needs_monitoring(state)

    def necessary(self, state):
        return self.applicable(state)

    def execute(self, state):
        changed = []
        for claim in state.claims.values():
            if claim.status not in (ValidationStatus.UNKNOWN, ValidationStatus.AMBIGUOUS):
                continue

            supporting = [
                evidence for evidence in state.evidence.values()
                if claim.id in evidence.supports
            ]
            opposing = [
                evidence for evidence in state.evidence.values()
                if claim.id in evidence.contradicts
            ]

            supporting = self.policy.supporting(supporting)
            opposing = self.policy.supporting(opposing)

            if supporting and opposing:
                claim.status = ValidationStatus.AMBIGUOUS
                state.validation[claim.id] = claim.status
                changed.append(f"{claim.id}:conflicted")
            elif opposing:
                claim.status = ValidationStatus.CONTRADICTED
                state.validation[claim.id] = claim.status
                changed.append(f"{claim.id}:opposed")
            elif supporting:
                claim.status = ValidationStatus.SUPPORTED
                claim.confidence = max(
                    claim.confidence,
                    max(e.reliability for e in supporting),
                )
                state.validation[claim.id] = claim.status
                changed.append(f"{claim.id}:supported")

        return state, transition(
            state,
            self.name,
            "unresolved claims require semantic validation",
            state_changes=changed or ["no_status_change"],
        )
