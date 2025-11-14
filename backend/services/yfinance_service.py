"""
Yahoo Finance Service
Service to fetch company data using yfinance library
"""
import yfinance as yf
import pandas as pd
import asyncio
from typing import Dict, Optional, Callable
import os
import warnings
from contextlib import contextmanager
from config.settings import settings
import requests
import json
from datetime import datetime
import time

# Suppress yfinance deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

VERBOSE = (os.getenv("VERBOSE", "false") or "false").lower() in ("1", "true", "yes", "y")
SECTION_THROTTLE_SECONDS = float(os.getenv("YFINANCE_SECTION_DELAY", "0.35"))
MAX_FETCH_ATTEMPTS = int(os.getenv("YFINANCE_MAX_ATTEMPTS", "3"))
RATE_LIMIT_BACKOFF_SECONDS = float(os.getenv("YFINANCE_RATE_LIMIT_BACKOFF", "2.0"))
# Control whether to save response files (default: False - don't save)
SAVE_RESPONSE_FILES = os.getenv("YFINANCE_SAVE_RESPONSE_FILES", "false").lower() in ("1", "true", "yes", "y")

# Get proxy servers from settings
PROXY_SERVER = settings.PROXY_SERVER or os.getenv("PROXY_SERVER")
PROXY_SERVERS_STR = settings.PROXY_SERVERS or os.getenv("PROXY_SERVERS")

# Parse proxy servers list
PROXY_SERVERS_LIST = []
if PROXY_SERVERS_STR:
    # Parse comma-separated proxy list
    PROXY_SERVERS_LIST = [p.strip() for p in PROXY_SERVERS_STR.split(',') if p.strip()]
elif PROXY_SERVER:
    # If only single proxy, use it as list
    PROXY_SERVERS_LIST = [PROXY_SERVER]

# Proxy rotation index (thread-safe using threading.local or simple counter)
_proxy_index = 0
import threading
_proxy_lock = threading.Lock()


def is_rate_limit_error(exc: Exception) -> bool:
    """Determine if exception represents Yahoo rate limiting."""
    try:
        from requests import HTTPError
    except ImportError:
        HTTPError = requests.exceptions.HTTPError
    
    if isinstance(exc, HTTPError):
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 429:
            return True
    if isinstance(exc, requests.exceptions.RequestException):
        response = getattr(exc, "response", None)
        if response is not None and response.status_code == 429:
            return True
    message = str(exc).lower()
    return "429" in message or "too many requests" in message or "rate limit" in message


def throttle_section(section_name: str):
    """Small delay between Yahoo sections to avoid tripping rate limits."""
    if SECTION_THROTTLE_SECONDS <= 0:
        return
    try:
        time.sleep(SECTION_THROTTLE_SECONDS)
        if VERBOSE:
            debug(f"⏱️ Throttled after '{section_name}' for {SECTION_THROTTLE_SECONDS}s")
    except Exception:
        pass


