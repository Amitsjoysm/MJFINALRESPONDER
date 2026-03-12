#!/usr/bin/env python3
"""
Create comprehensive seed data for intents and knowledge base
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone
import uuid

async def create_seed_data():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.email_assistant_db
    
    # Get user
    user = await db.users.find_one({"email": "amits.joys@gmail.com"})
    if not user:
        print("❌ User not found")
        return
    
    user_id = user['id']
    print(f"✅ Found user: {user['email']} (ID: {user_id})")
    
    # Delete existing seed data
    await db.intents.delete_many({"user_id": user_id})
    await db.knowledge_base.delete_many({"user_id": user_id})
    print("🗑️  Cleared existing seed data")
    
    # Create intents
    intents = [
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Meeting Request",
            "description": "Handle meeting scheduling requests",
            "keywords": ["meeting", "schedule", "meet", "call", "discussion", "chat", "catch up", "sync", "connect"],
            "prompt": "You are responding to a meeting request. Be professional and accommodating. Suggest available times or confirm the proposed meeting time. If a calendar event is created, mention the meeting details and joining link.",
            "priority": 10,
            "auto_send": True,
            "is_lead": False,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Meeting Reschedule",
            "description": "Handle meeting rescheduling requests",
            "keywords": ["reschedule", "change meeting", "different time", "postpone", "move meeting", "another time"],
            "prompt": "You are responding to a meeting reschedule request. Be understanding and flexible. Acknowledge the need to reschedule and suggest alternative times or confirm the new time.",
            "priority": 9,
            "auto_send": True,
            "is_lead": False,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Support Request",
            "description": "Handle support and help requests",
            "keywords": ["help", "issue", "problem", "error", "bug", "not working", "support", "assistance", "trouble"],
            "prompt": "You are responding to a support request. Be helpful and empathetic. Acknowledge the issue and provide clear guidance or next steps. Reference the support knowledge base if applicable.",
            "priority": 8,
            "auto_send": True,
            "is_lead": False,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Demo Request",
            "description": "Handle demo and trial requests",
            "keywords": ["demo", "trial", "test", "try", "demonstration", "preview", "show me"],
            "prompt": "You are responding to a demo request. Be enthusiastic and helpful. Offer to schedule a demo session and explain what they'll see. This is a potential lead.",
            "priority": 8,
            "auto_send": True,
            "is_lead": True,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Pricing Request",
            "description": "Handle pricing and cost inquiries",
            "keywords": ["pricing", "price", "cost", "how much", "fee", "payment", "plan", "subscription"],
            "prompt": "You are responding to a pricing inquiry. Be clear and transparent. Reference the pricing knowledge base and offer to discuss their specific needs. This is a potential lead.",
            "priority": 7,
            "auto_send": True,
            "is_lead": True,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "General Inquiry",
            "description": "Handle general questions and information requests",
            "keywords": ["question", "inquiry", "information", "tell me", "explain", "how does", "what is", "wondering"],
            "prompt": "You are responding to a general inquiry. Be informative and friendly. Answer their question using the knowledge base and offer additional help if needed.",
            "priority": 5,
            "auto_send": True,
            "is_lead": False,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Thank You",
            "description": "Handle thank you messages and positive feedback",
            "keywords": ["thank", "thanks", "appreciate", "grateful", "awesome", "great", "excellent"],
            "prompt": "You are responding to a thank you message. Be warm and appreciative. Acknowledge their thanks and offer continued support.",
            "priority": 4,
            "auto_send": True,
            "is_lead": False,
            "is_default": False,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "name": "Default Response",
            "description": "Default response for emails that don't match any specific intent",
            "keywords": [],
            "prompt": "You are responding to an email that doesn't clearly match a specific category. Be professional and helpful. Acknowledge their message and offer appropriate assistance based on the context. Use the knowledge base to provide relevant information.",
            "priority": 1,
            "auto_send": True,
            "is_lead": False,
            "is_default": True,
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    result = await db.intents.insert_many(intents)
    print(f"✅ Created {len(result.inserted_ids)} intents")
    
    # Create knowledge base entries
    kb_entries = [
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Company Overview",
            "content": """We are an AI-powered email automation platform that helps businesses manage their email communications efficiently. 

Our mission is to save time and improve communication quality by automating routine email responses while maintaining a personal touch.

Founded in 2024, we serve businesses of all sizes, from startups to enterprises, helping them handle customer inquiries, schedule meetings, and manage follow-ups automatically.""",
            "category": "Company Information",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Product Features",
            "content": """Our platform includes:

1. Smart Email Classification: Automatically categorizes incoming emails based on intent
2. AI-Powered Responses: Generates contextual replies using your knowledge base and persona
3. Auto-Send: Automatically sends approved responses based on confidence levels
4. Meeting Detection: Identifies meeting requests and creates calendar events
5. Follow-Up Management: Schedules and sends follow-up emails automatically
6. Thread Tracking: Maintains conversation context across multiple emails
7. Calendar Integration: Syncs with Google Calendar and Microsoft Outlook
8. Knowledge Base: Centralized information that AI uses to answer questions
9. Intent Management: Customize how different types of emails are handled
10. Analytics: Track email volume, response times, and automation effectiveness""",
            "category": "Product",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Meeting and Calendar Features",
            "content": """Meeting Management:
- Automatically detects meeting requests from email content
- Extracts meeting details (date, time, attendees, purpose)
- Creates calendar events with Google Meet links
- Sends confirmation emails with all meeting details
- Includes joining links and calendar view links in responses
- Handles meeting rescheduling requests
- Sends reminders before meetings

Calendar Integration:
- Works with Google Calendar and Microsoft Outlook
- Creates events with proper timezone handling
- Generates Google Meet or Teams links automatically
- Syncs meeting updates across platforms
- Manages multiple calendar providers""",
            "category": "Meetings",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Pricing Information",
            "content": """Our pricing plans:

Starter Plan - $29/month:
- 500 emails per month
- 1 email account
- Basic intent classification
- Auto-send responses
- Email support

Professional Plan - $99/month:
- 2,000 emails per month
- 3 email accounts
- Advanced intent classification
- Calendar integration
- Follow-up automation
- Priority support

Enterprise Plan - Custom:
- Unlimited emails
- Unlimited accounts
- Custom integrations
- Dedicated account manager
- SLA guarantees
- Advanced analytics

All plans include a 14-day free trial with no credit card required.""",
            "category": "Pricing",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Getting Started Guide",
            "content": """Quick Start Guide:

1. Connect Your Email:
   - Click "Email Accounts" in the sidebar
   - Click "Connect Google Account" or "Connect Outlook"
   - Authorize access to read and send emails

2. Set Up Intents:
   - Go to "Intents" page
   - Create intents for different types of emails
   - Add keywords and custom prompts
   - Enable auto-send for approved intents

3. Add Knowledge Base:
   - Go to "Knowledge Base" page
   - Add information about your company, products, and services
   - The AI will use this to answer questions accurately

4. Configure Your Persona:
   - Go to Settings > Persona
   - Define your communication style and tone
   - Add your email signature

5. Test the System:
   - Send a test email to your connected account
   - Watch it get processed in the Dashboard
   - Review the generated draft before auto-send""",
            "category": "Documentation",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Support and Contact",
            "content": """Need Help?

Email Support: support@example.com
Response time: Within 24 hours (faster for paid plans)

Documentation: docs.example.com
Video tutorials, guides, and FAQs

Live Chat: Available on the dashboard (Pro and Enterprise plans)
Hours: Monday-Friday, 9 AM - 6 PM EST

Common Issues:
1. OAuth Connection Fails: Make sure you're granting all requested permissions
2. Emails Not Processing: Check that your email account is active in settings
3. Auto-Send Not Working: Verify intents have auto_send enabled and confidence threshold is met
4. Calendar Events Not Creating: Ensure calendar provider is connected and active

Emergency Support (Enterprise only): Call +1-XXX-XXX-XXXX""",
            "category": "Support",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Security and Privacy",
            "content": """Data Security:
- All data encrypted in transit (TLS 1.3) and at rest (AES-256)
- OAuth tokens stored securely with encryption
- No passwords stored (OAuth-only authentication)
- Regular security audits and penetration testing
- SOC 2 Type II certified
- GDPR and CCPA compliant

Privacy:
- We never read your emails for marketing purposes
- Email content only processed for automation features
- You can delete all data at any time
- No data shared with third parties
- Optional data retention policies

Access Control:
- Role-based access control (Enterprise)
- Two-factor authentication available
- Audit logs for all actions
- IP whitelisting (Enterprise)

Your emails are processed only to provide the automation services you've requested.""",
            "category": "Security",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "title": "Integration and API",
            "content": """Available Integrations:

Email Providers:
- Gmail (via OAuth)
- Microsoft Outlook (via OAuth)
- Custom SMTP/IMAP (coming soon)

Calendar Providers:
- Google Calendar
- Microsoft Outlook Calendar
- Apple Calendar (coming soon)

CRM Integrations:
- Salesforce (Enterprise)
- HubSpot (Enterprise)
- Pipedrive (coming soon)

Communication:
- Slack notifications
- Microsoft Teams notifications
- Webhook support for custom integrations

API Access:
- RESTful API available for all plans
- Rate limits: 1000 requests/hour (Starter), 10000/hour (Pro), unlimited (Enterprise)
- Webhooks for real-time events
- Comprehensive API documentation
- SDKs for Python, JavaScript, and Java

Contact our sales team to discuss custom integration needs.""",
            "category": "Integration",
            "is_active": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    result = await db.knowledge_base.insert_many(kb_entries)
    print(f"✅ Created {len(result.inserted_ids)} knowledge base entries")
    
    # Summary
    print("\n📊 Seed Data Summary:")
    print(f"   - Intents: 8 total (7 with auto_send enabled, 1 default)")
    print(f"   - Knowledge Base: 8 entries across 7 categories")
    print(f"   - User: {user['email']}")
    print(f"\n✅ All seed data created successfully!")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_seed_data())
