"""eBay adapter for scraping product information."""
import re
from typing import Dict, Any
from playwright.async_api import Page

from .base import BaseAdapter


class EbayAdapter(BaseAdapter):
    """Adapter for eBay product pages."""
    
    domains = ["ebay.com", "www.ebay.com"]
    
    async def scrape(self, page: Page, url: str) -> Dict[str, Any]:
        """Scrape eBay product information."""
        result = {
            "title": None,
            "image_url": None,
            "site_name": "eBay",
            "currency": "USD",
            "price": None,
            "flags": {}
        }
        
        try:
            # Extract OpenGraph metadata
            result["title"] = await self._get_meta_property(page, "og:title")
            result["image_url"] = await self._get_meta_property(page, "og:image")
            
            # Extract price using multiple strategies
            price_info = await self._extract_price(page)
            if price_info:
                result["price"] = price_info["price"]
                result["currency"] = price_info["currency"]
            
            # Extract flags
            result["flags"] = await self._extract_flags(page)
            
        except Exception as e:
            print(f"eBay adapter error for {url}: {e}")
        
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
    
    async def _extract_price(self, page: Page) -> Dict[str, Any]:
        """Extract price using multiple strategies."""
        # Strategy 1: Try specific eBay price selectors
        price_selectors = [
            "#prcIsum",
            "[data-testid='x-bin-price']",
            "[data-testid='x-price-primary']", 
            "#mm-saleDscPrc",
            "#prcIsum_bidPrice",
            ".notranslate",
            ".u-flL.condText"
        ]
        
        for selector in price_selectors:
            try:
                element = await page.query_selector(selector)
                if element:
                    text = await element.inner_text()
                    price_info = self._parse_price_text(text)
                    if price_info:
                        return price_info
            except:
                continue
        
        # Strategy 2: Regex over page text
        try:
            body_text = await page.inner_text("body")
            price_info = self._parse_price_text(body_text)
            if price_info:
                return price_info
        except:
            pass
        
        return None
    
    def _parse_price_text(self, text: str) -> Dict[str, Any]:
        """Parse price from text using regex patterns."""
        if not text:
            return None
        
        # Clean up text
        text = text.replace(",", "").strip()
        
        # Price patterns: $123.45, US $123.45, GBP 123.45, EUR 123.45
        patterns = [
            r'US\s*\$(\d+\.?\d*)',
            r'GBP\s*(\d+\.?\d*)', 
            r'EUR\s*(\d+\.?\d*)',
            r'\$(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*USD',
            r'(\d+\.?\d*)\s*GBP',
            r'(\d+\.?\d*)\s*EUR'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    price = float(match.group(1))
                    if price > 0:  # Valid price
                        currency = "USD"
                        if "GBP" in pattern.upper():
                            currency = "GBP"
                        elif "EUR" in pattern.upper():
                            currency = "EUR"
                        return {"price": price, "currency": currency}
                except ValueError:
                    continue
        
        return None
    
    async def _extract_flags(self, page: Page) -> Dict[str, Any]:
        """Extract special flags from the page."""
        flags = {}
        
        try:
            # Get page text for flag detection
            body_text = await page.inner_text("body")
            text_lower = body_text.lower()
            
            # Check for Best Offer / Make Offer
            if any(phrase in text_lower for phrase in ["best offer", "make offer"]):
                flags["accepts_offers"] = True
            
            # Check for free shipping
            if any(phrase in text_lower for phrase in ["free shipping", "free Shipping", "FREE Shipping"]):
                flags["free_shipping"] = True
                
        except Exception as e:
            print(f"Error extracting flags: {e}")
        
        return flags
