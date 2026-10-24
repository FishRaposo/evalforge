"""Frozen synthetic corpus integrity and real deterministic regression outcomes."""

import hashlib
import json
from collections import Counter

import yaml


def test_packaged_corpus_is_frozen_stratified_and_source_families_do_not_leak():
    from evalforge.portfolio import get_portfolio_profiles, get_portfolio_root

    root = get_portfolio_root()
    manifest = json.loads((root / "manifest.json").read_text())
    assert manifest["origin"] == "synthetic"
    assert manifest["label_origin"] == "agent-authored"
    assert manifest["human_reviewed"] is False
    for name, digest in manifest["files"].items():
        assert hashlib.sha256((root / name).read_bytes()).hexdigest() == digest
    profiles = get_portfolio_profiles()
    cases = yaml.safe_load(profiles[0]["suite_path"].read_text())["test_cases"]
    assert len(cases) == 100
    assert Counter(c["metadata"]["category"] for c in cases) == {
        "answerable": 60,
        "unanswerable": 20,
        "conflicting": 10,
        "adversarial": 10,
    }
    dev = [c for c in cases if c["metadata"]["split"] == "development"]
    held = [c for c in cases if c["metadata"]["split"] == "held_out"]
    assert Counter(c["metadata"]["category"] for c in dev) == {
        "answerable": 12,
        "unanswerable": 4,
        "conflicting": 2,
        "adversarial": 2,
    }
    assert len(held) == 80
    assert not (
        {c["metadata"]["source_family"] for c in dev}
        & {c["metadata"]["source_family"] for c in held}
    )


def test_actual_frozen_profiles_have_literal_expected_gate_counts():
    from evalforge.evaluation import evaluate_saved
    from evalforge.portfolio import get_portfolio_profiles

    expected = {
        "baseline": (0, 100, 0, 0),
        "candidate": (1, 94, 6, 0),
        "repaired": (0, 100, 0, 0),
        "indeterminate": (2, 99, 0, 1),
    }
    for profile in get_portfolio_profiles():
        result = evaluate_saved(profile["suite_path"], profile["response_path"])
        code, passed, failed, indeterminate = expected[profile["id"]]
        assert result.exit_code == code
        assert result.report.metadata["gate"]["counts"] == {
            "passed": passed,
            "failed": failed,
            "indeterminate": indeterminate,
            "error": 0,
        }


def test_wrong_source_canary_passes_legacy_mentions_but_fails_trusted_link_contract():
    from evalforge.evaluation import evaluate_saved
    from evalforge.judges.citation_check import CitationCheckJudge
    from evalforge.models.test_case import TestCase
    from evalforge.portfolio import get_portfolio_profiles

    profile = next(p for p in get_portfolio_profiles() if p["id"] == "candidate")
    outcome = evaluate_saved(profile["suite_path"], profile["response_path"])
    case = next(
        r for r in outcome.report.results if r.test_case_id == "ef-answerable-002"
    )
    expected_source = case.backend_metadata["authoritative_sources"][0]["id"]
    legacy_case = TestCase(
        id="legacy",
        name="legacy",
        type="must_cite",
        input="source?",
        expected={"sources": [expected_source]},
    )
    assert CitationCheckJudge().judge(legacy_case, case.actual_response).passed is True
    assert case.outcome == "failed"
