from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import settings
from app.controllers import scraper_controller, embedding_controller, multi_query_controller, chat_controller


# Create FastAPI app
app = FastAPI(
    title="GitLab Chatbot API",
    description="API for scraping GitLab Handbook and Direction pages",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(scraper_controller.router)
app.include_router(embedding_controller.router)
app.include_router(multi_query_controller.router)
app.include_router(chat_controller.router)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "GitLab Chatbot API",
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    from app.services.database_service import database_service
    
    return {
        "status": "healthy",
        "database_connected": database_service.is_connected(),
        "save_to_database": settings.save_to_database
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

