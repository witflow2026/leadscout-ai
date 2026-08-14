"""Configuration loading with a public example and optional private override."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from typing import Any

from .market import normalize_market


DEFAULT_CONFIG: dict[str, Any] = {
    "company_type": {
        "manufacturer": 20,
        "service_provider": 20,
        "contractor": 15,
        "technology_company": 20,
        "importer_exporter": 15,
        "retailer": 10,
        "distributor": 15,
        "engineering_consultant": 10,
    },
    "signals": {
        "business_relevance": 20,
        "purchase_intent": 25,
        "business_scale": 10,
        "technical_capability": 10,
        "distributor_or_partner": 15,
        "contactability": 10,
        "decision_maker_signal": 10,
    },
    "penalties": {
        "competitor_signal": -100,
        "unrelated_signal": -100,
    },
    "thresholds": {"A": 70, "B": 45, "C": 20, "D": 0},
    "profiles": {
        "international": {
            "signals": {
                "business_relevance": 20,
                "international_business": 20,
                "purchase_intent": 20,
                "distributor": 15,
                "business_scale": 10,
                "contactability": 10,
            }
        },
        "domestic": {
            "signals": {
                "domestic_business": 20,
                "purchase_intent": 25,
                "business_scale": 15,
                "utility_clients": 15,
                "technical_team": 10,
                "decision_maker_signal": 10,
            }
        },
        "general": {
            "signals": {
                "business_relevance": 20,
                "purchase_intent": 20,
                "business_scale": 10,
                "technical_capability": 10,
                "distributor_or_partner": 10,
                "contactability": 10,
                "decision_maker_signal": 10,
            }
        },
    },
}


def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result


def load_config(path: str | Path | None = None, market: str = "general") -> dict[str, Any]:
    """Load YAML configuration, falling back to safe public defaults."""

    config = deepcopy(DEFAULT_CONFIG)
    if path is not None:
        config_path = Path(path)
        if config_path.exists():
            try:
                import yaml
            except ImportError as exc:  # pragma: no cover
                raise RuntimeError("PyYAML is required to load scoring configuration") from exc
            raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            if not isinstance(raw, dict):
                raise ValueError("Scoring configuration must be a YAML mapping")
            config = _deep_merge(config, raw)

    profiles = config.pop("profiles", {})
    raw_market = (market or "").strip().casefold()
    profile_key = "domestic" if raw_market == "domestic" else normalize_market(market)
    selected = profiles.get(profile_key, profiles.get("general", {}))
    if not isinstance(selected, dict):
        selected = {}
    return _deep_merge(config, selected)
