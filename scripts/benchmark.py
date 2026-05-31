#!/usr/bin/env python3
"""Benchmark script for EvalForge performance testing."""

import subprocess
import time
import statistics
from pathlib import Path


def benchmark_suite(suite_path: str, iterations: int = 10) -> dict:
    """Benchmark evaluation suite execution."""
    durations = []
    errors = 0

    for _ in range(iterations):
        start = time.perf_counter()
        try:
            result = subprocess.run(
                ["python", "-m", "evalforge", "eval", suite_path, "--backend", "mock", "-o", "/tmp/benchmark.json"],
                capture_output=True,
                check=True,
            )
        except subprocess.CalledProcessError:
            errors += 1
        finally:
            durations.append(time.perf_counter() - start)

    return {
        "suite": Path(suite_path).name,
        "iterations": iterations,
        "errors": errors,
        "min_s": round(min(durations), 2),
        "max_s": round(max(durations), 2),
        "mean_s": round(statistics.mean(durations), 2),
        "p50_s": round(statistics.median(durations), 2),
        "p95_s": round(sorted(durations)[int(len(durations) * 0.95)], 2),
    }


def main():
    """Run all benchmarks."""
    print("\n" + "=" * 80)
    print("EvalForge Performance Benchmarks")
    print("=" * 80)

    suites = [
        "example_suites/rag_basic.yaml",
        "example_suites/rag_citation.yaml",
    ]

    for suite in suites:
        if Path(suite).exists():
            result = benchmark_suite(suite, iterations=5)
            print(f"\n{result['suite']}")
            print(f"  Iterations: {result['iterations']} | Errors: {result['errors']}")
            print(f"  Duration: min={result['min_s']}s, mean={result['mean_s']}s, max={result['max_s']}s")
            print(f"  Percentiles: p50={result['p50_s']}s, p95={result['p95_s']}s")

    print("\n" + "=" * 80)


if __name__ == "__main__":
    main()
