"""DECOMP_PLAN: turn a compound goal into explicit subgoals."""

from ..controller import CognitiveOperator
from ..state import Goal, GoalStatus, ReasoningState
from ._utils import transition


class DecompPlan(CognitiveOperator):
    name = "DECOMP_PLAN"

    @staticmethod
    def _parts(target: str) -> list[str]:
        normalized = target.replace(";", " AND ")
        parts = [part.strip() for part in normalized.split(" AND ")]
        return [part for part in parts if part]

    def applicable(self, state: ReasoningState) -> bool:
        return (
            state.goal.status == GoalStatus.OPEN
            and len(self._parts(state.goal.target)) > 1
        )

    def necessary(self, state: ReasoningState) -> bool:
        return self.applicable(state) and not state.subgoals

    def execute(self, state: ReasoningState):
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
        state.history.append(f"decomposed:{state.goal.id}")

        return state, transition(
            state,
            self.name,
            "compound goal requires decomposition",
            inputs=[state.goal.id],
            outputs=[goal.id for goal in state.subgoals],
            state_changes=["subgoals_created"],
        )
