# AI Email Assistant Platform - Complete Codebase Overview

**Last Updated:** November 19, 2025  
**Status:** ✅ All systems operational and production-ready

---

## 🎯 Application Overview

**AI Email Assistant Platform** is a comprehensive email automation and CRM system that uses AI to:
- Process incoming emails automatically
- Classify intent and generate intelligent responses
- Manage inbound leads through the sales pipeline
- Schedule meetings with calendar integration
- Run email campaigns with analytics
- Provide automated follow-ups

---

## 🏗️ Architecture

### Tech Stack
- **Backend**: FastAPI (Python 3.x)
- **Frontend**: React (with Create React App)
- **Database**: MongoDB
- **Cache/Queue**: Redis
- **AI/LLM**: Groq API (llama-3.3-70b-versatile)
- **OAuth**: Google & Microsoft OAuth2
- **Background Jobs**: Custom Python workers

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend (React)                      │
│  - Auth, Dashboard, Email Processing, Leads, Campaigns      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTPS API Calls
┌──────────────────────▼──────────────────────────────────────┐
│                     Backend (FastAPI)                        │
│  - REST APIs, Authentication, Business Logic                │
└──┬────────────┬─────────────┬────────────┬─────────────┬───┘
   │            │             │            │             │
   ▼            ▼             ▼            ▼             ▼
┌──────┐  ┌─────────┐  ┌──────────┐  ┌────────┐  ┌──────────┐
│MongoDB│  │  Redis  │  │ Google   │  │Microsoft│  │   Groq   │
│       │  │         │  │ Calendar │  │  OAuth  │  │   API    │
│       │  │         │  │  & Gmail │  │         │  │          │
└───────┘  └─────────┘  └──────────┘  └─────────┘  └──────────┘
     ▲           ▲
     │           │
