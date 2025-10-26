from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List

from app.models.schemas import (
    ScrapeRequest,
    ScrapeResponse,
    ScrapedDataOutput,
    AvailableSitesResponse,
    SiteConfig
)
from app.services.scraper_service import scraper_service


router = APIRouter(prefix="/scraper", tags=["Scraper"])


@router.get("/sites", response_model=AvailableSitesResponse)
async def get_available_sites():
    """Get all available sites from configuration"""
    sites_config = scraper_service.get_available_sites()
    
    # Convert to proper format
    formatted_sites = {}
    for site_name, configs in sites_config.items():
        formatted_sites[site_name] = [
            SiteConfig(**cfg) for cfg in configs
        ]
    
    return AvailableSitesResponse(sites=formatted_sites)


@router.post("/scrape", response_model=ScrapeResponse)
async def scrape_site(request: ScrapeRequest):
    """
    Scrape a site and store all discovered URLs
    
    - **site_name**: Name of the site from configuration (e.g., 'gitlab')
    - **max_depth**: Optional override for maximum scraping depth
    """
    try:
        result = await scraper_service.scrape_site(
            site_name=request.site_name,
            max_depth=request.max_depth
        )
        
        return ScrapeResponse(
            site_name=result.site_name,
            urls_count=result.total_urls,
            file_path="Database",
            scraped_at=result.scraped_at,
            message=f"Successfully scraped {result.total_urls} URLs ({result.total_content_pages} with content) from {len(result.base_urls)} base URL(s)"
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error scraping site: {str(e)}")



