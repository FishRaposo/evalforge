# Security Guide

## Secrets Management

### API Keys for Evaluation

When testing against real LLM providers:

```bash
export EVALFORGE_OPENAI_API_KEY=sk-...
```

### Mock Backend (Default)

Evaluations use mock backend by default - no API keys needed.

```yaml
# suite.yaml
backend:
  type: mock  # No secrets needed
```

## Security Checklist

- [ ] CI uses mock backend for PRs
- [ ] Real API keys only in protected branches
- [ ] No keys in test suite files
