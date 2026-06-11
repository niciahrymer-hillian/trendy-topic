WildChat country CSV starter pack
=================================

This folder contains separate CSV files for: United States, Canada, Great Britain/United Kingdom, China, Russia, France, Brazil, and Japan.

Important honesty note:
These CSVs are safe starter/sample files using WildChat-style fields. They are NOT a full export of real WildChat conversations. The full allenai/WildChat-4.8M dataset is very large, stored as many Parquet files, and includes sensitive metadata fields such as hashed_ip and request headers.

What is included:
- 8 country CSVs, 60 sample rows each
- 1 combined CSV with all requested countries
- 1 file index CSV
- 1 Python script to export real filtered country CSVs from Hugging Face on a machine with internet access

Source dataset:
https://huggingface.co/datasets/allenai/WildChat-4.8M

Recommended privacy practice:
For public dashboards, remove hashed_ip, header/user-agent, raw conversation text that contains personal information, and any rows marked redacted/toxic unless your project specifically needs those fields and has approval.