def debug(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


def save_response_to_file(symbol: str, section_name: str, data: any):
    """Save response data to a JSON file (only if SAVE_RESPONSE_FILES is enabled)"""
    if not SAVE_RESPONSE_FILES:
        return  # Don't save files if disabled
    
    try:
        # Get the backend directory (parent of services)
        backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # Create responses directory in project root
        responses_dir = os.path.join(backend_dir, "..", "yfinance_responses")
        responses_dir = os.path.abspath(responses_dir)
        
        if not os.path.exists(responses_dir):
            os.makedirs(responses_dir)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        # Clean section name for filename
        clean_section = section_name.replace(" ", "_").replace("/", "_").replace("(", "").replace(")", "").replace("_New_", "_New")
        filename = os.path.join(responses_dir, f"{symbol}_{clean_section}_{timestamp}.json")
        
        # Prepare data to save
        response_data = {
            "symbol": symbol,
            "section": section_name,
            "timestamp": timestamp,
            "data": data
        }
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(response_data, f, indent=2, default=str, ensure_ascii=False)
        
        print(f"💾 Saved response to: {filename}")
    except Exception as e:
        print(f"⚠️ Failed to save response to file: {e}")


def safe_get_data(func, default=None, symbol=None, section_name=None, on_error: Optional[Callable[[Exception], None]] = None):
    """Safely execute a function and return default on error"""
    try:
        result = func()
        # Save response to file if symbol and section_name provided
        if symbol and section_name:
            save_response_to_file(symbol, section_name, result)
        return result
    except Exception as e:
        debug(f"⚠️ Data fetch failed: {type(e).__name__}: {e}")
        error_payload = {"error": str(e), "error_type": type(e).__name__}
        if symbol and section_name:
            save_response_to_file(symbol, f"{section_name}_ERROR", error_payload)
        if on_error:
            try:
                on_error(e)
            except Exception:
                pass
        if is_rate_limit_error(e):
            raise
        return default


def get_current_ip(proxy_url: Optional[str] = None) -> Optional[str]:
    """Get current public IP address to verify proxy usage"""
    try:
        # Get proxy from parameter or environment
        proxies = None
        if proxy_url:
            proxies = {
                'http': proxy_url,
                'https': proxy_url
            }
        else:
            http_proxy = os.environ.get('HTTP_PROXY') or os.environ.get('HTTPS_PROXY')
            if http_proxy:
                proxies = {
                    'http': http_proxy,
                    'https': http_proxy
                }
        
        # Try multiple IP checking services
        ip_services = [
            'https://api.ipify.org?format=json',
            'https://httpbin.org/ip',
            'https://api.myip.com'
        ]
        
        for service_url in ip_services:
            try:
                response = requests.get(service_url, timeout=5, proxies=proxies)
                if response.status_code == 200:
                    data = response.json()
                    # Handle different response formats
                    if 'ip' in data:
                        return data['ip']
                    elif 'origin' in data:
                        # httpbin returns "origin" which can be comma-separated
                        origin = data['origin']
                        if isinstance(origin, str):
                            return origin.split(',')[0].strip()
                        return str(origin)
                    elif 'query' in data:
                        return data['query']
            except Exception:
                continue
        return None
    except Exception:
        return None


def get_next_proxy() -> Optional[str]:
    """Get next proxy from rotation list"""
    global _proxy_index
    if not PROXY_SERVERS_LIST:
        return None
    
    with _proxy_lock:
        proxy = PROXY_SERVERS_LIST[_proxy_index % len(PROXY_SERVERS_LIST)]
        _proxy_index += 1
        return proxy


@contextmanager
def proxy_context(proxy_url: Optional[str] = None, request_name: str = "request"):
    """
    Context manager to temporarily set proxy environment variables for requests.
    yfinance uses requests library internally, which automatically picks up HTTP_PROXY/HTTPS_PROXY.
    
    Args:
        proxy_url: Specific proxy to use (if None, uses rotation or single proxy)
        request_name: Name of the request for logging (e.g., "Company Profile", "Fast Info")
    """
    old_http_proxy = os.environ.get('HTTP_PROXY')
    old_https_proxy = os.environ.get('HTTPS_PROXY')
    
    # Determine which proxy to use
    if proxy_url is None:
        if PROXY_SERVERS_LIST:
            proxy_url = get_next_proxy()
        elif PROXY_SERVER:
            proxy_url = PROXY_SERVER
    
    if proxy_url:
        # Set proxy for both HTTP and HTTPS
        os.environ['HTTP_PROXY'] = proxy_url
        os.environ['HTTPS_PROXY'] = proxy_url
        
        # Get and log IP address
        try:
            current_ip = get_current_ip(proxy_url)
            if current_ip:
                print(f"🔗 [YFINANCE] [{request_name}] Proxy: {proxy_url} → IP: {current_ip}")
            else:
                print(f"🔗 [YFINANCE] [{request_name}] Using proxy: {proxy_url} (IP verification failed)")
        except Exception as e:
            print(f"🔗 [YFINANCE] [{request_name}] Using proxy: {proxy_url} (Error checking IP: {e})")
    else:
        # Remove proxy if it was set before
        if 'HTTP_PROXY' in os.environ:
            del os.environ['HTTP_PROXY']
        if 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']
        
        # Get and log IP address
        try:
            current_ip = get_current_ip()
            if current_ip:
                print(f"🌐 [YFINANCE] [{request_name}] Direct connection → IP: {current_ip}")
            else:
                print(f"🌐 [YFINANCE] [{request_name}] Direct connection (no proxy)")
        except Exception as e:
            print(f"🌐 [YFINANCE] [{request_name}] Direct connection (Error checking IP: {e})")
    
    try:
        yield
    finally:
        # Restore original proxy settings
        if old_http_proxy is not None:
            os.environ['HTTP_PROXY'] = old_http_proxy
        elif 'HTTP_PROXY' in os.environ:
            del os.environ['HTTP_PROXY']
            
        if old_https_proxy is not None:
            os.environ['HTTPS_PROXY'] = old_https_proxy
        elif 'HTTPS_PROXY' in os.environ:
            del os.environ['HTTPS_PROXY']


async def get_all_yfinance_data(symbol: str) -> Optional[Dict]:
    """
    Fetch ALL available data from Yahoo Finance using yfinance library.
    Returns data directly with API response keys (Company Profile, Fast Info, etc.)
    """
    try:
        # Run yfinance operations in executor (yfinance is synchronous)
        loop = asyncio.get_event_loop()
        
        def fetch_data():
            last_rate_limit_exc = None
            
            def run_with_proxy(proxy_for_run: Optional[str], attempt: int):
                proxy_label = "Direct connection"
                if proxy_for_run:
                    proxy_label = f"Proxy {proxy_for_run}"
                
                # Use the same proxy (or direct IP) for the whole session so Yahoo cookies stay valid
                request_name = f"{symbol} session attempt {attempt} ({proxy_label})"
                with proxy_context(proxy_url=proxy_for_run, request_name=request_name):
                    ticker = yf.Ticker(symbol)
                    all_data = {}
                    section_errors: Dict[str, list] = {}
                    
                    # Helper conversions live inside the proxy context so they can access ticker/session state
                    def df_to_dict(df):
                        """Convert DataFrame to JSON-serializable dict."""
                        if df is None or df.empty:
                            return None
                        result = {}
                        for idx, row in df.iterrows():
                            row_name = str(idx).strip()
                            result[row_name] = {}
                            for col in df.columns:
                                date_str = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                                val = row[col]
                                if pd.notna(val):
                                    result[row_name][date_str] = str(int(val)) if abs(val) >= 1 else str(val)
                                else:
                                    result[row_name][date_str] = None
                        return result
                    
                    def df_to_records(df):
                        """Convert DataFrame to list of records."""
                        if df is None or df.empty:
                            return None
                        records = []
                        for idx, row in df.iterrows():
                            record = {}
                            if hasattr(idx, 'strftime'):
                                record['date'] = idx.strftime("%Y-%m-%d")
                            else:
                                record['date'] = str(idx)
                            for col in df.columns:
                                val = row[col]
                                if pd.notna(val):
                                    record[str(col)] = float(val) if isinstance(val, (int, float)) else str(val)
                                else:
                                    record[str(col)] = None
                            records.append(record)
                        return records
                    
                    def series_to_dict(series):
                        """Convert Series to dict."""
                        if series is None or series.empty:
                            return None
                        result = {}
                        for date, value in series.items():
                            date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
                            if pd.notna(value):
                                result[date_str] = float(value) if isinstance(value, (int, float)) else str(value)
                            else:
                                result[date_str] = None
                        return result
                    
                    def fetch_section(section_name: str, func, default=None):
                        """Wrapper that applies safe_get_data + throttling per section."""
                        def record_error(exc: Exception):
                            section_errors.setdefault(section_name, []).append(str(exc))
                        result = safe_get_data(func, default, symbol=symbol, section_name=section_name, on_error=record_error)
                        throttle_section(section_name)
                        return result
                    
                    # 1. Company Profile & Info
                    all_data["Company Profile"] = fetch_section(
                        "Company Profile",
                        lambda: ticker.info if ticker.info and len(ticker.info) > 0 else None
                    )
                    
                    # 2. Fast Info (faster access to key metrics)
                    def get_fast_info():
                        fi = ticker.fast_info
                        try:
                            keys = list(fi.keys())
                        except Exception:
                            try:
                                return dict(fi)
                            except Exception:
                                return None
                        out = {}
                        for k in keys:
                            try:
                                val = fi[k]
                                if isinstance(val, (int, float, str, bool)) or val is None:
                                    out[k] = val
                                else:
                                    out[k] = str(val)
                            except Exception:
                                out[k] = None
                        return out or None
                    all_data["Fast Info"] = fetch_section("Fast Info", get_fast_info)
                    
                    # 3. Historical Price Data (OHLCV)
                    def get_historical_prices():
                        hist = ticker.history(period="max")
                        if not hist.empty:
                            hist_dict = {}
                            for col in hist.columns:
                                hist_dict[col] = {}
                                for date, value in hist[col].items():
                                    date_str = date.strftime("%Y-%m-%d") if hasattr(date, 'strftime') else str(date)
                                    hist_dict[col][date_str] = float(value) if pd.notna(value) else None
                            return hist_dict
                        return None
                    
                    all_data["Historical Prices"] = fetch_section("Historical Prices", get_historical_prices)
                    
                    # 4. Financial Statements - Income Statement
                    all_data["Income Statement Annual"] = fetch_section("Income Statement Annual", lambda: df_to_dict(ticker.financials))
                    all_data["Income Statement Quarterly"] = fetch_section("Income Statement Quarterly", lambda: df_to_dict(ticker.quarterly_financials))
                    all_data["Income Statement Annual (New)"] = fetch_section("Income Statement Annual (New)", lambda: df_to_dict(ticker.income_stmt))
                    all_data["Income Statement Quarterly (New)"] = fetch_section("Income Statement Quarterly (New)", lambda: df_to_dict(ticker.quarterly_income_stmt))
                    
                    # 5. Balance Sheet
                    all_data["Balance Sheet Annual"] = fetch_section("Balance Sheet Annual", lambda: df_to_dict(ticker.balance_sheet))
                    all_data["Balance Sheet Quarterly"] = fetch_section("Balance Sheet Quarterly", lambda: df_to_dict(ticker.quarterly_balance_sheet))
                    
                    # 6. Cash Flow
                    all_data["Cash Flow Annual"] = fetch_section("Cash Flow Annual", lambda: df_to_dict(ticker.cashflow))
                    all_data["Cash Flow Quarterly"] = fetch_section("Cash Flow Quarterly", lambda: df_to_dict(ticker.quarterly_cashflow))
                    
                    # 7. Analyst Recommendations
                    all_data["Analyst Recommendations"] = fetch_section("Analyst Recommendations", lambda: df_to_records(ticker.recommendations))
                    all_data["Recommendations Summary"] = fetch_section("Recommendations Summary", lambda: df_to_records(ticker.recommendations_summary))
                    
                    # 8. Analyst Price Target
                    all_data["Analyst Price Target"] = fetch_section(
                        "Analyst Price Target",
                        lambda: ticker.analyst_price_target.to_dict() if ticker.analyst_price_target is not None and not ticker.analyst_price_target.empty else None
                    )
                    
                    # 9. Earnings
                    all_data["Earnings Quarterly"] = fetch_section("Earnings Quarterly", lambda: series_to_dict(ticker.quarterly_earnings))
                    
                    # 10. Earnings Calendar
                    all_data["Earnings Calendar"] = fetch_section(
                        "Earnings Calendar",
                        lambda: ticker.calendar.to_dict() if ticker.calendar is not None and not ticker.calendar.empty else None
                    )
                    
                    # 11. Dividends
                    all_data["Dividends"] = fetch_section(
                        "Dividends",
                        lambda: [{"date": str(date), "amount": float(amount)} for date, amount in ticker.dividends.items()] if not ticker.dividends.empty else None
                    )
                    
                    # 12. Stock Splits
                    all_data["Splits"] = fetch_section(
                        "Splits",
                        lambda: [{"date": str(date), "split_factor": float(factor)} for date, factor in ticker.splits.items()] if not ticker.splits.empty else None
                    )
                    
                    # 13. Shares Outstanding
                    all_data["Shares Outstanding"] = fetch_section("Shares Outstanding", lambda: series_to_dict(ticker.shares))
                    
                    # 14. Major Holders
                    all_data["Major Holders"] = fetch_section("Major Holders", lambda: df_to_records(ticker.major_holders))
                    
                    # 15. Institutional Holders
                    all_data["Institutional Holders"] = fetch_section("Institutional Holders", lambda: df_to_records(ticker.institutional_holders))
                    
                    # 16. Insider Transactions
                    all_data["Insider Transactions"] = fetch_section("Insider Transactions", lambda: df_to_records(ticker.insider_transactions))
                    
                    # 17. Insider Purchases
                    all_data["Insider Purchases"] = fetch_section("Insider Purchases", lambda: df_to_records(ticker.insider_purchases))
                    
                    # 18. Insider Roster Holders
                    all_data["Insider Roster Holders"] = fetch_section("Insider Roster Holders", lambda: df_to_records(ticker.insider_roster_holders))
                    
                    # 19. Sustainability (ESG)
                    all_data["Sustainability"] = fetch_section(
                        "Sustainability",
                        lambda: ticker.sustainability.to_dict() if ticker.sustainability is not None and not ticker.sustainability.empty else None
                    )
                    
                    # 20. News
                    all_data["News"] = fetch_section("News", lambda: ticker.news if ticker.news else None)
                
                    # Filter out None values to keep only sections with data
                    filtered_data = {k: v for k, v in all_data.items() if v is not None}
                    
                    if not filtered_data:
                        if section_errors:
                            sample_section, errors = next(iter(section_errors.items()))
                            raise RuntimeError(
                                f"Yahoo Finance returned no usable data for {symbol}. "
                                f"Sample failure [{sample_section}]: {errors[-1]}"
                            )
                        raise RuntimeError(
                            f"Yahoo Finance returned empty data set for {symbol}. "
                            "This may indicate the proxy was blocked or the ticker is invalid."
                        )
                    
                    return filtered_data
            
            for attempt in range(1, MAX_FETCH_ATTEMPTS + 1):
                proxy_for_run = None
                if PROXY_SERVERS_LIST:
                    proxy_for_run = get_next_proxy()
                elif PROXY_SERVER:
                    proxy_for_run = PROXY_SERVER
                
                try:
                    result = run_with_proxy(proxy_for_run, attempt)
                    if result is not None:
                        return result
                except Exception as exc:
                    if is_rate_limit_error(exc):
                        last_rate_limit_exc = exc
                        if attempt < MAX_FETCH_ATTEMPTS:
                            wait_time = RATE_LIMIT_BACKOFF_SECONDS * attempt
                            print(f"⏳ [YFINANCE] Rate limit detected for {symbol}. Waiting {wait_time:.2f}s before retry #{attempt + 1}...")
                            time.sleep(wait_time)
                            continue
                        break
                    raise
            
            if last_rate_limit_exc:
                debug(f"❌ Rate limit persisted for {symbol} after {MAX_FETCH_ATTEMPTS} attempts: {last_rate_limit_exc}")
                raise last_rate_limit_exc
            return None
        
        # Execute in executor
        result = await loop.run_in_executor(None, fetch_data)
        return result
        
    except RuntimeError:
        raise
    except Exception as e:
        debug(f"⚠️ Failed to get all yfinance data: {e}")
        return None

