# Change 0021 — Reference Resolution V1 Audit

## Purpose

This change audits and stabilizes the reference-resolution subsystem after introduction of explicit agreement compatibility.

## Resolution state contract

- no candidates → UNKNOWN
- one compatible candidate → RESOLVED
- multiple compatible candidates → AMBIGUOUS
- candidates exist but all are explicitly incompatible → UNKNOWN
- mixed candidates → incompatible candidates remain in evidence while compatible candidates determine the resolution state

## Evidence contract

A contextual resolution preserves PRIOR_MENTION, ROLE, AGREEMENT_COMPATIBLE, and AGREEMENT_INCOMPATIBLE.

Evidence is explanatory data, not a ranking score.

## Memory boundary

Reference resolution does not create persistent user knowledge.

Contextual reference memory remains bounded and temporary. Persistent User Memory remains the source of established knowledge.

## Agreement boundary

Agreement only evaluates candidates already established through contextual evidence.

It does not create candidates, infer agreement, rank candidates, infer gender, infer number from morphology, or treat unknown agreement as false.

## Policy boundary

Agreement compatibility rules are validated declaratively. The current supported compatibility rule is EXACT.

Unknown or heuristic compatibility rules are rejected by the policy validator.

## Configuration boundary

The reference policy path is now an explicit resolver dependency rather than an implicit working-directory assumption.

## V1 audit result

The reference subsystem is structurally ready for the next grammar expansion phase, subject to the complete test suite.

No test execution is claimed by this change record.