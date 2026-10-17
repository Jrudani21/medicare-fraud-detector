# AGENTS.md - medicare-fraud-detector

Streamlit app that flags Medicare providers billing from a US and a foreign address at once, on a synthetic dataset. See `README.md` for usage and `PRD.md` for the purpose.

## Run

- `pip install -r requirements.txt`, then `streamlit run app.py`.
- Regenerate the synthetic data with `python data/generate.py`.

## Test

- No automated tests exist. See `TESTING.md`.

## Conventions

- The bundled `data/claims.csv` is synthetic; never replace it with real claims data.
- Follow `CODE_STYLE.md`; plain hyphens in text, no em-dashes.
- Read `ARCHITECTURE.md` and `SECURITY.md` before changing how data flows or what is stored.
- Never commit secrets, API keys or real personal data.

## Verified against

`README.md`, `requirements.txt`, `app.py`, `data/generate.py`.
