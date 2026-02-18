---
trigger: always_on
---

---

name: security-guardrail
description: Mandatory security constraints for all code generation

---

# Security Rules

- **No Secrets:** Never write hardcoded API keys, passwords, or tokens. Use `process.env` placeholders.
- **Injection Prevention:** Always use parameterized queries for database interactions; never concatenate strings into SQL.
- **Sanitization:** All user-provided input must be sanitized before being rendered in the DOM or used in file system operations.
- **Dependencies:** Before suggesting a new npm/pip package, check for known vulnerabilities or "typosquatting" risks.
