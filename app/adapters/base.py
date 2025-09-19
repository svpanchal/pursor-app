"""Base adapter interface for web scraping."""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from playwright.async_api import Page


class BaseAdapter(ABC):
    """Base class for all scraping adapters."""
    
    # List of domains this adapter can handle
    domains: List[str]
    
    @abstractmethod
    async def scrape(self, page: Page, url: str) -> Dict[str, Any]:
        """
        Scrape product information from a page.
        
        Args:
            page: Playwright page object
            url: The URL being scraped
            
        Returns:
            Dict with keys: title, image_url, site_name, currency, price, flags
            - title: str or None
            - image_url: str or None  
            - site_name: str or None
            - currency: str (default "USD")
            - price: float or None (price in dollars)
            - flags: dict with keys like free_shipping, accepts_offers, etc.
        """
        pass
