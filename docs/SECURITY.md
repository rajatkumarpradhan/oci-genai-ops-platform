# Security notes

Portfolio scope: heuristic controls, not certified security mechanisms.

- **Prompt injection**: fail-closed phrase screening in
  `guardrails.screen_injection`; a blocked request never reaches
  retrieval or generation.
- **PII**: regex redaction for email, Indian mobile numbers, card
  numbers and OCI IDs / API keys, applied on input and output.
- **Secrets**: the ADB admin password is a sensitive Terraform variable
  supplied via `TF_VAR_adb_admin_password`; nothing is committed.
- **Network**: the vector database rejects `0.0.0.0/0` in variable
  validation and requires mTLS.
- **Spend**: the cost guard raises before configured budget units are
  exceeded; Terraform adds a forecast-based 80% budget alert.
- **CI**: workflow permissions are `read-all`; tfsec runs non-soft-fail.