┌────┴───────────┴──────────────────────────────────────────┐
│              Background Workers (Python)                   │
│  - Email Polling    - Campaign Processing                 │
│  - Follow-ups       - Reminders                           │
└────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
/app/
├── backend/                      # FastAPI backend application
│   ├── config.py                 # Configuration and environment variables
│   ├── server.py                 # Main FastAPI application entry point
│   ├── container.py              # Dependency injection container
│   ├── exceptions.py             # Custom exception classes
│   │
│   ├── models/                   # Database models (MongoDB schemas)
│   │   ├── user.py              # User model (auth, profile, quota)
│   │   ├── email.py             # Email model (threads, drafts, status)
│   │   ├── email_account.py     # Email account connections (OAuth)
│   │   ├── intent.py            # Intent classification rules
│   │   ├── knowledge_base.py    # Knowledge base entries
│   │   ├── follow_up.py         # Follow-up emails
│   │   ├── calendar.py          # Calendar events and providers
│   │   ├── inbound_lead.py      # Lead management
│   │   ├── campaign.py          # Email campaigns
│   │   ├── campaign_email.py    # Campaign email tracking
│   │   ├── campaign_contact.py  # Campaign recipients
│   │   ├── campaign_template.py # Email templates
│   │   └── ...
│   │
│   ├── routes/                   # API endpoints (controllers)
│   │   ├── auth_routes.py       # Authentication (login, register, me)
│   │   ├── email_routes.py      # Email management
│   │   ├── email_account_routes.py  # Email account connections
│   │   ├── intent_routes.py     # Intent CRUD operations
│   │   ├── knowledge_base_routes.py # Knowledge base CRUD
│   │   ├── lead_routes.py       # Inbound lead management
│   │   ├── calendar_routes.py   # Calendar integration
│   │   ├── campaign_routes.py   # Campaign management
│   │   ├── follow_up_routes.py  # Follow-up management
│   │   ├── oauth_routes.py      # OAuth flows (Google, Microsoft)
│   │   └── ...
│   │
│   ├── services/                 # Business logic layer
│   │   ├── ai_agent_service.py  # AI intent classification, draft generation
│   │   ├── email_service.py     # Email sending/receiving (OAuth Gmail)
│   │   ├── calendar_service.py  # Google Calendar integration
│   │   ├── auth_service.py      # Authentication and JWT
│   │   ├── oauth_service.py     # OAuth token management
│   │   ├── campaign_service.py  # Campaign processing
│   │   ├── lead_agent_service.py # Lead scoring and management
│   │   ├── date_parser_service.py # Natural language date parsing
│   │   ├── email_formatter.py   # Email formatting and signatures
│   │   ├── conversation_linking_service.py # Thread detection
│   │   └── ...
│   │
│   ├── workers/                  # Background job processors
│   │   ├── email_worker.py      # Email polling, draft generation, auto-send
│   │   └── campaign_worker.py   # Campaign email sending and tracking
│   │
│   ├── repositories/             # Data access layer
│   │   └── base_repository.py   # Base repository with CRUD operations
│   │
│   ├── middleware/               # FastAPI middleware
│   │   ├── error_handler.py     # Global error handling
│   │   └── security.py          # Security headers
│   │
│   ├── utils/                    # Utility functions
│   │   ├── validators.py        # Data validation
│   │   ├── encryption.py        # Password encryption
│   │   ├── cache.py             # Redis caching
│   │   └── http_client.py       # HTTP client utilities
│   │
│   ├── scripts/                  # Utility scripts
│   │   ├── create_super_admin.py # Create super admin user
│   │   ├── create_seed_data.py  # Seed database with test data
│   │   └── ...
│   │
│   ├── run_email_worker.py      # Email worker entry point
│   ├── run_campaign_worker.py   # Campaign worker entry point
│   ├── requirements.txt          # Python dependencies
│   └── .env                      # Environment variables
│
├── frontend/                     # React frontend application
│   ├── src/
│   │   ├── index.js             # React app entry point
│   │   ├── App.js               # Main app component with routing
│   │   ├── api.js               # API client (Axios)
│   │   │
│   │   ├── context/             # React context providers
│   │   │   └── AuthContext.js   # Authentication state management
│   │   │
│   │   ├── pages/               # Page components (routes)
│   │   │   ├── AuthPage.js      # Login/Register page
│   │   │   ├── Dashboard.js     # Main dashboard with stats
│   │   │   ├── InboundLeads.js  # Lead management page ⭐
│   │   │   ├── EmailProcessing.js # Email inbox and processing
│   │   │   ├── EmailAccounts.js # Email account connections
│   │   │   ├── CalendarProviders.js # Calendar integration
│   │   │   ├── Intents.js       # Intent management
│   │   │   ├── KnowledgeBase.js # Knowledge base management
│   │   │   ├── Campaigns.js     # Campaign management
│   │   │   ├── FollowUps.js     # Follow-up management
│   │   │   ├── Settings.js      # User settings (persona, signature)
│   │   │   └── ...
│   │   │
│   │   ├── components/          # Reusable components
│   │   │   └── ui/              # Shadcn/UI components
│   │   │
│   │   └── hooks/               # Custom React hooks
│   │       └── use-toast.js     # Toast notifications
│   │
│   ├── package.json             # Node.js dependencies
│   ├── tailwind.config.js       # Tailwind CSS configuration
│   └── .env                     # Frontend environment variables
│
├── start_workers.sh             # Script to start background workers
├── test_result.md               # Testing protocol and results
├── SYSTEM_STATUS.md             # Current system status
├── PRODUCTION_READY_STATUS.md   # Production readiness checklist
└── CODEBASE_OVERVIEW.md         # This file

```

---

## 🔑 Key Features & Components

### 1. **Authentication System**
**Location**: `backend/routes/auth_routes.py`, `backend/services/auth_service.py`

- JWT-based authentication with 7-day token expiry
- User roles: `user`, `admin`, `super_admin`
- Password hashing with bcrypt
- User quota management (email sending limits)

**API Endpoints**:
- `POST /api/auth/register` - Create new user
- `POST /api/auth/login` - Authenticate and get JWT token
- `GET /api/auth/me` - Get current user profile

**Super Admin Credentials**:
- **Email**: `admin@crm.com`
- **Password**: `Admin@123`
- **Role**: `super_admin`
- **Quota**: 10,000 emails

---

### 2. **Email Processing Pipeline**
**Location**: `backend/workers/email_worker.py`, `backend/services/email_service.py`

**Flow**:
```
1. Email Polling (every 60s)
   ├─ Fetch new emails via OAuth Gmail API
   ├─ Extract thread information
   └─ Store in database with status: "new"

2. Intent Classification
   ├─ Use keyword matching (ai_agent_service.py)
   ├─ Match against user's intents
   └─ Assign confidence score

3. Meeting Detection
   ├─ Check for meeting keywords
   ├─ Extract date/time using date_parser
   └─ If confidence > 0.7, flag as meeting

4. Draft Generation (AI-powered)
   ├─ Use Groq API (llama-3.3-70b-versatile)
   ├─ Include thread context, intent prompt, knowledge base
   ├─ Generate contextual response
   └─ Status: "drafting" → "draft_ready"

