# SECURITY - medicare-fraud-detector

## Trust Boundaries
- The application processes local CSV and SQLite data; no external APIs or user-submitted code are involved.
- The trust boundary is the local filesystem where the data and application reside.
- No authentication or authorization is required as the tool is intended for local, trusted use.

## Controls
- **Secrets Handling**: No secrets, API keys, or credentials are used or stored in the repository.
- **Input Handling**: 
    - The application reads structured CSV data with a fixed schema; no arbitrary SQL or code execution from input.
    - SQL queries are static files; user input (via Streamlit widgets) is used for filtering and display only, not for query construction.
- **Data Protection**: 
    - The SQLite database is file-based and not encrypted; rely on filesystem permissions for protection.
    - No sensitive personal data is included in the synthetic dataset; real CMS data is public but contains provider identifiers (NPI) which are considered public information.
- **Dependencies**: 
    - Python packages are pinned via requirements.txt with minimum versions to reduce risk of known vulnerabilities.
    - No direct internet access from the application; all processing is offline.

## Verified against
- app.py
- data/generate.py
- queries/01_schema.sql
- requirements.txt