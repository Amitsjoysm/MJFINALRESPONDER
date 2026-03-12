# 🎯 Lead Qualification System - Complete Guide

## Overview

The Lead Qualification System is an intelligent, AI-powered feature that automatically evaluates and scores inbound leads based on their responses to strategic questions. It helps you identify high-quality leads and prioritize your sales efforts.

---

## 📊 System Status

✅ **Redis**: Running on localhost:6379  
✅ **Email Worker**: Running (PID: 1176)  
✅ **Campaign Worker**: Running (PID: 1177)  
✅ **Backend API**: Running on http://0.0.0.0:8001  
✅ **Frontend**: Running on http://0.0.0.0:3000  
✅ **MongoDB**: Running  
✅ **Global Lead Qualification**: ENABLED  
✅ **Global Lead Nurturing**: ENABLED  

---

## 🔧 How Lead Qualification Works

### 1. **Email Intent Detection**
When an email arrives, the system:
- Analyzes the email content
- Matches it against configured intents using keywords
- Determines if it's a lead-qualifying intent (e.g., "Pricing Inquiry", "Demo Request")

**Example Lead Intents:**
- **Pricing Inquiry (Lead)** - Keywords: pricing, price, cost, how much, quote
- **Demo Request (Lead)** - Keywords: demo, trial, test, try, demonstration
- **Partnership Inquiry (Lead)** - Keywords: partnership, partner, collaborate, integration

### 2. **Lead Creation**
If the email matches a lead intent:
- A lead record is created in the `inbound_leads` collection
- Initial stage is set to `awaiting_info`
- Initial score is 0

### 3. **Question Generation (Lead Nurturing)**
The system automatically generates 2 contextual questions per email from a configured pool:

**Available Nurturing Questions:**
1. What specific features are you most interested in? (Priority 1)
2. What is your company size? (Priority 2, Required)
3. What is your budget range for this solution? (Priority 3, Required)
4. When are you looking to implement this? (Priority 4)
5. What industry is your company in? (Priority 5, Required)

**Configuration:**
- `questions_per_email`: 2 questions per email
- `max_exchanges`: Up to 3 email exchanges
- `use_contextual_questions`: True (questions selected based on email context)
- `natural_integration`: True (questions integrated naturally into email)

### 4. **Answer Extraction**
When the lead replies:
- The system uses Groq AI (llama-3.3-70b-versatile model) to extract answers
- Matches answers to previously asked questions
- Stores answers in the lead record

**Example:**
```
Email: "Our company has 75 employees, budget is $10k/month, and we're in Technology"

Extracted Answers:
- company_size: "75 employees"
- budget: "$10k/month"
- industry: "Technology"
```

### 5. **Lead Scoring**
The system scores leads on a **0-100 scale** based on answers to qualification questions:

**Qualification Questions & Weights:**
1. What is your company size? - **25% weight** (Required)
2. What is your monthly budget for this solution? - **30% weight** (Required)
3. What industry are you in? - **20% weight** (Required)
4. What is your role in the company? - **25% weight** (Optional)

**Scoring Formula:**
```
Score = (Sum of weights for answered questions / Sum of weights for all required questions) × 100
```

**Example:**
- 2 out of 3 required questions answered
- Weight: (0.25 + 0.30) / (0.25 + 0.30 + 0.20) = 0.73
- Score: 73/100 ✅ **QUALIFIED** (≥60 threshold)

### 6. **Lead Stage Transitions**
Based on the score, leads are automatically categorized:

| Score Range | Stage | Action |
|------------|-------|--------|
| 0 (no answers) | `awaiting_info` | Send follow-up with questions |
| 1-59 | `unqualified` | Low priority, stop nurturing |
| 60-100 | `qualified` | High priority, route to sales |

### 7. **Follow-up Management**
- **Awaiting Info**: 3 follow-ups scheduled (Day 2, Day 4, Day 6)
- **Qualified/Unqualified**: No new follow-ups created
- **Reply Received**: Old follow-ups cancelled automatically

---

## 🎛️ Where Users Configure Lead Qualification

### **1. Lead Controls Page** (`/lead-settings`)

This is the **main control panel** for enabling/disabling lead features:

**Global Toggles:**
- ✅ **Enable Lead Qualification** - Turns on automatic lead scoring
- ✅ **Enable Lead Nurturing** - Turns on automatic question asking

**Purpose:**
- Master switches for the entire lead qualification system
- Must be enabled for lead processing to work
- Applies to all intents configured as lead intents

**Current Status:**
- ✅ Global Lead Qualification: **ENABLED**
- ✅ Global Lead Nurturing: **ENABLED**