5. Draft Validation
   ├─ AI validates draft quality
   ├─ Check for repetition, completeness
   └─ Max 2 retry attempts if validation fails

6. Auto-Send (if enabled)
   ├─ Check intent's auto_send flag
   ├─ Send via Gmail API with thread_id
   └─ Status: "sending" → "sent"

7. Follow-up Creation
   ├─ Create 3 follow-ups (2, 4, 6 days later)
   ├─ If meeting detected, add 3 more (9, 11, 13 days)
   └─ Automatic cancellation if reply received

8. Calendar Event (if meeting detected)
   ├─ Create event in Google Calendar
   ├─ Generate Google Meet link
   ├─ Include event details in draft
   └─ Send reminders 1 hour before
```

**Key Files**:
- `workers/email_worker.py` - Main email processing loop
- `services/email_service.py` - Gmail API integration
- `services/ai_agent_service.py` - AI classification and generation
- `services/calendar_service.py` - Google Calendar integration
- `services/date_parser_service.py` - Natural language date parsing

---

### 3. **Inbound Lead Management** ⭐
**Location**: `backend/routes/lead_routes.py`, `frontend/src/pages/InboundLeads.js`

**Purpose**: Track and manage potential customers through the sales pipeline

**Lead Stages**:
- **New**: Just received, not yet contacted
- **Contacted**: Initial contact made
- **Qualified**: Verified as potential customer
- **Converted**: Successfully closed as customer
- **Unqualified**: Not a good fit

**Lead Properties**:
- Personal info (name, email, company, phone)
- Lead score (0-100)
- Priority (low, medium, high, urgent)
- Stage and stage history
- Activity timeline
- Meeting scheduling
- Notes and tags

**API Endpoints**:
- `GET /api/leads` - List leads with filtering
- `GET /api/leads/stats/summary` - Lead statistics
- `GET /api/leads/{lead_id}` - Get lead details
- `PUT /api/leads/{lead_id}` - Update lead
- `POST /api/leads/{lead_id}/stage` - Change lead stage
- `GET /api/leads/{lead_id}/emails` - Get lead's emails

**Frontend Features**:
- Lead dashboard with statistics
- Filter by stage, priority, search
- Lead detail dialog with timeline
- Stage management
- Activity tracking

---

### 4. **Intent Classification**
**Location**: `backend/models/intent.py`, `backend/services/ai_agent_service.py`

**Purpose**: Automatically categorize incoming emails to determine appropriate response

**Intent Properties**:
- Name and description
- Keywords (comma-separated)
- Priority (higher = matched first)
- Auto-send flag (enable automatic responses)
- AI prompt (instructions for draft generation)
- Lead intent flag (mark as potential customer)
- Default intent flag (catch-all for unmatched emails)

**Example Intents**:
```
1. Meeting Request
   - Priority: 10
   - Keywords: meeting, schedule, call, zoom, meet
   - Auto-send: true
   - Action: Create calendar event + send confirmation

2. Support Request
   - Priority: 8
   - Keywords: help, issue, problem, error, broken
   - Auto-send: true
   - Action: Send helpful response with KB info

3. Demo Request (Lead Intent)
   - Priority: 8
   - Keywords: demo, trial, test, preview
   - Auto-send: true
   - Lead: true
   - Action: Create inbound lead + schedule demo

4. Default Response
   - Priority: 1
   - Is_default: true
   - Auto-send: true
   - Action: Send polite acknowledgment
```

**Classification Logic**:
```python
# Keyword-based matching with priority
def classify_intent(email_content, intents):
    for intent in sorted_by_priority(intents):
        for keyword in intent.keywords:
            if keyword in email_content.lower():
                return intent, confidence_score
    
    # Fallback to default intent
    return default_intent, 0.5
```

---

### 5. **Knowledge Base**
**Location**: `backend/models/knowledge_base.py`, `backend/routes/knowledge_base_routes.py`

**Purpose**: Provide AI with company-specific information for accurate responses

**Properties**:
- Title and content
- Category (Company, Product, Pricing, Support, etc.)
- Active/inactive status
- Created/updated timestamps

**Usage in AI**:
```python
# Knowledge base is injected into AI prompts
kb_context = "\n".join([f"{kb.title}: {kb.content}" for kb in knowledge_base])

