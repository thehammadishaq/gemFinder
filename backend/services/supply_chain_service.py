"""
Supply Chain Service
Service for fetching and processing supply chain data from Gemini AI
"""
import sys
import os
import json
import re
from typing import Dict, Optional, List
import asyncio

# Add supply-chain-graphs to path
supply_chain_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "supply-chain-graphs")
if supply_chain_path not in sys.path:
    sys.path.insert(0, supply_chain_path)

# Import from supply-chain-graphs
from supply_chain_fetcher import (
    fetch_supply_chain_data,
    parse_supply_chain_json,
    convert_to_graph_format,
    get_logo_url
)
from generate_graph import generate_supply_chain_graph


async def fetch_supply_chain_from_gemini(ticker: str) -> Optional[Dict]:
    """
    Fetch supply chain data from Gemini AI (async wrapper)
    
    Args:
        ticker: Stock ticker symbol (e.g., AAPL, TSLA)
        
    Returns:
        Dict containing supply chain data or None if failed
    """
    try:
        # Run synchronous function in thread pool
        loop = asyncio.get_event_loop()
        response_text = await loop.run_in_executor(
            None,
            fetch_supply_chain_data,
            ticker.upper()
        )
        
        if not response_text:
            return None
        
        # Parse JSON
        parsed_data = await loop.run_in_executor(
            None,
            parse_supply_chain_json,
            response_text
        )
        
        if not parsed_data:
            return None
        
        # Convert to graph format
        graph_data = await loop.run_in_executor(
            None,
            convert_to_graph_format,
            parsed_data,
            ticker.upper()
        )
        
        return graph_data
        
    except Exception as e:
        print(f"❌ Error fetching supply chain data: {e}")
        import traceback
        traceback.print_exc()
        return None


async def generate_supply_chain_graph_html(
    data: Dict,
    ticker: str,
    output_dir: Optional[str] = None
) -> Optional[str]:
    """
    Generate HTML graph from supply chain data
    
    Args:
        data: Supply chain data dictionary
        ticker: Stock ticker symbol
        output_dir: Directory to save HTML file (optional)
        
    Returns:
        Path to generated HTML file or None if failed
    """
    try:
        import tempfile
        
        # Create temporary file for data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            temp_data_file = f.name
        
        # Determine output directory
        if not output_dir:
            output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "supply-chain-graphs")
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate output filename
        output_file = os.path.join(output_dir, f"{ticker.lower()}_supply_chain.html")
        
        # Extract company name
        company_name = data.get("company", f"{ticker} Corporation")
        
        # Run graph generation in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            generate_supply_chain_graph,
            temp_data_file,
            output_file,
            company_name
        )
        
        # Clean up temp file
        try:
            os.unlink(temp_data_file)
        except:
            pass
        
        if result:
            return output_file
        return None
        
    except Exception as e:
        print(f"❌ Error generating graph: {e}")
        import traceback
        traceback.print_exc()
        return None


async def fetch_and_generate_supply_chain(ticker: str, output_dir: Optional[str] = None) -> Optional[Dict]:
    """
    Complete pipeline: Fetch supply chain data and generate graph
    
    Args:
        ticker: Stock ticker symbol
        output_dir: Directory to save HTML file (optional)
        
    Returns:
        Dict with 'data' (supply chain data) and 'graph_file' (path to HTML) or None if failed
    """
    # Fetch data
    supply_chain_data = await fetch_supply_chain_from_gemini(ticker)
    
    if not supply_chain_data:
        return None
    
    # Generate graph
    graph_file = await generate_supply_chain_graph_html(supply_chain_data, ticker, output_dir)
    
    return {
        "data": supply_chain_data,
        "graph_file": graph_file
    }


async def generate_supply_chain_graph_html_from_data(
    data: Dict,
    ticker: str
) -> Optional[str]:
    """
    Generate HTML graph from supply chain data in memory (returns HTML string)
    
    This is used for server-side rendering - generates HTML without saving to file.
    
    Args:
        data: Supply chain data dictionary
        ticker: Stock ticker symbol
        
    Returns:
        HTML string or None if failed
    """
    try:
        import tempfile
        import io
        
        # Create temporary file for data (required by generate_supply_chain_graph)
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            temp_data_file = f.name
        
        # Create temporary output file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False, encoding='utf-8') as f:
            temp_output_file = f.name
        
        # Extract company name
        company_name = data.get("company", f"{ticker} Corporation")
        
        # Run graph generation in thread pool
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            generate_supply_chain_graph,
            temp_data_file,
            temp_output_file,
            company_name
        )
        
        # Read generated HTML
        html_content = None
        if result:
            with open(temp_output_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
        
        # Clean up temp files
        try:
            os.unlink(temp_data_file)
        except:
            pass
        try:
            os.unlink(temp_output_file)
        except:
            pass
        
        return html_content
        
    except Exception as e:
        print(f"❌ Error generating graph HTML: {e}")
        import traceback
        traceback.print_exc()
        return None

