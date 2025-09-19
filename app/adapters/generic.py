"""Generic adapter for fallback scraping."""
from typing import Dict, Any
from playwright.async_api import Page

from .base import BaseAdapter


class GenericAdapter(BaseAdapter):
    """Generic adapter for any website using OpenGraph metadata."""
    
    domains = ["*"]  # Matches any domain
    
    async def scrape(self, page: Page, url: str) -> Dict[str, Any]:
        """Scrape generic product information using OpenGraph."""
        result = {
            "title": None,
            "image_url": None,
            "site_name": None,
            "currency": "USD",
            "price": None,
            "flags": {}
        }
        
        try:
            # Extract OpenGraph metadata
            result["title"] = await self._get_meta_property(page, "og:title")
            result["image_url"] = await self._get_meta_property(page, "og:image")
            result["site_name"] = await self._get_meta_property(page, "og:site_name")
            
            # Fallback to page title if no og:title
            if not result["title"]:
                result["title"] = await page.title()
            
            # Extract domain as site_name fallback
            if not result["site_name"]:
                from urllib.parse import urlparse
                parsed = urlparse(url)
                result["site_name"] = parsed.netloc.replace('www.', '')
                
        except Exception as e:
            print(f"Generic adapter error for {url}: {e}")
        
        return result
    
    async def _get_meta_property(self, page: Page, property_name: str) -> str:
        """Get OpenGraph meta property value."""
        try:
            element = await page.query_selector(f'meta[property="{property_name}"]')
            if element:
                return await element.get_attribute("content")
        except:
            pass
        return None