ai_prompt = f"""
You are an AI assistant for {company_name}.

Knowledge Base:
{kb_context}

Intent: {intent.name}
{intent.ai_prompt}

Email: {email_content}

Generate a response using the knowledge base information.
"""
```

**Benefits**:
- Prevents AI hallucination
- Ensures consistent responses
- Includes accurate company info
- Easy to update without code changes

---

### 6. **Calendar Integration**
**Location**: `backend/services/calendar_service.py`, `backend/routes/calendar_routes.py`

**Features**:
- Google Calendar OAuth integration
- Automatic event creation from meeting emails
- Google Meet link generation
- Event reminders (1 hour before)
- Event updates and rescheduling
- Conflict detection

**Event Creation Flow**:
```
1. Meeting detected in email
   ├─ Extract meeting details (date, time, attendees)
   └─ Confidence score > 0.7 required

2. Create Google Calendar event
   ├─ Title, description, start/end time
   ├─ Add attendees
   ├─ Generate Google Meet link (conferenceData)
   └─ Return event_id, meet_link, html_link

3. Include in draft response
   ├─ Meeting confirmation
   ├─ Date, time, timezone
   ├─ Google Meet link
   └─ Calendar link

4. Schedule reminder
   ├─ 1 hour before event
   └─ Send reminder email with event details
```

**API Endpoints**:
- `GET /api/calendar/providers` - List connected calendars
- `POST /api/calendar/providers` - Connect new calendar
- `GET /api/calendar/events` - List calendar events
- `POST /api/calendar/events` - Create new event
- `PUT /api/calendar/events/{event_id}` - Update event

---

### 7. **Campaign Management**
**Location**: `backend/routes/campaign_routes.py`, `workers/campaign_worker.py`

**Purpose**: Send bulk email campaigns with tracking and analytics

**Campaign Properties**:
- Name, subject, body
- Contact list selection
- Send schedule (immediate or scheduled)
- Status (draft, scheduled, sending, completed)
- Analytics (sent, delivered, opened, clicked, replied)

**Campaign Flow**:
```
1. Create campaign
   ├─ Select contact list
   ├─ Choose email template
   └─ Set schedule

2. Campaign worker processes
   ├─ Load contacts from list
   ├─ Create campaign_email for each contact
   └─ Send via email_service (every 30s batch)

3. Track engagement
   ├─ Sent timestamp
   ├─ Reply detection (every 2min check)
   ├─ Follow-up creation (if no reply)
   └─ Analytics update

4. Campaign analytics
   ├─ Total sent, delivered, bounced
   ├─ Open rate, click rate
   ├─ Reply rate, conversion rate
   └─ Revenue tracking
```

**Background Workers**:
- `campaign_worker.py` - Process scheduled campaigns
- Reply checker - Monitor for responses
- Follow-up worker - Send campaign follow-ups

---

### 8. **Background Workers**
**Location**: `backend/workers/`, started via `start_workers.sh`

#### Email Worker (`run_email_worker.py`)
**Runs**: Every 60 seconds

**Tasks**:
1. Poll email accounts for new emails
2. Process new emails (classify, draft, validate, send)
3. Send pending follow-ups
4. Send calendar event reminders

**Logs**: `/var/log/email_worker.log`

#### Campaign Worker (`run_campaign_worker.py`)
**Runs**: Every 30 seconds

**Tasks**:
1. Process scheduled campaigns
2. Send campaign emails in batches
3. Check for campaign replies
4. Update campaign analytics
5. Send campaign follow-ups

**Logs**: `/var/log/campaign_worker.log`

**Worker Management**:
```bash
# Start all workers
/app/start_workers.sh

# Check worker status
ps aux | grep "run_.*_worker.py"

# View logs
tail -f /var/log/email_worker.log
tail -f /var/log/campaign_worker.log

# Stop workers
pkill -f "run_email_worker.py"
pkill -f "run_campaign_worker.py"
```

---

### 9. **OAuth Integration**
**Location**: `backend/routes/oauth_routes.py`, `backend/services/oauth_service.py`

**Supported Providers**:
- Google (Gmail + Calendar)
- Microsoft (Outlook + Calendar)

**OAuth Flow**:
```
1. Frontend: User clicks "Connect Gmail"
   └─ GET /api/oauth/google/url?account_type=email

2. Backend: Generate OAuth URL
   ├─ Create state token (stored in DB)
   ├─ Return Google OAuth URL
   └─ Frontend redirects user to Google

3. User authorizes on Google
   └─ Google redirects to callback URL

