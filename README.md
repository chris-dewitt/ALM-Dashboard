# ALM Dashboard

**Asset-Liability Management (ALM) Dashboard** is an interactive Streamlit-based web app designed to provide comprehensive insights into bank balance sheets, liquidity, interest rate risk, funds transfer pricing (FTP), and derivatives valuation. This project showcases quantitative risk analysis techniques applied to realistic banking datasets.

---

## Features

- **Balance Sheet Overview:** Visual summary of assets, liabilities, and equity with interactive charts.
- **Liquidity Gap Table:** Analysis of cash inflows and outflows across time buckets.
- **Cash Flow Gap Analysis:** Detailed monthly inflow/outflow breakdown with gap visualizations.
- **Funds Transfer Pricing (FTP):** Calculates FTP charges and contributions by product.
- **Interest Rate Risk (IRR):** Scenario-based NII (Net Interest Income) and EVE (Economic Value of Equity) impact analysis.
- **Duration Gap Analysis:** Measures and compares asset and liability durations.
- **IRR/FX Derivatives Book:** Valuation impact of interest rate and FX shocks on derivatives portfolio.
- **Scenario Builder:** Custom yield curve shock creation and impact estimation tool.

---

## Usage

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/alm-dashboard.git
   cd alm-dashboard
Create and activate a Python virtual environment (recommended):

bash
Copy
Edit
python -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Run the app:

bash
Copy
Edit
streamlit run app.py
Use the sidebar to navigate between modules and upload your own CSV data for customized analysis.

Data
Sample balance sheet and derivatives data are included for demonstration purposes. The app supports uploading custom CSV files formatted to specified schemas.

Technologies Used
Python 3.9+

Streamlit for interactive UI

Pandas and NumPy for data manipulation

Plotly for interactive visualizations

About the Author
This project was developed by an overcaffeinated IRR analyst & Data Science student named Chris DeWitt.


Contact
For questions or collaborations, please reach out via [DeWittCN@gmail.com] or connect on LinkedIn.