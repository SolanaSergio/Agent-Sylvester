import aiohttp
import asyncio
from typing import Optional, Dict
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

class WebScraper:
    """Scrapes websites for analysis"""
    
    def __init__(self):
        self.session = None
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
    async def _ensure_session(self):
        if self.session is None:
            self.session = aiohttp.ClientSession(headers=self._headers)
            
    async def scrape_url(self, url: str) -> Optional[str]:
        """Scrape a URL and return its HTML content"""
        try:
            await self._ensure_session()
            
            async with self.session.get(url, timeout=30) as response:
                if response.status == 200:
                    return await response.text()
                else:
                    logging.error(f"Failed to fetch {url}: Status {response.status}")
                    return None
                    
        except aiohttp.ClientError as e:
            logging.error(f"Network error scraping {url}: {str(e)}")
            return None
        except asyncio.TimeoutError:
            logging.error(f"Timeout scraping {url}")
            return None
        except Exception as e:
            logging.error(f"Error scraping {url}: {str(e)}")
            return None
            
    async def scrape_assets(self, base_url: str, html_content: str) -> Dict[str, str]:
        """Scrape associated assets (CSS, images, etc.)"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            assets = {}
            
            # Scrape CSS
            for css in soup.find_all('link', rel='stylesheet'):
                if css.get('href'):
                    css_url = urljoin(base_url, css['href'])
                    css_content = await self._fetch_asset(css_url)
                    if css_content:
                        assets[css_url] = css_content
                        
            # Scrape images
            for img in soup.find_all('img'):
                if img.get('src'):
                    img_url = urljoin(base_url, img['src'])
                    assets[img_url] = img_url  # Store URL for later download
                    
            return assets
            
        except Exception as e:
            logging.error(f"Error scraping assets from {base_url}: {str(e)}")
            return {}
            
    async def _fetch_asset(self, url: str) -> Optional[str]:
        """Fetch a single asset"""
        try:
            await self._ensure_session()
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                return None
                
        except Exception as e:
            logging.error(f"Error fetching asset {url}: {str(e)}")
            return None
            
    async def close(self):
        """Close the aiohttp session"""
        if self.session:
            try:
                await self.session.close()
            except Exception as e:
                logging.error(f"Error closing web scraper session: {str(e)}")
            finally:
                self.session = None 