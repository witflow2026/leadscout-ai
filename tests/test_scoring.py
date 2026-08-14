from leadscout.config import DEFAULT_CONFIG
from leadscout.evidence import verify_evidence
from leadscout.llm import mock_analysis
from leadscout.schemas import LeadInput
from leadscout.scoring import score_lead


def test_mock_testing_lead_gets_rule_based_score():
    lead = LeadInput(
        company_name="ABC Testing",
        country="Kenya",
        source_text="Testing company. We provide high voltage testing and relay testing services.",
    )
    analysis = mock_analysis(lead)
    verification = verify_evidence(analysis, lead)
    score = score_lead(analysis, DEFAULT_CONFIG, verification)

    assert score.total == 65
    assert score.grade == "B"
    assert score.review_required is True
    assert score.evidence_coverage == 100


def test_unverified_positive_fact_does_not_change_score():
    lead = LeadInput(company_name="ABC", source_text="Electrical services only.")
    base = mock_analysis(lead)
    analysis = type(base).model_validate(
        {
            **base.model_dump(mode="json"),
            "facts": {**base.facts.model_dump(mode="json"), "company_type": "testing_company"},
            "evidence": [
                {
                    "field": "company_type",
                    "quote": "We provide transformer testing.",
                    "source": "source_text",
                }
            ],
        }
    )
    verification = verify_evidence(analysis, lead)
    score = score_lead(analysis, DEFAULT_CONFIG, verification)

    assert score.total == 0
    assert score.grade == "D"
    assert score.review_required is True
    assert score.evidence_coverage == 0


def test_unknown_facts_are_not_penalized():
    lead = LeadInput(company_name="ABC", source_text="A short company profile.")
    analysis = mock_analysis(lead)
    verification = verify_evidence(analysis, lead)
    score = score_lead(analysis, DEFAULT_CONFIG, verification)

    assert score.total == 0
    assert score.grade == "D"
