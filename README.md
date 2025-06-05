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
MIT License

Copyright (c) 2025 Daniel12009

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