4. Backend: Handle callback
   ├─ GET /api/oauth/google/callback?code=...&state=...
   ├─ Verify state token
   ├─ Exchange code for access_token + refresh_token
   ├─ Store tokens in email_accounts collection
   └─ Redirect to frontend with success/error

5. Token refresh (automatic)
   ├─ Check token expiry before API calls
   ├─ If expired, use refresh_token
   ├─ Update stored tokens
   └─ Continue with API call
```

**Token Management**:
- Access tokens expire after 1 hour
- Refresh tokens used to get new access tokens
- Automatic refresh in `email_service.py` and `calendar_service.py`
- `ensure_token_valid()` method handles refresh

**Scopes**:
- Gmail: `gmail.readonly`, `gmail.send`, `calendar`
- Microsoft: `Mail.Read`, `Mail.Send`, `Calendars.ReadWrite`

---

## 🗄️ Database Schema

### MongoDB Collections

#### `users`
```javascript
{
  _id: ObjectId,
  id: "uuid",                    // UUID for public reference
  email: "user@example.com",
  password_hash: "bcrypt_hash",
  full_name: "John Doe",
  role: "user",                  // user, admin, super_admin
  quota: 1000,                   // Email sending quota
  quota_used: 150,
  quota_reset_date: ISODate,
  created_at: ISODate,
  is_active: true,
  hubspot_enabled: false,
  persona: "I am a...",          // AI persona
  signature: "Best regards..."   // Email signature
}
```

#### `email_accounts`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  provider: "oauth_gmail",       // oauth_gmail, oauth_outlook
  email: "user@gmail.com",
  access_token: "encrypted",
  refresh_token: "encrypted",
  token_expiry: ISODate,
  last_sync: ISODate,
  is_active: true,
  created_at: ISODate
}
```

#### `emails`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  email_account_id: "uuid",
  message_id: "google_message_id",
  thread_id: "google_thread_id",
  from_email: "sender@example.com",
  to_email: ["recipient@example.com"],
  subject: "Email subject",
  body: "Email content",
  received_at: ISODate,
  
  // Processing status
  status: "sent",                // new, classifying, drafting, validating, 
                                 // draft_ready, sending, sent, error
  
  // Intent classification
  intent_id: "uuid",
  intent_name: "Meeting Request",
  intent_confidence: 0.9,
  
  // Meeting detection
  meeting_detected: true,
  meeting_confidence: 0.85,
  meeting_title: "Project Discussion",
  meeting_start_time: ISODate,
  
  // Draft
  draft_content: "AI generated response",
  draft_retry_count: 0,
  draft_validated: true,
  validation_issues: [],
  
  // Action history
  action_history: [
    {
      action: "intent_classified",
      timestamp: ISODate,
      details: {intent: "Meeting Request", confidence: 0.9}
    }
  ],
  
  created_at: ISODate
}
```

#### `intents`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  name: "Meeting Request",
  description: "When someone wants to schedule a meeting",
  keywords: ["meeting", "schedule", "call"],
  priority: 10,                  // Higher = matched first
  auto_send: true,               // Auto-send responses
  is_lead: false,                // Create inbound lead
  is_default: false,             // Default fallback intent
  ai_prompt: "Generate a professional response...",
  is_active: true,
  created_at: ISODate
}
```

#### `knowledge_base`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  title: "Company Overview",
  content: "Our company provides...",
  category: "Company Information",  // Company, Product, Pricing, etc.
  is_active: true,
  created_at: ISODate,
  updated_at: ISODate
}
```

#### `inbound_leads`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  
  // Contact information
  email: "lead@company.com",
  full_name: "Jane Smith",
  company: "ACME Corp",
  phone: "+1234567890",
  
  // Lead status
  stage: "qualified",            // new, contacted, qualified, converted, unqualified
  priority: "high",              // low, medium, high, urgent
  lead_score: 75,                // 0-100
  is_active: true,
  
  // Metadata
  source: "email",               // email, form, referral, etc.
  notes: "Interested in enterprise plan",
  tags: ["enterprise", "urgent"],
  
  // Meeting
  meeting_scheduled: true,
  meeting_date: ISODate,
  
  // History
  stage_history: [
    {
      from_stage: "contacted",
      to_stage: "qualified",
      changed_at: ISODate,
      reason: "Confirmed budget"
    }
  ],
  
  // Activity timeline
  activities: [
    {
      type: "email_sent",
      description: "Sent pricing information",
      timestamp: ISODate
    }
  ],
  
  created_at: ISODate,
  updated_at: ISODate
}
```

