"""Evidence admissibility policy for SRST.

Evidence is explicit state, while this policy defines when that evidence is
strong enough to change a claim's validation status.
"""

from dataclasses import dataclass

from .state import Evidence


@dataclass(frozen=True)
class EvidencePolicy:
    minimum_reliability: float = 0.0

    def admissible(self, evidence: Evidence) -> bool:
        return evidence.reliability >= self.minimum_reliability

    def supporting(self, evidence_items):
        return [
            evidence
            for evidence in evidence_items
            if self.admissible(evidence)
        ]
