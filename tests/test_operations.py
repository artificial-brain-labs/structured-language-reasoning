from src.operations import OperationDefinitions


def test_operation_definitions_load_from_knowledge():
    definitions = OperationDefinitions()

    assert definitions.get("ASSERT_STATE")["target"] == "MEMORY"
    assert "subject" in definitions.requires("ASSERT_STATE")
    assert "predicate" in definitions.requires("ASSERT_RELATION")


def test_unknown_operation_definition_is_not_invented():
    definitions = OperationDefinitions()

    assert definitions.get("MADE_UP_OPERATION") is None