#### `calendar_events`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  provider_id: "uuid",
  email_id: "uuid",              // Related email
  
  google_event_id: "google_id",
  title: "Project Discussion",
  description: "Discuss project scope",
  start_time: ISODate,
  end_time: ISODate,
  timezone: "UTC",
  
  attendees: ["attendee@example.com"],
  meet_link: "https://meet.google.com/xxx",
  html_link: "https://calendar.google.com/...",
  
  reminder_sent: false,
  created_at: ISODate
}
```

#### `follow_ups`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  email_id: "uuid",
  thread_id: "google_thread_id",
  
  scheduled_at: ISODate,
  status: "pending",             // pending, sent, cancelled
  
  // Automated follow-up
  is_automated: true,
  follow_up_context: "Follow up on meeting request",
  base_date: ISODate,
  matched_text: "next week",
  
  // Cancellation
  cancellation_reason: "Reply received in thread",
  
  created_at: ISODate,
  sent_at: ISODate
}
```

#### `campaigns`
```javascript
{
  _id: ObjectId,
  id: "uuid",
  user_id: "uuid",
  
  name: "Product Launch Campaign",
  subject: "Introducing our new product",
  body: "Email content...",
  
  contact_list_id: "uuid",
  template_id: "uuid",
  
  status: "completed",           // draft, scheduled, sending, completed
  scheduled_at: ISODate,
  
  // Analytics
  analytics: {
    total_sent: 1000,
    delivered: 980,
    bounced: 20,
    opened: 450,
    clicked: 120,
    replied: 45,
    open_rate: 45.9,
    click_rate: 12.2,
    reply_rate: 4.6
  },
  
  created_at: ISODate,
  completed_at: ISODate
}
```

---

## 🔐 Environment Variables

### Backend (.env)
```bash
# Database
MONGO_URL="mongodb://localhost:27017"
DB_NAME="email_assistant_db"

# JWT
JWT_SECRET="your-secret-key-change-in-production"

# Google OAuth
GOOGLE_CLIENT_ID="your-google-client-id"
GOOGLE_CLIENT_SECRET="your-google-client-secret"
GOOGLE_REDIRECT_URI="https://your-domain.com/api/oauth/google/callback"

# Microsoft OAuth
MICROSOFT_CLIENT_ID="your-microsoft-client-id"
MICROSOFT_CLIENT_SECRET="your-microsoft-client-secret"
MICROSOFT_TENANT_ID="your-tenant-id"
MICROSOFT_REDIRECT_URI="https://your-domain.com/api/oauth/microsoft/callback"

# AI APIs
GROQ_API_KEY="gsk_..."
EMERGENT_LLM_KEY="sk-emergent-..."

# Redis
REDIS_URL="redis://localhost:6379/0"

# Encryption
ENCRYPTION_KEY="your-encryption-key-32-bytes-long"
```

### Frontend (.env)
```bash
REACT_APP_BACKEND_URL=https://your-domain.com
WDS_SOCKET_PORT=443
```

---

## 🚀 Deployment & Operations

### Service Management

#### Start All Services
```bash
# Restart all services
sudo supervisorctl restart all

# Check status
sudo supervisorctl status
```

#### Start Background Workers
```bash
# Start email and campaign workers
/app/start_workers.sh

# Check workers
ps aux | grep "run_.*_worker.py"
```

#### Service Status Check
```bash
# Backend health check
curl http://localhost:8001/api/health

# Redis check
redis-cli ping

# MongoDB check
mongo --eval "db.adminCommand('ping')"

# Frontend check
curl http://localhost:3000
```

### Logs

#### Application Logs
```bash
# Backend logs
tail -f /var/log/supervisor/backend.out.log
tail -f /var/log/supervisor/backend.err.log

# Frontend logs
tail -f /var/log/supervisor/frontend.out.log

# Worker logs
tail -f /var/log/email_worker.log
tail -f /var/log/campaign_worker.log
```

#### Service Logs
```bash
# Supervisor logs
tail -f /var/log/supervisor/supervisord.log

# MongoDB logs
tail -f /var/log/mongodb/mongod.log

# Redis logs
tail -f /var/log/redis/redis-server.log
```

### Database Operations

#### Backup
```bash
# Backup entire database
mongodump --db email_assistant_db --out /backup/$(date +%Y%m%d)

# Backup specific collection
mongodump --db email_assistant_db --collection users --out /backup/users
```

