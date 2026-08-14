"""Deterministic evidence verification for model-generated quotes."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .schemas import EvidenceItem, LeadAnalysis, LeadInput


def _normalize(text: str) -> str:
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    return re.sub(r"\s+", " ", text).strip().casefold()


@dataclass(frozen=True)
class EvidenceVerification:
    index: int
    item: EvidenceItem
    verified: bool
    reason: str

    def to_dict(self) -> dict[str, object]:
        return {
            "index": self.index,
            "field": self.item.field,
            "quote": self.item.quote,
            "source": self.item.source,
            "verified": self.verified,
            "reason": self.reason,
        }


def verify_evidence(analysis: LeadAnalysis, lead: LeadInput) -> list[EvidenceVerification]:
    sources = {"notes": _normalize(lead.notes), "source_text": _normalize(lead.source_text)}
    results: list[EvidenceVerification] = []
    for index, item in enumerate(analysis.evidence):
        source_text = sources.get(item.source, "")
        verified = bool(source_text) and _normalize(item.quote) in source_text
        reason = "Exact quote found in supplied text" if verified else "Quote not found in supplied text"
        results.append(EvidenceVerification(index, item, verified, reason))
    return results


def verified_fields(verifications: list[EvidenceVerification]) -> set[str]:
    return {item.item.field for item in verifications if item.verified}
