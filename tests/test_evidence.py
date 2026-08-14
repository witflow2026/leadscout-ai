from leadscout.evidence import verify_evidence
from leadscout.schemas import (
    CompanyType,
    DataSufficiency,
    ExtractedFacts,
    LeadAnalysis,
    LeadInput,
    TriState,
)


def _analysis(quote: str) -> LeadAnalysis:
    return LeadAnalysis(
        summary="Test",
        facts=ExtractedFacts(
            company_type=CompanyType.TESTING_COMPANY,
            high_voltage_testing=TriState.YES,
            relay_testing=TriState.UNKNOWN,
            transformer_testing=TriState.UNKNOWN,
            transformer_manufacturing=TriState.UNKNOWN,
            distributor=TriState.UNKNOWN,
            utility_clients=TriState.UNKNOWN,
            technical_team=TriState.UNKNOWN,
            competitor_signal=TriState.UNKNOWN,
            unrelated_signal=TriState.UNKNOWN,
        ),
        potential_needs=[],
        recommended_contact_roles=[],
        outreach_angle="Test angle",
        confidence=80,
        data_sufficiency=DataSufficiency.HIGH,
        evidence=[{"field": "company_type", "quote": quote, "source": "source_text"}],
        caveats=[],
    )


def test_evidence_is_verified_case_and_whitespace_insensitive():
    lead = LeadInput(company_name="ABC", source_text="We   provide TESTING services.")
    result = verify_evidence(_analysis("we provide testing services."), lead)
    assert result[0].verified is True


def test_fabricated_evidence_is_rejected():
    lead = LeadInput(company_name="ABC", source_text="We provide electrical services.")
    result = verify_evidence(_analysis("We provide transformer testing."), lead)
    assert result[0].verified is False
