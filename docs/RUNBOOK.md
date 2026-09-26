# Runbook

## Local commands

```bash
PYTHONPATH=src python -m unittest discover -s tests -v          # 53 unit tests
PYTHONPATH=src python -m genai_ops.cli eval fixtures/docs fixtures/golden_eval.json --min-pass 0.8
PYTHONPATH=src python -m genai_ops.cli ingest fixtures/docs --store build_store.json
PYTHONPATH=src python -m genai_ops.cli query "<question>" --store build_store.json
PYTHONPATH=src python -m genai_ops.cli status --store build_store.json
```

## Terraform

```bash
cd terraform/environments/dev
terraform init -backend=false
terraform validate
terraform test   # mocked provider, no tenancy
```

## Operate

- **Eval regression in CI**: read the eval JSON in the failed job; a
  recall miss means retrieval changed, a faithfulness miss means the
  generator drifted from sources. Fix code or extend the golden set -
  never lower `--min-pass` to force green.
- **Budget warning in logs**: `budget warning threshold crossed` means
  spend passed 80% of configured units. Raise `monthly_budget_units`
  only deliberately.
- **Injection blocks**: exit code 3 from `query`; the matched phrases
  are logged with the trace id.
