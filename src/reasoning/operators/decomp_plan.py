"""DECOMP_PLAN: turn a compound goal into explicit subgoals."""

from ..controller import CognitiveOperator
from ..state import Goal, GoalStatus, ReasoningState
from ._utils import transition


class DecompPlan(CognitiveOperator):
    name = "DECOMP_PLAN"

    @staticmethod
    def _parts(target):
        normalized = target.replace(";", " AND ")
        return [part.strip() for part in normalized.split(" AND ") if part.strip()]

    def applicable(self, state):
        return (
            state.goal.status == GoalStatus.OPEN
            and len(self._parts(state.goal.target)) > 1
        )

    def necessary(self, state):
        return self.applicable(state) and not state.subgoals

    def execute(self, state):
        parts = self._parts(state.goal.target)
        state.subgoals = [
            Goal(
                id=f"{state.goal.id}.{index}",
                target=part,
                priority=state.goal.priority,
                parent_id=state.goal.id,
            )
            for index, part in enumerate(parts, start=1)
        ]

        return state, transition(
            state,
            self.name,
            "compound goal requires decomposition",
            inputs=[state.goal.id],
            outputs=[goal.id for goal in state.subgoals],
            state_changes=["subgoals_created"],
        )
