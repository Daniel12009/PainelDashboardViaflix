# PainelDashboardViaflix

PainelDashboardViaflix is a Streamlit dashboard used to analyze e-commerce sales data obtained from a Google Sheets spreadsheet. The project includes data processing utilities, interactive plots with Plotly, and visualization of Brazilian states on a map.

## Prerequisites

- Python 3.7 or higher
- Access to the Google Sheets document containing your sales data

## Installation

Install the Python dependencies using pip:

```bash
pip install -r requirements.txt
```

## Usage

Update the `GOOGLE_SHEET_URL` constant in `app_google_sheets.py` with the link to your Google Sheets spreadsheet if necessary. Then run the Streamlit application:

```bash
streamlit run app_google_sheets.py
```

The app expects the file `usuarios.json` in the project root to manage simple user authentication. You can edit this file to add or modify users and passwords.

Additional files referenced by the application include `logo.png` (displayed in the UI) and `historico.csv` (used to store processed history data).
