"""Build and verify EvalForge's credential-free portfolio evidence fixture."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUITE = ROOT / "example_suites" / "rag_basic.yaml"
GOLDEN = ROOT / "tests" / "fixtures" / "portfolio_evidence" / "reproducibility.json"

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evalforge.evidence import (  # noqa: E402
    EvidenceVerificationError,
    verify_evidence_bundle,
)


def _clear_bundle_files(output_dir: Path) -> None:
    """Remove only files owned by this check from a requested output directory."""
    output_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "manifest.json",
        "report.json",
        "report.md",
        "drift.json",
        "calibration.json",
        "trace.json",
        "checksums.sha256",
    ):
        path = output_dir / name
        if path.is_file():
            path.unlink()


def build_and_verify(output_dir: Path) -> str:
    """Run the public CLI offline, verify its bundle, and compare its golden hash."""
    _clear_bundle_files(output_dir)
    report_dir = output_dir.parent / f"{output_dir.name}-reports"
    command = [
        sys.executable,
        "-m",
        "evalforge.cli",
        "eval",
        str(SUITE),
        "--backend",
        "mock",
        "--no-save",
        "--format",
        "json",
        "--output",
        str(report_dir),
        "--evidence-dir",
        str(output_dir),
    ]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        raise RuntimeError(
            "Offline evidence evaluation failed:\n"
            f"{completed.stdout}\n{completed.stderr}"
        )

    try:
        manifest = verify_evidence_bundle(output_dir)
    except EvidenceVerificationError as exc:
        raise RuntimeError(f"Offline evidence verification failed: {exc}") from exc

    expected = json.loads(GOLDEN.read_text(encoding="utf-8"))
    expected_hash = expected.get("reproducibility_hash")
    if not isinstance(expected_hash, str) or not expected_hash:
        raise RuntimeError(f"Golden fixture has no reproducibility_hash: {GOLDEN}")
    if manifest.reproducibility_hash != expected_hash:
        raise RuntimeError(
            "Portfolio evidence reproducibility hash changed: "
            f"expected {expected_hash}, got {manifest.reproducibility_hash}"
        )
    return manifest.reproducibility_hash


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Keep the verified bundle in this directory (CI artifact mode)",
    )
    args = parser.parse_args()

    if args.output_dir is not None:
        output_dir = args.output_dir.resolve()
        digest = build_and_verify(output_dir)
        print(f"Portfolio evidence verified: {output_dir} ({digest})")
        return 0

    with tempfile.TemporaryDirectory(prefix="evalforge-evidence-") as temporary:
        digest = build_and_verify(Path(temporary) / "bundle")
    print(f"Portfolio evidence verified ({digest})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
