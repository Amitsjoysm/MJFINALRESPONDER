"""Campaign worker for processing campaign emails"""
import asyncio
import random
from motor.motor_asyncio import AsyncIOMotorClient
import logging
import os
from datetime import datetime, timezone, timedelta

from config import config
from services.email_service import EmailService
from services.campaign_service import CampaignService
from services.campaign_contact_service import CampaignContactService
from services.campaign_template_service import CampaignTemplateService
from models.campaign import Campaign
from models.campaign_email import CampaignEmail
from models.campaign_follow_up import CampaignFollowUp

logger = logging.getLogger(__name__)

# Database connection
client = AsyncIOMotorClient(config.MONGO_URL)
db = client[config.DB_NAME]

async def process_campaign_emails():
    """Process pending campaign emails with rate limiting and delays"""
    try:
        campaign_service = CampaignService(db)
        email_service = EmailService(db)
        contact_service = CampaignContactService(db)
        template_service = CampaignTemplateService(db)
        
        # Get all running campaigns
        running_campaigns = await db.campaigns.find({"status": "running"}).to_list(None)
        
        for campaign_dict in running_campaigns:
            campaign = Campaign(**campaign_dict)
            
            # Check if campaign should be paused due to schedule
            if campaign.scheduled_end:
                end_time = datetime.fromisoformat(campaign.scheduled_end)
                # Make end_time timezone-aware if it's naive
                if end_time.tzinfo is None:
                    end_time = end_time.replace(tzinfo=timezone.utc)
                if datetime.now(timezone.utc) > end_time:
                    await db.campaigns.update_one(
                        {"id": campaign.id},
                        {"$set": {
                            "status": "completed",
                            "completed_at": datetime.now(timezone.utc).isoformat()
                        }}
                    )
                    logger.info(f"Campaign {campaign.id} completed (end time reached)")
                    continue
            
            # Process emails for this campaign
            await _process_campaign(campaign, email_service, contact_service, template_service)
        
    except Exception as e:
        logger.error(f"Error in campaign processor: {e}", exc_info=True)

