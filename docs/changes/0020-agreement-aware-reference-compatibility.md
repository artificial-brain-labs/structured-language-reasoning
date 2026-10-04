# Change 0020 — Agreement-Aware Reference Compatibility

## Purpose

SLR now evaluates explicit agreement data against already-established contextual reference candidates.

Agreement is a constraint on candidates, not an independent reference-resolution mechanism.

## Compatibility

The contextual policy declares EXACT compatibility for number, person, and gender.

A dimension participates only when both the reference and candidate explicitly provide a value.

- explicit equal values → compatible
- explicit unequal values → incompatible
- either side unknown → undetermined, therefore not a mismatch

## Resolution pipeline

```
Contextual Evidence
        ↓
Candidate Set
        ↓
Agreement Compatibility
        ↓
Compatible Candidates
        ↓
0 → UNKNOWN
1 → RESOLVED
>1 → AMBIGUOUS
```

## Explainability

Resolution evidence records AGREEMENT_COMPATIBLE or AGREEMENT_INCOMPATIBLE.

An incompatible candidate remains represented in the evidence trace rather than silently disappearing.

## Architectural constraints

This change does not infer agreement, infer gender, infer number from morphology, rank candidates, create candidates, or treat unknown agreement as false.

Only explicit agreement values can produce an incompatibility.

## Verification

Regression coverage includes explicit mismatch, unknown candidate agreement, and agreement evidence tracing.