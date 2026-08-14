# Contributing to LeadScout AI

Thank you for helping improve LeadScout AI. The project is an evidence-first
B2B analysis assistant, so contributions should favor clear evidence handling,
deterministic scoring, and safe provider interactions.

## Before opening a pull request

- Use Python 3.10 or newer.
- Run `python -m pytest -q`.
- Use public or synthetic company text only; never commit customer lists,
  API keys, `.env` files, or provider responses containing private data.
- Update `CHANGELOG.md` when behavior or user-facing text changes.
- Add or update a regression test for bug fixes.

## Scope guidelines

- Keep general B2B behavior in the default profile.
- Put industry-specific scoring in an explicit profile or compatibility layer.
- Keep model output extraction separate from deterministic scoring.
- Treat model claims as untrusted until evidence verification succeeds.
- Do not add website crawling, social login, automated outreach, or credential
  collection without a documented privacy and security review.

## Pull requests

Describe the user problem, the behavior changed, tests run, and any privacy or
security implications. Small focused pull requests are easier to review.
