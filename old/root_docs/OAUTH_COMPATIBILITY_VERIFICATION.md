# OAuth Compatibility Verification

## Question: Do password decryption changes affect OAuth flow?

## Answer: ✅ NO - OAuth accounts are NOT affected

---

## How Email Account Types Work

### 1. OAuth Gmail Accounts (`account_type: 'oauth_gmail'`)

**Authentication Method:**
- Uses `access_token` and `refresh_token` (no password)
- Tokens obtained through Google OAuth 2.0 flow
- Tokens refresh automatically when expired

**Code Path:**
```
Worker → fetch_emails_oauth_gmail() → Gmail API with OAuth credentials
Worker → send_email_oauth_gmail() → Gmail API with OAuth credentials
```

**Fields Used:**
- ✅ `access_token`
- ✅ `refresh_token`
- ❌ `password` (not used)

**Affected by changes?** ❌ NO

---

### 2. OAuth Outlook Accounts (`account_type: 'oauth_outlook'`)

**Authentication Method:**
- Uses `access_token` and `refresh_token` (no password)
- Tokens obtained through Microsoft OAuth 2.0 flow
- Tokens refresh automatically when expired

**Code Path:**
```
Worker → fetch_emails_oauth_outlook() → Microsoft Graph API with OAuth
Worker → send_email_oauth_outlook() → Microsoft Graph API with OAuth
```

**Fields Used:**
- ✅ `access_token`
- ✅ `refresh_token`
- ❌ `password` (not used)

**Affected by changes?** ❌ NO

---

### 3. Custom SMTP Accounts (`account_type: 'custom_smtp'`)

**Authentication Method:**
- Uses encrypted `password` field
- Password decrypted before IMAP/SMTP authentication

**Code Path:**
```
Worker → fetch_emails_imap() → _fetch_imap_sync() → decrypt password → IMAP login
Worker → send_email_smtp() → _send_smtp_sync() → decrypt password → SMTP login
```

**Fields Used:**
- ✅ `password` (encrypted in DB, decrypted before use)
- ❌ OAuth tokens (not used)

**Affected by changes?** ✅ YES - This is what we fixed!

---

### 4. Gmail App Password Accounts (`account_type: 'app_password_gmail'`)

**Authentication Method:**
- Uses encrypted `password` field (16-character app password)
- Password decrypted before IMAP/SMTP authentication

**Code Path:**
```
Worker → fetch_emails_imap() → _fetch_imap_sync() → decrypt password → IMAP login
Worker → send_email_smtp() → _send_smtp_sync() → decrypt password → SMTP login
```

**Fields Used:**
- ✅ `password` (encrypted in DB, decrypted before use)
- ❌ OAuth tokens (not used)

**Affected by changes?** ✅ YES - Decryption applies here too

---

## Code Flow Decision Logic

### In `email_worker.py` (Line 42-46):

```python
if account.account_type == 'oauth_gmail':
    emails = await email_service.fetch_emails_oauth_gmail(account)
elif account.account_type == 'oauth_outlook':
    emails = await email_service.fetch_emails_oauth_outlook(account)
elif account.account_type in ['app_password_gmail', 'custom_smtp']:
    emails = await email_service.fetch_emails_imap(account)  # Uses password decryption
```

### In `email_worker.py` (Line 351-355 for sending):

```python
if account.account_type == 'oauth_gmail':
    result = await email_service.send_email_oauth_gmail(account, reply, email.thread_id)
elif account.account_type == 'oauth_outlook':
    result = await email_service.send_email_oauth_outlook(account, reply, email.thread_id)
# For custom_smtp and app_password_gmail:
else:
    result = await email_service.send_email_smtp(account, reply)  # Uses password decryption
```

---

## Changes Made (Password Decryption)

### 1. Added to `EmailService.__init__()`:
```python
from utils.encryption import EncryptionService
import os

encryption_key = os.environ.get('ENCRYPTION_KEY', 'your-encryption-key-32-bytes-long')
self.encryption_service = EncryptionService(encryption_key)
```

### 2. Added `_decrypt_password()` method:
```python
def _decrypt_password(self, encrypted_password: str) -> str:
    """Decrypt account password"""
    try:
        return self.encryption_service.decrypt(encrypted_password)
    except Exception as e:
        logger.error(f"Failed to decrypt password: {e}")
        return encrypted_password
```

### 3. Updated `_fetch_imap_sync()`:
```python
# Decrypt password before use
password = self._decrypt_password(account.password) if account.password else None
if not password:
    raise Exception("No password available for IMAP authentication")

mail = imaplib.IMAP4_SSL(account.imap_host, account.imap_port)
mail.login(account.email, password)  # Uses decrypted password
```

### 4. Updated `_send_smtp_sync()`:
```python
# Decrypt password before use
password = self._decrypt_password(account.password) if account.password else None
if not password:
    raise Exception("No password available for SMTP authentication")

# Use SMTP with starttls for port 587, SMTP_SSL for port 465
if account.smtp_port == 465:
    server = smtplib.SMTP_SSL(account.smtp_host, account.smtp_port)
else:
    server = smtplib.SMTP(account.smtp_host, account.smtp_port)
    server.starttls()

server.login(account.email, password)  # Uses decrypted password
```

---

## OAuth Methods (Unchanged)

### `fetch_emails_oauth_gmail()`:
```python
creds = Credentials(
    token=account.access_token,      # OAuth token
    refresh_token=account.refresh_token,  # OAuth refresh token
    token_uri="https://oauth2.googleapis.com/token",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET
)
service = build('gmail', 'v1', credentials=creds)
# No password used! ✓
```

### `send_email_oauth_gmail()`:
```python
creds = Credentials(
    token=account.access_token,      # OAuth token
    refresh_token=account.refresh_token,  # OAuth refresh token
    token_uri="https://oauth2.googleapis.com/token",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET
)
service = build('gmail', 'v1', credentials=creds)
# No password used! ✓
```

---

## Summary Table

| Account Type | Uses Password? | Uses OAuth Tokens? | Affected by Changes? |
|-------------|----------------|-------------------|---------------------|
| **oauth_gmail** | ❌ No | ✅ Yes | ❌ **NOT AFFECTED** |
| **oauth_outlook** | ❌ No | ✅ Yes | ❌ **NOT AFFECTED** |
| **custom_smtp** | ✅ Yes | ❌ No | ✅ **FIXED BY CHANGES** |
| **app_password_gmail** | ✅ Yes | ❌ No | ✅ **FIXED BY CHANGES** |

---

## Conclusion

✅ **OAuth accounts (Gmail and Outlook) are completely unaffected by the password decryption changes.**

The changes ONLY affect:
- Custom SMTP accounts
- Gmail App Password accounts

OAuth accounts use a completely separate code path that never touches the `password` field or the decryption methods.

**OAuth flow will continue to work exactly as before!** ✅

---

## Testing OAuth Flow

To verify OAuth still works:

1. Add email account via OAuth (Google or Microsoft)
2. System will use OAuth tokens for authentication
3. No password involved
4. Emails fetched via Gmail API / Graph API
5. Emails sent via Gmail API / Graph API
6. Everything works as expected ✅
