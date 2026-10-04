# Change 0005 — Declarative Negated Transitive Statements

## Status

Implemented on `v1.0-development`.

## Problem

The relation model already defined explicit opposite predicates such as `EATS` and `NOT_EATS`, and the semantic mappings already defined a generic negation transformation. However, the foundational grammar did not contain a production for a transitive statement with an auxiliary, negation marker, verb, and object:

`cat does not eat rat`

As a result, the sentence failed during parsing before the existing semantic negation mechanism could operate.

## Decision

Add negation as a declarative grammatical feature rather than a sentence-specific parser rule.

The grammar now declares a generic production for:

`NP AUX NEGATION VERB NP`

with:

- meaning: `SUBJECT_VERB_OBJECT`
- operation: `ASSERT_RELATION`
- `negated: true`
- subject, verb, and object roles derived from production metadata.

`NEGATION` is also a declared lexical category. The parser propagates the production's declarative negation feature into `ParsedSentence.negated`.

The existing semantic mapping then performs the generic transformation:

`EATS + negation -> NOT_EATS`

No word-specific or sentence-specific Python logic is introduced.

## Result

The statement:

`cat does not eat rat`

now follows the normal pipeline:

`Natural Language -> Grammar -> Semantic Representation -> NOT_EATS -> Memory`

When both:

`cat eats rat`

and:

`cat does not eat rat`

are explicitly asserted, the existing conflict model marks the opposing memories as conflicted and query traversal does not select the conflicted relation as an uncontested answer.

## Invariants preserved

- Grammar remains data-driven.
- No hard-coded linguistic phrase matching.
- Negation remains a semantic transformation, not a parser special case.
- Existing `EATS/NOT_EATS` relation opposition remains declarative.
- Conflict handling remains in the memory/reasoning layer.
- Unknown is not converted into false.

## Regression coverage

Added tests for:

- parsing a generic negated transitive statement;
- propagation of the declarative negation feature;
- storage and conflict behavior for positive and negative versions of the same relation.
