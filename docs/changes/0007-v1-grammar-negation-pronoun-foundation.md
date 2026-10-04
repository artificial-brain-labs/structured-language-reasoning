# V1 Grammar Foundation Implementation: Negation and Pronouns

## Change

Expanded the declarative grammar foundation to cover additional V1 constructions without adding sentence-specific parser logic.

### Implemented declarative constructions

- Pronoun as noun phrase: `NP -> PRONOUN`
- Negated state: `NP AUX NEGATION STATE`
- Negated property: `NP AUX NEGATION ADJECTIVE`
- Negated classification: `NP AUX NEGATION NP`, constrained to a noun-headed classification target

The lexical foundation also now includes `am` as an auxiliary with the existing `IS` concept.

## Semantic mapping

Negation remains a generic semantic transformation driven by `knowledge/semantics.json`:

- state predicates become `NOT_<predicate>`
- classification becomes `NOT_IS_A`
- property becomes `NOT_HAS_PROPERTY`

No linguistic construction is encoded in Python.

## Regression coverage

`tests/test_grammar_foundation_v1.py` covers:

- pronoun subject composition
- negated state parsing and semantic representation
- negated classification parsing and semantic representation
- negated property parsing and semantic representation

## Architectural significance

This implementation follows the V1 grammar completion strategy:

`lexicon -> grammar production -> semantic mapping -> regression test -> documented change`

The grammar coverage contract is updated to distinguish implemented constructions from constructions that are still partial or planned. This prevents the project from claiming broader English coverage than the declarative foundation actually provides.

## Next step

Continue auditing the required V1 grammar families systematically rather than adding isolated sentence-specific rules. The next audit should cover the remaining interrogative and noun-phrase combinations, followed by a complete grammar-to-semantic regression matrix.
