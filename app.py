"""Streamlit entry point for LeadScout AI V0.2.1."""

from __future__ import annotations

import json
import os
from html import escape
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

from leadscout.config import load_config
from leadscout.evidence import verify_evidence
from leadscout.llm import LLMError, LLMSettings, analyze_lead, check_connection
from leadscout.market import MARKET_LABELS, MARKET_UI_OPTIONS
from leadscout.report import build_report
from leadscout.schemas import LeadInput
from leadscout.scoring import score_lead

load_dotenv()

APP_VERSION = "0.2.1"
MAX_TEXT_LENGTH = 12_000

st.set_page_config(page_title="LeadScout AI", page_icon=":material/ads_click:", layout="wide")
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');

    :root {
      --ls-primary: #1e40af;
      --ls-primary-dark: #1e3a8a;
      --ls-secondary: #3b82f6;
      --ls-accent: #d97706;
      --ls-bg: #f8fafc;
      --ls-card: #ffffff;
      --ls-muted: #e9eef6;
      --ls-border: #dbeafe;
      --ls-text: #172554;
      --ls-subtle: #475569;
      --ls-shadow: 0 12px 30px rgba(30, 64, 175, 0.08);
    }

    .stApp { background: var(--ls-bg); color: var(--ls-text); }
    .block-container { max-width: 1240px; padding-top: 3rem; padding-bottom: 4rem; }
    h1, h2, h3, h4 { font-family: 'Fira Sans', system-ui, sans-serif; color: var(--ls-text); letter-spacing: -0.02em; }
    p, label, [data-testid="stCaptionContainer"], [data-testid="stMarkdownContainer"] { font-family: 'Fira Sans', system-ui, sans-serif; }
    [data-testid="stSidebar"] { background: #eef4ff; border-right: 1px solid var(--ls-border); }
    [data-testid="stSidebar"] > div:first-child { padding-top: 2rem; }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color: var(--ls-subtle); }

    .ls-hero { margin: 0 0 2rem; }
    .ls-brand-row { display: flex; align-items: center; gap: 0.9rem; }
    .ls-mark { width: 42px; height: 42px; border: 3px solid var(--ls-primary-dark); border-radius: 50%; position: relative; background: #fff; box-shadow: 0 4px 12px rgba(30,64,175,.16); }
    .ls-mark::before { content: ''; position: absolute; inset: 6px; border: 3px solid var(--ls-secondary); border-radius: 50%; }
    .ls-mark::after { content: ''; position: absolute; width: 7px; height: 7px; top: 14px; left: 14px; border-radius: 50%; background: var(--ls-accent); box-shadow: 8px -8px 0 -1px var(--ls-accent); }
    .ls-eyebrow, .ls-section-kicker, .ls-sidebar-kicker { color: var(--ls-primary); font-family: 'Fira Code', monospace; font-size: 0.72rem; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; }
    .ls-brand-title { margin: 0; color: var(--ls-primary-dark); font-size: clamp(2rem, 4vw, 2.85rem); line-height: 1; font-weight: 700; }
    .ls-hero-copy { max-width: 760px; margin: 1rem 0 0 3.35rem; }
    .ls-hero-copy p { margin: 0; color: var(--ls-subtle); font-size: 1.05rem; line-height: 1.65; }
    .ls-trust-row { display: flex; flex-wrap: wrap; gap: 0.65rem; margin-top: 0.95rem; }
    .ls-trust-chip { display: inline-flex; align-items: center; gap: 0.4rem; border: 1px solid var(--ls-border); border-radius: 999px; background: #fff; color: var(--ls-subtle); padding: 0.35rem 0.7rem; font-size: 0.78rem; }
    .ls-status-dot { width: 7px; height: 7px; border-radius: 50%; background: #16a34a; box-shadow: 0 0 0 3px #dcfce7; }

    .ls-sidebar-title { color: var(--ls-primary-dark); font-family: 'Fira Sans', system-ui, sans-serif; font-size: 1.45rem; font-weight: 700; margin: 0.2rem 0 0.45rem; }
    .ls-sidebar-note { border: 1px solid #c7d7f5; border-radius: 12px; background: rgba(255,255,255,.68); padding: 0.8rem 0.9rem; margin-top: 1rem; color: var(--ls-subtle); font-size: 0.8rem; line-height: 1.55; }
    .ls-sidebar-note strong { color: var(--ls-primary-dark); }
    .ls-group-label { margin: 1.2rem 0 0.35rem; color: var(--ls-primary-dark); font-family: 'Fira Code', monospace; font-size: 0.7rem; font-weight: 700; letter-spacing: .07em; text-transform: uppercase; }

    div[data-testid="stForm"] { background: var(--ls-card); border: 1px solid var(--ls-border); border-radius: 20px; padding: 1.25rem 1.35rem 1.35rem; box-shadow: var(--ls-shadow); }
    div[data-testid="stForm"] [data-testid="stMarkdownContainer"] p { color: var(--ls-subtle); }
    [data-testid="stMetric"] { min-height: 112px; background: #fff; border: 1px solid var(--ls-border); border-radius: 14px; padding: 15px 16px; box-shadow: 0 4px 14px rgba(30,64,175,.05); }
    [data-testid="stMetricLabel"] { color: var(--ls-subtle); font-size: .78rem; font-weight: 600; }
    [data-testid="stMetricValue"] { color: var(--ls-primary-dark); font-family: 'Fira Code', monospace; font-size: 1.8rem; }
    [data-testid="stMetricDelta"] { font-family: 'Fira Code', monospace; }
    [data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea { border-radius: 10px; border-color: #cbd5e1; background: #fff; transition: border-color 180ms ease, box-shadow 180ms ease; }
    [data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus { border-color: var(--ls-primary); box-shadow: 0 0 0 3px rgba(30,64,175,.14); }
    [data-testid="stFormSubmitButton"] button, [data-testid="stDownloadButton"] button { min-height: 2.8rem; border-radius: 10px; font-weight: 700; transition: background 180ms ease, border-color 180ms ease, box-shadow 180ms ease; cursor: pointer; }
    [data-testid="stFormSubmitButton"] button { background: var(--ls-primary); border-color: var(--ls-primary); color: #fff !important; }
    [data-testid="stFormSubmitButton"] button p, [data-testid="stFormSubmitButton"] button span { color: #fff !important; }
    [data-testid="stFormSubmitButton"] button:hover { background: var(--ls-primary-dark); border-color: var(--ls-primary-dark); box-shadow: 0 6px 16px rgba(30,64,175,.2); }
    [data-testid="stDownloadButton"] button { color: var(--ls-primary); border-color: #b8cbed; background: #fff; }
    [data-testid="stDownloadButton"] button:hover { border-color: var(--ls-primary); background: #eff6ff; }
    button:focus-visible, input:focus-visible, textarea:focus-visible { outline: 3px solid rgba(217,119,6,.48); outline-offset: 2px; }
    [data-testid="stDataFrame"] { border: 1px solid var(--ls-border); border-radius: 12px; overflow: hidden; }
    [data-testid="stAlert"] { border-radius: 12px; }
    .ls-result-header { display: flex; align-items: flex-start; justify-content: space-between; gap: 1rem; margin-bottom: 1.1rem; }
    .ls-result-title { margin: .12rem 0 .25rem; color: var(--ls-primary-dark); font-size: 1.55rem; font-weight: 700; }
    .ls-result-meta { color: var(--ls-subtle); font-size: .88rem; }
    .ls-mode-pill { flex: 0 0 auto; border: 1px solid #fed7aa; border-radius: 999px; background: #fff7ed; color: #9a3412; padding: .42rem .7rem; font-size: .76rem; font-weight: 700; }
    .ls-section-note { color: var(--ls-subtle); font-size: .86rem; margin-top: -.35rem; }
    .ls-summary-label { color: var(--ls-primary); font-family: 'Fira Code', monospace; font-size: .72rem; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; }
    .ls-summary { border-left: 3px solid var(--ls-accent); background: #fffaf2; border-radius: 0 10px 10px 0; padding: .75rem .9rem; color: #422006; line-height: 1.65; }
    .ls-footer-note { color: var(--ls-subtle); font-size: .78rem; margin-top: .75rem; }
    .ls-fact-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: .65rem; margin: .55rem 0 .8rem; }
    .ls-fact-card { min-height: 72px; border: 1px solid var(--ls-border); border-radius: 12px; background: #fff; padding: .7rem .8rem; }
    .ls-fact-label { color: var(--ls-subtle); font-size: .78rem; line-height: 1.35; }
    .ls-fact-value { color: var(--ls-primary-dark); font-size: .98rem; font-weight: 700; line-height: 1.45; margin-top: .25rem; }
    .ls-fact-status { color: var(--ls-subtle); font-size: .76rem; margin-top: .18rem; }
    .ls-fact-card--yes { border-left: 3px solid #16a34a; }
    .ls-fact-card--no { border-left: 3px solid #94a3b8; }
    .ls-fact-card--unknown { border-left: 3px solid #f59e0b; background: #fffbeb; }
    .ls-evidence-card { border: 1px solid var(--ls-border); border-radius: 12px; background: #fff; padding: .75rem .85rem; margin: .55rem 0; }
    .ls-evidence-card--verified { border-left: 3px solid #16a34a; }
    .ls-evidence-card--unverified { border-left: 3px solid #f59e0b; background: #fffbeb; }
    .ls-evidence-label { color: var(--ls-primary-dark); font-weight: 700; font-size: .9rem; }
    .ls-evidence-status { font-size: .78rem; font-weight: 700; margin-top: .2rem; }
    .ls-evidence-status--verified { color: #166534; }
    .ls-evidence-status--unverified { color: #92400e; }
    .ls-evidence-quote { color: var(--ls-text); line-height: 1.55; margin-top: .35rem; }
    @media (max-width: 800px) {
      .block-container { padding-top: 1.25rem; padding-left: 1rem; padding-right: 1rem; }
      .ls-hero-copy { margin-left: 0; }
      .ls-hero { margin-bottom: 1.35rem; }
      .ls-result-header { flex-direction: column; }
      div[data-testid="stForm"] { padding: 1rem; }
      .ls-fact-grid { grid-template-columns: 1fr; }
    }
    @media (prefers-reduced-motion: reduce) {
      *, *::before, *::after { animation-duration: .01ms !important; animation-iteration-count: 1 !important; scroll-behavior: auto !important; transition-duration: .01ms !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def _env_bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).strip().casefold() in {"1", "true", "yes", "on"}


def _config_path() -> Path:
    local = Path("config.local.yaml")
    return local if local.exists() else Path("config.example.yaml")


OUTPUT_MODE_LABELS = {
    "auto": "自动判断（自动选择兼容方式）",
    "structured": "结构化输出（固定字段格式）",
    "json": "JSON 数据（程序可读取的标准格式）",
}

MODEL_PRESETS = {
    "deepseek-v4-flash": "DeepSeek · deepseek-v4-flash（速度优先）",
    "deepseek-v4-pro": "DeepSeek · deepseek-v4-pro（能力优先）",
    "gpt-5-mini": "OpenAI · gpt-5-mini（经济型）",
    "gpt-5": "OpenAI · gpt-5（通用）",
    "__custom__": "自定义模型名称（手动输入）",
}
DEFAULT_MODEL = "deepseek-v4-flash"

FACT_LABELS = {
    "company_type": "公司类型",
    "business_relevance": "业务相关性",
    "purchase_intent": "采购意向",
    "business_scale": "企业规模",
    "technical_capability": "技术/实施能力",
    "distributor_or_partner": "渠道/合作伙伴潜力",
    "contactability": "可联系性",
    "decision_maker_signal": "决策人信号",
    "competitor_signal": "竞争对手信号",
    "unrelated_signal": "行业相关性",
    "international_business": "国际业务",
    "domestic_business": "国内业务",
}

PRIMARY_FACT_FIELDS = (
    "company_type",
    "business_relevance",
    "purchase_intent",
    "business_scale",
    "technical_capability",
    "distributor_or_partner",
    "contactability",
    "decision_maker_signal",
)

COMPANY_TYPE_LABELS = {
    "manufacturer": "制造商",
    "service_provider": "服务商",
    "contractor": "承包商/工程公司",
    "technology_company": "科技/软件公司",
    "importer_exporter": "进出口商",
    "retailer": "零售/经销企业",
    "testing_company": "测试公司",
    "transformer_manufacturer": "变压器制造商",
    "utility_contractor": "电力承包商",
    "distributor": "经销商/代理商",
    "engineering_consultant": "工程咨询公司",
    "other": "其他类型",
    "unknown": "资料不足",
}

EVIDENCE_FIELD_LABELS = {
    **FACT_LABELS,
    "high_voltage_testing": "高压测试",
    "relay_testing": "继电保护测试",
    "transformer_testing": "变压器测试",
    "transformer_manufacturing": "变压器制造",
    "distributor": "经销商/代理商",
    "utility_clients": "电力公司客户",
    "technical_team": "技术团队",
}


def _fact_value(value: object) -> str:
    return str(getattr(value, "value", value)).strip().casefold()


def _fact_display_value(field: str, value: object) -> tuple[str, str, str]:
    normalized = _fact_value(value)
    if field == "company_type":
        if normalized == "unknown":
            return COMPANY_TYPE_LABELS["unknown"], "需要补充资料", "unknown"
        return COMPANY_TYPE_LABELS.get(normalized, "其他类型"), "有原文依据", "yes"
    if normalized == "yes":
        return "已确认", "有原文依据", "yes"
    if normalized == "no":
        return "未发现", "当前资料未提供明确依据", "no"
    return "资料不足", "需要补充资料", "unknown"


def _display_fact_overview(facts: dict) -> None:
    rows = []
    for field, label in FACT_LABELS.items():
        value, status, status_class = _fact_display_value(field, facts.get(field, "unknown"))
        rows.append(
            {
                "field": field,
                "label": label,
                "value": value,
                "status": status,
                "status_class": status_class,
            }
        )

    confirmed_count = sum(row["status_class"] == "yes" for row in rows)
    not_found_count = sum(row["status_class"] == "no" for row in rows)
    unknown_count = sum(row["status_class"] == "unknown" for row in rows)
    st.caption(
        f"已确认 {confirmed_count} 项 · 未发现 {not_found_count} 项 · 资料不足 {unknown_count} 项"
    )
    if confirmed_count == 0:
        st.info(
            "当前资料不足，仅凭公司名称无法判断客户类型和采购需求。建议补充公司简介、产品服务或采购相关描述。"
        )

    cards = []
    for row in rows:
        if row["field"] not in PRIMARY_FACT_FIELDS:
            continue
        cards.append(
            "<div class='ls-fact-card ls-fact-card--{status}'>"
            "<div class='ls-fact-label'>{label}</div>"
            "<div class='ls-fact-value'>{value}</div>"
            "<div class='ls-fact-status'>{status_text}</div>"
            "</div>".format(
                status=row["status_class"],
                label=escape(row["label"]),
                value=escape(row["value"]),
                status_text=escape(row["status"]),
            )
        )
    st.markdown("<div class='ls-fact-grid'>" + "".join(cards) + "</div>", unsafe_allow_html=True)

    with st.expander("查看全部事实字段"):
        st.dataframe(
            [{"事实": row["label"], "判断": row["value"], "状态": row["status"]} for row in rows],
            width="stretch",
            hide_index=True,
        )
    with st.expander("查看原始 JSON（开发调试）"):
        st.json(facts)


def _display_evidence_verification(rows: list[dict]) -> None:
    if not rows:
        st.info("模型没有返回可核验的原文引用。当前结果不会因为没有引用而自动加分。")
        return

    verified_count = sum(bool(row.get("verified")) for row in rows)
    unverified_count = len(rows) - verified_count
    st.caption(f"已找到原文依据 {verified_count} 条 · 未找到原文依据 {unverified_count} 条")

    for row in rows:
        verified = bool(row.get("verified"))
        status_class = "verified" if verified else "unverified"
        status_text = "已找到原文依据" if verified else "未找到原文依据，已排除评分"
        source_label = {"notes": "补充备注", "source_text": "公开资料"}.get(
            str(row.get("source", "")), "输入资料"
        )
        field_label = EVIDENCE_FIELD_LABELS.get(str(row.get("field", "")), "待核验事项")
        quote = escape(str(row.get("quote", ""))) or "未提供引用内容"
        st.markdown(
            "<div class='ls-evidence-card ls-evidence-card--{status}'>"
            "<div class='ls-evidence-label'>{field}</div>"
            "<div class='ls-evidence-status ls-evidence-status--{status}'>{status_text}</div>"
            "<div class='ls-evidence-quote'>“{quote}”</div>"
            "</div>".format(
                status=status_class,
                field=escape(field_label),
                status_text=escape(f"{status_text} · 来源：{source_label}"),
                quote=quote,
            ),
            unsafe_allow_html=True,
        )

    with st.expander("查看技术核验表"):
        st.dataframe(
            [
                {
                    "判断事项": EVIDENCE_FIELD_LABELS.get(str(row.get("field", "")), "待核验事项"),
                    "原文引用": row.get("quote", ""),
                    "来源": {"notes": "补充备注", "source_text": "公开资料"}.get(
                        str(row.get("source", "")), "输入资料"
                    ),
                    "核验结果": "已找到原文依据" if row.get("verified") else "未找到原文依据",
                    "评分处理": "允许作为评分依据" if row.get("verified") else "不纳入评分",
                }
                for row in rows
            ],
            width="stretch",
            hide_index=True,
        )


def _display_report(report: dict) -> None:
    analysis = report["analysis"]
    score = report["score"]

    with st.container(border=True):
        st.markdown(
            f'<div class="ls-result-header"><div><div class="ls-section-kicker">分析结果</div><div class="ls-result-title">分析结果</div><div class="ls-result-meta">基于当前输入资料生成，建议结合证据核验后再联系客户。</div></div><div class="ls-mode-pill">{report.get("market_label", report.get("market", "通用企业客户"))}</div></div>',
            unsafe_allow_html=True,
        )
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("客户评分", score["total"])
        col2.metric("客户等级（A优先，D较低）", score["grade"])
        col3.metric("证据覆盖率", f'{score["evidence_coverage"]}%')
        col4.metric("模型判断置信度", f'{analysis["confidence"]}%')

        if score["review_required"]:
            st.warning("该客户需要人工复核后再联系。")
        else:
            st.success("证据和数据质量达到当前规则的自动判断标准。")
        st.markdown('<div class="ls-summary-label">结论摘要</div>', unsafe_allow_html=True)
        st.info(analysis["summary"])

    st.markdown("#### 评分明细")
    st.markdown('<div class="ls-section-note">规则评分独立于模型输出，便于复核每一项加分或扣分。</div>', unsafe_allow_html=True)
    if score["breakdown"]:
        st.dataframe(score["breakdown"], width="stretch", hide_index=True)
    else:
        st.info("没有足够的已验证事实产生加分或扣分。")

    if score["warnings"]:
        st.markdown("#### 注意事项")
        for warning in score["warnings"]:
            st.write(f"- {warning}")

    left, right = st.columns(2)
    with left:
        st.markdown("#### 提取事实")
        _display_fact_overview(analysis["facts"])
        st.markdown("#### 潜在需求")
        for item in analysis["potential_needs"] or ["暂无明确需求"]:
            st.write(f"- {item}")
    with right:
        st.markdown("#### 推荐联系人职位")
        for item in analysis["recommended_contact_roles"] or ["暂无明确职位"]:
            st.write(f"- {item}")
        st.markdown("#### 开发切入点")
        st.write(analysis["outreach_angle"])

    st.markdown("#### 判断依据")
    st.markdown(
        '<div class="ls-section-note">只把能在你提供的资料中找到原文依据的判断用于评分；未找到依据的内容会保留提示，但不会计入评分。</div>',
        unsafe_allow_html=True,
    )
    _display_evidence_verification(report["evidence_verification"])
    st.download_button(
        "下载报告（JSON 数据）",
        data=json.dumps(report, ensure_ascii=False, indent=2),
        file_name="leadscout-report.json",
        mime="application/json",
    )


st.markdown(
    f'<div class="ls-hero"><div class="ls-brand-row"><div class="ls-mark" aria-hidden="true"></div><div><div class="ls-eyebrow">企业客户分析工具 · 版本 {APP_VERSION}</div><div class="ls-brand-title">LeadScout AI</div></div></div><div class="ls-hero-copy"><p>把公开资料整理成可复核的客户判断，帮助你更快决定“先联系谁、为什么联系、下一步问什么”。</p><div class="ls-trust-row"><span class="ls-trust-chip"><span class="ls-status-dot"></span>证据优先</span><span class="ls-trust-chip">规则评分</span><span class="ls-trust-chip">本地会话</span></div></div></div>',
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="ls-sidebar-kicker">工作区</div>', unsafe_allow_html=True)
    st.markdown('<div class="ls-sidebar-title">分析配置</div>', unsafe_allow_html=True)
    st.caption("先选择分析市场，再决定是否调用真实模型。")
    st.markdown('<div class="ls-group-label">分析范围</div>', unsafe_allow_html=True)
    market = st.selectbox(
        "分析市场",
        options=list(MARKET_UI_OPTIONS),
        format_func=lambda value: MARKET_LABELS[value],
        index=0,
        help="通用 B2B 适用于国内和国际公司；国际 B2B 会额外关注跨境业务、出口、进口和海外渠道信号。",
    )
    st.markdown('<div class="ls-group-label">模型连接</div>', unsafe_allow_html=True)
    mock_default = _env_bool("MOCK_MODE", True)
    live_mode = st.checkbox("调用在线模型接口（API）", value=not mock_default, help="打开后会向你填写的模型服务发送资料；关闭后使用本地模拟模式，不产生接口费用。")
    configured_model = os.getenv("LEADSCOUT_MODEL", "").strip()
    default_model_index = (
        list(MODEL_PRESETS).index(configured_model)
        if configured_model in MODEL_PRESETS
        else list(MODEL_PRESETS).index(DEFAULT_MODEL)
        if not configured_model
        else len(MODEL_PRESETS) - 1
    )
    model_choice = st.selectbox(
        "模型名称",
        options=list(MODEL_PRESETS),
        index=default_model_index,
        format_func=lambda value: MODEL_PRESETS[value],
        help="可以直接选择常用模型，也可以选择“自定义模型名称”填写服务商提供的模型标识。",
    )
    if model_choice == "__custom__":
        model = st.text_input(
            "自定义模型名称",
            value=configured_model,
            placeholder="例如：服务商提供的模型标识",
        )
    else:
        model = model_choice
        st.caption(f"当前模型标识：{model_choice}")
    api_key_default = os.getenv(
        "DEEPSEEK_API_KEY" if model_choice.startswith("deepseek-") else "OPENAI_API_KEY",
        "",
    )
    api_key = st.text_input(
        "接口密钥（API Key）",
        value=api_key_default,
        type="password",
        autocomplete="new-password",
        help="API Key 是调用在线模型服务的授权密钥，只在当前本地会话使用，不会写入报告。",
    )
    configured_base_url = os.getenv("OPENAI_BASE_URL", "").strip()
    base_url_default = configured_base_url or (
        "https://api.deepseek.com" if model_choice.startswith("deepseek-") else ""
    )
    base_url = st.text_input(
        "接口地址（Base URL，可选）",
        value=base_url_default,
        placeholder="官方接口地址可留空",
    )
    mode = st.selectbox(
        "返回格式",
        options=list(OUTPUT_MODE_LABELS),
        format_func=lambda value: OUTPUT_MODE_LABELS[value],
        index=0,
        help="自动判断会优先尝试结构化输出，失败时再尝试 JSON 数据格式。",
    )
    connection_test_requested = st.button(
        "测试模型连接",
        use_container_width=True,
        help="只发送最小测试请求，不会发送客户名称、备注或公开资料。",
    )
    st.caption("测试连接只验证模型、接口地址和 API Key 是否可用。")
    st.markdown(
        f'<div class="ls-sidebar-note"><strong>隐私提示</strong><br>版本 {APP_VERSION} 不会自动访问官网，也不会登录或抓取社交平台。接口密钥（API Key）只在当前本地会话使用。</div>',
        unsafe_allow_html=True,
    )

if connection_test_requested:
    if not live_mode:
        st.sidebar.info("当前关闭了在线模型接口；请先打开“调用在线模型接口（API）”。")
    elif not api_key.strip():
        st.sidebar.error("请先填写接口密钥（API Key）。")
    else:
        connection_settings = LLMSettings(
            api_key=api_key,
            model=model,
            base_url=base_url,
            mode=mode,
            market=market,
        )
        with st.sidebar:
            with st.spinner("正在测试模型连接..."):
                try:
                    st.success(check_connection(connection_settings))
                except LLMError as exc:
                    st.error(str(exc))

config = load_config(_config_path(), market=market)

with st.form("lead_form"):
    st.markdown('<div class="ls-section-kicker">客户资料</div>', unsafe_allow_html=True)
    st.subheader("客户资料")
    st.caption("填写你已经掌握的资料；系统不会自动抓取官网或社交平台。")
    company_col, country_col = st.columns(2)
    with company_col:
        company_name = st.text_input("公司名称 *", placeholder="例如：星河科技有限公司")
    with country_col:
        country_label = "国家/地区（可选）" if market == "international" else "目标市场/地区（可选）"
        country_placeholder = "例如：肯尼亚、阿联酋" if market == "international" else "例如：华东、全国、东南亚"
        country = st.text_input(country_label, placeholder=country_placeholder)
    website = st.text_input("官网地址（仅记录，不抓取）", placeholder="https://example.com")
    notes_col, source_col = st.columns(2)
    with notes_col:
        notes = st.text_area(
            "我方产品/服务与补充备注",
            height=180,
            placeholder="可填写我方产品、服务、目标客户条件、客户来源或已知判断...",
        )
    with source_col:
        source_text = st.text_area(
            "公开资料文本 *",
            height=260,
            placeholder=f"粘贴公司简介、关于我们、产品或服务页面的公开内容。版本 {APP_VERSION} 只分析你粘贴的内容。",
        )
    st.caption(f"单个文本框上限 {MAX_TEXT_LENGTH:,} 个字符 · 建议优先粘贴公司简介、产品服务或采购相关描述。")
    submitted = st.form_submit_button("开始分析  →", type="primary", width="stretch")

if submitted:
    if not company_name.strip():
        st.error("请填写公司名称。")
    elif not notes.strip() and not source_text.strip():
        st.error("请至少填写备注或公开资料文本。")
    elif len(notes) > MAX_TEXT_LENGTH or len(source_text) > MAX_TEXT_LENGTH:
        st.error(f"单个文本框不能超过 {MAX_TEXT_LENGTH:,} 个字符。")
    elif live_mode and not api_key.strip():
        st.error("在线模型接口（API）模式需要填写接口密钥（API Key）；也可以关闭该选项，先使用本地模拟模式（Mock）。")
    else:
        try:
            lead = LeadInput(
                company_name=company_name.strip(),
                country=country.strip(),
                website=website.strip(),
                notes=notes,
                source_text=source_text,
            )
            settings = LLMSettings(
                api_key=api_key,
                model=model,
                base_url=base_url,
                mode=mode,
                market=market,
            )
            with st.spinner("正在分析，请稍候..."):
                analysis = analyze_lead(lead, settings, mock=not live_mode)
                verifications = verify_evidence(analysis, lead)
                score = score_lead(analysis, config, verifications)
                report = build_report(
                    lead,
                    analysis,
                    score,
                    verifications,
                    provider="mock" if not live_mode else (base_url or "openai"),
                    model=model,
                    market=market,
                )
            st.session_state["report"] = report
        except (ValueError, LLMError) as exc:
            st.error(str(exc))
        except Exception:
            st.error("分析失败。请检查配置、输入内容和运行日志。")

if "report" in st.session_state:
    _display_report(st.session_state["report"])
