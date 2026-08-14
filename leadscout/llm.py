"""LLM adapter with Mock, structured-output, and JSON fallback modes."""

from __future__ import annotations

import json
from dataclasses import dataclass

from .market import MARKET_LABELS, normalize_market
from .prompts import build_messages
from .schemas import (
    CompanyType,
    DataSufficiency,
    ExtractedFacts,
    LeadAnalysis,
    LeadInput,
    TriState,
)


class LLMError(RuntimeError):
    """A user-safe error raised for provider configuration or response failures."""


@dataclass(frozen=True)
class LLMSettings:
    api_key: str
    model: str
    base_url: str = ""
    mode: str = "auto"
    market: str = "general"


def _is_deepseek(settings: LLMSettings) -> bool:
    model = settings.model.strip().casefold()
    base_url = settings.base_url.strip().casefold()
    return model.startswith("deepseek-") or "api.deepseek.com" in base_url


def _provider_error_message(exc: Exception, settings: LLMSettings) -> str:
    """Turn provider failures into an actionable message without exposing the key."""

    status_code = getattr(exc, "status_code", None)
    status_hints = {
        401: "接口密钥无效或已过期，请重新生成 API Key。",
        402: "账户余额不足，或当前账户没有可用额度。",
        403: "接口权限不足，请检查账户权限和模型访问权限。",
        404: "模型名称或接口地址不存在，请检查模型标识和 Base URL。",
        408: "请求超时，请稍后重试或检查网络连接。",
        429: "请求频率超限，请稍后重试。",
    }
    if status_code in status_hints:
        return f"{status_hints[status_code]}（HTTP {status_code}）"

    detail = ""
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        error = body.get("error")
        if isinstance(error, dict):
            detail = str(error.get("message") or error.get("type") or "")
        elif isinstance(error, str):
            detail = error
    if not detail:
        detail = str(exc).strip()
    if settings.api_key.strip():
        detail = detail.replace(settings.api_key.strip(), "***")
    detail = " ".join(detail.split())[:240]
    status = f"（HTTP {status_code}）" if status_code else ""
    if detail:
        return f"在线模型请求失败{status}：{detail}"
    return f"在线模型请求失败{status}，服务商未返回具体原因。"


def _mock_quote(lead: LeadInput) -> tuple[str, str]:
    if lead.source_text.strip():
        return "source_text", lead.source_text.strip().splitlines()[0][:350]
    if lead.notes.strip():
        return "notes", lead.notes.strip().splitlines()[0][:350]
    return "source_text", ""


