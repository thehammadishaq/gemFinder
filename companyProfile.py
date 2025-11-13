import yfinance as yf
import pandas as pd
import json
import os
import warnings

# Optional: wikipedia summary for richer business description
try:
    import wikipedia  # pip install wikipedia
except Exception:
    wikipedia = None

# Suppress yfinance deprecation warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)

VERBOSE = (os.getenv("VERBOSE", "false") or "false").lower() in ("1", "true", "yes", "y")


def debug(*args, **kwargs):
    if VERBOSE:
        print(*args, **kwargs)


def save_json(filename, data):
    """Save dictionary data to JSON file"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    debug(f"✅ Saved → {filename}")


def safe_get(func, default=None):
    """Safely execute a function and return default on any error."""
    try:
        result = func()
        return result if result is not None else default
    except Exception as e:
        debug(f"⚠️ Data fetch failed: {type(e).__name__}: {e}")
        return default


def get_company_profile(symbol):
    """Extract company profile using ONLY yfinance data - no hardcoded logic."""
    try:
        ticker = yf.Ticker(symbol)
        profile = {}
        
        # Get basic info
        info = safe_get(lambda: ticker.info, {})

        # Helper: get Wikipedia summary if possible
        def get_wikipedia_summary():
            if wikipedia is None:
                debug("⚠️ Wikipedia module not installed. Install with: pip install wikipedia")
                return None
            
            long_name = info.get("longName") or ""
            short_name = info.get("shortName") or ""
            
            if not long_name and not short_name:
                debug("⚠️ No company name available for Wikipedia search")
                return None
            
            try:
                # Build search candidates with company-specific terms
                search_candidates = []
                
                # 1. Try exact company names
                if long_name:
                    search_candidates.append(long_name)
                if short_name and short_name != long_name:
                    search_candidates.append(short_name)
                
                # 2. Try with common suffixes
                if long_name:
                    for suffix in [" Inc.", " Inc", " Corporation", " Corp.", " Corp", " Company", " Co.", " Co", " Ltd.", " Ltd", " LLC", " PLC"]:
                        if suffix not in long_name:
                            search_candidates.append(long_name + suffix)
                
                # 3. Try ticker symbol with company/stock
                search_candidates.append(f"{symbol} (company)")
                search_candidates.append(f"{symbol} stock")
                if long_name:
                    search_candidates.append(f"{long_name} ({symbol})")
                
                # 4. Try searching and filtering results
                if long_name:
                    try:
                        search_results = wikipedia.search(long_name, results=10)
                        # Filter results that seem company-related
                        for result in search_results:
                            result_lower = result.lower()
                            # Skip generic terms
                            if any(generic in result_lower for generic in ["cryptocurrency", "stock market", "exchange", "trading", "investment"]):
                                continue
                            # Prefer results with company name or ticker
                            if long_name.lower() in result_lower or symbol.lower() in result_lower:
                                if result not in search_candidates:
                                    search_candidates.append(result)
                    except Exception as e:
                        debug(f"⚠️ Wikipedia search failed: {e}")
                
                # Try each candidate
                for candidate in search_candidates:
                    if not candidate:
                        continue
                    try:
                        summary = wikipedia.summary(candidate, auto_suggest=False, sentences=5)
                        if not summary:
                            continue
                        
                        summary_lower = summary.lower()
                        candidate_lower = candidate.lower()
                        
                        # Validation: Check if summary is about the company
                        # Accept if it mentions company name, ticker, or candidate name
                        name_mentioned = (long_name and long_name.lower() in summary_lower) or \
                                       (short_name and short_name.lower() in summary_lower) or \
                                       (symbol.lower() in summary_lower) or \
                                       (candidate_lower in summary_lower)
                        
                        # Reject generic cryptocurrency/blockchain definitions
                        is_generic = any(generic in summary_lower for generic in [
                            "cryptocurrency", "digital currency", "blockchain technology",
                            "a cryptocurrency", "cryptocurrencies are"
                        ])
                        
                        if name_mentioned and not is_generic:
                            return summary
                        
                        # If summary is short and candidate matches, accept it (less strict)
                        if len(summary) < 300 and candidate_lower in summary_lower and not is_generic:
                            return summary
                            
                    except wikipedia.exceptions.DisambiguationError as e:
                        # Try the first few disambiguation options
                        for option in e.options[:3]:
                            try:
                                summary = wikipedia.summary(option, sentences=5)
                                summary_lower = summary.lower()
                                if (long_name and long_name.lower() in summary_lower) or \
                                   (symbol.lower() in summary_lower) or \
                                   (option.lower() in summary_lower):
                                    # Check it's not generic
                                    if not any(generic in summary_lower for generic in ["cryptocurrency", "digital currency"]):
                                        return summary
                            except Exception:
                                continue
                    except wikipedia.exceptions.PageError:
                        continue
                    except Exception as e:
                        debug(f"⚠️ Wikipedia summary for '{candidate}' failed: {type(e).__name__}")
                        continue
                
                # Last resort: try with auto_suggest (less strict validation)
                if long_name:
                    try:
                        summary = wikipedia.summary(long_name, auto_suggest=True, sentences=5)
                        if summary:
                            summary_lower = summary.lower()
                            # Less strict: just check it's not generic cryptocurrency definition
                            if not any(generic in summary_lower for generic in ["a cryptocurrency", "cryptocurrencies are", "digital currency designed"]):
                                return summary
                    except Exception as e:
                        debug(f"⚠️ Wikipedia auto_suggest failed: {e}")
                        
            except Exception as e:
                debug(f"⚠️ Wikipedia summary failed: {type(e).__name__}: {e}")
                return None
            
            debug(f"⚠️ No Wikipedia summary found for {symbol} ({long_name or short_name})")
            return None
        
        # ========== WHAT: Sector, Industry, Niche ==========
        profile["What"] = {
            "Sector": info.get("sector"),
            "Industry": info.get("industry"),
            "Industry Classification": info.get("industryDisp"),
            "Business Summary": info.get("longBusinessSummary"),
            "Wikipedia Summary": get_wikipedia_summary(),
            "Short Description": info.get("shortBusinessSummary"),
            "Full Time Employees": info.get("fullTimeEmployees"),
            "Company Type": info.get("quoteType"),
        }
        
        # ========== WHEN: Founded, IPO Date, Growth Timeline ==========
        profile["When"] = {
            "Founded Year": info.get("founded"),
            "IPO Date": info.get("ipoDate"),
            "First Trade Date": info.get("firstTradeDateEpochUtc"),
            "Exchange": info.get("exchange"),
            "Listed Exchange": info.get("exchangeTimezoneName"),
        }
        
        # ========== WHERE: HQ Location, Operational Footprint ==========
        profile["Where"] = {
            "Headquarters Address": info.get("address1"),
            "City": info.get("city"),
            "State": info.get("state"),
            "Country": info.get("country"),
            "Zip Code": info.get("zip"),
            "Phone": info.get("phone"),
            "Website": info.get("website"),
        }
        
        # ========== HOW: Business Model, Revenue Streams, Key Products ==========
        profile["How"] = {
            "Business Model": get_wikipedia_summary() or info.get("longBusinessSummary"),
        }
        
        # Get ALL financials data (not just specific rows)
        try:
            financials = safe_get(lambda: ticker.financials, None)
            if financials is not None and not financials.empty:
                financials_dict = {}
                for idx, row in financials.iterrows():
                    row_name = str(idx).strip()
                    financials_dict[row_name] = {}
                    for col in financials.columns:
                        date_str = col.strftime("%Y-%m-%d") if hasattr(col, 'strftime') else str(col)
                        val = financials.loc[row_name, col]
                        if pd.notna(val):
                            financials_dict[row_name][date_str] = float(val)
                        else:
                            financials_dict[row_name][date_str] = None
                profile["How"]["Financials Annual"] = financials_dict
        except Exception as e:
            debug(f"⚠️ Financials failed: {e}")
            profile["How"]["Financials Annual"] = None
        
        # ========== WHO: CEO, Leadership, Institutional Holders, Insider Ownership ==========
        profile["Who"] = {
            "Company Officers": info.get("companyOfficers"),  # Raw list from yfinance
        }
        
        # Institutional Holders - extract all available columns
        try:
            institutional_holders = safe_get(lambda: ticker.institutional_holders, None)
            if institutional_holders is not None and not institutional_holders.empty:
                holders_list = []
                for idx, row in institutional_holders.iterrows():
                    holder = {}
                    for col in institutional_holders.columns:
                        val = row[col]
                        if pd.notna(val):
                            holder[str(col)] = float(val) if isinstance(val, (int, float)) else str(val)
                        else:
                            holder[str(col)] = None
                    holders_list.append(holder)
                profile["Who"]["Institutional Holders"] = holders_list
            else:
                profile["Who"]["Institutional Holders"] = None
        except Exception as e:
            debug(f"⚠️ Institutional holders failed: {e}")
            profile["Who"]["Institutional Holders"] = None
        
        # Major Holders - raw data
        try:
            major_holders = safe_get(lambda: ticker.major_holders, None)
            if major_holders is not None and not major_holders.empty:
                holders_list = []
                for idx, row in major_holders.iterrows():
                    holder = {}
                    if isinstance(row, pd.Series):
                        for col_idx, val in enumerate(row):
                            holder[f"Column_{col_idx}"] = str(val) if pd.notna(val) else None
                    else:
                        holder["Value"] = str(row) if pd.notna(row) else None
                    holder["Index"] = str(idx)
                    holders_list.append(holder)
                profile["Who"]["Major Holders"] = holders_list
            else:
                profile["Who"]["Major Holders"] = None
        except Exception as e:
            debug(f"⚠️ Major holders failed: {e}")
            profile["Who"]["Major Holders"] = None
        
        # Insider Ownership - raw percentages
        profile["Who"]["Insider Ownership"] = {
            "Percent Insiders": info.get("heldPercentInsiders"),
            "Percent Institutions": info.get("heldPercentInstitutions"),
            "Percent Institutions Float": info.get("heldPercentInstitutionsFloat"),
        }
        
        # Insider Transactions - all available data
        try:
            insider_transactions = safe_get(lambda: ticker.insider_transactions, None)
            if insider_transactions is not None and not insider_transactions.empty:
                transactions_list = []
                for idx, row in insider_transactions.iterrows():
                    transaction = {}
                    for col in insider_transactions.columns:
                        val = row[col]
                        if pd.notna(val):
                            transaction[str(col)] = float(val) if isinstance(val, (int, float)) else str(val)
                        else:
                            transaction[str(col)] = None
                    transactions_list.append(transaction)
                profile["Who"]["Insider Transactions"] = transactions_list
            else:
                profile["Who"]["Insider Transactions"] = None
        except Exception as e:
            debug(f"⚠️ Insider transactions failed: {e}")
            profile["Who"]["Insider Transactions"] = None
        
        # Insider Purchases
        try:
            insider_purchases = safe_get(lambda: ticker.insider_purchases, None)
            if insider_purchases is not None and not insider_purchases.empty:
                purchases_list = []
                for idx, row in insider_purchases.iterrows():
                    purchase = {}
                    for col in insider_purchases.columns:
                        val = row[col]
                        if pd.notna(val):
                            purchase[str(col)] = float(val) if isinstance(val, (int, float)) else str(val)
                        else:
                            purchase[str(col)] = None
                    purchases_list.append(purchase)
                profile["Who"]["Insider Purchases"] = purchases_list
            else:
                profile["Who"]["Insider Purchases"] = None
        except Exception as e:
            debug(f"⚠️ Insider purchases failed: {e}")
            profile["Who"]["Insider Purchases"] = None
        
        # Insider Roster Holders
        try:
            insider_roster = safe_get(lambda: ticker.insider_roster_holders, None)
            if insider_roster is not None and not insider_roster.empty:
                roster_list = []
                for idx, row in insider_roster.iterrows():
                    roster_item = {}
                    for col in insider_roster.columns:
                        val = row[col]
                        if pd.notna(val):
                            roster_item[str(col)] = float(val) if isinstance(val, (int, float)) else str(val)
                        else:
                            roster_item[str(col)] = None
                    roster_list.append(roster_item)
                profile["Who"]["Insider Roster Holders"] = roster_list
            else:
                profile["Who"]["Insider Roster Holders"] = None
        except Exception as e:
            debug(f"⚠️ Insider roster failed: {e}")
            profile["Who"]["Insider Roster Holders"] = None
        
        # ========== WHY IT MATTERS: Company Validation Metrics ==========
        profile["Why It Matters"] = {
            "Market Capitalization": info.get("marketCap"),
            "Enterprise Value": info.get("enterpriseValue"),
            "Shares Outstanding": info.get("sharesOutstanding"),
            "Float Shares": info.get("floatShares"),
            "Revenue TTM": info.get("totalRevenue"),
            "Profit Margin": info.get("profitMargins"),
            "Operating Margin": info.get("operatingMargins"),
            "Return on Equity": info.get("returnOnEquity"),
            "Return on Assets": info.get("returnOnAssets"),
            "Gross Profit": info.get("grossProfits"),
            "EBITDA": info.get("ebitda"),
            "Net Income": info.get("netIncomeToCommon"),
        }
        
        return profile
        
    except Exception as e:
        debug(f"⚠️ Failed to get company profile: {e}")
        return None


# ------------------ RUN SCRIPT ------------------

ticker = input("Enter Stock Ticker (e.g., TSLA, NVDA, AAPL): ").upper()

profile_data = get_company_profile(ticker)

if profile_data:
    save_json(f"company_profile_{ticker}.json", profile_data)
    print(f"✅ Company profile saved to company_profile_{ticker}.json")
else:
    print(f"❌ Failed to fetch company profile for {ticker}")
