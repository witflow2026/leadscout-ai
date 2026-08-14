from types import SimpleNamespace
from unittest.mock import patch

from leadscout.llm import (
    LLMError,
    LLMSettings,
    _provider_error_message,
    analyze_lead,
    check_connection,
)
from leadscout.schemas import CompanyType, LeadInput, TriState


def test_mock_mode_never_needs_api_key():
    lead = LeadInput(
        company_name="ABC Testing",
        source_text="Testing company with high voltage testing services.",
    )
    result = analyze_lead(lead, LLMSettings(api_key="", model=""), mock=True)
    assert result.facts.company_type == CompanyType.TESTING_COMPANY
    assert result.facts.high_voltage_testing == TriState.YES


def test_provider_error_hides_api_key():
    class ProviderError(Exception):
        status_code = 401

    settings = LLMSettings(api_key="secret-key", model="demo-model")
    message = _provider_error_message(ProviderError("secret-key is invalid"), settings)

    assert "secret-key" not in message
    assert "401" in message


def test_connection_rejects_missing_credentials():
    try:
        check_connection(LLMSettings(api_key="", model="demo-model"))
    except LLMError as exc:
        assert "API Key" in str(exc)
    else:  # pragma: no cover - the assertion above must raise
        raise AssertionError("missing credentials should fail before any network request")


def test_connection_sends_only_minimal_probe():
    response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))]
    )
    settings = LLMSettings(api_key="secret-key", model="demo-model")

    with patch("leadscout.llm._client", return_value=object()), patch(
        "leadscout.llm._request_json", return_value=response
    ) as request:
        result = check_connection(settings)

    assert "连接成功" in result
    messages = request.call_args.args[2]
    assert "customer" not in str(messages).casefold()
    assert "secret-key" not in str(messages)
