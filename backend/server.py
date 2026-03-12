from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import asyncio

from config import config
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

# MongoDB connection with connection pooling
client = AsyncIOMotorClient(
    config.MONGO_URL,
    maxPoolSize=50,
    minPoolSize=10,
    maxIdleTimeMS=45000,
    serverSelectionTimeoutMS=5000
)
db = client[config.DB_NAME]

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
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "database": "disconnected"}

# Startup event - Initialize services and start background worker
@app.on_event("startup")
async def startup_event():
    logger.info("=" * 60)
    logger.info("Starting AI Email Assistant API...")
    logger.info("=" * 60)
    
    try:
        # Test database connection
        await db.command('ping')
        logger.info("✓ Database connection established")
        
        # Initialize dependency injection container
        initialize_container(db, config.JWT_SECRET)
        logger.info("✓ Service container initialized")
        
        # Start background workers in separate tasks
        from workers.email_worker import poll_all_accounts, check_follow_ups, check_reminders
        from workers.campaign_worker import process_campaign_emails, process_campaign_follow_ups, check_campaign_replies
        
        async def background_worker():
            poll_counter = 0
            follow_up_counter = 0
            reminder_counter = 0
            campaign_counter = 0
            campaign_followup_counter = 0
            campaign_reply_counter = 0
            
            logger.info("✓ Background workers started")
            logger.info("  - Email polling: Every 60 seconds")
            logger.info("  - Follow-up checking: Every 5 minutes")
            logger.info("  - Reminder checking: Every 1 hour")
            logger.info("  - Campaign processor: Every 30 seconds")
            logger.info("  - Campaign follow-ups: Every 5 minutes")
            logger.info("  - Campaign reply checker: Every 2 minutes")
            
            while True:
                try:
                    # Poll emails every 60 seconds
                    if poll_counter % config.EMAIL_POLL_INTERVAL == 0:
                        asyncio.create_task(poll_all_accounts())
                        poll_counter = 0
                    
                    # Check follow-ups every 5 minutes
                    if follow_up_counter % config.FOLLOW_UP_CHECK_INTERVAL == 0:
                        asyncio.create_task(check_follow_ups())
                        follow_up_counter = 0
                    
                    # Check reminders every hour
                    if reminder_counter % config.REMINDER_CHECK_INTERVAL == 0:
                        asyncio.create_task(check_reminders())
                        reminder_counter = 0
                    
                    # Process campaign emails every 30 seconds
                    if campaign_counter % 30 == 0:
                        asyncio.create_task(process_campaign_emails())
                        campaign_counter = 0
                    
                    # Process campaign follow-ups every 5 minutes (300 seconds)
                    if campaign_followup_counter % 300 == 0:
                        asyncio.create_task(process_campaign_follow_ups())
                        campaign_followup_counter = 0
                    
                    # Check campaign replies every 2 minutes (120 seconds)
                    if campaign_reply_counter % 120 == 0:
                        asyncio.create_task(check_campaign_replies())
                        campaign_reply_counter = 0
                    
                    await asyncio.sleep(1)
                    poll_counter += 1
                    follow_up_counter += 1
                    reminder_counter += 1
                    campaign_counter += 1
                    campaign_followup_counter += 1
                    campaign_reply_counter += 1
                except Exception as e:
                    logger.error(f"Background worker error: {e}", exc_info=True)
                    await asyncio.sleep(5)
        
        # Start background worker
        asyncio.create_task(background_worker())
        
        logger.info("=" * 60)
        logger.info("✓ AI Email Assistant API is ready!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}", exc_info=True)
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down AI Email Assistant API...")
    
    # Close HTTP client pool
    from utils.http_client import http_client_pool
    await http_client_pool.close()
    logger.info("✓ HTTP client pool closed")
    
    # Close database connection
    client.close()
    logger.info("✓ Database connection closed")
    
    logger.info("✓ Shutdown complete")
