"""
Supply Chain Controller
Controller for supply chain operations
"""
from services.supply_chain_service import (
    fetch_supply_chain_from_gemini,
    generate_supply_chain_graph_html,
    generate_supply_chain_graph_html_from_data,
    fetch_and_generate_supply_chain
)
from services.company_profile_service import CompanyProfileService
from typing import Optional, Dict


class SupplyChainController:
    """Controller for supply chain operations"""
    
    async def fetch_supply_chain(self, ticker: str) -> Optional[Dict]:
        """
        Fetch supply chain data from Gemini AI
        
        Args:
            ticker: Stock ticker symbol (e.g., AAPL, TSLA)
            
        Returns:
            Dict containing supply chain data or None if failed
        """
        try:
            supply_chain_data = await fetch_supply_chain_from_gemini(ticker.upper())
            return supply_chain_data
        except Exception as e:
            print(f"❌ Error fetching supply chain data: {e}")
            return None
    
    async def generate_graph(self, data: Dict, ticker: str) -> Optional[str]:
        """
        Generate HTML graph from supply chain data
        
        Args:
            data: Supply chain data dictionary
            ticker: Stock ticker symbol
            
        Returns:
            Path to generated HTML file or None if failed
        """
        try:
            graph_file = await generate_supply_chain_graph_html(data, ticker.upper())
            return graph_file
        except Exception as e:
            print(f"❌ Error generating graph: {e}")
            return None
    
    async def fetch_and_generate(self, ticker: str) -> Optional[Dict]:
        """
        Complete pipeline: Fetch supply chain data and generate graph
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            Dict with 'data' and 'graph_file' or None if failed
        """
        try:
            result = await fetch_and_generate_supply_chain(ticker.upper())
            return result
        except Exception as e:
            print(f"❌ Error in fetch and generate: {e}")
            return None
    
    async def generate_graph_html_from_db(self, ticker: str) -> Optional[str]:
        """
        Generate HTML graph from data stored in MongoDB
        
        Args:
            ticker: Stock ticker symbol
            
        Returns:
            HTML string or None if failed
        """
        try:
            # Fetch data from database
            service = CompanyProfileService()
            profile = await service.get_by_ticker(ticker.upper())
            
            if not profile or not profile.data:
                return None
            
            # Extract supply chain data
            supply_chain_data = profile.data.get("SupplyChain")
            if not supply_chain_data:
                return None
            
            # Generate HTML from data
            html_content = await generate_supply_chain_graph_html_from_data(
                supply_chain_data,
                ticker.upper()
            )
            
            return html_content
        except Exception as e:
            print(f"❌ Error generating graph from database: {e}")
            import traceback
            traceback.print_exc()
            return None