def mock_analysis(lead: LeadInput, market: str = "general") -> LeadAnalysis:
    """Return deterministic output for UI development without an API key."""

    text = f"{lead.notes}\n{lead.source_text}".casefold()
    source, quote = _mock_quote(lead)

    def state_for(*terms: str) -> TriState:
        return TriState.YES if any(term in text for term in terms) else TriState.UNKNOWN

    high_voltage = state_for("high voltage", "high-voltage", "hv testing", "高压测试", "高压试验")
    relay = state_for("relay testing", "protective relay", "relay test", "继电保护测试", "继保测试")
    transformer_testing = state_for(
        "transformer testing",
        "transformer diagnosis",
        "transformer diagnostic",
        "变压器测试",
        "变压器试验",
        "变压器诊断",
    )
    transformer_manufacturing = state_for(
        "manufacture transformer", "transformer manufacturer", "变压器制造", "变压器生产"
    )
    distributor = state_for("distributor", "dealer", "代理商")
    partner_signal = state_for("partner", "partnership", "合作伙伴", "合作关系")
    utility_clients = state_for("utility", "power company", "电力公司")
    technical_team = state_for(
        "engineer", "engineering team", "technical team", "工程师", "技术团队", "测试团队"
    )
    international_business = state_for(
        "export", "import", "overseas", "international", "global", "出口", "进口", "海外"
    )
    domestic_business = state_for(
        "domestic", "local market", "local project", "tender", "招标", "国内", "本地", "国网", "南网"
    )
    purchase_intent = state_for(
        "procurement", "purchasing", "looking for", "project need", "tender", "采购", "招标", "需求", "项目"
    )
    business_scale = state_for(
        "large company", "major company", "enterprise", "employees", "revenue", "大型", "集团", "员工", "营收"
    )
    contactability = state_for("email", "phone", "contact", "邮箱", "电话", "联系方式")
    decision_maker = state_for(
        "purchasing manager", "procurement manager", "director", "decision maker", "采购经理", "采购负责人", "负责人"
    )
    business_relevance = state_for(
        "relevant", "relevance", "fit", "match", "suitable", "compatible", "相关", "匹配", "适合", "符合"
    )
    distributor_or_partner = (
        TriState.YES
        if distributor == TriState.YES or partner_signal == TriState.YES
        else TriState.UNKNOWN
    )
    technical_capability = technical_team

    if any(
        term in text
        for term in (
            "testing company",
            "testing services",
            "testing laboratory",
            "测试公司",
            "测试服务",
            "检测公司",
            "检测服务",
        )
    ):
        company_type = CompanyType.TESTING_COMPANY
    elif transformer_manufacturing == TriState.YES:
        company_type = CompanyType.TRANSFORMER_MANUFACTURER
    elif distributor == TriState.YES:
        company_type = CompanyType.DISTRIBUTOR
    elif any(term in text for term in ("manufacturer", "manufacturing", "制造商", "生产企业")):
        company_type = CompanyType.MANUFACTURER
    elif any(term in text for term in ("service provider", "服务商", "服务公司")):
        company_type = CompanyType.SERVICE_PROVIDER
    elif any(term in text for term in ("contractor", "承包商", "工程公司")):
        company_type = CompanyType.CONTRACTOR
    elif any(term in text for term in ("software company", "technology company", "软件公司", "科技公司")):
        company_type = CompanyType.TECHNOLOGY_COMPANY
    elif any(term in text for term in ("importer", "exporter", "进出口", "进口商", "出口商")):
        company_type = CompanyType.IMPORTER_EXPORTER
    else:
        company_type = CompanyType.UNKNOWN

    facts = ExtractedFacts(
        company_type=company_type,
        business_relevance=business_relevance,
        purchase_intent=purchase_intent,
        business_scale=business_scale,
        technical_capability=technical_capability,
        distributor_or_partner=distributor_or_partner,
        contactability=contactability,
        decision_maker_signal=decision_maker,
        international_business=international_business,
        domestic_business=domestic_business,
        competitor_signal=TriState.UNKNOWN,
        unrelated_signal=TriState.UNKNOWN,
        high_voltage_testing=high_voltage,
        relay_testing=relay,
        transformer_testing=transformer_testing,
        transformer_manufacturing=transformer_manufacturing,
        distributor=distributor,
        utility_clients=utility_clients,
        technical_team=technical_team,
    )
    positive_fields = {
        "company_type": company_type != CompanyType.UNKNOWN,
        "business_relevance": business_relevance == TriState.YES,
        "purchase_intent": purchase_intent == TriState.YES,
        "business_scale": business_scale == TriState.YES,
        "technical_capability": technical_capability == TriState.YES,
        "distributor_or_partner": distributor_or_partner == TriState.YES,
        "contactability": contactability == TriState.YES,
        "decision_maker_signal": decision_maker == TriState.YES,
        "international_business": international_business == TriState.YES,
        "domestic_business": domestic_business == TriState.YES,
        "high_voltage_testing": high_voltage == TriState.YES,
        "relay_testing": relay == TriState.YES,
        "transformer_testing": transformer_testing == TriState.YES,
        "transformer_manufacturing": transformer_manufacturing == TriState.YES,
        "distributor": distributor == TriState.YES,
        "utility_clients": utility_clients == TriState.YES,
        "technical_team": technical_team == TriState.YES,
        "international_business": international_business == TriState.YES,
        "domestic_business": domestic_business == TriState.YES,
        "purchase_intent": purchase_intent == TriState.YES,
        "business_scale": business_scale == TriState.YES,
        "contactability": contactability == TriState.YES,
        "decision_maker_signal": decision_maker == TriState.YES,
    }
    evidence = []
    if quote:
        for field, present in positive_fields.items():
            if present:
                evidence.append({"field": field, "quote": quote, "source": source})

    return LeadAnalysis(
        summary=f"已完成{MARKET_LABELS[normalize_market(market)]}的本地模拟分析：{lead.company_name}。",
        facts=facts,
        potential_needs=[
            item
            for condition, item in (
                (purchase_intent == TriState.YES, "确认采购范围、预算和时间表"),
                (business_relevance == TriState.YES, "核对产品或服务与客户业务的匹配度"),
                (technical_capability == TriState.YES, "了解客户的技术需求与实施能力"),
            )
            if condition
        ],
        recommended_contact_roles=["技术负责人", "总经理/董事总经理"],
        outreach_angle="建议询问当前测试流程、设备需求和项目计划。",
        confidence=75 if quote else 20,
        data_sufficiency=DataSufficiency.MEDIUM if quote else DataSufficiency.LOW,
        evidence=evidence,
        caveats=["当前为本地模拟模式（Mock），结果是固定规则生成，不会调用在线模型接口。"],
    )


def _client(settings: LLMSettings):
    try:
        from openai import OpenAI
    except ImportError as exc:  # pragma: no cover
        raise LLMError("未安装在线模型接口依赖。请先安装项目依赖后再使用在线模型接口（API）。") from exc

    kwargs: dict[str, object] = {"api_key": settings.api_key, "timeout": 60.0, "max_retries": 0}
    if settings.base_url.strip():
        kwargs["base_url"] = settings.base_url.strip()
    return OpenAI(**kwargs)


