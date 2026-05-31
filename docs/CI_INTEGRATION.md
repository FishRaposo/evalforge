# CI Integration

## GitHub Actions Setup

EvalForge integrates seamlessly with GitHub Actions to run evaluations on every push and pull request.

### Quick Setup

1. Add your OpenAI API key as a repository secret:
   - Go to **Settings → Secrets and variables → Actions**
   - Add `OPENAI_API_KEY` with your key

2. Create `.github/workflows/eval-ci.yml` in your repository.

3. Evaluations will run automatically on pushes to `main` and on pull requests.

### Example Workflow

```yaml
name: AI Evaluation

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  evaluate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -e .

      - name: Run RAG evaluations
        run: evalforge eval example_suites/rag_basic.yaml --format json
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}

      - name: Run citation evaluations
        run: evalforge eval example_suites/rag_citation.yaml --format markdown

      - name: Run compliance checks
        run: evalforge eval example_suites/compliance.yaml --format json

      - name: Upload evaluation reports
        uses: actions/upload-artifact@v4
        if: always()
        with:
          name: eval-reports
          path: reports/
          retention-days: 30
```

## Fail Build on Regression

Use the `--fail-threshold` flag to fail the build when quality drops:

```yaml
- name: Run evaluations with quality gate
  run: evalforge eval suite.yaml --fail-threshold 0.8
```

This command will exit with code 1 if the pass rate falls below 80%, causing the CI build to fail.

## Scheduled Drift Detection

Run evaluations on a schedule to detect quality drift over time:

```yaml
on:
  schedule:
    - cron: '0 6 * * *'  # Daily at 6 AM UTC
```

Combine with artifact retention to build a history of evaluation results.

## Report Artifacts

Reports are uploaded as CI artifacts for review:

- **JSON reports**: Can be consumed by downstream tooling or dashboards
- **Markdown reports**: Easy to read in the GitHub UI
- **HTML reports**: Can be deployed to a static site for team review

### Downloading Artifacts

```bash
# Via GitHub CLI
gh run download --name eval-reports

# Via API
curl -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/repos/:owner/:repo/actions/artifacts
```

## Multi-Environment Evaluation

Test across different environments:

```yaml
jobs:
  evaluate-staging:
    runs-on: ubuntu-latest
    steps:
      - run: evalforge eval suite.yaml --backend openai
        env:
          OPENAI_BASE_URL: https://staging-api.example.com/v1

  evaluate-production:
    runs-on: ubuntu-latest
    needs: evaluate-staging
    steps:
      - run: evalforge eval suite.yaml --backend openai
        env:
          OPENAI_BASE_URL: https://api.example.com/v1
```

## Best Practices

1. **Version your test suites**: Keep YAML suites in the repo alongside code
2. **Start with mock backend**: Use mock responses for fast CI feedback
3. **Add real backend in nightly runs**: Full API calls in scheduled builds
4. **Set meaningful thresholds**: 80% is a reasonable starting point
5. **Review failures promptly**: Check report artifacts on every failure
6. **Track trends**: Compare reports across runs to spot gradual drift
