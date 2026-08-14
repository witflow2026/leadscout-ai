# Security Policy

## Do not commit secrets

Never commit API keys, `.env`, Streamlit secrets, customer lists, or private
scoring profiles. If a key is exposed, revoke it immediately at the provider.

## Data handling

Live mode sends entered text to the configured AI provider. Use public or
approved data only. V0.1 does not provide authentication, database encryption,
or multi-user isolation.

## Reporting

For a security issue, open a private report to the repository maintainer when
that channel is available. Do not publish active credentials in an issue.
