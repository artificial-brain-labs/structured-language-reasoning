from src.entity_resolver import EntityResolver
from src.lexicon import Lexicon
from src.ontology import Ontology
from src.memory import DynamicMemory


def test_unknown_name_resolves_as_unknown_without_classification():
    lexicon = Lexicon()
    ontology = Ontology()
    memory = DynamicMemory()
    resolver = EntityResolver(lexicon, ontology, memory)

    entity = resolver.resolve("Tom")

    assert memory.entities[entity]["name"] == "Tom"
    assert memory.entities[entity]["concept"] == "UNKNOWN"


def test_known_ontology_concept_resolves_to_class_entity():
    lexicon = Lexicon()
    ontology = Ontology()
    memory = DynamicMemory()
    resolver = EntityResolver(lexicon, ontology, memory)

    entity = resolver.resolve("cat")

    assert memory.entities[entity]["concept"] == "CAT"


def test_type_resolution_requires_ontology_class():
    lexicon = Lexicon()
    ontology = Ontology()
    memory = DynamicMemory()
    resolver = EntityResolver(lexicon, ontology, memory)

    assert resolver.resolve_type("cat")[0] == "CAT"
    assert resolver.resolve_type("Tom") is None
