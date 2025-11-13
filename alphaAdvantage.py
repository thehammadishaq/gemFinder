import requests
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

ALPHAVANTAGE_API_KEY = os.getenv("ALPHAVANTAGE_API_KEY")
VERBOSE = (os.getenv("VERBOSE", "false") or "false").lower() in ("1", "true", "yes", "y")


def debug(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


def save_json(filename, data):
    """Save dictionary data to JSON file"""
    with open(filename, "w") as f:
        json.dump(data, f, indent=4)
    debug(f"✅ Saved → {filename}")


def get_company_profile(symbol):
    # Alpha Vantage OVERVIEW (only)
    try:
        if ALPHAVANTAGE_API_KEY:
            av_url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            av = requests.get(av_url, timeout=20).json()
            if isinstance(av, dict) and av:
                return av
    except Exception as e:
        debug(f"⚠️ Alpha Vantage overview failed: {e}")

    debug("⚠️ No profile data found from free sources.")
    return None


def get_global_quote(symbol):
    """Fetch latest price/volume using Alpha Vantage GLOBAL_QUOTE."""
    try:
        if ALPHAVANTAGE_API_KEY:
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            data = requests.get(url, timeout=20).json()
            if isinstance(data, dict):
                return data.get("Global Quote") or data
    except Exception as e:
        debug(f"⚠️ Alpha Vantage global quote failed: {e}")
    return None


def get_dividends(symbol):
    """Fetch historical and future dividend distributions using Alpha Vantage DIVIDENDS."""
    try:
        if ALPHAVANTAGE_API_KEY:
            url = f"https://www.alphavantage.co/query?function=DIVIDENDS&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            data = requests.get(url, timeout=20).json()
            if isinstance(data, dict):
                return data
    except Exception as e:
        debug(f"⚠️ Alpha Vantage dividends failed: {e}")
    return None


def get_splits(symbol):
    """Fetch historical stock split events using Alpha Vantage SPLITS."""
    try:
        if ALPHAVANTAGE_API_KEY:
            url = f"https://www.alphavantage.co/query?function=SPLITS&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            data = requests.get(url, timeout=20).json()
            if isinstance(data, dict):
                return data
    except Exception as e:
        debug(f"⚠️ Alpha Vantage splits failed: {e}")
    return None


def get_income_statement(symbol):
    """Fetch annual and quarterly income statements using Alpha Vantage INCOME_STATEMENT."""
    try:
        if ALPHAVANTAGE_API_KEY:
            url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            data = requests.get(url, timeout=30).json()
            if isinstance(data, dict):
                return data
    except Exception as e:
        debug(f"⚠️ Alpha Vantage income statement failed: {e}")
    return None


def get_balance_sheet(symbol):
    """Fetch annual and quarterly balance sheets using Alpha Vantage BALANCE_SHEET."""
    try:
        if ALPHAVANTAGE_API_KEY:
            url = f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            data = requests.get(url, timeout=30).json()
            if isinstance(data, dict):
                return data
    except Exception as e:
        debug(f"⚠️ Alpha Vantage balance sheet failed: {e}")
    return None


def get_cash_flow(symbol):
    """Fetch annual and quarterly cash flow statements using Alpha Vantage CASH_FLOW."""
    try:
        if ALPHAVANTAGE_API_KEY:
            url = f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}"
            data = requests.get(url, timeout=30).json()
            if isinstance(data, dict):
                return data
    except Exception as e:
        debug(f"⚠️ Alpha Vantage cash flow failed: {e}")
    return None
def latest_value(series):
    return series[-1]["value"] if series else None


def growth_rates(series, periods_back=4):
    """Compute QoQ (last vs prev) and YoY (last vs N-back)."""
    qoq = None
    yoy = None
    if len(series) >= 2:
        a, b = series[-1]["value"], series[-2]["value"]
        try:
            qoq = (a - b) / abs(b) if b not in (0, None) else None
        except Exception:
            qoq = None
    if len(series) > periods_back:
        a, b = series[-1]["value"], series[-1 - periods_back]["value"]
        try:
            yoy = (a - b) / abs(b) if b not in (0, None) else None
        except Exception:
            yoy = None
    return qoq, yoy
 
def compute_margins(revenue_series, gross_profit_series, operating_income_series, net_income_series):
    latest_revenue = latest_value(revenue_series) or 0
    margins = {"gross": None, "operating": None, "net": None}
    if latest_revenue:
        gp = latest_value(gross_profit_series)
        oi = latest_value(operating_income_series)
        ni = latest_value(net_income_series)
        margins["gross"] = (gp / latest_revenue) if gp is not None else None
        margins["operating"] = (oi / latest_revenue) if oi is not None else None
        margins["net"] = (ni / latest_revenue) if ni is not None else None
    return margins
 
