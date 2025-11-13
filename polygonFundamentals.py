import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

POLYGON_API_KEY = os.getenv("POLYGON_API_KEY")
VERBOSE = (os.getenv("VERBOSE", "false") or "false").lower() in ("1", "true", "yes", "y")


def debug(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


def save_json(filename, data):
    """Save dictionary data to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    print(f"✅ Saved → {filename}")


def safe_get(url, params=None):
    """Safely make API request"""
    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        debug(f"⚠️ API request failed: {type(e).__name__}: {e}")
        return None


def get_polygon_fundamentals(symbol):
    """Fetch all fundamental data from Polygon.io"""
    if not POLYGON_API_KEY:
        print("❌ POLYGON_API_KEY not found in .env file")
        print("   Get free API key from: https://polygon.io/")
        return None
    
    base_url = "https://api.polygon.io"
    all_data = {}
    
    # 1. Ticker Details
    print(f"📊 Fetching ticker details for {symbol}...")
    ticker_url = f"{base_url}/v3/reference/tickers/{symbol}"
    ticker_data = safe_get(ticker_url, params={"apiKey": POLYGON_API_KEY})
    if ticker_data:
        all_data["Ticker Details"] = ticker_data
        debug(f"✅ Ticker details: {len(str(ticker_data))} chars")
    
    # 2. Company Fundamentals (VX API - vX is the fundamentals endpoint)
    print(f"📊 Fetching company fundamentals for {symbol}...")
    fundamentals_url = f"{base_url}/vX/reference/financials"
    fundamentals_data = safe_get(fundamentals_url, params={
        "ticker": symbol,
        "apiKey": POLYGON_API_KEY,
        "timeframe": "annual",
        "limit": 10
    })
    if fundamentals_data:
        all_data["Financials Annual"] = fundamentals_data
    
    # Also get quarterly
    print(f"📊 Fetching quarterly fundamentals for {symbol}...")
    fundamentals_qtr = safe_get(fundamentals_url, params={
        "ticker": symbol,
        "apiKey": POLYGON_API_KEY,
        "timeframe": "quarterly",
        "limit": 10
    })
    if fundamentals_qtr:
        all_data["Financials Quarterly"] = fundamentals_qtr
    
    # 3. Company Profile/Info
    print(f"📊 Fetching company profile for {symbol}...")
    # Polygon doesn't have a direct "profile" endpoint, but ticker details has some info
    # We already got this in ticker details
    
    # 4. Dividends
    print(f"📊 Fetching dividends for {symbol}...")
    dividends_url = f"{base_url}/v2/reference/dividends/{symbol}"
    dividends_data = safe_get(dividends_url, params={"apiKey": POLYGON_API_KEY})
    if dividends_data:
        all_data["Dividends"] = dividends_data
    
    # 5. Stock Splits
    print(f"📊 Fetching stock splits for {symbol}...")
    splits_url = f"{base_url}/v2/reference/splits/{symbol}"
    splits_data = safe_get(splits_url, params={"apiKey": POLYGON_API_KEY})
    if splits_data:
        all_data["Splits"] = splits_data
    
    # 6. Company News
    print(f"📊 Fetching company news for {symbol}...")
    news_url = f"{base_url}/v2/reference/news"
    news_data = safe_get(news_url, params={
        "ticker": symbol,
        "apiKey": POLYGON_API_KEY,
        "limit": 10
    })
    if news_data:
        all_data["News"] = news_data
    
    # 7. Market Status (to check if market is open)
    print(f"📊 Fetching market status...")
    market_status_url = f"{base_url}/v1/marketstatus/now"
    market_status = safe_get(market_status_url, params={"apiKey": POLYGON_API_KEY})
    if market_status:
        all_data["Market Status"] = market_status
    
    # 8. Previous Close
    print(f"📊 Fetching previous close for {symbol}...")
    prev_close_url = f"{base_url}/v2/aggs/ticker/{symbol}/prev"
    prev_close = safe_get(prev_close_url, params={"apiKey": POLYGON_API_KEY})
    if prev_close:
        all_data["Previous Close"] = prev_close
    
    # 9. Grouped Daily (for latest price)
    print(f"📊 Fetching latest price data for {symbol}...")
    latest_url = f"{base_url}/v2/aggs/ticker/{symbol}/range/1/day/latest/latest"
    latest = safe_get(latest_url, params={"apiKey": POLYGON_API_KEY})
    if latest:
        all_data["Latest Price Data"] = latest
    
    # 10. Company Details (if available in ticker details)
    if ticker_data and "results" in ticker_data:
        ticker_info = ticker_data.get("results", {})
        all_data["Company Info"] = {
            "Name": ticker_info.get("name"),
            "Description": ticker_info.get("description"),
            "Ticker": ticker_info.get("ticker"),
            "Market": ticker_info.get("market"),
            "Locale": ticker_info.get("locale"),
            "Primary Exchange": ticker_info.get("primary_exchange"),
            "Type": ticker_info.get("type"),
            "Active": ticker_info.get("active"),
            "Currency": ticker_info.get("currency_name"),
            "CIK": ticker_info.get("cik"),
            "Composite FIGI": ticker_info.get("composite_figi"),
            "Share Class FIGI": ticker_info.get("share_class_figi"),
            "Last Updated UTC": ticker_info.get("last_updated_utc"),
            "Delisted UTC": ticker_info.get("delisted_utc"),
        }
    
    return all_data


# ------------------ RUN SCRIPT ------------------

if __name__ == "__main__":
    if not POLYGON_API_KEY:
        print("\n" + "="*60)
        print("⚠️  POLYGON_API_KEY not found!")
        print("="*60)
        print("1. Get free API key from: https://polygon.io/")
        print("2. Add to .env file: POLYGON_API_KEY=your_key_here")
        print("="*60 + "\n")
    
    ticker = input("Enter Stock Ticker (e.g., TSLA, NVDA, AAPL): ").upper()
    
    print(f"\n🔍 Fetching Polygon.io data for {ticker}...\n")
    
    data = get_polygon_fundamentals(ticker)
    
    if data:
        # Save raw data
        save_json(f"polygon_fundamentals_{ticker}.json", data)
        
        # Print summary
        print("\n" + "="*60)
        print(f"📋 SUMMARY - Available Data Sections for {ticker}")
        print("="*60)
        for section, content in data.items():
            if content:
                if isinstance(content, dict):
                    if "results" in content:
                        count = len(content.get("results", []))
                        print(f"✅ {section}: {count} items")
                    else:
                        print(f"✅ {section}: Available")
                elif isinstance(content, list):
                    print(f"✅ {section}: {len(content)} items")
                else:
                    print(f"✅ {section}: Available")
            else:
                print(f"❌ {section}: Not available")
        print("="*60)
        
        # Show sample of each section
        if VERBOSE:
            print("\n📄 DETAILED DATA:")
            print("="*60)
            for section, content in data.items():
                if content:
                    print(f"\n--- {section} ---")
                    print(json.dumps(content, indent=2)[:500] + "..." if len(str(content)) > 500 else json.dumps(content, indent=2))
    else:
        print(f"❌ Failed to fetch data for {ticker}")

