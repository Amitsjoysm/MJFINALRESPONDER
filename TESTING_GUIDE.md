# Testing Guide - AI Email Automation System

**Account**: amits.joys@gmail.com  
**Password**: ij@123  
**Date**: March 12, 2025

---

## ✅ Seed Data Created

### Intents (8 total)
All intents have **auto-send enabled** for automatic testing:

1. **Meeting Request** - Priority 10
   - Keywords: meeting, schedule, meet, call, discussion, chat, catch up, sync, connect
   - Auto-send: ✅ YES

2. **Meeting Reschedule** - Priority 9
   - Keywords: reschedule, change meeting, different time, postpone, move meeting, another time
   - Auto-send: ✅ YES

3. **Support Request** - Priority 8
   - Keywords: help, issue, problem, error, bug, not working, support, assistance, trouble
   - Auto-send: ✅ YES

4. **Demo Request** - Priority 8 (Lead Intent)
   - Keywords: demo, trial, test, try, demonstration, preview, show me
   - Auto-send: ✅ YES
   - Creates inbound lead

5. **Pricing Request** - Priority 7 (Lead Intent)
   - Keywords: pricing, price, cost, how much, fee, payment, plan, subscription
   - Auto-send: ✅ YES
   - Creates inbound lead

6. **General Inquiry** - Priority 5
   - Keywords: question, inquiry, information, tell me, explain, how does, what is, wondering
   - Auto-send: ✅ YES

7. **Thank You** - Priority 4
   - Keywords: thank, thanks, appreciate, grateful, awesome, great, excellent
   - Auto-send: ✅ YES

8. **Default Response** - Priority 1
   - No keywords (catches everything else)
   - Auto-send: ✅ YES

### Knowledge Base (8 entries)

1. **Company Overview** - Company Information
2. **Product Features** - Product
3. **Meeting and Calendar Features** - Meetings
4. **Pricing Information** - Pricing
5. **Getting Started Guide** - Documentation
6. **Support and Contact** - Support
7. **Security and Privacy** - Security
8. **Integration and API** - Integration

### User Persona
Professional and friendly business representative with clear, concise communication style.

---

## 🧪 Test Scenarios

### Test 1: Meeting Request (High Priority)
**Send this email to**: amits.joys@gmail.com

```
Subject: Can we schedule a meeting?

Hi,

I'd like to discuss our project requirements. Are you available for a call next Tuesday at 2 PM?

Looking forward to hearing from you.

Best,
John Doe
john.doe@example.com
```

**Expected Result:**
- ✅ Intent detected: "Meeting Request"
- ✅ Meeting detected with medium confidence
- ✅ Draft generated asking for confirmation
- ✅ Auto-reply sent (since auto_send = true)
- ✅ Response includes meeting details
- ✅ Calendar event may be created if confidence >= 0.8

**What to Check:**
- Dashboard shows email as "processed"
- Status shows "sent"
- Draft content is NOT just "Hi John," (validation fix applied)
- Response has meeting confirmation details

---

### Test 2: Pricing Inquiry (Lead Intent)
**Send this email to**: amits.joys@gmail.com

```
Subject: Question about pricing

Hello,

I'm interested in your email automation platform. Can you tell me more about your pricing plans and features?

I'm looking for a solution for our team of about 10 people.

Thanks,
Sarah Smith
sarah.smith@company.com
```

**Expected Result:**
- ✅ Intent detected: "Pricing Request"
- ✅ Inbound lead created
- ✅ Draft generated with pricing details from knowledge base
- ✅ Auto-reply sent with comprehensive pricing info
- ✅ Lead qualification may trigger additional questions

**What to Check:**
- Email processed successfully
- Inbound lead appears in "Inbound Leads" page
- Response includes pricing from knowledge base (Starter $29, Pro $99, Enterprise Custom)
- Response is substantial (>100 words, not greeting-only)

---

### Test 3: Demo Request (Lead Intent)
**Send this email to**: amits.joys@gmail.com

```
Subject: Demo Request

Hi,

I'd like to see a demo of your platform. Can you show me how it works?

Thank you,
Mike Johnson
mike@startup.io
```

