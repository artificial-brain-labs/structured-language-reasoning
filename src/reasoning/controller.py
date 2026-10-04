"""Operator contract and demand-driven controller for SRST."""

from abc import ABC, abstractmethod

from .state import ReasoningState
from .termination import TerminationResult, check_termination
from .transition import Transition


class CognitiveOperator(ABC):
    """Contract implemented by each reasoning operator.

    Applicability asks whether an operator can act.
    Necessity asks whether it should act now.
    Execution is only permitted when both are true.
    """

    name: str

    @abstractmethod
    def applicable(self, state: ReasoningState) -> bool:
        raise NotImplementedError

    @abstractmethod
    def necessary(self, state: ReasoningState) -> bool:
        raise NotImplementedError

    @abstractmethod
    def execute(
        self, state: ReasoningState
    ) -> tuple[ReasoningState, Transition]:
        raise NotImplementedError


class OperatorController:
    def __init__(self, operators: list[CognitiveOperator] | None = None):
        self.operators = operators or []

    def select(self, state: ReasoningState) -> CognitiveOperator | None:
        for operator in self.operators:
            if operator.applicable(state) and operator.necessary(state):
                return operator
        return None

    def reason(self, state: ReasoningState, max_steps: int = 32) -> tuple[
        ReasoningState, TerminationResult
    ]:
        for _ in range(max_steps):
            result = check_termination(state)
            if result.terminated:
                return state, result

            operator = self.select(state)
            if operator is None:
                return state, result

            state, transition = operator.execute(state)

            if not transition.success:
                return state, check_termination(state)

            if not transition.is_valid_step():
                raise ValueError(
                    "SRST transition must advance exactly one reasoning step."
                )

            state.step = transition.resulting_step
            state.history.append(transition.id)

        return state, check_termination(state)
