from pathlib import Path


def test_main_does_not_encode_domain_semantic_branches():
    source = Path("src/main.py").read_text(encoding="utf-8")

    forbidden = [
        'parsed.question_type == "TYPE"',
        'concept == "UNKNOWN"',
        'get(operation.predicate) or {}).get("type") == "IDENTITY"',
        'return "I don\'t know."',
        'return "I could not execute that statement."',
    ]

    for fragment in forbidden:
        assert fragment not in source