**Expected Result:**
- ✅ Intent detected: "Demo Request"
- ✅ Inbound lead created
- ✅ Draft generated offering to schedule demo
- ✅ Auto-reply sent enthusiastically
- ✅ May include meeting scheduling

**What to Check:**
- Lead created with "Demo Request" intent
- Response offers to schedule a demo session
- Response explains what they'll see
- Not greeting-only

---

### Test 4: Support Request
**Send this email to**: amits.joys@gmail.com

```
Subject: Help needed

I'm having trouble connecting my Gmail account. It keeps saying "OAuth error". Can you help?

Thanks,
Alex Brown
alex@company.com
```

**Expected Result:**
- ✅ Intent detected: "Support Request"
- ✅ Draft generated with helpful guidance
- ✅ Auto-reply sent with troubleshooting steps
- ✅ References support knowledge base

**What to Check:**
- Empathetic and helpful tone
- Provides clear guidance
- References support contact info from KB

---

### Test 5: Thank You Message (Simple)
**Send this email to**: amits.joys@gmail.com

```
Subject: Re: Demo Session

Thanks for the great demo session yesterday! Really appreciated it.

Best,
Lisa
```

**Expected Result:**
- ✅ Intent detected: "Thank You"
- ✅ Draft generated with warm acknowledgment
- ✅ Auto-reply sent
- ✅ Short but complete response (not just greeting)

**What to Check:**
- Warm and appreciative tone
- Acknowledges their thanks
- Offers continued support
- NOT greeting-only

---

### Test 6: General Inquiry
**Send this email to**: amits.joys@gmail.com

```
Subject: How does your platform work?

Hi,

I'm curious about how your email automation works. What technologies do you use?

Regards,
Tom Wilson
```

**Expected Result:**
- ✅ Intent detected: "General Inquiry"
- ✅ Draft generated with product information
- ✅ Auto-reply sent using knowledge base
- ✅ Comprehensive response about features

**What to Check:**
- Uses "Product Features" from knowledge base
- Lists features like Smart Classification, AI Responses, etc.
- Offers additional help

---

### Test 7: Greeting-Only Protection (Validation Test)
**This should NOT happen, but let's verify:**

If any draft is generated as just "Hi [Name]," the system should:
1. ❌ Reject in Layer 2 validation (greeting-only detection)
2. 🔄 Retry draft generation (max 2 times)
3. ✅ Generate complete response on retry
4. 📊 Or escalate if retry fails

**Monitor logs for:**
```bash
tail -f /var/log/supervisor/email-worker.out.log | grep "VALIDATION"
```

You should see:
- ✅ "Draft validation PASSED"
- ❌ NOT "Greeting-only response detected"

---

## 📊 Testing Checklist

### Before Testing
- [x] Seed data created (8 intents, 8 KB entries)
- [x] User persona set
- [x] Backend running (port 8001)
- [x] MongoDB connected
- [x] GROQ API key configured
- [x] Validation fix applied

### During Testing
- [ ] Send at least one email for each intent type
- [ ] Verify auto-replies are sent
- [ ] Check responses are NOT greeting-only
- [ ] Verify intents are correctly classified
- [ ] Check knowledge base is used in responses
- [ ] Verify meeting detection works
- [ ] Verify lead creation for demo/pricing requests
- [ ] Check email thread tracking works

### After Testing
- [ ] Review all processed emails in Dashboard
- [ ] Check Inbound Leads page for created leads
- [ ] Verify no emails in "escalated" status
- [ ] Check validation passed for all drafts
- [ ] Review email_worker logs for errors

---

## 🔍 Monitoring & Debugging

### View Backend Logs
```bash
# Email processing logs
tail -f /var/log/supervisor/email-worker.out.log

# Look for these key messages:
# - "Processing email {id}"
# - "Intent '{name}' matched"
# - "Draft validation PASSED"
# - "Auto-sent reply"
```

### Check Database
```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017/email_assistant_db

# Check processed emails
db.emails.find({
  user_id: "1727993d-2348-4d48-bef6-c6637f69703f",
  processed: true
}).sort({received_at: -1}).limit(5)

# Check created leads
db.inbound_leads.find({
  user_id: "1727993d-2348-4d48-bef6-c6637f69703f"
})

# Check intents
db.intents.find({
  user_id: "1727993d-2348-4d48-bef6-c6637f69703f"
}).count()
```

