import json
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker


ROOT = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT / "crp" / "v0.1" / "cognitive-event.schema.json"
VALID_PATH = ROOT / "crp" / "v0.1" / "examples" / "john-cancelled-meeting.json"
INVALID_PATH = ROOT / "crp" / "v0.1" / "examples" / "invalid-guessing.json"


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_schema_is_valid_and_accepts_reference_event():
    schema = load_json(SCHEMA_PATH)
    Draft202012Validator.check_schema(schema)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())

    errors = list(validator.iter_errors(load_json(VALID_PATH)))
    assert errors == []


def test_schema_rejects_undeclared_cognitive_fields():
    schema = load_json(SCHEMA_PATH)
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    event = load_json(VALID_PATH)
    event["unexpected_field"] = "should fail"

    errors = list(validator.iter_errors(event))
    assert errors
