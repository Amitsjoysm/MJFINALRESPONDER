# Worker Status and Email Issue Resolution

## Date: January 12, 2026

---

## ✅ Workers Status: ALL ACTIVE

### Email Worker
- **Status**: ✅ Running (PID: 2425)
- **Uptime**: Since 05:24
- **Redis**: ✅ Connected (PONG)
- **Polling Interval**: Every 60 seconds
- **Last Activity**: Polling active accounts

### Campaign Worker
- **Status**: ✅ Running (PID: 2426)
- **Uptime**: Since 05:24
- **Polling**: Every 30 seconds
- **Status**: Active and processing

### Backend Server
- **Status**: ✅ Running
- **API**: Responding correctly
- **Database**: Connected

### Frontend Server
- **Status**: ✅ Running
- **Hot Reload**: Enabled

---

## ❌ Email Issue: Authentication Failure

### Problem
Email sent from **Sharinara68@gmail.com** not received because the email account **amits.joys@gmail.com** has authentication failure.

### Root Cause
```
IMAP sync error: [AUTHENTICATIONFAILED] Invalid credentials (Failure)
```

The email account credentials in the database are **invalid or expired**.

### Why This Happens
1. Gmail App Password expired or was regenerated
2. Account password was changed
3. Wrong credentials were entered during setup
4. 2-Factor Authentication not properly configured

---

## 🔧 Solution Steps

### Step 1: Remove Existing Account
1. Log in to the application as **amits.joys@gmail.com**
2. Go to **Email Accounts** page
3. Delete the existing account with authentication error

### Step 2: Re-add Email Account with Valid Credentials

**For Gmail with App Password (Recommended):**

1. Go to Google Account Settings: https://myaccount.google.com/
2. Navigate to **Security** → **2-Step Verification** (must be enabled)
3. Scroll down to **App passwords**
4. Generate a new app password:
   - Select app: **Mail**
   - Select device: **Other (Custom name)** → Enter "AI Email Assistant"
   - Click **Generate**
5. Copy the 16-character app password (format: xxxx xxxx xxxx xxxx)

6. In the application:
   - Click **"Add Email Account"**
   - Choose **"Gmail (App Password)"**
   - Enter:
     - Email: **amits.joys@gmail.com**
     - App Password: **[paste the 16-character password]**
   - Click **Connect**

**For Gmail with OAuth (Alternative):**
1. Click **"Add Email Account"**
2. Choose **"Gmail (OAuth)"**
3. Click **"Connect with Google"**
4. Authorize the application
5. Complete the OAuth flow

### Step 3: Verify Connection
1. Check the email account status shows **"Active"**
2. Wait 60 seconds for the next polling cycle
3. Check worker logs to confirm no authentication errors:
   ```bash
   tail -f /var/log/email_worker.log
   ```

### Step 4: Send Test Email
1. Send an email from **Sharinara68@gmail.com** to **amits.joys@gmail.com**
2. Subject: "Test - Pricing Inquiry"
3. Body: "Hi, I'm interested in your pricing plans."
4. Wait 60 seconds (polling interval)
5. Check Conversations or Inbox page for the received email

---

## 🔍 Monitoring Commands

### Check Workers
```bash
# Check if workers are running
ps aux | grep -E "run_email_worker|run_campaign_worker" | grep -v grep

# Check worker logs
tail -f /var/log/email_worker.log
tail -f /var/log/campaign_worker.log
```

### Check Redis
```bash
redis-cli ping  # Should return PONG
```

### Check Email Account Status
```bash
# Via MongoDB
cd /app/backend && python -c "
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from config import config

async def check():
    client = AsyncIOMotorClient(config.MONGO_URL)
    db = client[config.DB_NAME]
    user = await db.users.find_one({'email': 'amits.joys@gmail.com'})
    accounts = await db.email_accounts.find({'user_id': user['id']}).to_list(10)
    for acc in accounts:
        print(f'Email: {acc[\"email\"]}')
        print(f'Status: {acc[\"sync_status\"]}')
        print(f'Error: {acc.get(\"error_message\", \"None\")}')

asyncio.run(check())
"
```

---

## ⚡ Quick Fix Summary

1. **Problem**: Email account has invalid credentials
2. **Solution**: Re-add email account with valid Gmail App Password
3. **Workers**: All running correctly ✅
4. **Expected Result**: Emails will be received and processed automatically every 60 seconds

---

## 📋 How Email Flow Works (After Fix)

1. **Email Arrives** at amits.joys@gmail.com from Sharinara68@gmail.com
2. **Worker Polls** (every 60 seconds) and fetches new emails via IMAP
3. **AI Processes**:
   - Classifies intent ("Pricing Request")
   - Detects it's a lead
   - Generates 2 qualifying questions
   - Creates draft email with questions naturally integrated
4. **Draft Ready** for review in the Conversations page
5. **Auto-Send** (if enabled) or Manual Send
6. **Lead Created** in "awaiting_info" stage
7. **Follow-ups Scheduled** (Day 2, 4, 6) automatically

---

## ✅ Status: Workers Active, Waiting for Valid Email Credentials

The system is ready to process emails as soon as valid email account credentials are added.
