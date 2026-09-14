from src.ontology import Ontology
from src.memory import DynamicMemory
from src.reasoner import Reasoner

def test_is_a_inference():
    ontology = Ontology()
    memory = DynamicMemory()
    reasoner = Reasoner(ontology, memory)
    cat = memory.find_entity("CAT")
    inferred = reasoner.infer_is_a(cat)
    objects = {item["object"] for item in inferred}
    assert "ANIMAL" in objects
    assert "LIVING_THING" in objects
