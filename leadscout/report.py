"""Serializable report assembly for the Streamlit UI and JSON download."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from .evidence import EvidenceVerification
from .market import MARKET_LABELS, normalize_market
from .schemas import LeadAnalysis, LeadInput, ScoreResult


def build_report(
    lead: LeadInput,
    analysis: LeadAnalysis,
    score: ScoreResult,
    verifications: list[EvidenceVerification],
    provider: str,
    model: str,
    market: str = "general",
) -> dict[str, Any]:
    selected_market = normalize_market(market)
    return {
        "schema_version": "0.2.0",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": selected_market,
        "market_label": MARKET_LABELS[selected_market],
        "provider": provider,
        "model": model or "mock",
        "input": lead.model_dump(mode="json"),
        "analysis": analysis.model_dump(mode="json"),
        "score": score.model_dump(mode="json"),
        "evidence_verification": [item.to_dict() for item in verifications],
    }
