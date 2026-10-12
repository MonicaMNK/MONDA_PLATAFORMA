# Security policy

This repository is a thesis/prototype project. Do not expose the demo deployment to the public Internet with seeded accounts enabled.

- Never commit `.env`, API keys, JWT signing keys, passwords, tokens, student data, uploaded materials or database dumps.
- Report vulnerabilities privately to the repository owner instead of publishing exploit details.
- Before deployment: disable demo seeds, rotate all secrets, enforce HTTPS and secure cookies, restrict network ingress, review CORS/CSRF, audit dependency/image vulnerabilities, and verify access-control tests.
- Educational records and information about minors require an institutional privacy/legal review before real-data use.
