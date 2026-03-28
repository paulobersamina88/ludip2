# TUP LUDIP Streamlit Dashboard Package

This package contains a dynamic Streamlit dashboard for LUDIP planning.

## Features
- Dynamic row input using `st.data_editor`
- Facility-level planning inputs
- Automatic computation of:
  - required floor area
  - proposed total floor area
  - future total area
  - deficit / surplus
  - compliance percentage
- Building inventory editor
- Overview metrics and motivation tracker
- Visual charts for area comparison, deficit, and compliance
- CSV export of computed facility analysis

## Files
- `app.py` - main Streamlit app
- `requirements.txt` - Python dependencies
- `data/facility_inputs.csv` - sample facility input data
- `data/building_inventory.csv` - sample building inventory

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Suggested next upgrades
- TUP-specific standards table by facility category
- Per-college filters
- Phasing by year
- Campus map integration
- PDF / Excel reporting
- Red-yellow-green executive cards
