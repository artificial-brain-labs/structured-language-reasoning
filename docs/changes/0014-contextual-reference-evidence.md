# Change 0014 — Contextual Reference Evidence Model

## Purpose

Contextual reference resolution now exposes the evidence supporting each candidate.

The resolver still makes only a binary semantic decision:

- uniquely supported candidate → RESOLVED
- multiple supported candidates → AMBIGUOUS
- no supported candidate → UNKNOWN

No probabilistic ranking or salience scoring is introduced.

## Evidence representation

Each contextual mention carries explicit evidence records.

Current evidence kinds are:

- PRIOR_MENTION
- ROLE

PRIOR_MENTION records that the entity entered contextual reference memory through a successful semantic operation.

ROLE records the semantic role in which the entity was previously established.

## Declarative evidence requirements

Reference policies can declare required evidence such as `required_evidence: ["PRIOR_MENTION"]`.

The resolver evaluates the declared requirements generically. Python does not contain pronoun-specific evidence rules.

## Traceability

ReferenceResolution now exposes:

- resolved reference, when unique
- candidate entity IDs, when ambiguous
- evidence kinds associated with each candidate

This makes contextual reference resolution inspectable rather than opaque.

## Boundary

The evidence model does not introduce:

- recency scoring
- salience scoring
- grammatical agreement
- probability
- heuristic ranking
- inferred antecedents

A candidate is either supported by the declared evidence contract or it is not.

## Relationship to TCM

TCM continues to store raw communication.

Contextual Reference Memory stores the structured projection required for reference resolution.

Therefore:

TCM → raw communication
Contextual Reference Memory → temporary reference evidence
User Memory → persistent asserted knowledge

These remain separate responsibilities.

## Regression contract

Tests verify:

- mentions contain explicit evidence
- required evidence filters candidates
- successful resolution exposes its evidence trace
- unsupported evidence requirements produce no candidate

This preserves the no-guessing principle while improving reference-resolution observability.
