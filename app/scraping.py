"""Scraping orchestrator that manages adapters and fetches listing data."""
import asyncio
from urllib.parse import urlparse
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page

from .adapters.base import BaseAdapter
from .adapters.ebay import EbayAdapter
from .adapters.generic import GenericAdapter


class ScrapingOrchestrator:
    """Orchestrates scraping using registered adapters."""
    
    def __init__(self):
        self.adapters: list[BaseAdapter] = []
        self._register_adapters()
    
    def _register_adapters(self):
        """Register all available adapters in order of preference."""
        # Add specific adapters first (most specific to least specific)
        self.adapters.append(EbayAdapter())
        
        # Add generic adapter last as fallback
        self.adapters.append(GenericAdapter())
    
    def find_adapter(self, url: str) -> BaseAdapter:
        """Find the best adapter for the given URL."""
        domain = self._extract_domain(url)
        
        # Try specific adapters first
        for adapter in self.adapters:
            if domain in adapter.domains:
                return adapter
        
        # Fallback to generic adapter
        return self.adapters[-1]  # GenericAdapter is always last
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except:
            return "unknown"
    
    async def fetch_listing(self, url: str) -> Dict[str, Any]:
        """
        Fetch listing data from a URL using the appropriate adapter.
        
        Args:
            url: The URL to scrape
            
        Returns:
            Dict with scraped data or fallback data if scraping fails
        """
        adapter = self.find_adapter(url)
        
        try:
            async with async_playwright() as p:
                # Launch browser in headless mode
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    # Navigate to the page
                    await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                    
                    # Scrape using the adapter
                    result = await adapter.scrape(page, url)
                    
                    return result
                    
                except Exception as e:
                    print(f"Error scraping {url}: {e}")
                    # Return fallback result
                    return self._get_fallback_result(url)
                    
                finally:
                    await browser.close()
                    
        except Exception as e:
            print(f"Error launching browser for {url}: {e}")
            return self._get_fallback_result(url)
    
    def _get_fallback_result(self, url: str) -> Dict[str, Any]:
        """Get fallback result when scraping fails."""
        domain = self._extract_domain(url)
        return {
            "title": url,  # Use URL as title fallback
            "image_url": None,
            "site_name": domain,
            "currency": "USD",
            "price": None,
            "flags": {}
        }


# Global orchestrator instance
orchestrator = ScrapingOrchestrator()


async def fetch_listing(url: str) -> Dict[str, Any]:
    """
    Convenience function to fetch listing data.
    
    Args:
        url: The URL to scrape
        
    Returns:
        Dict with scraped data
    """
    return await orchestrator.fetch_listing(url)
