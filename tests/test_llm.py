from leadscout.llm import LLMSettings, analyze_lead
from leadscout.schemas import CompanyType, LeadInput, TriState


def test_mock_mode_never_needs_api_key():
    lead = LeadInput(
        company_name="ABC Testing",
        source_text="Testing company with high voltage testing services.",
    )
    result = analyze_lead(lead, LLMSettings(api_key="", model=""), mock=True)
    assert result.facts.company_type == CompanyType.TESTING_COMPANY
    assert result.facts.high_voltage_testing == TriState.YES
