"""
MarkezardAI FastAPI Backend
Main application entry point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import pathlib
from dotenv import load_dotenv

from .routers import auth, website, campaign, analytics
from .models.responses import HealthResponse

# Load environment variables from project root
project_root = pathlib.Path(__file__).parent.parent.parent
load_dotenv(project_root / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MarkezardAI API",
    description="AI-powered marketing campaign generation and management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(website.router, prefix="", tags=["website"])
app.include_router(campaign.router, prefix="", tags=["campaign"])
app.include_router(analytics.router, prefix="", tags=["analytics"])

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        message="MarkezardAI API is running",
        version="1.0.0"
    )

@app.get("/")
async def root():
    """Root endpoint"""
    return {"message": "MarkezardAI API", "docs": "/docs"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