#### Restore
```bash
# Restore database
mongorestore --db email_assistant_db /backup/20251119/email_assistant_db

# Restore specific collection
mongorestore --db email_assistant_db --collection users /backup/users/users.bson
```

#### Seed Data
```bash
# Create super admin
cd /app/backend
python scripts/create_super_admin.py

# Create seed data for testing
python scripts/create_seed_data.py
```

---

## 🧪 Testing

### Manual Testing Flow

#### 1. Authentication Test
```bash
# Register new user
curl -X POST http://localhost:8001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"Test@123"}'

# Get profile (with token)
curl -X GET http://localhost:8001/api/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

#### 2. Email Processing Test
```bash
# Connect email account via frontend
# Send test email to connected account
# Wait 60 seconds for polling
# Check email processed and draft generated
```

#### 3. Inbound Lead Test
```bash
# List leads
curl -X GET http://localhost:8001/api/leads \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

# Get lead statistics
curl -X GET http://localhost:8001/api/leads/stats/summary \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Automated Testing

See `/app/tests/` directory for:
- `test_result.md` - Testing protocol and results
- `backend_test.py` - Backend API tests
- `test_production_flow.py` - End-to-end flow tests

---

## 📊 System Status

### Current Status (as of November 19, 2025)

✅ **All Systems Operational**

| Component | Status | Details |
|-----------|--------|---------|
| Backend API | ✅ Running | Port 8001, PID: 953 |
| Frontend | ✅ Running | Port 3000, PID: 955 |
| MongoDB | ✅ Running | Port 27017, PID: 956 |
| Redis | ✅ Running | Port 6379 |
| Email Worker | ✅ Running | PID: 1156 (60s polling) |
| Campaign Worker | ✅ Running | PID: 1157 (30s batch) |
| Nginx Proxy | ✅ Running | PID: 952 |

### Super Admin Credentials

**Email**: `admin@crm.com`  
**Password**: `Admin@123`  
**Role**: `super_admin`  
**Quota**: 10,000 emails

---

## 🎯 Key Endpoints Reference

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT
- `GET /api/auth/me` - Get current user

### Email Management
- `GET /api/emails` - List user's emails
- `GET /api/emails/{email_id}` - Get email details
- `PUT /api/emails/{email_id}/draft` - Update draft
- `POST /api/emails/{email_id}/send` - Send email manually

### Email Accounts
- `GET /api/email-accounts` - List connected accounts
- `DELETE /api/email-accounts/{account_id}` - Disconnect account

### OAuth
- `GET /api/oauth/google/url?account_type=email` - Get Google OAuth URL
- `GET /api/oauth/google/callback?code=...&state=...` - Handle OAuth callback
- `GET /api/oauth/microsoft/url?account_type=email` - Get Microsoft OAuth URL

### Intents
- `GET /api/intents` - List intents
- `POST /api/intents` - Create intent
- `PUT /api/intents/{intent_id}` - Update intent
- `DELETE /api/intents/{intent_id}` - Delete intent

### Knowledge Base
- `GET /api/knowledge-base` - List knowledge base entries
- `POST /api/knowledge-base` - Create entry
- `PUT /api/knowledge-base/{kb_id}` - Update entry
- `DELETE /api/knowledge-base/{kb_id}` - Delete entry

### Inbound Leads
- `GET /api/leads` - List leads (with filters)
- `GET /api/leads/stats/summary` - Lead statistics
- `GET /api/leads/{lead_id}` - Get lead details
- `PUT /api/leads/{lead_id}` - Update lead
- `POST /api/leads/{lead_id}/stage` - Change lead stage
- `GET /api/leads/{lead_id}/emails` - Get lead emails

### Calendar
- `GET /api/calendar/providers` - List calendar providers
- `POST /api/calendar/providers` - Connect calendar
- `GET /api/calendar/events` - List events
- `POST /api/calendar/events` - Create event
- `PUT /api/calendar/events/{event_id}` - Update event

### Campaigns
- `GET /api/campaigns` - List campaigns
- `POST /api/campaigns` - Create campaign
- `GET /api/campaigns/{campaign_id}` - Get campaign details
- `POST /api/campaigns/{campaign_id}/send` - Send campaign
- `GET /api/campaigns/{campaign_id}/analytics` - Campaign analytics

### Follow-ups
- `GET /api/follow-ups` - List follow-ups
- `GET /api/follow-ups/{follow_up_id}` - Get follow-up details
- `DELETE /api/follow-ups/{follow_up_id}` - Cancel follow-up

### System
- `GET /api/health` - Health check
- `GET /api/system/stats` - System statistics

