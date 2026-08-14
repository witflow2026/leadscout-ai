# Changelog

## 0.2.1 - 2026-08-14

- Generalized the default scoring profile so legacy electrical fields are not
  scored unless explicitly enabled in a private configuration.
- Added a model connection test that sends no customer information.
- Added actionable provider error handling and regression coverage for API-key
  redaction and missing credentials.
- Added a neutral example lead, contribution guidance, and a bug report template.
- Updated the UI, README, and privacy notes to identify the release as 0.2.1.

## 0.2.0 - 2026-08-14

- Added general B2B and international B2B market modes.
- Merged domestic B2B into the general mode in the public UI while preserving
  a compatibility alias for older configuration files.
- Replaced industry-specific primary facts with general company type,
  relevance, purchase intent, scale, capability, contactability, and
  decision-maker signals.
- Added the selected market and label to exported reports.

## 0.1.0 - 2026-08-14

- Added single-lead Streamlit interface.
- Added light custom UI theme and responsive result layout.
- Added Mock mode for no-cost local testing.
- Added OpenAI-compatible live analysis adapter.
- Added Pydantic schemas and evidence verification.
- Added deterministic YAML-configured scoring.
- Added JSON report download and unit tests.
