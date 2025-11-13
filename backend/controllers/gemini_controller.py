"""
Gemini Controller
Controller for Gemini scraping operations
"""
from services.gemini_scraper_service import fetch_company_profile_from_gemini
from typing import Optional, Dict


class GeminiController:
    """Controller for Gemini scraping operations"""
    
    async def fetch_company_profile(self, ticker: str) -> Optional[Dict]:
        """
        Fetch company profile from Gemini AI
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, CIFR)
            
        Returns:
            Dict containing company profile data or None if failed
        """
        try:
            profile_data = await fetch_company_profile_from_gemini(ticker.upper())
            return profile_data
        except Exception as e:
            print(f"❌ Error fetching company profile: {e}")
            return None

