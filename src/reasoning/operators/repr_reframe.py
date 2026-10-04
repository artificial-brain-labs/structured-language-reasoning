"""REPR_REFRAME: change representation without changing semantic facts."""

from ..controller import CognitiveOperator
from ..state import GoalStatus, ReasoningState
from ._utils import transition


class ReprReframe(CognitiveOperator):
    name = "REPR_REFRAME"
    PREFIX = "representation_blocked:"

    def _requested(self, state: ReasoningState):
        for item in state.assumptions:
            if item.startswith(self.PREFIX):
                value = item[len(self.PREFIX):].strip()
                if value:
                    return item, value
        return None

    def applicable(self, state: ReasoningState) -> bool:
        return state.goal.status == GoalStatus.OPEN and self._requested(state) is not None

    def necessary(self, state: ReasoningState) -> bool:
        return self.applicable(state) and self._requested(state)[1] != state.representation

    def execute(self, state: ReasoningState):
        requested = self._requested(state)
        if requested is None:
            return state, transition(
                state,
                self.name,
                "no representation change requested",
                success=False,
                failure_reason="no representation request",
            )

        marker, representation = requested
        previous = state.representation
        state.representation = representation
        state.assumptions.remove(marker)

        return state, transition(
            state,
            self.name,
            "current representation blocks the goal",
            state_changes=[f"representation:{previous}->{representation}"],
        )
