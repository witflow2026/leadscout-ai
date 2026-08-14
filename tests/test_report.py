from leadscout.config import DEFAULT_CONFIG
from leadscout.evidence import verify_evidence
from leadscout.llm import mock_analysis
from leadscout.report import build_report
from leadscout.schemas import LeadInput
from leadscout.scoring import score_lead


def test_report_declares_v021_schema():
    lead = LeadInput(company_name="Example Services", source_text="Service provider.")
    analysis = mock_analysis(lead)
    verifications = verify_evidence(analysis, lead)
    score = score_lead(analysis, DEFAULT_CONFIG, verifications)

    report = build_report(lead, analysis, score, verifications, provider="mock", model="")

    assert report["schema_version"] == "0.2.1"
