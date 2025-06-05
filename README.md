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

The app expects the file `usuarios.json` in the project root to manage simple user authentication. **Passwords are now stored as SHA‑256 hashes.**

To add a new user, first generate the hash of the desired password. A quick way is using Python:

```bash
python - <<'EOF'
import hashlib, sys; print(hashlib.sha256(b'my_secret').hexdigest())
EOF
```

Replace `my_secret` with the password you want. Use the resulting hash in `usuarios.json`:

```json
{
  "novo_usuario": {"senha": "<hash_gerado>", "role": "user"}
}
```

Existing entries in `usuarios.json` have already been converted to this hashed format.

Additional files referenced by the application include `logo.png` (displayed in the UI) and `historico.csv` (used to store processed history data).
