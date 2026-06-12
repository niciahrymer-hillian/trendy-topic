# Ethics and Privacy Policy

This project analyzes AI conversation data for aggregate research insights. The dashboard should avoid exposing sensitive raw user content.

## Rules

1. Do not display hashed IP addresses, request headers, or other tracking metadata.
2. Do not send raw sensitive conversations to translation, LLM, or voice APIs.
3. Use cleaned summaries for dashboards and AI voice briefings.
4. Exclude toxic, unsafe, or highly personal conversations from public views.
5. Redact emails, phone numbers, addresses, account numbers, and names where possible.
6. Prefer aggregate metrics over raw conversation display.
7. Make data limitations visible in the dashboard.
8. Keep large source data out of GitHub.
9. Store API keys in environment variables or Streamlit secrets.
10. Clearly label AI-generated insights as generated summaries, not absolute facts.

> Note on rule 9: this project now uses a FastAPI backend with a React frontend, so
> API keys live in a git-ignored `.env` file (see `.env.example`). The Streamlit
> secrets option still applies to any Streamlit-based view.

## What data we use

- **Default source:** the safe WildChat sample pack in `data/wildchat_country_csv_pack/`
  — 480 curated rows derived from [`allenai/WildChat-4.8M`](https://huggingface.co/datasets/allenai/WildChat-4.8M).
  These rows ship with `privacy_level = safe_preview_no_hash_no_headers`: **no hashed
  IPs, no request headers, only cleaned prompt summaries**.
- **Full dataset (scale path):** the real WildChat corpus is ~3.2M conversations and
  *does* include `hashed_ip`, request/User-Agent headers, and raw conversation text.
  It must never be analyzed or displayed without first applying the redaction rules below.

## Translation, LLM & voice safety gate

Before any text is sent to an external provider:

1. The row must pass the safe filter (not toxic).
2. The text must be a **cleaned summary or aggregated insight** — never raw conversation
   turns or any field that could contain PII.
3. Generated output (translations, AI topics, voice scripts) is treated as derived and
   non-authoritative, and is labeled as such in the UI.

Raw individual conversation text is never a valid input to these APIs.

## Where these rules are enforced in code

- **Safe filter:** `src/data_access.py` sets `safe_for_dashboard = ~toxic`; every API
  endpoint and page reads through `safe_conversations()`, so unsafe rows cannot leak.
- **Aggregates only:** the FastAPI layer (`api/main.py`) returns counts, shares, and
  cleaned sample prompts — not raw conversation turns.
- **Voice/translation:** `src/voice_briefing.py` builds scripts from aggregated metrics
  only; translation operates on safe summaries.
- **Raw data out of git:** `.gitignore` excludes `data/raw`, `*.parquet`, `*.jsonl`, and DB files.

## Responsibilities for the full-dataset path

Anyone enabling the real Hugging Face export must, **before** loading into the app or DB:

- Drop `hashed_ip` and all header/User-Agent fields at ingestion.
- Run a PII redaction pass over conversation text (rule 5 above).
- Exclude rows flagged toxic/unsafe from any public surface.
- Keep raw files in `data/raw/` (git-ignored) and never commit them.

## License & attribution

This project analyzes data derived from `allenai/WildChat-4.8M`. Respect the source
dataset's license and terms, and attribute it in any published report or demo.

## Review

Revisit this policy whenever a new external API, data field, or public surface is added.
If a change would expose raw or sensitive data, it does not ship until this policy is
updated and the safeguards are in place.
