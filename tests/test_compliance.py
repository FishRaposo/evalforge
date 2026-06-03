"""Tests for the compliance rule engine."""

from __future__ import annotations

import pytest

from evalforge.compliance.engine import ComplianceEngine


@pytest.fixture
def engine() -> ComplianceEngine:
    """Provide a fresh ComplianceEngine."""
    return ComplianceEngine()


class TestRequiredRule:
    """Tests for the 'required' rule type."""

    def test_field_present(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "required", "field": "name", "severity": "high", "message": "Name required"}]
        report = engine.evaluate({"name": "Alice"})
        assert report.score == 1.0
        assert report.results[0].passed is True

    def test_field_missing(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "required", "field": "name", "severity": "high", "message": "Name required"}]
        report = engine.evaluate({"age": 30})
        assert report.score == 0.0
        assert report.results[0].passed is False

    def test_field_empty_string(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "required", "field": "name", "severity": "high", "message": "Name required"}]
        report = engine.evaluate({"name": ""})
        assert report.score == 0.0

    def test_nested_field(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "required", "field": "user.email", "severity": "high", "message": "Email required"}]
        report = engine.evaluate({"user": {"email": "a@b.com"}})
        assert report.score == 1.0


class TestFormatRule:
    """Tests for the 'format' rule type."""

    def test_regex_match(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "F1", "type": "format", "field": "email", "severity": "high", "message": "Invalid email", "condition": r"^\S+@\S+\.\S+$"}]
        report = engine.evaluate({"email": "alice@example.com"})
        assert report.results[0].passed is True

    def test_regex_no_match(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "F1", "type": "format", "field": "email", "severity": "high", "message": "Invalid email", "condition": r"^\S+@\S+\.\S+$"}]
        report = engine.evaluate({"email": "not-an-email"})
        assert report.results[0].passed is False

    def test_invalid_regex(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "F1", "type": "format", "field": "x", "severity": "high", "message": "Bad regex", "condition": "[invalid"}]
        report = engine.evaluate({"x": "test"})
        assert report.results[0].passed is False


class TestRangeRule:
    """Tests for the 'range' rule type."""

    def test_within_bounds(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "range", "field": "score", "severity": "medium", "message": "Out of range", "condition": {"min": 0, "max": 100}}]
        report = engine.evaluate({"score": "50"})
        assert report.results[0].passed is True

    def test_below_min(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "range", "field": "score", "severity": "medium", "message": "Out of range", "condition": {"min": 0, "max": 100}}]
        report = engine.evaluate({"score": "-5"})
        assert report.results[0].passed is False

    def test_above_max(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "range", "field": "score", "severity": "medium", "message": "Out of range", "condition": {"min": 0, "max": 100}}]
        report = engine.evaluate({"score": "150"})
        assert report.results[0].passed is False

    def test_non_numeric(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "range", "field": "score", "severity": "medium", "message": "Out of range", "condition": {"min": 0, "max": 100}}]
        report = engine.evaluate({"score": "abc"})
        assert report.results[0].passed is False

    def test_boundary_values(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "R1", "type": "range", "field": "score", "severity": "medium", "message": "Out of range", "condition": {"min": 0, "max": 100}}]
        assert engine.evaluate({"score": "0"}).results[0].passed is True
        assert engine.evaluate({"score": "100"}).results[0].passed is True


class TestCrossFieldRule:
    """Tests for the 'cross_field' rule type."""

    def test_equal(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "C1", "type": "cross_field", "field": "a", "severity": "medium", "message": "Mismatch", "condition": {"depends_on": "b", "operator": "eq"}}]
        report = engine.evaluate({"a": "same", "b": "same"})
        assert report.results[0].passed is True

    def test_not_equal(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "C1", "type": "cross_field", "field": "a", "severity": "medium", "message": "Mismatch", "condition": {"depends_on": "b", "operator": "neq"}}]
        report = engine.evaluate({"a": "x", "b": "y"})
        assert report.results[0].passed is True

    def test_after(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "C1", "type": "cross_field", "field": "end", "severity": "medium", "message": "Invalid", "condition": {"depends_on": "start", "operator": "after"}}]
        report = engine.evaluate({"end": "2024-02", "start": "2024-01"})
        assert report.results[0].passed is True


class TestPIICheck:
    """Tests for the 'pii_check' rule type."""

    def test_no_pii(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "P1", "type": "pii_check", "severity": "critical", "message": "PII detected"}]
        report = engine.evaluate("Hello world")
        assert report.results[0].passed is True

    def test_ssn_detected(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "P1", "type": "pii_check", "severity": "critical", "message": "PII detected"}]
        report = engine.evaluate("My SSN is 123-45-6789")
        assert report.results[0].passed is False

    def test_credit_card_detected(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "P1", "type": "pii_check", "severity": "critical", "message": "PII detected"}]
        report = engine.evaluate("Card: 1234-5678-9012-3456")
        assert report.results[0].passed is False


class TestBiasCheck:
    """Tests for the 'bias_check' rule type."""

    def test_balanced(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "B1", "type": "bias_check", "severity": "high", "message": "Bias detected"}]
        report = engine.evaluate("She and he both worked on the project.")
        assert report.results[0].passed is True

    def test_skewed(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "B1", "type": "bias_check", "severity": "high", "message": "Bias detected"}]
        text = "He did it. He led it. He managed it. He decided. He planned. He executed."
        report = engine.evaluate(text)
        assert report.results[0].passed is False

    def test_too_short(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "B1", "type": "bias_check", "severity": "high", "message": "Bias detected"}]
        report = engine.evaluate("He went.")
        assert report.results[0].passed is True  # Not enough pronouns


class TestToxicityCheck:
    """Tests for the 'toxicity_check' rule type."""

    def test_clean(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "T1", "type": "toxicity_check", "severity": "critical", "message": "Toxic", "condition": {"threshold": 0.1}}]
        report = engine.evaluate("Have a wonderful day!")
        assert report.results[0].passed is True

    def test_toxic(self, engine: ComplianceEngine) -> None:
        engine._rules = [{"id": "T1", "type": "toxicity_check", "severity": "critical", "message": "Toxic", "condition": {"threshold": 0.01}}]
        report = engine.evaluate("I will kill you")
        assert report.results[0].passed is False


class TestComplianceReport:
    """Tests for the ComplianceReport structure."""

    def test_empty_rules(self, engine: ComplianceEngine) -> None:
        report = engine.evaluate("anything")
        assert report.score == 1.0
        assert report.total_rules == 0

    def test_multiple_rules(self, engine: ComplianceEngine) -> None:
        engine._rules = [
            {"id": "R1", "type": "required", "field": "a", "severity": "high", "message": "Need a"},
            {"id": "R2", "type": "required", "field": "b", "severity": "high", "message": "Need b"},
        ]
        report = engine.evaluate({"a": "ok"})
        assert report.total_rules == 2
        assert report.passed_rules == 1
        assert report.failed_rules == 1
        assert report.score == 0.5

    def test_load_rule_pack(self, tmp_path: pytestFixture) -> None:
        import yaml
        path = tmp_path / "rules.yaml"
        data = {
            "standard": {"id": "std-1", "name": "Test Standard"},
            "rules": [
                {"id": "R1", "type": "required", "field": "x", "severity": "high", "message": "X needed"},
            ],
        }
        path.write_text(yaml.dump(data), encoding="utf-8")
        engine = ComplianceEngine(str(path))
        report = engine.evaluate({"x": "yes"})
        assert report.standard_id == "std-1"
        assert report.passed_rules == 1


# Type alias for pytest fixture type annotation
pytestFixture = pytest.fixture
