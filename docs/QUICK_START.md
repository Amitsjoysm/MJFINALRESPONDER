# Quick Start Guide

## ✅ Your System is Ready!

**User**: amits.joys@gmail.com  
**Status**: All services running, seed data created

---

## What Was Done

✅ Removed old seed data  
✅ Created 8 comprehensive intents  
✅ Created 6 knowledge base entries  
✅ Fixed "failed to load" error (was missing data)  
✅ Created production deployment script  
✅ All systems operational  

---

## Try It Now

### 1. Login to Frontend
```
URL: http://localhost:3000
Email: amits.joys@gmail.com
Password: ij@123
```

### 2. View Your Data

**Intents Page**  
Click "Intents" → See 8 intents with keywords and prompts

**Knowledge Base Page**  
Click "Knowledge Base" → See 6 comprehensive entries

**Emails Page**  
Click "Emails" → View processed emails (if any)

---

## Test Email Processing

1. Send email to your connected Gmail account
2. Include keywords like: "meeting", "help", "question"
3. Wait 60 seconds (worker polls every minute)
4. Check "Emails" page for:
   - ✅ Intent classification
   - ✅ Draft generation
   - ✅ Auto-send (if enabled)

---

## Deployment Script

### Basic Usage
```bash
./deploy.sh
```

### Options
```bash
--branch <name>     # Deploy specific branch
--db-name <name>    # Custom database name
--skip-git          # Skip git operations
--skip-deps         # Skip dependency install
--dev               # Development mode
--help              # Show all options
```

### Example
```bash
./deploy.sh --branch production --db-name prod_email_db
```

---

## Check System Status

```bash
# View all services
sudo supervisorctl status

# Check backend logs
tail -f /var/log/email-assistant-backend.err.log

# Check frontend logs  
tail -f /var/log/email-assistant-frontend.err.log
```

---

## Quick Commands

```bash
# Restart everything
sudo supervisorctl restart all

# Check API health
curl http://localhost:8001/api/health

# Check Redis
redis-cli ping

# Check MongoDB
mongosh email_assistant_db --eval "db.intents.countDocuments()"
```

---

## Seed Data Summary

### 8 Intents Created
- Meeting Request (auto-send ✅)
- Support Request (auto-send ✅)
- General Inquiry (auto-send ✅)
- Follow-up Request (auto-send ✅)
- Introduction (auto-send ✅)
- Thank You (auto-send ✅)
- Urgent Request (manual review ❌)
- Default (catches all unmatched ✅)

### 6 Knowledge Base Entries
- Company Overview
- Product Features
- Pricing Information
- Getting Started Guide
- Support and Contact
- Security and Privacy

---

## What's Running

```
✅ Backend:  http://localhost:8001
✅ Frontend: http://localhost:3000
✅ MongoDB:  mongodb://localhost:27017
✅ Redis:    redis://localhost:6379
✅ Workers:  Email (60s), Follow-up (5m), Reminder (1h)
```

---

## Need Help?

📚 Full Guide: `/app/DEPLOYMENT_GUIDE.md`  
📊 Test Results: `/app/test_result.md`  
🏗️ Architecture: `/app/ARCHITECTURE.md`  

---

**🎉 Everything is ready! Start using your AI Email Assistant now!**
