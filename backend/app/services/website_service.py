"""
Website integration and scraping service
Supports Shopify, WordPress, and custom sites
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin, urlparse
import re

import requests
import aiohttp
import asyncio
from bs4 import BeautifulSoup
import bleach

from ..models.responses import Product, SiteMeta, WebsiteIntegrationResponse

logger = logging.getLogger(__name__)

class WebsiteService:
    def __init__(self):
        self.session_timeout = 30
        self.max_products = 50
        self.allowed_tags = ['p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']
    
    async def integrate_website(
        self,
        platform: str,
        url: str,
        oauth: Optional[Dict[str, Any]] = None
    ) -> WebsiteIntegrationResponse:
        """
        Integrate with a website and extract products and metadata
        
        Args:
            platform: 'shopify', 'wordpress', or 'custom'
            url: Website URL
            oauth: OAuth credentials if available
        
        Returns:
            WebsiteIntegrationResponse with products and site metadata
        """
        try:
            if platform == "shopify":
                return await self._integrate_shopify(url, oauth)
            elif platform == "wordpress":
                return await self._integrate_wordpress(url, oauth)
            else:
                return await self._integrate_custom(url)
                
        except Exception as e:
            logger.error(f"Website integration failed for {url}: {str(e)}")
            # Return empty response on error
            return WebsiteIntegrationResponse(
                products=[],
                site_meta=SiteMeta(title="Unknown Site", description=""),
                sample_images=[]
            )
    
    async def _integrate_shopify(self, url: str, oauth: Optional[Dict[str, Any]]) -> WebsiteIntegrationResponse:
        """Integrate with Shopify store"""
        try:
            # Try Shopify API first if we have credentials
            if oauth and oauth.get('access_token'):
                return await self._shopify_api_integration(url, oauth['access_token'])
            
            # Fallback to public endpoints
            return await self._shopify_public_integration(url)
            
        except Exception as e:
            logger.error(f"Shopify integration failed: {str(e)}")
            return await self._integrate_custom(url)
    
    async def _shopify_api_integration(self, url: str, access_token: str) -> WebsiteIntegrationResponse:
        """Use Shopify Admin API"""
        shop_domain = self._extract_shopify_domain(url)
        api_url = f"https://{shop_domain}/admin/api/2023-10/products.json"
        
        headers = {
            'X-Shopify-Access-Token': access_token,
            'Content-Type': 'application/json'
        }
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.get(api_url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    products = self._parse_shopify_products(data.get('products', []))
                    
                    # Get shop info
                    shop_url = f"https://{shop_domain}/admin/api/2023-10/shop.json"
                    async with session.get(shop_url, headers=headers) as shop_response:
                        shop_data = await shop_response.json() if shop_response.status == 200 else {}
                        site_meta = self._parse_shopify_shop_meta(shop_data.get('shop', {}))
                    
                    return WebsiteIntegrationResponse(
                        products=products[:self.max_products],
                        site_meta=site_meta,
                        sample_images=self._extract_sample_images(products)
                    )
        
        # Fallback to public integration
        return await self._shopify_public_integration(url)
    
    async def _shopify_public_integration(self, url: str) -> WebsiteIntegrationResponse:
        """Use Shopify public endpoints"""
        try:
            shop_domain = self._extract_shopify_domain(url)
            products_url = f"https://{shop_domain}/products.json"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
                async with session.get(products_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        products = self._parse_shopify_products(data.get('products', []))
                        
                        # Get site metadata by scraping
                        site_meta = await self._scrape_site_meta(url, session)
                        
                        return WebsiteIntegrationResponse(
                            products=products[:self.max_products],
                            site_meta=site_meta,
                            sample_images=self._extract_sample_images(products)
                        )
        except Exception as e:
            logger.error(f"Shopify public integration failed: {str(e)}")
        
        # Final fallback to custom scraping
        return await self._integrate_custom(url)
    
    async def _integrate_wordpress(self, url: str, oauth: Optional[Dict[str, Any]]) -> WebsiteIntegrationResponse:
        """Integrate with WordPress site (WooCommerce)"""
        try:
            # Try WooCommerce REST API if credentials available
            if oauth and oauth.get('consumer_key') and oauth.get('consumer_secret'):
                return await self._woocommerce_api_integration(url, oauth)
            
            # Fallback to scraping
            return await self._integrate_custom(url)
            
        except Exception as e:
            logger.error(f"WordPress integration failed: {str(e)}")
            return await self._integrate_custom(url)
    
    async def _woocommerce_api_integration(self, url: str, oauth: Dict[str, Any]) -> WebsiteIntegrationResponse:
        """Use WooCommerce REST API"""
        api_url = f"{url.rstrip('/')}/wp-json/wc/v3/products"
        
        auth = aiohttp.BasicAuth(oauth['consumer_key'], oauth['consumer_secret'])
        
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            async with session.get(api_url, auth=auth, params={'per_page': self.max_products}) as response:
                if response.status == 200:
                    products_data = await response.json()
                    products = self._parse_woocommerce_products(products_data)
                    
                    site_meta = await self._scrape_site_meta(url, session)
                    
                    return WebsiteIntegrationResponse(
                        products=products,
                        site_meta=site_meta,
                        sample_images=self._extract_sample_images(products)
                    )
        
        return await self._integrate_custom(url)
    
    async def _integrate_custom(self, url: str) -> WebsiteIntegrationResponse:
        """Scrape custom website for products and metadata"""
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.session_timeout)) as session:
            # Get site metadata
            site_meta = await self._scrape_site_meta(url, session)
            
            # Try to find products
            products = await self._scrape_products(url, session)
            
            return WebsiteIntegrationResponse(
                products=products[:self.max_products],
                site_meta=site_meta,
                sample_images=self._extract_sample_images(products)
            )
    
    async def _scrape_site_meta(self, url: str, session: aiohttp.ClientSession) -> SiteMeta:
        """Scrape basic site metadata"""
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract title
                    title_tag = soup.find('title')
                    title = title_tag.get_text().strip() if title_tag else "Unknown Site"
                    
                    # Extract description
                    desc_tag = soup.find('meta', attrs={'name': 'description'}) or \
                              soup.find('meta', attrs={'property': 'og:description'})
                    description = desc_tag.get('content', '').strip() if desc_tag else ""
                    
                    # Extract logo
                    logo_tag = soup.find('meta', attrs={'property': 'og:image'}) or \
                              soup.find('link', attrs={'rel': 'icon'})
                    logo = None
                    if logo_tag:
                        logo_url = logo_tag.get('content') or logo_tag.get('href')
                        if logo_url:
                            logo = urljoin(url, logo_url)
                    
                    # Extract theme colors
                    theme_colors = []
                    theme_color_tag = soup.find('meta', attrs={'name': 'theme-color'})
                    if theme_color_tag:
                        theme_colors.append(theme_color_tag.get('content', ''))
                    
                    return SiteMeta(
                        title=self._sanitize_text(title),
                        description=self._sanitize_text(description),
                        logo=logo,
                        theme_colors=theme_colors
                    )
        except Exception as e:
            logger.error(f"Failed to scrape site meta for {url}: {str(e)}")
        
        return SiteMeta(title="Unknown Site", description="")
    
    async def _scrape_products(self, url: str, session: aiohttp.ClientSession) -> List[Product]:
        """Scrape products from custom website"""
        products = []
        
        try:
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for JSON-LD structured data
                    json_ld_products = self._extract_json_ld_products(soup)
                    if json_ld_products:
                        products.extend(json_ld_products)
                    
                    # Look for microdata
                    microdata_products = self._extract_microdata_products(soup)
                    if microdata_products:
                        products.extend(microdata_products)
                    
                    # Fallback: look for common product patterns
                    if not products:
                        products = self._extract_pattern_products(soup, url)
                        
        except Exception as e:
            logger.error(f"Failed to scrape products from {url}: {str(e)}")
        
        return products
    
    def _extract_json_ld_products(self, soup: BeautifulSoup) -> List[Product]:
        """Extract products from JSON-LD structured data"""
        products = []
        
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, list):
                    data = data[0] if data else {}
                
                if data.get('@type') == 'Product':
                    product = self._parse_json_ld_product(data)
                    if product:
                        products.append(product)
                elif data.get('@type') == 'ItemList' and data.get('itemListElement'):
                    for item in data['itemListElement']:
                        if item.get('@type') == 'Product':
                            product = self._parse_json_ld_product(item)
                            if product:
                                products.append(product)
                                
            except (json.JSONDecodeError, KeyError) as e:
                logger.debug(f"Failed to parse JSON-LD: {str(e)}")
                continue
        
        return products
    
    def _parse_json_ld_product(self, data: Dict[str, Any]) -> Optional[Product]:
        """Parse a single product from JSON-LD data"""
        try:
            name = data.get('name', '')
            description = data.get('description', '')
            
            # Extract price
            offers = data.get('offers', {})
            if isinstance(offers, list):
                offers = offers[0] if offers else {}
            
            price = 0.0
            currency = 'USD'
            if offers:
                price = float(offers.get('price', 0))
                currency = offers.get('priceCurrency', 'USD')
            
            # Extract images
            images = []
            image_data = data.get('image', [])
            if isinstance(image_data, str):
                images = [image_data]
            elif isinstance(image_data, list):
                images = [img if isinstance(img, str) else img.get('url', '') for img in image_data]
            
            if name:
                return Product(
                    id=f"scraped_{hash(name)}",
                    name=self._sanitize_text(name),
                    description=self._sanitize_text(description),
                    price=price,
                    currency=currency,
                    images=images[:3],  # Limit to 3 images
                    category=data.get('category', '')
                )
                
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to parse JSON-LD product: {str(e)}")
        
        return None
    
    def _extract_microdata_products(self, soup: BeautifulSoup) -> List[Product]:
        """Extract products from microdata"""
        products = []
        
        for item in soup.find_all(attrs={'itemtype': re.compile(r'.*Product')}):
            try:
                name_elem = item.find(attrs={'itemprop': 'name'})
                name = name_elem.get_text().strip() if name_elem else ''
                
                desc_elem = item.find(attrs={'itemprop': 'description'})
                description = desc_elem.get_text().strip() if desc_elem else ''
                
                price_elem = item.find(attrs={'itemprop': 'price'})
                price = 0.0
                if price_elem:
                    price_text = price_elem.get('content') or price_elem.get_text()
                    price = float(re.sub(r'[^\d.]', '', price_text)) if price_text else 0.0
                
                # Extract images
                images = []
                for img in item.find_all('img', attrs={'itemprop': 'image'}):
                    src = img.get('src')
                    if src:
                        images.append(src)
                
                if name:
                    products.append(Product(
                        id=f"microdata_{hash(name)}",
                        name=self._sanitize_text(name),
                        description=self._sanitize_text(description),
                        price=price,
                        currency='USD',
                        images=images[:3]
                    ))
                    
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse microdata product: {str(e)}")
                continue
        
        return products
    
    def _extract_pattern_products(self, soup: BeautifulSoup, base_url: str) -> List[Product]:
        """Extract products using common HTML patterns"""
        products = []
        
        # Look for common product containers
        product_selectors = [
            '.product', '.product-item', '.product-card',
            '[data-product]', '.woocommerce-product',
            '.shop-item', '.catalog-item'
        ]
        
        for selector in product_selectors:
            items = soup.select(selector)
            if items:
                for item in items[:10]:  # Limit to 10 items per pattern
                    product = self._parse_pattern_product(item, base_url)
                    if product:
                        products.append(product)
                break  # Use first successful pattern
        
        return products
    
    def _parse_pattern_product(self, item: BeautifulSoup, base_url: str) -> Optional[Product]:
        """Parse product from HTML pattern"""
        try:
            # Extract name
            name_selectors = ['h1', 'h2', 'h3', '.title', '.name', '.product-title']
            name = ''
            for selector in name_selectors:
                name_elem = item.select_one(selector)
                if name_elem:
                    name = name_elem.get_text().strip()
                    break
            
            # Extract description
            desc_selectors = ['.description', '.summary', '.excerpt', 'p']
            description = ''
            for selector in desc_selectors:
                desc_elem = item.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text().strip()
                    break
            
            # Extract price
            price_selectors = ['.price', '.cost', '.amount', '[data-price]']
            price = 0.0
            for selector in price_selectors:
                price_elem = item.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text() or price_elem.get('data-price', '')
                    price_match = re.search(r'[\d.]+', price_text)
                    if price_match:
                        price = float(price_match.group())
                        break
            
            # Extract images
            images = []
            for img in item.find_all('img'):
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(base_url, src)
                    images.append(full_url)
            
            if name:
                return Product(
                    id=f"pattern_{hash(name)}",
                    name=self._sanitize_text(name),
                    description=self._sanitize_text(description),
                    price=price,
                    currency='USD',
                    images=images[:3]
                )
                
        except Exception as e:
            logger.debug(f"Failed to parse pattern product: {str(e)}")
        
        return None
    
    def _parse_shopify_products(self, products_data: List[Dict[str, Any]]) -> List[Product]:
        """Parse Shopify products data"""
        products = []
        
        for product_data in products_data:
            try:
                variants = product_data.get('variants', [])
                first_variant = variants[0] if variants else {}
                
                images = []
                for img in product_data.get('images', []):
                    if isinstance(img, dict):
                        images.append(img.get('src', ''))
                    else:
                        images.append(str(img))
                
                products.append(Product(
                    id=str(product_data.get('id', '')),
                    name=self._sanitize_text(product_data.get('title', '')),
                    description=self._sanitize_text(product_data.get('body_html', '')),
                    price=float(first_variant.get('price', 0)),
                    currency='USD',
                    images=images[:3],
                    category=product_data.get('product_type', '')
                ))
                
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse Shopify product: {str(e)}")
                continue
        
        return products
    
    def _parse_shopify_shop_meta(self, shop_data: Dict[str, Any]) -> SiteMeta:
        """Parse Shopify shop metadata"""
        return SiteMeta(
            title=self._sanitize_text(shop_data.get('name', 'Shopify Store')),
            description=self._sanitize_text(shop_data.get('description', '')),
            logo=shop_data.get('logo', {}).get('url') if shop_data.get('logo') else None
        )
    
    def _parse_woocommerce_products(self, products_data: List[Dict[str, Any]]) -> List[Product]:
        """Parse WooCommerce products data"""
        products = []
        
        for product_data in products_data:
            try:
                images = []
                for img in product_data.get('images', []):
                    images.append(img.get('src', ''))
                
                products.append(Product(
                    id=str(product_data.get('id', '')),
                    name=self._sanitize_text(product_data.get('name', '')),
                    description=self._sanitize_text(product_data.get('description', '')),
                    price=float(product_data.get('price', 0)),
                    currency='USD',
                    images=images[:3],
                    category=', '.join([cat.get('name', '') for cat in product_data.get('categories', [])])
                ))
                
            except (ValueError, TypeError) as e:
                logger.debug(f"Failed to parse WooCommerce product: {str(e)}")
                continue
        
        return products
    
    def _extract_sample_images(self, products: List[Product]) -> List[str]:
        """Extract sample images from products"""
        images = []
        for product in products:
            images.extend(product.images)
            if len(images) >= 10:  # Limit to 10 sample images
                break
        return images[:10]
    
    def _extract_shopify_domain(self, url: str) -> str:
        """Extract Shopify domain from URL"""
        parsed = urlparse(url)
        domain = parsed.netloc
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize HTML text content"""
        if not text:
            return ""
        
        # Remove HTML tags and sanitize
        clean_text = bleach.clean(text, tags=self.allowed_tags, strip=True)
        
        # Remove extra whitespace
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()
        
        return clean_text[:500]  # Limit length

# Global instance
website_service = WebsiteService()