⚠️ **Known Issue**: Toggle switches have 520 API errors on `/api/auth/settings` endpoint. This is a backend issue that needs investigation.

---

### **2. Lead Qualification Page** (`/lead-qualification`)

This is where users **define the specific criteria and questions** for qualifying leads:

**What Users Can Configure:**

#### A. **Criteria Information**
- **Criteria Name**: "B2B SaaS Lead Qualification"
- **Description**: Purpose of the criteria
- **Min Score**: 60 (threshold for qualification)
- **Max Exchanges**: 3 (maximum email attempts)
- **Auto-disqualify**: Automatically disqualify if threshold not met

#### B. **Qualification Questions**
Users add questions that will be used to score leads:

**Example Configuration:**
```
Question 1:
  Text: "What is your company size?"
  Key: "company_size"
  Weight: 25%
  Required: Yes

Question 2:
  Text: "What is your monthly budget for this solution?"
  Key: "budget"
  Weight: 30%
  Required: Yes

Question 3:
  Text: "What industry are you in?"
  Key: "industry"
  Weight: 20%
  Required: Yes

Question 4:
  Text: "What is your role in the company?"
  Key: "job_title"
  Weight: 25%
  Required: No
```

**How It Works:**
1. User clicks "New Criteria" button
2. Fills out criteria name, description, scoring parameters
3. Adds questions with text, key (unique identifier), weight, and required status
4. Saves the criteria
5. System uses these questions to evaluate leads

**Purpose of Questions:**
- **Scoring**: Each question has a weight that contributes to the final score
- **Qualification**: Required questions must be answered for qualification
- **Intelligence**: Questions gather critical information to assess lead quality
- **Automation**: System automatically asks these questions via email
- **Prioritization**: Higher weights indicate more important questions

---

### **3. Intent Configuration** (Backend/API)

Each intent can be configured as a lead intent:

**Lead Intent Settings:**
- `is_inbound_lead`: true/false (marks intent as lead-qualifying)
- `enable_lead_qualification`: true/false (enable scoring for this intent)
- `enable_lead_nurturing`: true/false (enable questions for this intent)
- `auto_send`: true/false (automatically send reply)

**Current Lead Intents:**
1. **Pricing Inquiry (Lead)** ✅ Qualification ✅ Nurturing
2. **Demo Request (Lead)** ✅ Qualification ✅ Nurturing
3. **Partnership Inquiry (Lead)** ✅ Qualification ❌ Nurturing

---

## 💡 Purpose of Questions in Lead Qualification

### **1. Nurturing Questions (Asked via Email)**
**Location:** Lead Nurturing Configuration  
**Purpose:** Gather information naturally through conversation

**Characteristics:**
- Contextual and conversational
- 2 questions per email (not overwhelming)
- Integrated naturally into email drafts
- Selected based on email context and priority
- Asked across multiple exchanges (up to 3)

**Example Integration:**
```
"Thank you for your interest in our pricing! I'd be happy to help you 
find the right plan for your needs.

To provide you with the most accurate recommendation, could you share:
- What is your company size?
- What is your budget range for this solution?

Our plans are designed to scale with your business, and I want to ensure 
we match you with the perfect fit.

Looking forward to hearing from you!"
```

### **2. Qualification Questions (Used for Scoring)**
**Location:** Lead Qualification Criteria  
**Purpose:** Evaluate and score lead quality

**Characteristics:**
- Strategic and targeted
- Weighted by importance (25-30%)
- Some required, some optional
- Used to calculate qualification score
- Determine lead stage (qualified/unqualified/awaiting_info)

**Scoring Logic:**
- Required questions are essential for qualification
- Optional questions add bonus points
- Weight determines impact on final score
- Score ≥60 = Qualified, <60 = Unqualified

### **3. How They Work Together**