async def _process_campaign(campaign: Campaign, email_service, contact_service, template_service):
    """Process emails for a single campaign with rate limiting"""
    try:
        # Check daily limits per account
        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Track sends per account today
        account_send_counts = {}
        for account_id in campaign.email_account_ids:
            sent_today = await db.campaign_emails.count_documents({
                "campaign_id": campaign.id,
                "email_account_id": account_id,
                "status": "sent",
                "sent_at": {"$gte": today_start.isoformat()}
            })
            account_send_counts[account_id] = sent_today
        
        # Get pending campaign emails
        pending_emails = await db.campaign_emails.find({
            "campaign_id": campaign.id,
            "status": "pending"
        }).limit(100).to_list(None)
        
        if not pending_emails:
            # Check if campaign is complete
            total_pending = await db.campaign_emails.count_documents({
                "campaign_id": campaign.id,
                "status": {"$in": ["pending", "scheduled"]}
            })
            
            if total_pending == 0:
                await db.campaigns.update_one(
                    {"id": campaign.id},
                    {"$set": {
                        "status": "completed",
                        "completed_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                logger.info(f"Campaign {campaign.id} completed")
            return
        
        # Process emails with delays
        for email_dict in pending_emails:
            campaign_email = CampaignEmail(**email_dict)
            
            # Check if account has reached daily limit
            if account_send_counts.get(campaign_email.email_account_id, 0) >= campaign.daily_limit_per_account:
                logger.info(f"Account {campaign_email.email_account_id} reached daily limit")
                continue
            
            # Get email account
            email_account_dict = await db.email_accounts.find_one({"id": campaign_email.email_account_id})
            if not email_account_dict or not email_account_dict.get("is_active"):
                logger.warning(f"Email account {campaign_email.email_account_id} not active")
                await db.campaign_emails.update_one(
                    {"id": campaign_email.id},
                    {"$set": {
                        "status": "failed",
                        "error_message": "Email account not active"
                    }}
                )
                continue
            
            # Send email
            try:
                # Mark as sending
                await db.campaign_emails.update_one(
                    {"id": campaign_email.id},
                    {"$set": {"status": "sending"}}
                )
                
                # Send via appropriate method
                from models.email import EmailSend
                from models.email_account import EmailAccount
                
                # Convert dict to EmailAccount model
                email_account = EmailAccount(**email_account_dict)
                
                email_data = EmailSend(
                    email_account_id=campaign_email.email_account_id,
                    to_email=[campaign_email.to_email],
                    subject=campaign_email.subject,
                    body=campaign_email.body
                )
                
                if email_account.account_type == "oauth_gmail":
                    result = await email_service.send_email_oauth_gmail(
                        email_account,
                        email_data,
                        thread_id=campaign_email.thread_id
                    )
                    # Gmail returns dict with email_id and thread_id
                    if not result.get("success"):
                        raise Exception("Failed to send email via Gmail")
                    email_id = result.get("email_id")
                    thread_id = result.get("thread_id")
                else:
                    smtp_result = await email_service.send_email_smtp(
                        email_account,
                        email_data
                    )
                    # SMTP returns bool
                    if not smtp_result:
                        raise Exception("Failed to send email via SMTP")
                    email_id = None
                    thread_id = None
                
                # Mark as sent
                sent_at = datetime.now(timezone.utc).isoformat()
                await db.campaign_emails.update_one(
                    {"id": campaign_email.id},
                    {"$set": {
                        "status": "sent",
                        "sent_at": sent_at,
                        "email_id": email_id,
                        "thread_id": thread_id
                    }}
                )
                
                # Update campaign stats - only decrement pending if it's > 0
                update_query = {
                    "$inc": {"emails_sent": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
                
                # Get current campaign state to check pending count
                current_campaign = await db.campaigns.find_one({"id": campaign.id})
                if current_campaign and current_campaign.get("emails_pending", 0) > 0:
                    update_query["$inc"]["emails_pending"] = -1
                
                await db.campaigns.update_one(
                    {"id": campaign.id},
                    update_query
                )
                
                # Update contact stats
                await contact_service.update_engagement_stats(
                    campaign_email.contact_id,
                    email_sent=True
                )
                
                # Increment account send count
                account_send_counts[campaign_email.email_account_id] = \
                    account_send_counts.get(campaign_email.email_account_id, 0) + 1
                
                # Create follow-up tasks if enabled
                if campaign.follow_up_config.enabled and campaign_email.email_type == "initial":
                    await _create_campaign_follow_ups(
                        campaign,
                        campaign_email,
                        sent_at
                    )
                
                logger.info(f"Sent campaign email {campaign_email.id} to {campaign_email.to_email}")
                
                # Apply random delay
                delay = random.randint(campaign.random_delay_min, campaign.random_delay_max)
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"Error sending campaign email {campaign_email.id}: {e}")
                await db.campaign_emails.update_one(
                    {"id": campaign_email.id},
                    {
                        "$set": {
                            "status": "failed",
                            "error_message": str(e)
                        },
                        "$inc": {"retry_count": 1}
                    }
                )
                
                # Update campaign stats for failed email
                update_query_failed = {
                    "$inc": {"emails_failed": 1},
                    "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                }
                
                # Only decrement pending if it's > 0
                current_campaign_failed = await db.campaigns.find_one({"id": campaign.id})
                if current_campaign_failed and current_campaign_failed.get("emails_pending", 0) > 0:
                    update_query_failed["$inc"]["emails_pending"] = -1
                
                await db.campaigns.update_one(
                    {"id": campaign.id},
                    update_query_failed
                )
                
    except Exception as e:
        logger.error(f"Error processing campaign {campaign.id}: {e}", exc_info=True)

async def _create_campaign_follow_ups(campaign: Campaign, initial_email: CampaignEmail, sent_at: str):
    """Create follow-up tasks for campaign email"""
    try:
        sent_datetime = datetime.fromisoformat(sent_at)
        
        for i, (days, template_id) in enumerate(zip(
            campaign.follow_up_config.intervals,
            campaign.follow_up_config.template_ids
        ), start=1):
            if i > campaign.follow_up_config.count:
                break
            
            scheduled_date = sent_datetime + timedelta(days=days)
            
            follow_up = CampaignFollowUp(
                user_id=campaign.user_id,
                campaign_id=campaign.id,
                contact_id=initial_email.contact_id,
                initial_campaign_email_id=initial_email.id,
                thread_id=initial_email.thread_id,
                follow_up_number=i,
                template_id=template_id,
                scheduled_date=scheduled_date.isoformat(),
                days_after_initial=days,
                status="scheduled"
            )
            
            await db.campaign_follow_ups.insert_one(follow_up.model_dump())
        
        logger.info(f"Created {campaign.follow_up_config.count} follow-ups for email {initial_email.id}")
        
    except Exception as e:
        logger.error(f"Error creating follow-ups: {e}", exc_info=True)

async def process_campaign_follow_ups():
    """Process scheduled campaign follow-ups"""
    try:
        email_service = EmailService(db)
        contact_service = CampaignContactService(db)
        template_service = CampaignTemplateService(db)
        
        # Get due follow-ups
        now = datetime.now(timezone.utc)
        # Query scheduled_date - handle both string and datetime formats
        due_follow_ups_cursor = db.campaign_follow_ups.find({
            "status": "scheduled",
            "$or": [
                {"scheduled_date": {"$lte": now.isoformat()}},  # String comparison
                {"scheduled_date": {"$lte": now}}  # Datetime comparison
            ]
        })
        due_follow_ups = await due_follow_ups_cursor.to_list(None)
        
        logger.info(f"Found {len(due_follow_ups)} campaign follow-ups to send")
        
        for follow_up_dict in due_follow_ups:
            follow_up = CampaignFollowUp(**follow_up_dict)
            
            # Check if contact has replied
            replied = await db.campaign_emails.count_documents({
                "campaign_id": follow_up.campaign_id,
                "contact_id": follow_up.contact_id,
                "replied": True
            })
            
            if replied > 0:
                # Cancel follow-up
                await db.campaign_follow_ups.update_one(
                    {"id": follow_up.id},
                    {"$set": {
                        "status": "cancelled",
                        "cancelled_reason": "reply_received",
                        "cancelled_at": now.isoformat()
                    }}
                )
                logger.info(f"Cancelled follow-up {follow_up.id} - contact replied")
                continue
            
            # Get campaign
            campaign = await db.campaigns.find_one({"id": follow_up.campaign_id})
            if not campaign or campaign.get("status") != "running":
                await db.campaign_follow_ups.update_one(
                    {"id": follow_up.id},
                    {"$set": {
                        "status": "cancelled",
                        "cancelled_reason": "campaign_not_running",
                        "cancelled_at": now.isoformat()
                    }}
                )
                continue
            
            # Get initial email to get email account and thread
            initial_email = await db.campaign_emails.find_one({"id": follow_up.initial_campaign_email_id})
            if not initial_email:
                continue
            
            # Get contact
            contact = await contact_service.get_contact(follow_up.user_id, follow_up.contact_id)
            if not contact:
                continue
            
            # Get template
            template = await template_service.get_template(follow_up.user_id, follow_up.template_id)
            if not template:
                continue
            
            # Personalize template
            personalized = await template_service.personalize_template(template, contact.model_dump())
            
            # Create campaign email
            campaign_email = CampaignEmail(
                user_id=follow_up.user_id,
                campaign_id=follow_up.campaign_id,
                contact_id=follow_up.contact_id,
                email_account_id=initial_email["email_account_id"],
                to_email=contact.email,
                subject=personalized["subject"],
                body=personalized["body"],
                email_type=f"follow_up_{follow_up.follow_up_number}",
                follow_up_number=follow_up.follow_up_number,
                parent_campaign_email_id=follow_up.initial_campaign_email_id,
                thread_id=initial_email.get("thread_id"),
                status="pending"
            )
            
            await db.campaign_emails.insert_one(campaign_email.model_dump())
            
            # Update follow-up status
            await db.campaign_follow_ups.update_one(
                {"id": follow_up.id},
                {"$set": {
                    "status": "sent",
                    "sent_at": now.isoformat(),
                    "campaign_email_id": campaign_email.id
                }}
            )
            
            logger.info(f"Queued follow-up {follow_up.id} for sending")
        
    except Exception as e:
        logger.error(f"Error processing campaign follow-ups: {e}", exc_info=True)

async def check_campaign_replies():
    """Check for replies to campaign emails and cancel follow-ups"""
    try:
        # Get all sent campaign emails that haven't been marked as replied
        sent_emails = await db.campaign_emails.find({
            "status": "sent",
            "replied": False,
            "thread_id": {"$ne": None}
        }).to_list(None)
        
        for campaign_email in sent_emails:
            # Check if there's a reply in the main emails collection
            reply = await db.emails.find_one({
                "thread_id": campaign_email["thread_id"],
                "from_email": campaign_email["to_email"],
                "direction": "inbound",
                "received_at": {"$gt": campaign_email.get("sent_at", "")}
            })
            
            if reply:
                # Mark campaign email as replied
                await db.campaign_emails.update_one(
                    {"id": campaign_email["id"]},
                    {"$set": {
                        "replied": True,
                        "replied_at": reply["received_at"]
                    }}
                )
                
                # Update campaign stats
                await db.campaigns.update_one(
                    {"id": campaign_email["campaign_id"]},
                    {
                        "$inc": {"emails_replied": 1},
                        "$set": {"updated_at": datetime.now(timezone.utc).isoformat()}
                    }
                )
                
                # Update contact stats
                contact_service = CampaignContactService(db)
                await contact_service.update_engagement_stats(
                    campaign_email["contact_id"],
                    email_replied=True
                )
                
                # Cancel pending follow-ups for this contact/campaign
                await db.campaign_follow_ups.update_many(
                    {
                        "campaign_id": campaign_email["campaign_id"],
                        "contact_id": campaign_email["contact_id"],
                        "status": {"$in": ["pending", "scheduled"]}
                    },
                    {"$set": {
                        "status": "cancelled",
                        "cancelled_reason": "reply_received",
                        "cancelled_at": datetime.now(timezone.utc).isoformat()
                    }}
                )
                
                logger.info(f"Cancelled follow-ups for contact {campaign_email['contact_id']} - reply received")
        
    except Exception as e:
        logger.error(f"Error checking campaign replies: {e}", exc_info=True)