### API Endpoints to Test
```bash
# Health check
curl http://localhost:8001/api/health

# Get user intents (requires auth token from UI)
curl http://localhost:8001/api/intents \
  -H "Authorization: Bearer YOUR_TOKEN"

# Get knowledge base (requires auth token)
curl http://localhost:8001/api/knowledge-base \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 📧 Email Format Tips

### Good Test Emails
- Include specific keywords from intents
- Ask clear questions
- Provide context
- Use realistic names and email addresses

### Avoid
- Single word emails
- Spam-like content
- Missing context
- Very short messages (unless testing greeting detection)

---

## 🎯 Success Criteria

For the system to be working correctly, you should see:

✅ **Intent Classification**
- All test emails correctly matched to appropriate intents
- Keywords trigger the right intent (e.g., "meeting" → Meeting Request)
- Default intent catches unmatched emails

✅ **Draft Generation**
- All drafts are complete responses (>50 chars after greeting)
- Drafts reference knowledge base information
- Drafts are contextual to the email content
- No greeting-only responses like "Hi Name,"

✅ **Validation**
- All drafts pass validation (visible in logs)
- No escalated emails (unless intentional failure)
- Retry logic works (2nd attempt succeeds)

✅ **Auto-Send**
- Emails with auto_send=true are sent automatically
- Sent emails visible in Dashboard with "sent" status
- Replies appear in the original email thread

✅ **Lead Management**
- Demo requests create leads
- Pricing inquiries create leads
- Leads appear in "Inbound Leads" page with correct status

✅ **Meeting Detection**
- Meeting requests detected
- Calendar events created (if confidence >= 0.8)
- Meeting confirmation in response

---

## 🚨 Common Issues & Solutions

### Issue: Emails not being processed
**Check:**
- Email account is connected and active
- Email worker is running: `sudo supervisorctl status`
- Check logs: `tail -f /var/log/supervisor/email-worker.out.log`

### Issue: No auto-reply sent
**Check:**
- Intent has `auto_send: true`
- Draft validation passed
- Email account can send (OAuth permissions)
- Check for errors in logs

### Issue: Response is too short or greeting-only
**This should NOT happen with validation fix**
**If it does:**
- Check validation logs for "VALIDATION FAILED"
- Verify GROQ API key is working
- Check if retry logic triggered
- Review ai_agent_service.py validation code

### Issue: Wrong intent detected
**Check:**
- Keywords in email match intent keywords
- Intent priority is correct (higher priority = first match)
- Check intent configuration in database or UI

---

## 📞 Need Help?

If you encounter issues during testing:

1. **Check Logs First**
   ```bash
   tail -n 100 /var/log/supervisor/email-worker.err.log
   tail -n 100 /var/log/supervisor/backend.err.log
   ```

2. **Verify Services Running**
   ```bash
   sudo supervisorctl status
   ```

3. **Test Backend Health**
   ```bash
   curl http://localhost:8001/api/health
   ```

4. **Review Validation**
   ```bash
   cd /app
   python test_validation_fix.py
   ```

---

## ✅ Quick Start Testing

**Fastest way to test:**

1. **Login to UI**
   - URL: `https://followup-enhance.preview.emergentagent.com`
   - Email: amits.joys@gmail.com
   - Password: ij@123

2. **Send Test Email**
   - From any email account, send to: amits.joys@gmail.com
   - Subject: "Can we schedule a meeting next Tuesday?"
   - Body: Include "meeting" keyword

3. **Check Dashboard**
   - Go to Dashboard
   - Wait 1-2 minutes for processing
   - Email should show as "processed" and "sent"
   - Click to view draft content

4. **Verify Response**
   - Check your sent email for reply
   - Should NOT be just "Hi [Name],"
   - Should include meeting discussion

---

**Happy Testing! 🚀**

All seed data is in place. The system is configured for comprehensive testing of intents, validation, meeting detection, and lead management.