```
┌─────────────────────────────────────────────────────────────────┐
│                    EMAIL ARRIVES (Lead Intent)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              NURTURING: Select 2 Questions to Ask                │
│              (From nurturing question pool)                      │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              DRAFT: Integrate Questions Naturally                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                   SEND: Auto-reply with Questions                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                  LEAD REPLIES with Answers                       │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│              AI: Extract Answers from Reply Email                │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│    QUALIFICATION: Score Lead Based on Answered Questions         │
│    (Using qualification criteria with weights)                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│           STAGE UPDATE: qualified/unqualified/awaiting_info      │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Current Configuration Summary

### Demo User Settings
- **Email**: demo@example.com
- **Password**: demo123
- **User ID**: 19d7c857-fa0b-4fb8-85c5-c8108554c81c
- **Global Qualification**: ✅ ENABLED
- **Global Nurturing**: ✅ ENABLED

### Qualification Criteria
- **Name**: B2B SaaS Lead Qualification
- **Type**: Question-based
- **Min Score**: 60% threshold
- **Max Exchanges**: 3 attempts
- **Questions**: 4 (3 required, 1 optional)
- **Status**: ✅ Active

### Nurturing Configuration
- **Name**: Standard B2B Nurturing
- **Questions Pool**: 5 questions (3 required, 2 optional)
- **Questions Per Email**: 2
- **Max Exchanges**: 3
- **Status**: ✅ Active

### Lead Intents
- **Pricing Inquiry (Lead)** - 90% confidence
- **Demo Request (Lead)** - 90% confidence
- **Partnership Inquiry (Lead)** - 90% confidence

### Sample Leads Created
- 5 sample leads with various stages (qualified, awaiting_info, new, unqualified)
- Scores ranging from 0 to 95
- Realistic test data for demonstration

---

## 🧪 Testing Lead Qualification

### Test the Complete Flow

Use the Test Session API endpoint:

```bash
# Step 1: Send initial lead email
POST /api/test-session/send-message
{
  "sender_email": "john@techcompany.com",
  "sender_name": "John Smith",
  "subject": "Pricing Information",
  "body": "Hi, I'm interested in your product. Can you share pricing details?",
  "test_user_email": "demo@example.com"
}

# Expected: 
# - Intent: "Pricing Inquiry (Lead)"
# - Lead created with stage="awaiting_info"
# - 2 questions generated and included in draft
# - 3 follow-ups scheduled

# Step 2: Send reply with answers
POST /api/test-session/send-message
{
  "sender_email": "john@techcompany.com",
  "subject": "Re: Pricing Information",
  "body": "Our company has 75 employees, budget is $10k/month, and we're in Technology",
  "session_id": "<session_id_from_step_1>"
}

# Expected:
# - Answers extracted (company_size, budget, industry)
# - Lead scored (e.g., 73/100)
# - Stage updated to "qualified" (score ≥60)
# - Old follow-ups cancelled
```

### Check Lead Status

```python
# Query lead record
lead = await db.inbound_leads.find_one({"email": "john@techcompany.com"})

# Check fields
print(f"Stage: {lead['stage']}")  # qualified/unqualified/awaiting_info
print(f"Score: {lead['qualification_score']}")  # 0-100
print(f"Answers: {lead['qualification_answers']}")
print(f"Questions Asked: {lead['last_questions_asked']}")
```

---

## 🐛 Known Issues

### 1. Lead Controls Toggle (520 Error)
**Issue**: Toggle switches on `/lead-settings` page fail with 520 errors  
**Endpoint**: `/api/auth/settings`  
**Impact**: Users cannot enable/disable global settings via UI  
**Workaround**: Settings can be updated via database directly  
**Status**: ⚠️ Needs Backend Investigation

---

## ✅ System Health Check

Run this command to verify everything is working:

```bash
cd /app && python3 << 'EOF'
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def health_check():
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    db = client.email_assistant_db
    
    user = await db.users.find_one({"email": "demo@example.com"})
    criteria = await db.lead_qualification_criteria.find_one({"user_id": user['id']})
    nurturing = await db.lead_nurturing_config.find_one({"user_id": user['id']})
    intents = await db.intents.find({"user_id": user['id'], "is_inbound_lead": True}).to_list(100)
    leads = await db.inbound_leads.find({"user_id": user['id']}).to_list(100)
    
    print("✅ Demo User:", "FOUND" if user else "MISSING")
    print("✅ Qualification Criteria:", "CONFIGURED" if criteria else "MISSING")
    print("✅ Nurturing Config:", "CONFIGURED" if nurturing else "MISSING")
    print(f"✅ Lead Intents: {len(intents)} configured")
    print(f"✅ Sample Leads: {len(leads)} in database")
    print(f"✅ Global Qualification: {'ENABLED' if user.get('global_lead_qualification_enabled') else 'DISABLED'}")
    print(f"✅ Global Nurturing: {'ENABLED' if user.get('global_lead_nurturing_enabled') else 'DISABLED'}")
    
    client.close()

asyncio.run(health_check())
EOF
```

---

## 📚 Additional Resources

- **Test Results**: `/app/test_result.md` - Complete testing documentation
- **Seed Data**: `/app/SEED_DATA_README.md` - Seed data documentation
- **API Documentation**: Check backend routes for API endpoints
- **Worker Logs**: 
  - Email Worker: `/var/log/email_worker.log`
  - Campaign Worker: `/var/log/campaign_worker.log`

---

**Last Updated**: January 7, 2026  
**System Version**: Production-ready with Parlant.io architecture  
**Demo Credentials**: demo@example.com / demo123
