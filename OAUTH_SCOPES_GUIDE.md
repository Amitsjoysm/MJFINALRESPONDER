# Google OAuth Scopes & Authorization Setup

**Application**: AI Email Automation System  
**Date**: March 12, 2025

---

## 📋 Required OAuth Scopes

### Gmail Scopes

#### 1. **gmail.readonly** (Read Emails)
```
https://www.googleapis.com/auth/gmail.readonly
```
**Purpose**: Read all emails from user's mailbox
**Used for**: 
- Fetching incoming emails
- Reading email content for AI processing
- Thread tracking
- Email classification

#### 2. **gmail.send** (Send Emails)
```
https://www.googleapis.com/auth/gmail.send
```
**Purpose**: Send emails on behalf of the user
**Used for**:
- Auto-sending AI-generated replies
- Follow-up emails
- Meeting confirmations
- Draft responses

#### 3. **gmail.modify** (Modify Emails)
```
https://www.googleapis.com/auth/gmail.modify
```
**Purpose**: Modify email labels and status
**Used for**:
- Marking emails as read
- Adding/removing labels
- Email organization
- Thread management

#### 4. **gmail.compose** (Optional - Compose Drafts)
```
https://www.googleapis.com/auth/gmail.compose
```
**Purpose**: Create and update draft emails
**Used for**:
- Saving drafts before sending
- Draft preview functionality

### Google Calendar Scopes

#### 5. **calendar** (Full Calendar Access)
```
https://www.googleapis.com/auth/calendar
```
**Purpose**: Full read/write access to user's calendar
**Used for**:
- Creating calendar events from meeting requests
- Reading existing events to check conflicts
- Updating/deleting events
- Creating Google Meet links

#### 6. **calendar.events** (Calendar Events Only)
```
https://www.googleapis.com/auth/calendar.events
```
**Purpose**: Create, read, update, and delete calendar events
**Used for**:
- Meeting detection and creation
- Event reminders
- Conflict detection
- Meeting rescheduling

### User Info Scopes

#### 7. **userinfo.email** (User Email)
```
https://www.googleapis.com/auth/userinfo.email
```
**Purpose**: Get user's email address
**Used for**:
- User identification
- Account linking
- Email verification

#### 8. **userinfo.profile** (User Profile)
```
https://www.googleapis.com/auth/userinfo.profile
```
**Purpose**: Get user's basic profile information
**Used for**:
- User name display
- Profile picture
- Account information

---

## 🔧 Google Cloud Console Setup

### Step 1: Create OAuth 2.0 Credentials

1. **Go to Google Cloud Console**
   ```
   https://console.cloud.google.com
   ```

2. **Create/Select Project**
   - Click "Select a project" → "New Project"
   - Project name: "Email Automation App"
   - Click "Create"

3. **Enable APIs**
   - Go to "APIs & Services" → "Library"
   - Search and enable:
     - ✅ Gmail API
     - ✅ Google Calendar API
     - ✅ Google+ API (for profile info)

4. **Configure OAuth Consent Screen**
   - Go to "APIs & Services" → "OAuth consent screen"
   - User Type: **External** (for testing) or **Internal** (for organization only)
   - Click "Create"

5. **Fill OAuth Consent Screen Details**
   ```
   App name: Email Automation Assistant
   User support email: your-email@example.com
   Developer contact: your-email@example.com
   
   App domain (optional):
   - Home page: https://your-domain.com
   - Privacy policy: https://your-domain.com/privacy
   - Terms of service: https://your-domain.com/terms
   ```

6. **Add Scopes**
   Click "Add or Remove Scopes" and add these scopes:
   
   ```
   ✅ https://www.googleapis.com/auth/gmail.readonly
   ✅ https://www.googleapis.com/auth/gmail.send
   ✅ https://www.googleapis.com/auth/gmail.modify
   ✅ https://www.googleapis.com/auth/calendar
   ✅ https://www.googleapis.com/auth/calendar.events
   ✅ https://www.googleapis.com/auth/userinfo.email
   ✅ https://www.googleapis.com/auth/userinfo.profile
   ```

7. **Add Test Users** (if app is not published)
   - Add email addresses that can test the app
   - Add: amits.joys@gmail.com

8. **Create OAuth 2.0 Credentials**
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: **Web application**
   - Name: "Email Automation Web Client"
   
   **Authorized JavaScript origins:**
   ```
   https://followup-enhance.preview.emergentagent.com
   https://your-production-domain.com
   http://localhost:3000  (for local testing)
   ```
   
   **Authorized redirect URIs:**
   ```
   https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback
   https://your-production-domain.com/api/oauth/google/callback
   http://localhost:3000/api/oauth/google/callback  (for local testing)
   ```

