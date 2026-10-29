"""Legacy checks disclose synthetic origins and the actual fallback method."""

import json

from typer.testing import CliRunner

from evalforge.cli import app
from evalforge.judges.citation_check import CitationCheckJudge
from evalforge.judges.semantic_match import SemanticMatchJudge
from evalforge.models.test_case import TestCase


def test_legacy_semantic_fallback_identifies_actual_lexical_method(monkeypatch):
    from evalforge.config import get_settings

    monkeypatch.setattr(get_settings(), "OPENAI_API_KEY", "")
    case = TestCase(
        id="a",
        name="a",
        type="semantic_answer",
        input="hi",
        expected="refund in seven days",
    )
    result = SemanticMatchJudge().judge(case, "refund in seven days")
    assert result.score == 1
    assert result.details.get("assessment", {}).get("method") == "lexical_tfidf_cosine"
    assert result.details["assessment"]["quality_validated"] is False


def test_legacy_citation_checker_requires_marker_or_fuzzy_opt_in():
    case = TestCase(
        id="a", name="a", type="must_cite", input="hi", expected={"sources": ["NASA"]}
    )
    strict = CitationCheckJudge().judge(case, "NASA says anything I invent.")
    # Strict by default: a bare prose mention is not a citation (02f8714).
    assert strict.passed is False
    fuzzy_case = TestCase(
        id="b",
        name="b",
        type="must_cite",
        input="hi",
        expected={"sources": ["NASA"]},
        metadata={"match": "fuzzy"},
    )
    fuzzy = CitationCheckJudge().judge(fuzzy_case, "NASA says anything I invent.")
    assert fuzzy.passed is True
    assert fuzzy.details.get("assessment", {}).get("method") == "source_mentions_only"
    assert fuzzy.details["assessment"]["quality_validated"] is False


def test_legacy_mock_report_serializes_synthetic_origin_and_judge_limit(tmp_path):
    path = tmp_path / "suite.yaml"
    path.write_text(
        "name: legacy\ntest_cases:\n- id: a\n  name: a\n"
        "  type: semantic_answer\n  input: hi\n"
        "  expected: This is a mock response.\n"
    )
    result = CliRunner().invoke(
        app,
        [
            "eval",
            str(path),
            "--backend",
            "mock",
            "--no-save",
            "--format",
            "json",
            "--output",
            str(tmp_path / "out"),
        ],
    )
    assert result.exit_code == 0, result.stdout
    report = json.loads(next((tmp_path / "out").glob("*.json")).read_text())
    assert report["metadata"].get("assessment", {}).get("origin") == "synthetic"
    assert (
        report["results"][0]["judge_details"]["assessment"]["method"]
        == "lexical_tfidf_cosine"
    )
    assert (
        report["results"][0]["backend_metadata"]["assessment"]["origin"] == "synthetic"
    )
