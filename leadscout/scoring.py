"""Rule-based, evidence-gated lead scoring."""

from __future__ import annotations

from typing import Any

from .evidence import EvidenceVerification, verified_fields
from .schemas import LeadAnalysis, ScoreItem, ScoreResult, TriState


def _add_item(
    breakdown: list[ScoreItem],
    rule_id: str,
    label: str,
    points: int,
    reason: str,
    field: str,
) -> None:
    breakdown.append(
        ScoreItem(
            rule_id=rule_id,
            label=label,
            points=points,
            reason=reason,
            evidence_fields=[field],
        )
    )


def _grade(total: int, thresholds: dict[str, Any]) -> str:
    for grade in ("A", "B", "C", "D"):
        if total >= int(thresholds.get(grade, 0)):
            return grade
    return "D"


def score_lead(
    analysis: LeadAnalysis,
    config: dict[str, Any],
    verifications: list[EvidenceVerification],
) -> ScoreResult:
    """Score only positive facts supported by exact user-provided evidence."""

    supported = verified_fields(verifications)
    breakdown: list[ScoreItem] = []
    warnings: list[str] = []
    facts = analysis.facts
    company_weights = config.get("company_type", {})
    signal_weights = config.get("signals", {})
    penalty_weights = config.get("penalties", {})
    positive_claim_fields: list[str] = []

    company_type = facts.company_type.value
    company_type_labels = {
        "manufacturer": "制造商",
        "service_provider": "服务商",
        "contractor": "承包商/工程公司",
        "technology_company": "科技/软件公司",
        "importer_exporter": "进出口商",
        "retailer": "零售/经销企业",
        "distributor": "经销商/代理商",
        "testing_company": "测试公司",
        "transformer_manufacturer": "变压器制造商",
        "utility_contractor": "电力承包商",
        "engineering_consultant": "工程咨询公司",
        "other": "其他类型",
        "unknown": "资料不足",
    }
    if company_type != "unknown":
        positive_claim_fields.append("company_type")
        if "company_type" in supported:
            points = int(company_weights.get(company_type, 0))
            if points:
                _add_item(
                    breakdown,
                    f"company_type:{company_type}",
                    f"公司类型：{company_type_labels.get(company_type, company_type)}",
                    points,
                    "有已核验的公司类型证据支持",
                    "company_type",
                )
        else:
            warnings.append("公司类型因证据无法核验，未计入评分。")

    signal_labels = {
        "business_relevance": "业务相关性",
        "purchase_intent": "采购意向",
        "business_scale": "企业规模",
        "technical_capability": "技术/实施能力",
        "distributor_or_partner": "渠道/合作伙伴潜力",
        "contactability": "可联系性",
        "decision_maker_signal": "决策人信号",
        "international_business": "国际业务信号",
        "domestic_business": "国内业务信号",
        "high_voltage_testing": "高压测试",
        "relay_testing": "继电保护测试",
        "transformer_testing": "变压器测试",
        "transformer_manufacturing": "变压器制造",
        "utility_clients": "电力客户",
        "technical_team": "技术团队",
        "distributor": "经销商信号",
        "international_business": "国际业务信号",
        "domestic_business": "国内业务信号",
        "purchase_intent": "采购意向信号",
        "business_scale": "企业规模信号",
        "contactability": "联系方式信号",
        "decision_maker_signal": "决策人信号",
    }
    for field, label in signal_labels.items():
        if getattr(facts, field) == TriState.YES:
            positive_claim_fields.append(field)
            if field in supported:
                points = int(signal_weights.get(field, 0))
                if points:
                    _add_item(
                        breakdown,
                        f"signal:{field}",
                        label,
                        points,
                        "有已核验的正面证据支持",
                        field,
                    )
            else:
                warnings.append(f"{label}因证据无法核验，未计入评分。")

    for field, label in (
        ("competitor_signal", "竞争对手信号"),
        ("unrelated_signal", "无关行业信号"),
    ):
        if getattr(facts, field) == TriState.YES:
            positive_claim_fields.append(field)
            if field in supported:
                points = int(penalty_weights.get(field, 0))
                _add_item(
                    breakdown,
                    f"penalty:{field}",
                    label,
                    points,
                    "有已核验的负面证据支持",
                    field,
                )
            else:
                warnings.append(f"{label}因证据无法核验，未应用扣分。")

    total = sum(item.points for item in breakdown)
    coverage = 100 if not positive_claim_fields else round(
        100 * sum(field in supported for field in positive_claim_fields) / len(positive_claim_fields)
    )
    grade = _grade(total, config.get("thresholds", {}))
    review_required = bool(
        warnings
        or analysis.data_sufficiency.value != "high"
        or analysis.confidence < 60
        or coverage < 80
    )
    if review_required:
        warnings.append("联系该客户前，请先人工复核证据和资料来源质量。")

    return ScoreResult(
        total=total,
        grade=grade,
        review_required=review_required,
        evidence_coverage=coverage,
        breakdown=breakdown,
        warnings=list(dict.fromkeys(warnings)),
    )