9. **Save Credentials**
   - Copy **Client ID**
   - Copy **Client Secret**
   - Update in `/app/backend/.env`:
     ```
     GOOGLE_CLIENT_ID="your-client-id-here"
     GOOGLE_CLIENT_SECRET="your-client-secret-here"
     GOOGLE_REDIRECT_URI="https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback"
     ```

---

## 🔐 Current Configuration

### Your Backend .env File
```bash
# Google OAuth (Currently configured)
GOOGLE_CLIENT_ID="387382505084-m1tg4q71lulso2m33mr9a7ni8p6qddlt.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET="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"
GOOGLE_REDIRECT_URI="https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback"
```

### Verify These Credentials Have Required Scopes

1. **Go to Google Cloud Console**
2. **Check OAuth Consent Screen** → Scopes
3. **Verify all 7 scopes listed above are added**
4. **Check Redirect URIs** match your backend configuration

---

## 📝 Scope Combinations by Feature

### Minimal Setup (Email Only)
```
✅ gmail.readonly
✅ gmail.send
✅ userinfo.email
```
**Features**: Basic email reading and sending

### Standard Setup (Email + Basic Calendar)
```
✅ gmail.readonly
✅ gmail.send
✅ gmail.modify
✅ calendar.events
✅ userinfo.email
✅ userinfo.profile
```
**Features**: Full email automation + meeting creation

### Full Setup (All Features) - RECOMMENDED
```
✅ gmail.readonly
✅ gmail.send
✅ gmail.modify
✅ calendar (includes calendar.events)
✅ userinfo.email
✅ userinfo.profile
```
**Features**: Everything including conflict detection, rescheduling

---

## 🚀 Testing OAuth Flow

### Test the OAuth Connection

1. **Start Application**
   ```bash
   # Backend should be running
   sudo supervisorctl status backend
   ```

2. **Go to Application UI**
   ```
   https://followup-enhance.preview.emergentagent.com
   ```

3. **Login**
   - Email: amits.joys@gmail.com
   - Password: ij@123

4. **Connect Gmail Account**
   - Click "Email Accounts" in sidebar
   - Click "Connect Google Account"
   - You should see OAuth consent screen

5. **Review Permissions**
   You'll be asked to grant:
   ```
   ✅ Read your emails
   ✅ Send emails on your behalf
   ✅ Manage your email labels and settings
   ✅ See, edit, share, and permanently delete your calendars
   ✅ View your email address
   ✅ View your basic profile info
   ```

6. **Grant Access**
   - Click "Allow"
   - Should redirect back to application
   - Account should show as "Connected"

---

## 🔍 Troubleshooting OAuth Issues

### Issue 1: "Access blocked: This app's request is invalid"

**Cause**: Redirect URI mismatch

**Solution**:
1. Check redirect URI in Google Cloud Console exactly matches backend .env
2. URL must be HTTPS (except localhost)
3. No trailing slashes
4. Port must match (if using custom port)

### Issue 2: "This app isn't verified"

**Cause**: App is in testing mode

**Solutions**:
- Click "Advanced" → "Go to [App Name] (unsafe)" for testing
- Or submit app for verification (production)
- Or set app to "Internal" (organization only)

### Issue 3: "Required scopes not granted"

**Cause**: Missing scopes in OAuth consent screen

**Solution**:
1. Go to OAuth consent screen
2. Edit app → Scopes
3. Add all required scopes
4. Save changes
5. Re-authenticate user

### Issue 4: "Token expired" or "Invalid credentials"

**Cause**: Access token expired, refresh token not working

**Solution**:
- Application automatically refreshes tokens (check backend logs)
- If refresh fails, user needs to re-authenticate
- Check refresh token is stored in database

### Issue 5: "redirect_uri_mismatch"

**Error Message**: 
```
Error 400: redirect_uri_mismatch
The redirect URI in the request does not match the ones authorized for the OAuth client.
```

**Solution**:
1. Backend .env `GOOGLE_REDIRECT_URI` must EXACTLY match one in Google Cloud Console
2. Common issues:
   - HTTP vs HTTPS mismatch
   - Trailing slash difference
   - Port number missing/wrong
   - Domain spelling

