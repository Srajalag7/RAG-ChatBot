import uvicorn
from app.config.settings import settings

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", settings.api_port))

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=port,
        reload=False
    )

