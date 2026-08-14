"""Typed input, model-output, and scoring schemas for LeadScout AI."""

from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class TriState(str, Enum):
    """A fact can be present, absent, or not established."""

    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


class CompanyType(str, Enum):
    MANUFACTURER = "manufacturer"
    SERVICE_PROVIDER = "service_provider"
    CONTRACTOR = "contractor"
    TECHNOLOGY_COMPANY = "technology_company"
    IMPORTER_EXPORTER = "importer_exporter"
    RETAILER = "retailer"
    TESTING_COMPANY = "testing_company"
    TRANSFORMER_MANUFACTURER = "transformer_manufacturer"
    UTILITY_CONTRACTOR = "utility_contractor"
    DISTRIBUTOR = "distributor"
    ENGINEERING_CONSULTANT = "engineering_consultant"
    OTHER = "other"
    UNKNOWN = "unknown"


class DataSufficiency(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class LeadInput(BaseModel):
    """The information sent to an LLM in V0.2."""

    company_name: str = Field(min_length=1, max_length=200)
    country: str = Field(default="", max_length=120)
    website: str = Field(default="", max_length=500)
    notes: str = Field(default="", max_length=12_000)
    source_text: str = Field(default="", max_length=12_000)


class EvidenceItem(BaseModel):
    """A verbatim quote that supports one extracted fact."""

    field: str = Field(min_length=1, max_length=80)
    quote: str = Field(min_length=1, max_length=400)
    source: Literal["notes", "source_text"]


class ExtractedFacts(BaseModel):
    """Facts extracted from supplied text; no final score is generated here."""

    company_type: CompanyType
    business_relevance: TriState = TriState.UNKNOWN
    purchase_intent: TriState = TriState.UNKNOWN
    business_scale: TriState = TriState.UNKNOWN
    technical_capability: TriState = TriState.UNKNOWN
    distributor_or_partner: TriState = TriState.UNKNOWN
    contactability: TriState = TriState.UNKNOWN
    decision_maker_signal: TriState = TriState.UNKNOWN
    international_business: TriState = TriState.UNKNOWN
    domestic_business: TriState = TriState.UNKNOWN
    competitor_signal: TriState = TriState.UNKNOWN
    unrelated_signal: TriState = TriState.UNKNOWN

    # Legacy industry-specific fields remain optional for old reports/configs.
    high_voltage_testing: TriState = TriState.UNKNOWN
    relay_testing: TriState = TriState.UNKNOWN
    transformer_testing: TriState = TriState.UNKNOWN
    transformer_manufacturing: TriState = TriState.UNKNOWN
    distributor: TriState = TriState.UNKNOWN
    utility_clients: TriState = TriState.UNKNOWN
    technical_team: TriState = TriState.UNKNOWN


class LeadAnalysis(BaseModel):
    """Structured LLM response for a single lead."""

    summary: str = Field(min_length=1, max_length=800)
    facts: ExtractedFacts
    potential_needs: list[str] = Field(max_length=12)
    recommended_contact_roles: list[str] = Field(max_length=8)
    outreach_angle: str = Field(min_length=1, max_length=800)
    confidence: int = Field(ge=0, le=100)
    data_sufficiency: DataSufficiency
    evidence: list[EvidenceItem] = Field(max_length=30)
    caveats: list[str] = Field(max_length=12)


class ScoreItem(BaseModel):
    rule_id: str
    label: str
    points: int
    reason: str
    evidence_fields: list[str] = Field(default_factory=list)


class ScoreResult(BaseModel):
    total: int
    grade: Literal["A", "B", "C", "D"]
    review_required: bool
    evidence_coverage: int = Field(ge=0, le=100)
    breakdown: list[ScoreItem] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
