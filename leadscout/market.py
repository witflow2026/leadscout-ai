"""Market modes shared by prompts, scoring profiles, and the UI."""

from __future__ import annotations

from typing import Final


MARKET_LABELS: Final[dict[str, str]] = {
    "general": "通用 B2B",
    "international": "国际 B2B（跨境）",
    # Kept for old saved configurations; it is not shown as a separate UI option.
    "domestic": "国内 B2B（已并入通用模式）",
}

MARKET_UI_OPTIONS: Final[tuple[str, ...]] = ("general", "international")

MARKET_GUIDANCE: Final[dict[str, str]] = {
    "international": (
        "Analyze this lead for international B2B development. Look for explicit evidence of "
        "export, import, overseas projects, international sourcing, distributor or agent activity, "
        "and cross-border purchasing. Do not treat English content, a foreign country, or social "
        "media presence alone as proof of buying ability."
    ),
    "domestic": (
        "Analyze this lead for domestic B2B development. Look for explicit evidence of local "
        "projects, tenders, domestic utility or industrial customers, procurement needs, company "
        "scale, technical capability, and identifiable purchasing responsibility. Do not penalize "
        "a company merely because it lacks English content, LinkedIn, or overseas activity."
    ),
    "general": (
        "Analyze this lead as a general B2B opportunity. Focus on business relevance to the supplied "
        "offer or target-customer notes, explicit purchase intent, business scale, operational or "
        "technical capability, contactability, and decision-maker signals. Avoid assumptions based "
        "only on geography, language, or company name. This mode can be used for both domestic and "
        "international companies."
    ),
}


def normalize_market(market: str) -> str:
    """Return a supported market mode, defaulting safely to general B2B."""

    value = (market or "").strip().casefold()
    if value == "domestic":
        return "general"
    return value if value in MARKET_LABELS else "general"
