from leadscout.config import load_config
from leadscout.evidence import verify_evidence
from leadscout.llm import mock_analysis
from leadscout.market import MARKET_LABELS
from leadscout.prompts import build_messages
from leadscout.schemas import LeadInput
from leadscout.scoring import score_lead


def test_market_profiles_have_different_weights():
    international = load_config(market="international")
    domestic = load_config(market="domestic")
    general = load_config(market="general")

    assert international["signals"]["international_business"] == 20
    assert domestic["signals"]["domestic_business"] == 20
    assert domestic["signals"]["purchase_intent"] == 25
    assert general["signals"]["purchase_intent"] == 20


def test_domestic_mode_scores_domestic_signals():
    lead = LeadInput(
        company_name="Domestic Utility Testing Group",
        country="China",
        source_text=(
            "Domestic testing company with utility clients and a large technical team. "
            "The procurement manager is preparing a tender for transformer testing."
        ),
    )
    analysis = mock_analysis(lead, market="domestic")
    score = score_lead(analysis, load_config(market="domestic"), verify_evidence(analysis, lead))

    rule_ids = {item.rule_id for item in score.breakdown}
    assert "signal:domestic_business" in rule_ids
    assert "signal:purchase_intent" in rule_ids
    assert score.total > 0


def test_prompt_contains_selected_market_guidance():
    lead = LeadInput(company_name="ABC", source_text="A short company profile.")
    messages = build_messages(lead, market="general")

    assert "general B2B" in messages[0]["content"]
    assert "business relevance" in messages[0]["content"]


def test_market_labels_are_user_facing():
    assert MARKET_LABELS["international"] == "国际 B2B（跨境）"