**Check both:**
```bash
# Backend config
cat /app/backend/.env | grep GOOGLE_REDIRECT_URI

# Should match one of these in Google Cloud Console:
# https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback
```

---

## 📊 OAuth Flow in Application

### 1. User Clicks "Connect Google Account"
```
Frontend → Backend: GET /api/oauth/google/authorize
Backend generates OAuth URL with:
- client_id
- redirect_uri
- scopes (all 7 required scopes)
- access_type=offline (for refresh token)
```

### 2. User Redirects to Google
```
Google shows consent screen:
"Email Automation Assistant wants to access your Google Account"

Permissions:
✅ Read, compose, send, and permanently delete emails from Gmail
✅ See, edit, share, and permanently delete all calendars
✅ See your personal info
```

### 3. User Grants Permission
```
Google redirects back to:
https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback?code=...
```

### 4. Backend Exchanges Code for Tokens
```
Backend → Google: POST /token
Parameters:
- code (from redirect)
- client_id
- client_secret
- redirect_uri
- grant_type=authorization_code

Response:
{
  "access_token": "ya29.a0...",
  "refresh_token": "1//0e...",
  "expires_in": 3600,
  "scope": "gmail.readonly gmail.send ...",
  "token_type": "Bearer"
}
```

### 5. Backend Stores Tokens
```
Database: email_accounts collection
{
  user_id: "...",
  email: "amits.joys@gmail.com",
  account_type: "oauth_gmail",
  access_token: "encrypted",
  refresh_token: "encrypted",
  token_expires_at: "2025-03-12T08:00:00Z",
  is_active: true
}
```

### 6. Application Uses Tokens
```
Every API call to Gmail/Calendar:
Headers: {
  Authorization: "Bearer ya29.a0..."
}

If token expired:
- Backend automatically uses refresh_token
- Gets new access_token
- Updates database
- Retries request
```

---

## 🔒 Security Best Practices

### 1. Store Tokens Securely
```bash
# Backend encrypts tokens before storing
ENCRYPTION_KEY="your-32-byte-encryption-key"  # In .env
```

### 2. Use HTTPS Only
```
# Production redirect URIs must use HTTPS
❌ http://example.com/callback
✅ https://example.com/callback
```

### 3. Validate Redirect URIs
```
# Only allow pre-configured redirect URIs
# Never use user-provided redirect URIs
```

### 4. Request Minimum Scopes
```
# Only request scopes you actually use
# More scopes = more security review required
```

### 5. Handle Token Refresh
```
# Always implement automatic token refresh
# Don't ask user to re-authenticate unnecessarily
```

### 6. Revoke Tokens on Disconnect
```
# When user disconnects account:
# 1. Revoke OAuth token with Google
# 2. Delete from database
# 3. Clear any cached data
```

---

## 📞 Support & Resources

### Google Documentation
- OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Gmail API: https://developers.google.com/gmail/api
- Calendar API: https://developers.google.com/calendar/api

### OAuth 2.0 Playground
Test scopes and API calls:
```
https://developers.google.com/oauthplayground
```

### Google Cloud Console
```
https://console.cloud.google.com
```

---

## ✅ Verification Checklist

Before going live, verify:

- [ ] All 7 scopes added to OAuth consent screen
- [ ] Redirect URIs exactly match backend configuration
- [ ] Gmail API enabled in Google Cloud Console
- [ ] Calendar API enabled in Google Cloud Console
- [ ] OAuth credentials (Client ID & Secret) in backend .env
- [ ] Test users added (if app not published)
- [ ] OAuth flow tested end-to-end
- [ ] Token refresh working automatically
- [ ] Email reading works
- [ ] Email sending works
- [ ] Calendar event creation works
- [ ] Error handling for expired tokens
- [ ] Account disconnection works

---

## 🎯 Quick Reference

**Minimum Required Scopes:**
```
gmail.readonly
gmail.send
calendar.events
userinfo.email
```

**Recommended Scopes:**
```
gmail.readonly
gmail.send
gmail.modify
calendar (full access)
userinfo.email
userinfo.profile
```

**Critical Config:**
```bash
GOOGLE_CLIENT_ID="your-client-id"
GOOGLE_CLIENT_SECRET="your-client-secret"
GOOGLE_REDIRECT_URI="https://your-domain.com/api/oauth/google/callback"
```

**Redirect URI Format:**
```
https://{your-domain}/api/oauth/google/callback
```

---

**Last Updated**: March 12, 2025  
**App Status**: OAuth credentials already configured in system
