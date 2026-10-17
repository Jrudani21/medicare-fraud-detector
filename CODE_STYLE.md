# CODE_STYLE - medicare-fraud-detector

## Overview
The codebase follows a consistent Python style with 4-space indentation, snake_case for variables and functions, and UPPER_SNAKE_CASE for constants.

## Formatting
- Indentation: 4 spaces.
- Line length: No strict limit, but lines are kept readable (typically under 100 characters).
- String quotes: Double quotes are used predominantly, with single quotes used for SQL strings and dictionary keys when necessary.
- Blank lines: Used to separate logical sections in functions and between top-level definitions.

## Naming
- Variables and functions: snake_case.
- Constants: UPPER_SNAKE_CASE (e.g., COUNTRY_NAMES, HCPCS).
- Classes: Not present in the current codebase.

## Documentation
- Module docstrings are present in both main Python files.
- Function docstrings are present in data/generate.py but not in app.py (which is a Streamlit script).
- Inline comments are used to explain non-obvious sections.

## Imports
- Standard library imports first, then third-party, then local (if any). In app.py: streamlit, pandas, sqlite3, plotly.
- No relative imports.

## Security
- No use of `eval` or `exec`.
- SQL queries are read from static files, not constructed from user input.

## Verified against
- app.py
- data/generate.py