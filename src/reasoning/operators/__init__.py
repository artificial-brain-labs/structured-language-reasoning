"""Concrete SRST cognitive operators."""

from .decomp_plan import DecompPlan
from .relational_traverse import RelationalTraverse
from .causal_infer import CausalInfer
from .repr_reframe import ReprReframe
from .monitor import Monitor
from .backtrack import Backtrack


def default_operators():
    """Return the canonical V0.3 operator set in deterministic order."""
    return [
        DecompPlan(),
        RelationalTraverse(),
        CausalInfer(),
        ReprReframe(),
        Monitor(),
        Backtrack(),
    ]


__all__ = [
    "DecompPlan",
    "RelationalTraverse",
    "CausalInfer",
    "ReprReframe",
    "Monitor",
    "Backtrack",
    "default_operators",
]
