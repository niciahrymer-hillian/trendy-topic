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
