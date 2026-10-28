"""Report names are display data; exports stay local and retain earlier files."""

from datetime import datetime
from importlib import import_module

import pytest
import yaml
from typer.testing import CliRunner

from evalforge.cli import app
from evalforge.models.report import Report, ReportSummary
from tests.test_strict_gate import input_pair

REPORTERS = [
    ("json_report", "JsonReporter"),
    ("markdown", "MarkdownReporter"),
    ("html", "HtmlReporter"),
]


@pytest.mark.parametrize("module_name,class_name", REPORTERS)
@pytest.mark.parametrize(
    "name",
    [
        "../outside",
        r"..\outside",
        "/absolute",
        r"C:\outside",
        r"\\host\share",
        "CON.txt",
        '<>:"|?*\x00',
        "..",
    ],
)
def test_report_names_are_one_portable_filename(
    tmp_path, module_name, class_name, name
):
    module = import_module(f"evalforge.reporters.{module_name}")
    report = Report(
        suite_name=name,
        summary=ReportSummary(total=1, passed=1, failed=0, pass_rate=1, avg_score=1),
        results=[],
    )
    output = tmp_path / "reports"
    path = getattr(module, class_name)().generate(report, output)
    assert path.resolve().parent == output.resolve()
    assert path.is_file()


@pytest.mark.parametrize("module_name,class_name", REPORTERS)
def test_same_second_exports_preserve_original_bytes(
    tmp_path, monkeypatch, module_name, class_name
):
    module = import_module(f"evalforge.reporters.{module_name}")

    class FixedTime:
        @staticmethod
        def now():
            return datetime(2026, 10, 28, 12, 0, 0)

    monkeypatch.setattr(module, "datetime", FixedTime)
    report = Report(
        suite_name="Valid Suite-1",
        summary=ReportSummary(total=1, passed=1, failed=0, pass_rate=1, avg_score=1),
        results=[],
    )
    reporter = getattr(module, class_name)()
    first = reporter.generate(report, tmp_path)
    original = first.read_bytes()
    second = reporter.generate(
        report.model_copy(update={"metadata": {"run": 2}}), tmp_path
    )
    assert first != second
    assert first.read_bytes() == original
    assert first.name.startswith("valid_suite-1_20261028_120000.")


@pytest.mark.parametrize("format", ["json", "markdown", "html"])
def test_real_saved_cli_export_contains_untrusted_suite_name(tmp_path, format):
    suite, responses = input_pair(tmp_path)
    raw = yaml.safe_load(suite.read_text())
    raw["name"] = "../outside"
    suite.write_text(yaml.safe_dump(raw))
    output = tmp_path / "reports"
    result = CliRunner().invoke(
        app,
        [
            "eval",
            str(suite),
            "--backend",
            "saved",
            "--response-file",
            str(responses),
            "--strict-evidence",
            "--no-save",
            "--format",
            format,
            "--output",
            str(output),
        ],
    )
    assert result.exit_code == 0, result.stdout
    assert len(list(output.iterdir())) == 1
    assert not list(tmp_path.glob("outside_*"))
