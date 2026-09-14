from src.ontology import Ontology
from src.memory import DynamicMemory
from src.reasoner import Reasoner

def test_eats_validation():
    ontology = Ontology()
    memory = DynamicMemory()
    reasoner = Reasoner(ontology, memory)
    cat = memory.find_entity("CAT")
    mouse = memory.find_entity("MOUSE")
    assert reasoner.validate_relation(cat, "EATS", mouse)