def _validation_details(exc: Exception) -> str:
    errors = getattr(exc, "errors", lambda: [])()
    details = []
    for item in errors[:5]:
        location = ".".join(str(part) for part in item.get("loc", ())) or "根字段"
        details.append(f"{location}: {item.get('msg', '字段格式错误')}")
    return "; ".join(details)[:260]


def _clean_json_content(content: object) -> str:
    text = str(content).strip()
    if text.startswith("```"):
        lines = text.splitlines()
        if lines and lines[0].lstrip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    if not text.startswith("{"):
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            text = text[start : end + 1]
    return text


def _repair_text_fields(payload: object) -> dict:
    if not isinstance(payload, dict):
        raise LLMError("模型返回的 JSON 不是对象格式，无法读取 LeadScout 分析字段。")

    repaired = dict(payload)
    defaults = {
        "summary": "当前资料不足，暂无法形成可靠的客户判断。",
        "outreach_angle": "建议先补充公司简介、产品服务和采购需求，再确定具体开发切入点。",
    }
    repaired_fields = []
    for field, default in defaults.items():
        value = repaired.get(field)
        if not isinstance(value, str) or not value.strip():
            repaired[field] = default
            repaired_fields.append(field)

    if repaired_fields:
        caveats = repaired.get("caveats")
        caveats = list(caveats) if isinstance(caveats, list) else []
        caveats.append("模型未返回完整的建议文本，系统已使用保守的通用提示。")
        repaired["caveats"] = caveats
    return repaired


def _parse_completion(completion) -> LeadAnalysis:
    message = completion.choices[0].message
    parsed = getattr(message, "parsed", None)
    if parsed is not None:
        try:
            return parsed if isinstance(parsed, LeadAnalysis) else LeadAnalysis.model_validate(parsed)
        except Exception as exc:
            detail = _validation_details(exc)
            raise LLMError(f"模型返回的结构化字段不完整或格式不匹配：{detail}") from exc
    content = getattr(message, "content", None)
    if not content:
        raise LLMError("模型服务返回了空的分析结果，请重试一次；如果持续出现，请检查模型输出格式。")
    cleaned_content = _clean_json_content(content)
    try:
        payload = _repair_text_fields(json.loads(cleaned_content))
    except json.JSONDecodeError as exc:
        raise LLMError("模型返回的内容不是有效 JSON，请重试一次或切换返回格式。") from exc
    try:
        return LeadAnalysis.model_validate(payload)
    except Exception as exc:
        detail = _validation_details(exc)
        raise LLMError(f"模型已返回 JSON，但字段不符合 LeadScout 要求：{detail}") from exc


def _request_json(client, settings: LLMSettings, messages):
    request_kwargs: dict[str, object] = {
        "model": settings.model,
        "messages": messages,
        "response_format": {"type": "json_object"},
    }
    if _is_deepseek(settings):
        # DeepSeek's reasoning is unnecessary for this short extraction task and
        # can make a JSON-only response less predictable.
        request_kwargs["max_tokens"] = 1800
        request_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    return client.chat.completions.create(**request_kwargs)


def analyze_lead(lead: LeadInput, settings: LLMSettings, mock: bool = False) -> LeadAnalysis:
    if mock:
        return mock_analysis(lead, market=settings.market)
    if not settings.api_key.strip():
        raise LLMError("在线模型接口（API）模式需要接口密钥（API Key），或关闭该模式使用本地模拟模式（Mock）。")
    if not settings.model.strip():
        raise LLMError("在线模型接口（API）模式需要填写模型名称。")

    client = _client(settings)
    selected_market = normalize_market(settings.market)
    messages = build_messages(lead, selected_market)

    # DeepSeek supports JSON Output, but not the OpenAI SDK's Pydantic
    # `chat.completions.parse` request shape. Use its compatible JSON mode
    # directly instead of spending a request on an incompatible format.
    if _is_deepseek(settings):
        try:
            return _parse_completion(_request_json(client, settings, messages))
        except Exception as exc:
            if isinstance(exc, LLMError):
                raise
            raise LLMError(_provider_error_message(exc, settings)) from exc

    if settings.mode in {"auto", "structured"}:
        try:
            completion = client.chat.completions.parse(
                model=settings.model,
                messages=messages,
                response_format=LeadAnalysis,
            )
            return _parse_completion(completion)
        except Exception as exc:
            if settings.mode == "structured":
                raise LLMError(_provider_error_message(exc, settings)) from exc

    try:
        completion = _request_json(client, settings, messages)
        return _parse_completion(completion)
    except Exception as exc:
        if isinstance(exc, LLMError):
            raise
        raise LLMError(_provider_error_message(exc, settings)) from exc
