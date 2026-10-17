# DESIGN_SYSTEM - medicare-fraud-detector

## Overview
The design system is minimal and implemented via Streamlit's custom CSS and theme settings. No external design system or component library is used.

## Colors
- Risk levels:
    - HIGH: #e05555 (red)
    - MEDIUM: #e0a855 (orange)
    - LOW: #55a8e0 (blue)
- Metric values: #d9615a (red) for stMetricValue

## Typography
- Uses Streamlit's default fonts.
- Metric values are set to 2rem font size via custom CSS.

## Components
- Custom styling for risk labels (via .risk-HIGH, .risk-MEDIUM, .risk-LOW classes).
- Metric cards are styled via [data-testid=\"stMetricValue\"].

## Implementation
- Custom CSS is injected via st.markdown with unsafe_allow_html=True in app.py (lines 22-29).
- No external CSS or design token files.

## Verified against
- app.py