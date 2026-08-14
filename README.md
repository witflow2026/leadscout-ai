# LeadScout AI

LeadScout AI is an early-stage open-source, general-purpose B2B lead analysis
assistant. V0.2 accepts one manually entered lead, extracts general company
facts and evidence with an optional LLM, and calculates a deterministic
rule-based score.

## Current scope

- One lead at a time
- Manual company information and pasted public text
- Optional offer, target-customer, or business context in the notes field
- Streamlit local web UI with a light custom theme
- Mock mode without an API key
- OpenAI-compatible live analysis
- Evidence verification against supplied text
- Rule-based A/B/C/D scoring
- General B2B and international B2B profiles
- JSON report download

V0.2 does not crawl websites, log in to Facebook or LinkedIn, discover emails,
process CSV files, store a database, or provide user accounts.

## Run on Windows

Use Python 3.10 or newer. From PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

The browser opens a local page, normally `http://localhost:8501`.

## Mock mode

Mock mode is enabled by default and does not call an AI provider. Enter a
company name and sample public text, then press **开始分析**.

## Market modes

Choose a market mode in the sidebar:

- **通用 B2B**: the default profile for domestic or international companies;
  it focuses on business relevance, purchase intent, company scale,
  contactability, and decision-maker signals without assuming a geography.
- **国际 B2B（跨境）**: adds emphasis on export/import, overseas projects,
  international sourcing, distributors, and cross-border purchasing.

The target market/region field is optional in general mode. In international
mode, country or region is still optional, but it helps interpret cross-border
context. The former domestic profile is not shown as a separate option because
its current rules overlap substantially with general B2B; the old domestic key
remains supported as a compatibility alias.

## Live API mode

Enable **调用在线模型接口（API）** in the sidebar and provide an API Key and
model name. An optional Base URL supports an OpenAI-compatible provider. The
model output is validated against the LeadScout schema, with JSON fallback for
providers that do not support OpenAI-style structured parsing.

The API key is never included in the downloaded report.

## Private scoring rules

The public `config.example.yaml` is a neutral example profile. Copy it to
`config.local.yaml` for private weights or exclusions. That file is ignored by
Git and should not contain customer lists in a public checkout. Use
`profiles.international` or `profiles.general` for profile-specific overrides.
The legacy `profiles.domestic` section remains supported for older local files.

## Test

```powershell
python -m pytest -q
```

## Privacy and limitations

Any text sent in live mode is sent to the selected provider. Do not paste
confidential customer information unless your company and provider policies
allow it. LeadScout is an assistive research tool; verify evidence yourself
before contacting a prospect.

## Roadmap

- V0.3: controlled website crawling with source URLs, contact-role analysis,
  and CSV batch analysis
- V0.4: editable ICP profiles, score history, and optional local persistence
- V0.5: CRM export and time-sensitive buying signals

## License

MIT. See [LICENSE](LICENSE).
