# Security Policy

## Do not commit secrets

Never commit API keys, `.env`, Streamlit secrets, customer lists, or private
scoring profiles. If a key is exposed, revoke it immediately at the provider.

## Data handling

Live mode sends entered text to the configured AI provider. Use public or
approved data only. V0.1 does not provide authentication, database encryption,
or multi-user isolation.

## Reporting

For a security issue, use GitHub's private vulnerability reporting for this
repository when available, or contact the maintainer privately through the
GitHub profile. Do not publish active credentials, customer data, or exploit
details in a public issue.

When reporting, include the affected version, reproduction steps using
synthetic data, impact, and a suggested mitigation if known.
