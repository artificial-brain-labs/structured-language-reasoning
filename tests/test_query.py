from src.main import SLR

def test_object_query():
    slr = SLR()
    slr.process("The cat eats the mouse.")
    answer = slr.process("What does the cat eat?")
    assert "mouse" in answer.lower()

def test_subject_query():
    slr = SLR()
    slr.process("The cat eats the mouse.")
    answer = slr.process("Who eats the mouse?")
    assert "cat" in answer.lower()
