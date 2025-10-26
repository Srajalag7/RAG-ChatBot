import json
import re
import time
from datetime import datetime
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

from app.config.settings import settings
from app.models.schemas import UrlData, ScrapedDataOutput
from app.services.database_service import database_service


class ScraperService:
    """Service for scraping websites and storing URLs"""
    
    def __init__(self):
        self.settings = settings
    
    async def scrape_site(self, site_name: str, max_depth: int = None) -> ScrapedDataOutput:
        """
        Scrape a site and store all discovered URLs
        
        Args:
            site_name: Name of the site from configuration
            max_depth: Maximum depth for recursive scraping (overrides config)
        
        Returns:
            ScrapedDataOutput with all discovered URLs
        """
        # Get site configuration
        sites_config = self.settings.get_sites_config()
        
        if site_name not in sites_config:
            raise ValueError(f"Site '{site_name}' not found in configuration")
        
        site_configs = sites_config[site_name]
        enabled_urls = [cfg["url"] for cfg in site_configs if cfg.get("enabled", True)]
        
        if not enabled_urls:
            raise ValueError(f"No enabled URLs found for site '{site_name}'")
        
        # Use provided max_depth or fall back to settings
        depth = max_depth if max_depth is not None else self.settings.max_depth
        
        # Get existing URLs from database for this site
        existing_urls = set()
        if database_service.is_connected():
            existing_urls = set(await self._get_existing_urls_from_db(site_name))
            if existing_urls:
                print(f"Found {len(existing_urls)} existing URLs in database for site '{site_name}'")
        
        # Extract all links first
        all_urls_set: Set[str] = set()
        url_data_list: List[UrlData] = []
        content_pages_count = 0
        
        for base_url in enabled_urls:
            print(f"Extracting links from {base_url} with max_depth={depth}...")
            urls = self._extract_all_links(base_url, depth)
            
            for url, url_depth in urls.items():
                if url not in all_urls_set:
                    all_urls_set.add(url)
                    
                    # Check if URL already exists in database
                    if url in existing_urls:
                        print(f"Skipping existing URL: {url}")
                        continue
                    
                    # Process new URL
                    print(f"Processing new URL: {url}")
                    
                    # Extract content and save immediately
                    content_data = self._extract_page_content(url)
                    content = content_data.get('content') if content_data else None
                    title = content_data.get('title') if content_data else None
                    status_code = content_data.get('status_code') if content_data else None
                    
                    if content and len(content.strip()) > 0:
                        content_pages_count += 1
                        
                        # Save to database immediately
                        if database_service.is_connected():
                            await database_service.save_url_with_content(
                                site_name, url, url_depth, content, title
                            )
                    
                    url_data_list.append(
                        UrlData(
                            url=url,
                            discovered_at=datetime.now().isoformat(),
                            depth=url_depth,
                            content=content,
                            content_length=len(content) if content else 0,
                            title=title,
                            status_code=status_code
                        )
                    )

                    print(f"Added new URL: {url} to list")
        
        # Create output data
        scraped_at = datetime.now().isoformat()
        output_data = ScrapedDataOutput(
            site_name=site_name,
            base_urls=enabled_urls,
            max_depth=depth,
            total_urls=len(url_data_list),
            total_content_pages=content_pages_count,
            scraped_at=scraped_at,
            urls=url_data_list
        )
        
        return output_data
    
    def _extract_all_links(self, base_url: str, max_depth: int) -> Dict[str, int]:
        """
        Extract all links from a website up to max_depth
        
        Args:
            base_url: Starting URL
            max_depth: Maximum depth for link extraction
        
        Returns:
            Dictionary mapping URLs to their depth level
        """
        url_depth_map: Dict[str, int] = {}
        visited_urls: Set[str] = set()
        urls_to_process: List[tuple[str, int]] = [(base_url, 0)]
        
        while urls_to_process:
            current_url, current_depth = urls_to_process.pop(0)
            
            if current_url in visited_urls or current_depth > max_depth:
                continue
                
            visited_urls.add(current_url)
            url_depth_map[current_url] = current_depth
            
            if current_depth < max_depth:
                # Extract links from current page
                links = self._extract_links_from_page(current_url)
                print(f"Found {len(links)} links from {current_url}")
                
                for link in links:
                    if link not in visited_urls and link not in [url for url, _ in urls_to_process]:
                        urls_to_process.append((link, current_depth + 1))
        
        print(f"Found {len(url_depth_map)} URLs from {base_url}")
        return url_depth_map
    
    def _extract_links_from_page(self, url: str) -> List[str]:
        """Extract all links from a single page"""
        try:
            response = requests.get(
                url, 
                timeout=self.settings.request_timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code != 200:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            links = []
            
            # Extract all href attributes
            for link in soup.find_all('a', href=True):
                href = link['href']
                absolute_url = urljoin(url, href)
                
                # Filter out unwanted URLs
                if self._is_valid_url(absolute_url, url):
                    links.append(absolute_url)
            
            return list(set(links))  # Remove duplicates
            
        except Exception as e:
            print(f"Error extracting links from {url}: {str(e)}")
            return []
    
    def _is_valid_url(self, url: str, base_url: str) -> bool:
        """Check if URL is valid for scraping"""
        try:
            parsed_url = urlparse(url)
            parsed_base = urlparse(base_url)
            
            # Must be HTTP/HTTPS
            if parsed_url.scheme not in ['http', 'https']:
                return False
            
            # Must be from same domain
            if parsed_url.netloc != parsed_base.netloc:
                return False
            
            # Skip common non-content URLs
            skip_patterns = [
                '/api/', '/admin/', '/login/', '/logout/', '/register/',
                '.pdf', '.doc', '.docx', '.zip', '.rar', '.exe',
                'mailto:', 'tel:', 'javascript:', '#'
            ]
            
            for pattern in skip_patterns:
                if pattern in url.lower():
                    return False
            
            return True
            
        except Exception:
            return False
    
    def _calculate_url_depth(self, base_url: str, url: str) -> int:
        """Calculate the depth of a URL relative to base URL"""
        base_path = base_url.rstrip("/").split("/")
        url_path = url.rstrip("/").split("/")
        
        # Count additional path segments beyond base
        if len(url_path) > len(base_path):
            return len(url_path) - len(base_path)
        return 0
    
    def _extract_page_content(self, url: str) -> Optional[Dict]:
        """Extract content from a single page"""
        try:
            print(f"Extracting content from: {url}")
            
            # Add delay between requests
            if self.settings.request_delay > 0:
                time.sleep(self.settings.request_delay)
            
            response = requests.get(
                url, 
                timeout=self.settings.request_timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            
            if response.status_code != 200:
                return {
                    'content': None,
                    'content_length': 0,
                    'title': None,
                    'status_code': response.status_code
                }
            
            # Parse HTML content
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract title
            title_tag = soup.find('title')
            title = title_tag.get_text().strip() if title_tag else None
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Get main content areas
            main_content = soup.find('main') or soup.find('article') or soup.find('div', class_='content')
            if main_content:
                content = main_content.get_text()
            else:
                content = soup.get_text()
            
            # Clean and normalize content
            content = self._normalize_content(content)
            
            # Limit content length
            if len(content) > self.settings.max_content_length:
                content = content[:self.settings.max_content_length]
            
            return {
                'content': content,
                'content_length': len(content),
                'title': title,
                'status_code': response.status_code
            }
            
        except Exception as e:
            print(f"Error extracting content from {url}: {str(e)}")
            return None
    
    def _normalize_content(self, content: str) -> str:
        """Normalize and clean content"""
        # Remove extra whitespace
        content = re.sub(r'\s+', ' ', content)
        # Remove leading/trailing whitespace
        content = content.strip()
        return content
    
    async def _get_existing_urls_from_db(self, site_name: str) -> List[str]:
        """Check if site already has URLs in database"""
        try:
            if not database_service.is_connected():
                return []
            
            # Get site ID first
            site_result = database_service.client.table("sites")\
                .select("id")\
                .eq("name", site_name)\
                .execute()
            
            if not site_result.data:
                return []
            
            site_id = site_result.data[0]["id"]
            
            # Get URLs for the site
            urls_result = database_service.client.table("scraped_urls")\
                .select("url")\
                .eq("site_id", site_id)\
                .execute()
            
            return [url["url"] for url in urls_result.data]
            
        except Exception as e:
            print(f"Error checking existing URLs: {str(e)}")
            return []
    
    def get_available_sites(self) -> Dict[str, List[Dict[str, any]]]:
        """Get all available sites from configuration"""
        return self.settings.get_sites_config()


# Global scraper service instance
scraper_service = ScraperService()