def get_fundamentals(symbol):
    """Compute fundamentals using Alpha Vantage statements (quarterly)."""
    try:
        inc = requests.get(
            f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}",
            timeout=30,
        ).json()
        bal = requests.get(
            f"https://www.alphavantage.co/query?function=BALANCE_SHEET&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}",
            timeout=30,
        ).json()
        cfs = requests.get(
            f"https://www.alphavantage.co/query?function=CASH_FLOW&symbol={symbol}&apikey={ALPHAVANTAGE_API_KEY}",
            timeout=30,
        ).json()
    except Exception as e:
        debug(f"⚠️ Alpha Vantage statements fetch failed: {e}")
        return {}

    q_income = inc.get("quarterlyReports", []) if isinstance(inc, dict) else []
    q_balance = bal.get("quarterlyReports", []) if isinstance(bal, dict) else []
    q_cash = cfs.get("quarterlyReports", []) if isinstance(cfs, dict) else []

    def to_float(x):
        try:
            return float(x)
        except Exception:
            return None

    def parse_series(reports, field):
        series = []
        for r in reports:
            date_str = r.get("fiscalDateEnding")
            val = to_float(r.get(field))
            if date_str and val is not None:
                try:
                    dt = datetime.strptime(date_str, "%Y-%m-%d")
                    series.append({"date": dt, "value": val})
                except Exception:
                    continue
        series.sort(key=lambda x: x["date"])
        return series

    revenue = parse_series(q_income, "totalRevenue")
    eps_diluted = parse_series(q_income, "reportedEPS")
    gross_profit = parse_series(q_income, "grossProfit")
    operating_income = parse_series(q_income, "operatingIncome")
    net_income = parse_series(q_income, "netIncome")

    liabilities = parse_series(q_balance, "totalLiabilities")
    equity = parse_series(q_balance, "totalShareholderEquity")

    cfo = parse_series(q_cash, "operatingCashflow")
    capex = parse_series(q_cash, "capitalExpenditures")

    rev_qoq, rev_yoy = growth_rates(revenue, periods_back=4)
    eps_qoq, eps_yoy = growth_rates(eps_diluted, periods_back=4)

    dte = None
    try:
        liab_val = latest_value(liabilities)
        eq_val = latest_value(equity)
        if liab_val is not None and eq_val not in (None, 0):
            dte = liab_val / abs(eq_val)
    except Exception:
        dte = None

    # FCF = OCF - CapEx (capex may be negative)
    fcf_series = []
    n = min(len(cfo), len(capex))
    if n > 0:
        for i in range(-n, 0):
            ocf = cfo[i]["value"] or 0
            cx = capex[i]["value"] or 0
            fcf_series.append({"date": cfo[i]["date"], "value": ocf - cx})
    fcf_qoq, fcf_yoy = growth_rates(fcf_series, periods_back=4)

    margins = compute_margins(revenue, gross_profit, operating_income, net_income)

    return {
        "revenueGrowthQoQ": rev_qoq,
        "revenueGrowthYoY": rev_yoy,
        "epsGrowthQoQ": eps_qoq,
        "epsGrowthYoY": eps_yoy,
        "debtToEquity": dte,
        "freeCashFlowGrowthQoQ": fcf_qoq,
        "freeCashFlowGrowthYoY": fcf_yoy,
        "margins": margins,
    }


def get_company_identity_layer(symbol):
    profile = get_company_profile(symbol)
    quote = get_global_quote(symbol)
    dividends = get_dividends(symbol)
    splits = get_splits(symbol)
    income_statement = get_income_statement(symbol)
    balance_sheet = get_balance_sheet(symbol)
    cash_flow = get_cash_flow(symbol)

    # Return all seven sections separated
    return {
        "Overview": profile,
        "Global Quote": quote,
        "Dividends": dividends,
        "Splits": splits,
        "Income Statement": income_statement,
        "Balance Sheet": balance_sheet,
        "Cash Flow": cash_flow
    }


# ------------------ RUN SCRIPT ------------------

ticker = input("Enter Stock Ticker (e.g., TSLA, NVDA, AAPL): ").upper()

data = get_company_identity_layer(ticker)

# Save one combined results file; no terminal output unless VERBOSE=true
save_json(f"results_{ticker}.json", data)
