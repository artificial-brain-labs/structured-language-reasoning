# Grammar Foundation Completion Plan

## Purpose

This change establishes a declared grammar-coverage contract for SLR V1.x.

The project will no longer expand grammar reactively by adding an isolated rule whenever a sentence fails. Instead, grammar work is organized around a finite, explicit SLR-English V1 subset.

## Architectural rule

`grammar_coverage.json` is a specification layer. It does not replace `grammar_foundation.json`.

- `grammar_coverage.json` declares what the V1 grammar must cover.
- `grammar_foundation.json` contains the executable declarative productions.
- `lexicon.json` supplies lexical categories and lexical knowledge.
- `semantics.json` maps compositional structures into semantic representations.
- Python remains generic infrastructure and must not contain sentence-specific linguistic knowledge.

## V1 completion gate

The required foundation families are:

1. Noun phrases
2. Declarative statements
3. Negation
4. Interrogatives
5. Pronouns

A construction is not considered complete merely because a production exists. It requires parser coverage and, where applicable, semantic regression coverage.

Coordination, richer tense/aspect, prepositional phrases, and complex clauses are explicitly tracked as planned extensions rather than being silently treated as V1 gaps.

## Development consequence

Until the V1 completion gate is satisfied, new reasoning capabilities should not drive ad-hoc grammar expansion. Grammar coverage is stabilized first; semantic composition is then completed against that grammar; reasoning expands only after the language foundation is regression-tested.

## Historical traceability

This document formalizes the architectural decision to move from reactive grammar patching to a declared grammar-completion milestone. Future grammar additions must update both the coverage contract and the corresponding implementation/tests when they change the supported language surface.