---

## 🛠️ Troubleshooting

### Common Issues

#### Backend Not Starting
```bash
# Check logs
tail -f /var/log/supervisor/backend.err.log

# Common causes:
# - MongoDB not running
# - Redis not running
# - Missing environment variables
# - Port 8001 already in use

# Solutions:
sudo supervisorctl restart mongodb
redis-server --daemonize yes
sudo supervisorctl restart backend
```

#### Workers Not Processing
```bash
# Check if workers are running
ps aux | grep "run_.*_worker.py"

# Check worker logs
tail -f /var/log/email_worker.log
tail -f /var/log/campaign_worker.log

# Restart workers
pkill -f "run_.*_worker.py"
/app/start_workers.sh
```

#### OAuth Token Expired
```bash
# Tokens expire after 1 hour
# Automatic refresh is implemented
# If issues persist:

# 1. Check email_accounts collection
mongo email_assistant_db --eval "db.email_accounts.find().pretty()"

# 2. Reconnect OAuth account via frontend
# 3. Check backend logs for refresh errors
tail -f /var/log/supervisor/backend.err.log | grep "token"
```

#### Email Not Auto-Sending
```bash
# Checklist:
# 1. Intent has auto_send=true?
mongo email_assistant_db --eval "db.intents.find({auto_send: true}).pretty()"

# 2. Email worker running?
ps aux | grep "run_email_worker.py"

# 3. Check email status
mongo email_assistant_db --eval "db.emails.find({status: 'draft_ready'}).pretty()"

# 4. Check worker logs
tail -f /var/log/email_worker.log | grep "auto-send"
```

---

## 📚 Additional Documentation

- `/app/tests/test_result.md` - Complete testing protocol and results
- `/app/SYSTEM_STATUS.md` - Current system status and seed data
- `/app/PRODUCTION_READY_STATUS.md` - Production readiness checklist
- `/app/docs/` - Additional documentation (if exists)

---

## 👥 User Roles & Permissions

### User
- Manage own emails and accounts
- Create intents and knowledge base
- View own campaigns and leads
- Connect OAuth accounts
- Send emails within quota

### Admin
- All user permissions
- View all users (read-only)
- Higher email quota
- Access to system statistics

### Super Admin
- All admin permissions
- Create/delete users
- Access all data
- System configuration
- Unlimited quota

---

## 🔄 Data Flow Diagrams

### Email Processing Flow
```
Incoming Email
    ↓
Email Worker Polls (60s)
    ↓
Store in DB (status: new)
    ↓
Classify Intent (keyword matching)
    ↓
Detect Meeting (if keywords present)
    ↓
Generate Draft (AI with KB + context)
    ↓
Validate Draft (AI quality check)
    ↓
[If auto_send enabled]
    ↓
Send via Gmail API (in thread)
    ↓
Create Follow-ups (2, 4, 6 days)
    ↓
[If meeting detected]
    ↓
Create Calendar Event (with Meet link)
    ↓
Send Reminder (1hr before)
```

### OAuth Flow
```
User clicks "Connect Gmail"
    ↓
Frontend calls GET /api/oauth/google/url
    ↓
Backend generates OAuth URL + state
    ↓
Frontend redirects to Google OAuth
    ↓
User authorizes on Google
    ↓
Google redirects to /api/oauth/google/callback
    ↓
Backend exchanges code for tokens
    ↓
Store tokens in email_accounts
    ↓
Backend redirects to frontend with success
    ↓
Frontend shows success message
    ↓
Email worker starts polling account
```

---

## 🎯 Next Steps & Roadmap

### Immediate Tasks
1. ✅ Redis installed and running
2. ✅ Background workers deployed
3. ✅ Super admin created
4. ✅ System fully operational

### Recommended Enhancements
1. Add webhook support for instant email notifications
2. Implement advanced lead scoring algorithms
3. Add team collaboration features
4. Create email templates library
5. Add A/B testing for campaigns
6. Implement detailed analytics dashboard
7. Add custom fields for leads
8. Integrate with more CRM systems

### Production Checklist
- ✅ All services running
- ✅ Background workers active
- ✅ Authentication working
- ✅ Email processing functional
- ✅ OAuth integration working
- ✅ Calendar integration working
- ✅ Lead management working
- ✅ Campaign system working
- ✅ Error handling implemented
- ✅ Logging configured

---

**Last Updated:** November 19, 2025  
**System Version:** Production 1.0  
**Status:** ✅ Fully Operational

