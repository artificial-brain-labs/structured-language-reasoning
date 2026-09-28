# CRP v0.1

The **Cognitive Representation Protocol (CRP)** is the structured representation layer between a foundation model's interpretation and the GRI cognitive kernel.

## Boundary

Foundation Model -> CRP Candidate -> Validation -> Cognitive Kernel -> Governance -> PCG

CRP is not a reasoning engine and does not establish truth. Schema validity means only that a representation conforms to the CRP structure.

## Core distinction

CRP preserves the separation:

- observation: explicitly available information
- interpretation: structured semantic representation
- inference: non-explicit hypothesis
- uncertainty: unknown or ambiguous information
- cognitive update: proposed change to persistent cognition
- governance: authorization state for the proposed update
- provenance: traceability back to the interaction

## No-guessing rule

A missing fact must not be silently promoted into an observation or confirmed belief.

## Version

CRP v0.1 uses JSON Schema Draft 2020-12. The JSON Schema specification identifies 2020-12 as the current published draft. See https://json-schema.org/specification.

## Scope

v0.1 intentionally defines only the Cognitive Event envelope and its core objects. Belief decay, temporal state transitions, dimension ontology, goal conflict resolution, and richer governance semantics remain future protocol work.
