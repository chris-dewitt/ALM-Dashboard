# ALM Dashboard

An interactive Streamlit application for exploring bank balance sheet structure, liquidity gaps, interest rate risk, funds transfer pricing, duration exposure, and simple derivatives shock analysis.

This project is designed as a professional portfolio piece for asset-liability management, interest rate risk, and quantitative finance analytics. It uses a realistic sample balance sheet by default and also supports user-uploaded CSV data.

## Core Features

- **Balance Sheet Overview**: Asset, liability, and equity summary with portfolio composition charts.
- **Liquidity Gap Table**: Maturity-bucketed inflows, outflows, gaps, and cumulative gap exposure.
- **Cash Flow Gap Analysis**: Monthly cash flow estimates across maturity buckets.
- **Funds Transfer Pricing**: Product-level FTP rate mapping and net FTP contribution.
- **Interest Rate Risk Simulation**: Scenario-based NII and EVE sensitivity analysis.
- **Duration Gap Analysis**: Weighted average asset duration, liability duration, and duration gap.
- **IRR/FX Derivatives Book**: Sample derivative exposures with mark-to-market and delta summary.
- **Scenario Builder**: Custom yield curve scenarios with estimated DV01 impact.

## Repository Structure

```text
ALM-Dashboard/
├── ALM_Dashboard.py          # Main Streamlit entry point
├── liquidity_gap.py          # Liquidity gap analysis module
├── cash_flow_gap.py          # Cash flow gap analysis module
├── ftp.py                    # Funds transfer pricing module
├── irr.py                    # Interest rate risk simulation module
├── duration_gap.py           # Duration gap analysis module
├── derivatives_book.py       # IRR/FX derivatives exposure module
├── scenario_builder.py       # Custom rate scenario builder
├── requirements.txt          # Python dependencies
└── README.md                 # Project documentation
```

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/chris-dewitt/ALM-Dashboard.git
cd ALM-Dashboard
```

### 2. Create and activate a virtual environment

Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the dashboard

```bash
streamlit run ALM_Dashboard.py
```

## Input Data Schema

The app runs with a built-in sample balance sheet, but uploaded CSV files should include the following columns:

| Column | Description | Example |
|---|---|---|
| `Product` | Product or portfolio category | Fixed Mortgage |
| `Type` | Balance sheet classification: `Asset` or `Liability` | Asset |
| `Amount ($)` | Current balance or notional amount | 5500000 |
| `Rate (%)` | Current product rate in percent | 4.0 |
| `Duration (Years)` | Effective duration estimate | 5.0 |
| `Maturity (Months)` | Remaining maturity in months | 60 |

## Sample Use Cases

- Demonstrate ALM analytics in a portfolio or interview setting.
- Compare balance sheet composition across asset and liability categories.
- Estimate liquidity gaps and cumulative funding mismatches.
- Simulate NII and EVE sensitivity under rate shock scenarios.
- Show how FTP assumptions can change product profitability analysis.

## Notes and Limitations

This is an educational and portfolio-oriented analytics dashboard. It uses simplified assumptions for rate shocks, balance sensitivity, FTP curve mapping, duration-based EVE, and derivative valuation. It should not be used for production risk management or investment decision-making without further model validation, audit controls, and institution-specific calibration.

## Technologies

- Python
- Streamlit
- pandas
- NumPy
- Plotly

## Author

Built by Chris DeWitt as part of a quantitative finance and data science portfolio focused on ALM, interest rate risk, and financial analytics.

## Contact

For questions or collaboration, reach out via email at DeWittCN@gmail.com or connect on LinkedIn.
