# Knowledge Model

The knowledge layer follows four rules:

1. **No guessing:** unknown information remains unknown.
2. **Explicit facts:** user-provided facts are stored as asserted graph edges.
3. **Inheritance:** class properties are inherited through the ontology and are not duplicated on instances.
4. **Provenance:** graph edges record their source and status.

Example:

```text
Tom --instance_of--> CAT
CAT --is_a--> FELINE --is_a--> MAMMAL --is_a--> ANIMAL --is_a--> LIVING_THING
Tom --state--> SLEEPING
```

The graph stores only the explicit facts. `Tom is a mammal` is derived through the ontology and is not written as a separate fact.
