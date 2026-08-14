import pytest
from pydantic import ValidationError

from leadscout.schemas import CompanyType, ExtractedFacts, TriState


def test_fact_schema_accepts_explicit_enum_values():
    facts = ExtractedFacts(
        company_type=CompanyType.DISTRIBUTOR,
        high_voltage_testing=TriState.UNKNOWN,
        relay_testing=TriState.NO,
        transformer_testing=TriState.UNKNOWN,
        transformer_manufacturing=TriState.UNKNOWN,
        distributor=TriState.YES,
        utility_clients=TriState.UNKNOWN,
        technical_team=TriState.UNKNOWN,
        competitor_signal=TriState.UNKNOWN,
        unrelated_signal=TriState.UNKNOWN,
    )
    assert facts.distributor == TriState.YES


def test_invalid_enum_value_is_rejected():
    with pytest.raises(ValidationError):
        ExtractedFacts(
            company_type="made_up_type",
            high_voltage_testing="unknown",
            relay_testing="unknown",
            transformer_testing="unknown",
            transformer_manufacturing="unknown",
            distributor="unknown",
            utility_clients="unknown",
            technical_team="unknown",
            competitor_signal="unknown",
            unrelated_signal="unknown",
        )
