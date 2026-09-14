from src.ontology import Ontology

def test_cat_is_animal():
    ontology = Ontology()
    assert ontology.is_a("CAT", "ANIMAL")
    assert ontology.is_a("CAT", "LIVING_THING")

def test_inherited_properties():
    ontology = Ontology()
    props = ontology.properties("CAT")
    assert props["alive"] is True
    assert props["can_eat"] is True
    assert props["warm_blooded"] is True
