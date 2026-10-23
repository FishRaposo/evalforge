"""Saved input boundary: exact identities, never fuzzy prompt matching."""

import json

import pytest


def test_saved_backend_requires_exact_reserved_case_identity(tmp_path):
    from evalforge.backends.saved import SavedResponseBackend

    path = tmp_path / "responses.jsonl"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "case_id": "a",
                "answer": "42",
                "retrieved_sources": [],
                "citations": [],
                "provenance": {"origin": "synthetic"},
            }
        )
        + "\n"
    )
    backend = SavedResponseBackend(path)
    import asyncio

    result = asyncio.run(backend.query("irrelevant", {"_evalforge_case_id": "a"}))
    assert result.content == "42"
    with pytest.raises(ValueError, match="case"):
        asyncio.run(backend.query("a"))
    with pytest.raises(ValueError, match="missing"):
        asyncio.run(backend.query("a", {"_evalforge_case_id": "missing"}))


@pytest.mark.parametrize(
    "contents",
    [
        "{broken",
        "{}",
        "\n".join(
            [
                '{"schema_version":1,"case_id":"a","answer":"x"}',
                '{"schema_version":1,"case_id":"a","answer":"y"}',
            ]
        ),
    ],
)
def test_saved_backend_rejects_malformed_or_duplicate_records(tmp_path, contents):
    from evalforge.backends.saved import SavedResponseBackend

    path = tmp_path / "responses.jsonl"
    path.write_text(contents)
    with pytest.raises(ValueError):
        SavedResponseBackend(path)


@pytest.mark.parametrize("origin", [{"nested": "synthetic"}, ["synthetic"]])
def test_non_scalar_origin_is_a_validation_error(tmp_path, origin):
    from evalforge.backends.saved import SavedResponseBackend

    path = tmp_path / "responses.jsonl"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "case_id": "a",
                "answer": "x",
                "provenance": {"origin": origin},
            }
        )
    )
    with pytest.raises(ValueError, match="origin"):
        SavedResponseBackend(path)


def test_deep_json_is_a_validation_error_not_a_runtime_crash(tmp_path):
    from evalforge.backends.saved import SavedResponseBackend

    path = tmp_path / "responses.jsonl"
    path.write_text("[" * 2000 + "0" + "]" * 2000)
    with pytest.raises(ValueError, match="record"):
        SavedResponseBackend(path)
