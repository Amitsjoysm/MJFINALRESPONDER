from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
import logging
import asyncio

from config import config
from db import get_mongo_client, get_db, close_db
from container import initialize_container
from middleware.error_handler import global_exception_handler, validation_exception_handler
from middleware.security import RateLimitMiddleware, SecurityHeadersMiddleware
from exceptions import EmailAssistantException

# Configure logging with better format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

# Use shared database connection
client = get_mongo_client()
db = get_db()

# Create FastAPI app
app = FastAPI(
    title="AI Email Assistant API",
    description="Production-ready AI-powered email automation platform with SOLID principles",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Add security middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RateLimitMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=config.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add exception handlers
app.add_exception_handler(EmailAssistantException, global_exception_handler)
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Import routes
from routes.auth_routes import router as auth_router
from routes.email_account_routes import router as email_account_router
from routes.email_routes import router as email_router
from routes.intent_routes import router as intent_router
from routes.knowledge_base_routes import router as knowledge_base_router
from routes.oauth_routes import router as oauth_router
from routes.calendar_routes import router as calendar_router
from routes.follow_up_routes import router as follow_up_router
from routes.system_routes import router as system_router
from routes.test_routes import router as test_router
from routes.campaign_contact_routes import router as campaign_contact_router
from routes.campaign_template_routes import router as campaign_template_router
from routes.campaign_routes import router as campaign_router
from routes.contact_list_routes import router as contact_list_router
from routes.lead_routes import router as lead_router
from routes.hubspot_routes import router as hubspot_router
from routes.lead_qualification_routes import router as lead_qualification_router
from routes.lead_nurturing_routes import router as lead_nurturing_router
from routes.test_flow_routes import router as test_flow_router
from routes.test_session_routes import router as test_session_router
from routes.error_routes import router as error_router
from routes.health_routes import router as health_router

# Include routers under /api prefix
app.include_router(auth_router, prefix="/api")
app.include_router(email_account_router, prefix="/api")
app.include_router(email_router, prefix="/api")
app.include_router(intent_router, prefix="/api")
app.include_router(knowledge_base_router, prefix="/api")
app.include_router(oauth_router, prefix="/api")
app.include_router(calendar_router, prefix="/api")
app.include_router(follow_up_router, prefix="/api")
app.include_router(system_router, prefix="/api")
app.include_router(test_router, prefix="/api")
app.include_router(hubspot_router, prefix="/api")
app.include_router(health_router, prefix="/api")
app.include_router(lead_qualification_router)
app.include_router(lead_nurturing_router)
app.include_router(test_flow_router)
app.include_router(test_session_router)
app.include_router(error_router)
app.include_router(lead_router)
app.include_router(campaign_contact_router)
app.include_router(campaign_template_router)
app.include_router(campaign_router)
app.include_router(contact_list_router)

# Special OAuth callback route (without /api prefix for Google OAuth redirect)
from fastapi import Query
from fastapi.responses import RedirectResponse

@app.get("/oauth/google/callback")
async def oauth_google_callback_public(
    code: str = Query(...),
    state: str = Query(...),
):
    """Public OAuth callback endpoint for Google (redirects from Google don't go through /api)"""
    from routes.oauth_routes import google_oauth_callback_get
    return await google_oauth_callback_get(code=code, state=state, db=db)

# Root endpoint
@app.get("/api")
async def root():
    return {
        "message": "AI Email Assistant API",
        "version": "1.0.0",
        "status": "running"
    }

# Health check
@app.get("/api/health")
async def health_check():
    try:
        await db.command('ping')
        from services.orchestrator_service import orchestrator
        from utils.ai_concurrency import ai_concurrency
        return {
            "status": "healthy",
            "database": "connected",
            "orchestrator": orchestrator.get_metrics(),
            "ai_concurrency": ai_concurrency.get_stats(),
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected"}

# Startup event - Initialize services and start orchestrator
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Starting AI Email Assistant API...")
    logger.info("=" * 60)
    
    try:
        # Test database connection
        await db.command('ping')
        logger.info("âœ“ Database connection established (shared pool)")
        
        # Initialize dependency injection container
        initialize_container(db, config.JWT_SECRET)
        logger.info("âœ“ Service container initialized")
        
        # Start the Task Orchestrator (replaces monolithic background_worker)
        from services.orchestrator_service import orchestrator
        await orchestrator.start()
        logger.info("âœ“ Task Orchestrator started (per-user fair scheduling)")
        
        logger.info("=" * 60)
        logger.info("âœ“ AI Email Assistant API is ready!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"âœ— Startup failed: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Email Assistant API...")
    
    # Stop orchestrator
    from services.orchestrator_service import orchestrator
    await orchestrator.stop()
    logger.info("âœ“ Task Orchestrator stopped")
    
    # Close HTTP client pool
    from utils.http_client import http_client_pool
    await http_client_pool.close()
    logger.info("âœ“ HTTP client pool closed")
    
    # Close shared database connection
    await close_db()
    logger.info("âœ“ Database connection closed")
    
    logger.info("âœ“ Shutdown complete")
