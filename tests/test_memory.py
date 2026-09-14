from src.memory import DynamicMemory

def test_memory_and_contradiction():
    memory = DynamicMemory()
    cat = memory.find_entity("CAT")
    mouse = memory.find_entity("MOUSE")
    first = memory.add_memory(cat, "EATS", mouse)
    assert first.status == "ASSERTED"
    second = memory.add_memory(cat, "NOT_EATS", mouse)
    assert second.status == "CONFLICTED"
    assert first.status == "CONFLICTED"
