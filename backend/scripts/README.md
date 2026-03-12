# Backend Scripts Directory

This directory contains utility and administrative scripts for the Email Assistant application.

## Available Scripts

### 1. Admin User Management

#### `create_admin_user.py`
Creates an admin user with predefined credentials.

**Usage:**
```bash
cd /app/backend
python scripts/create_admin_user.py
```

**Credentials:**
- Email: `admin@emailassistant.com`
- Password: `Admin@123`
- Role: `admin`
- Quota: 1000 emails/day

**Features:**
- Creates admin user if doesn't exist
- Sets up HubSpot access flags
- Higher quota than regular users

---

#### `create_super_admin.py`
Creates a super admin user with elevated privileges.

**Usage:**
```bash
cd /app/backend
python scripts/create_super_admin.py
```

**Credentials:**
- Email: `admin@crm.com`
- Password: `Admin@123`
- Role: `super_admin`
- Quota: 10,000 emails/day

**Features:**
- Highest level of access
- Used for system administration
- Cannot be created through UI

---

### 2. Email Processing Utilities

#### `process_received_emails.py`
Manually processes emails stuck in 'received' status.

**Usage:**
```bash
cd /app/backend
python scripts/process_received_emails.py
```

**What it does:**
- Finds emails in 'received' status for `amits.joys@gmail.com`
- Processes each email through the worker pipeline
- Shows processing statistics
- Displays intent detection results
- Lists created inbound leads

**Use cases:**
- Emails stuck after worker restart
- Manual reprocessing after configuration changes
- Debugging email processing issues

---

#### `reprocess_emails.py`
Resets failed emails or emails without intent for reprocessing.

**Usage:**
```bash
cd /app/backend
python scripts/reprocess_emails.py
```

**What it does:**
- Finds emails with status `error` or no intent
- Resets them to `received` status
- Clears error messages
- Adds reprocessing log to action history
- Worker will pick them up in next poll (~60 seconds)

**Use cases:**
- After adding new intents
- After fixing intent keywords
- Recovering from processing errors

---

### 3. Worker Management

#### `run_workers.py`
Orchestrates all background workers in a single process.

**Usage:**
```bash
cd /app/backend
python scripts/run_workers.py
```

**Workers Started:**
1. **Email Polling** - Every 60 seconds
2. **Follow-up Checking** - Every 5 minutes
3. **Reminder Checking** - Every 1 hour
4. **Campaign Processor** - Every 30 seconds
5. **Campaign Follow-ups** - Every 5 minutes
6. **Campaign Reply Checker** - Every 2 minutes

**Note:** 
- This script is for development/testing only
- Production uses individual worker scripts via supervisor:
  - `run_email_worker.py`
  - `run_campaign_worker.py`

---

## General Usage Patterns

### Running Scripts from Root
```bash
cd /app
python backend/scripts/create_admin_user.py
```

### Running Scripts from Backend
```bash
cd /app/backend
python scripts/create_admin_user.py
```

---

## Important Notes

### Database Connection
All scripts use the following environment variables:
- `MONGO_URL` - MongoDB connection string
- `DB_NAME` - Database name (default: `email_assistant_db`)

These are automatically loaded from `/app/backend/.env`

### User Targeting
Some scripts target specific users:
- `process_received_emails.py` - Hard-coded to `amits.joys@gmail.com`
- `reprocess_emails.py` - Hard-coded to `amits.joys@gmail.com`

**To use for other users:**
Edit the script and change the email address in the query.

### Worker Management
**Development:**
```bash
python backend/scripts/run_workers.py
```

**Production (via supervisor):**
```bash
sudo supervisorctl start email_worker
sudo supervisorctl start campaign_worker
```

Or use the helper script:
```bash
cd /app && bash start_workers.sh
```

---

## Removed Scripts

The following scripts were removed as they were outdated, duplicates, or one-time migrations:

- `add_conversation_linking_to_worker.py` - Migration script
- `amitscomprehensive_seed_data.py` - User-specific seed
- `create_comprehensive_seed.py` - Duplicate seed
- `create_full_seed_data.py` - Duplicate seed
- `create_inbound_leads_seed.py` - Specific seed
- `create_production_seed_data.py` - Duplicate seed
- `create_seed_data.py` - Duplicate seed
- `create_seed_data_for_user.py` - Duplicate seed
- `create_seed_for_amits.py` - User-specific seed
- `create_test_user_seed.py` - Duplicate seed
- `create_topleaders_list.py` - Feature-specific seed
- `fix_lead_intent_keywords.py` - One-time fix
- `seed_campaign_data.py` - Specific seed
- `setup_complete_system.py` - Duplicate setup
- `test_conversation_linking.py` - Test script

**Note:** For seed data creation, use the main application's UI or create custom scripts as needed.

---

## Creating New Scripts

When creating new utility scripts:

1. Add Python shebang and docstring
2. Add backend to path:
   ```python
   import sys
   import os
   sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
   ```
3. Use async/await with motor for MongoDB
4. Import from `config` for environment variables
5. Add proper error handling and logging
6. Document in this README

---

## Troubleshooting

### Script Can't Import Modules
Ensure you're running from the correct directory or the script adds backend to path.

### Database Connection Failed
Check `.env` file has correct `MONGO_URL` and MongoDB is running:
```bash
sudo supervisorctl status mongodb
```

### Script Hangs
Some scripts use async/await and need proper event loop:
```python
asyncio.run(main_function())
```

---

## Security Notes

⚠️ **IMPORTANT:**
- Admin scripts create users with **default passwords**
- Change passwords immediately after first login
- Don't commit credentials to version control
- Use environment variables for sensitive data

---

## Last Updated
January 12, 2026 - Cleaned up duplicate and outdated scripts
