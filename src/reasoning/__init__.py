"""Structured Reasoning State Transition (SRST) foundation for SLR V0.3."""

from .state import (
    Claim,
    Conflict,
    Evidence,
    Goal,
    GoalStatus,
    ReasoningState,
    ValidationStatus,
)
from .transition import Transition
from .proof import ProofEdge, ProofGraph, ProofNode
from .validation import validate_state
from .termination import TerminationResult, check_termination
from .controller import CognitiveOperator, OperatorController

__all__ = [
    "Claim",
    "Conflict",
    "Evidence",
    "Goal",
    "GoalStatus",
    "ReasoningState",
    "ValidationStatus",
    "Transition",
    "ProofEdge",
    "ProofGraph",
    "ProofNode",
    "validate_state",
    "TerminationResult",
    "check_termination",
    "CognitiveOperator",
    "OperatorController",
]
