# Metrics

EvalForge computes several metrics to quantify AI system quality across different dimensions.

## Pass Rate

**Formula**: `passed / total`

The percentage of test cases that pass evaluation. This is the primary metric for overall system health.

**Interpretation**:
- 90-100%: System is performing well
- 70-89%: Some regression detected, investigate failures
- Below 70%: Significant issues, do not deploy

## Exact Match Rate

**Judge**: `ExactMatchJudge`

**Scoring**: Binary (1.0 or 0.0)

Measures factual accuracy for questions with definitive answers. A high exact match rate indicates the system retrieves and presents factual information correctly.

## Semantic Similarity Score

**Judge**: `SemanticMatchJudge`

**Scoring**: Continuous (0.0 to 1.0)

Measures how close the response is to the expected answer in embedding space. This handles paraphrasing and alternative phrasings.

**Threshold**: Default 0.8. Configurable per test case via `metadata.threshold`.

## Citation Accuracy

**Judge**: `CitationCheckJudge`

**Scoring**: Ratio of expected sources found (0.0 to 1.0)

Measures whether the system properly attributes information to its sources. Critical for trust and verification.

## Refusal Accuracy

**Judge**: `RefusalCheckJudge`

**Scoring**: Binary (1.0 or 0.0)

Measures whether the system correctly refuses inappropriate requests and correctly answers legitimate ones. A misconfigured refusal rate indicates safety issues.

## Retrieval Precision

**Judge**: `RetrievalCheckJudge`

**Scoring**: Ratio of expected documents retrieved (0.0 to 1.0)

Measures whether the retrieval system surfaces the correct documents for a given query.

## Forbidden Content Rate

**Judge**: `ForbiddenContentJudge`

**Scoring**: Binary (1.0 for clean, 0.0 for violation)

Measures whether the system avoids generating prohibited content. Zero tolerance: any violation fails the test.

## How Thresholds Work

Each judge uses a threshold to determine pass/fail:

```
if score >= threshold:
    passed = True
else:
    passed = False
```

Default thresholds:
| Metric | Default Threshold |
|--------|------------------|
| Exact Match | 1.0 (must be exact) |
| Semantic Similarity | 0.8 |
| Citation | 1.0 (all sources required) |
| Refusal | 1.0 (binary) |
| Retrieval | 1.0 (all docs required) |
| Forbidden Content | 1.0 (zero tolerance) |

Thresholds can be overridden per test case via the `metadata.threshold` field.

## Interpreting Reports

### Markdown Report

The markdown report includes:
- Summary table with pass/fail counts and pass rate
- Individual test results with scores and details
- Failed tests highlighted with expected vs actual output

### JSON Report

The JSON report provides:
- Machine-readable results for CI integration
- Full detail on each test including judge reasoning
- Metadata for trend analysis

### HTML Report

The HTML report includes:
- Styled tables with color-coded results
- Score distribution visualization
- Expandable sections for detailed judge output

## Aggregation

For a test suite, the overall score is computed as:

```
avg_score = sum(test_scores) / total_tests
```

The suite passes if `pass_rate >= fail_threshold` (configurable via CLI).
