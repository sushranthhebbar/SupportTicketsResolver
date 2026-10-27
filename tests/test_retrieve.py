import json

import pytest

from src.retrieve import load_documentation


def test_load_documentation_chunks_and_preserves_source_metadata(tmp_path):
    source = tmp_path / "documentation.json"
    source.write_text(
        json.dumps(
            [
                {
                    "doc_id": "DOC-TEST-001",
                    "title": "Test article",
                    "category": "testing",
                    "applies_to": ["All plans", "API"],
                    "content": "A useful troubleshooting article. " * 50,
                }
            ]
        ),
        encoding="utf-8",
    )

    passages = load_documentation(source)

    assert len(passages) > 1
    assert all(p.metadata["doc_id"] == "DOC-TEST-001" for p in passages)
    assert all(p.metadata["title"] == "Test article" for p in passages)
    assert all(p.metadata["applies_to"] == "All plans, API" for p in passages)


def test_load_documentation_rejects_missing_required_fields(tmp_path):
    source = tmp_path / "documentation.json"
    source.write_text(json.dumps([{"doc_id": "DOC-TEST-001"}]), encoding="utf-8")

    with pytest.raises(ValueError, match="missing"):
        load_documentation(source)
