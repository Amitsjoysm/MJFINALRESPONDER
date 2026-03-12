# Production Deployment Guide - aaPanel

## 🚀 System Overview

This is an AI-powered email automation system with enhanced validation to prevent incomplete auto-replies.

### Key Features
- **Smart Email Classification**: Automatically classifies incoming emails by intent
- **AI-Powered Draft Generation**: Creates contextual replies using GROQ LLM
- **Multi-Layer Validation**: 5-layer validation system to prevent greeting-only responses
- **Meeting Detection**: Automatically detects and creates calendar events
- **Lead Qualification**: Autonomous lead nurturing and qualification
- **Follow-up Automation**: Scheduled follow-ups based on time references

---

## 📋 Recent Changes (Latest Update)

### ✅ Fixed: Validation Agent Greeting-Only Bug
**Problem**: Random emails were being auto-sent with just "Hi [Name]," responses.

**Solution**: Enhanced validation with stricter checks:
1. **Layer 1**: Basic length validation (minimum 50 characters)
2. **Layer 2 (ENHANCED)**: 
   - Detects greeting-only patterns with regex
   - Checks content after greeting (minimum 50 chars, 15 words)
   - Normalizes whitespace to prevent bypass attempts
3. **Layer 3**: Word count validation (minimum 20 words total)
4. **Layer 4**: Sentence count validation (minimum 2 sentences)
5. **Layer 5**: AI-powered semantic validation

**Draft Generation Pre-Check**: Now rejects greeting-only drafts before validation
- Checks normalized content (removes extra whitespace)
- Validates content after greeting line
- Raises ValueError to trigger retry (max 2 retries)

### ✅ Codebase Cleanup
**Moved to `/old/` directory:**
- `/old/root_test_files/` - All root-level test files
  - `backend_test.py`, `edge_case_test.py`, `focused_test.py`, `focused_edge_test.py`, `validation_edge_test.py`, `test_validation.py`
  - JSON test results
  
- `/old/root_docs/` - Documentation files
  - All `.md` files from root (except README.md)

### ✅ Updated Configuration
- **GROQ API Key**: Updated to user-provided key
- **Primary Provider**: GROQ (llama-3.3-70b-versatile)
- **Fallback Provider**: Claude (if configured)

---

## 🔧 aaPanel Deployment Steps

### 1. Prerequisites
- **aaPanel** installed on server
- **Python 3.10+** installed
- **Node.js 18+** and npm/yarn
- **MongoDB** (local or Atlas)
- **Redis** (optional, for caching)

### 2. Initial Setup

#### A. Create Website in aaPanel
```bash
# In aaPanel Dashboard:
1. Go to "Website" → "Add site"
2. Domain: your-domain.com
3. Root directory: /www/wwwroot/your-domain.com
4. PHP: Not needed (Python app)
```

#### B. Upload Code
```bash
# Via aaPanel File Manager or FTP/SFTP
1. Upload entire /app directory to: /www/wwwroot/your-domain.com/
2. Or use Git:
cd /www/wwwroot/your-domain.com/
git clone <your-repo-url> .
```

#### C. Install Dependencies

**Backend:**
```bash
cd /www/wwwroot/your-domain.com/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Frontend:**
```bash
cd /www/wwwroot/your-domain.com/frontend
npm install
# or
yarn install
```

### 3. Configuration

#### A. Environment Variables
Update `/backend/.env`:
```bash
# MongoDB (use MongoDB Atlas or local)
MONGO_URL="mongodb://localhost:27017"
DB_NAME="email_assistant_db"

# CORS (set your domain)
CORS_ORIGINS="https://your-domain.com,http://your-domain.com"

# JWT Secret (generate strong secret)
JWT_SECRET="your-strong-secret-key-here"

# Google OAuth (update redirect URIs)
GOOGLE_REDIRECT_URI="https://your-domain.com/api/oauth/google/callback"

# Microsoft OAuth (update redirect URIs)
MICROSOFT_REDIRECT_URI="https://your-domain.com/api/oauth/microsoft/callback"

# AI API Keys
GROQ_API_KEY="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"
CLAUDE_API_KEY=""  # Optional fallback

# Encryption key for passwords
ENCRYPTION_KEY="generate-a-32-byte-key-here"
```

Update `/frontend/.env`:
```bash
REACT_APP_BACKEND_URL="https://your-domain.com"
```

#### B. OAuth Callback URLs
Update in respective OAuth consoles:
- **Google Cloud Console**: Add `https://your-domain.com/api/oauth/google/callback`
- **Microsoft Azure**: Add `https://your-domain.com/api/oauth/microsoft/callback`

### 4. Build Frontend
```bash
cd /www/wwwroot/your-domain.com/frontend
npm run build
# or
yarn build
```

### 5. Setup Services with Supervisor

#### A. Install Supervisor (if not installed)
```bash
# In aaPanel Terminal
yum install supervisor -y  # CentOS/RHEL
# or
apt-get install supervisor -y  # Ubuntu/Debian
```

#### B. Create Supervisor Configs

Create `/etc/supervisor/conf.d/email-backend.conf`:
```ini
[program:email-backend]
command=/www/wwwroot/your-domain.com/backend/venv/bin/python /www/wwwroot/your-domain.com/backend/server.py
directory=/www/wwwroot/your-domain.com/backend
user=www
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/email-backend.err.log
stdout_logfile=/var/log/supervisor/email-backend.out.log
```

Create `/etc/supervisor/conf.d/email-worker.conf`:
```ini
[program:email-worker]
command=/www/wwwroot/your-domain.com/backend/venv/bin/python /www/wwwroot/your-domain.com/backend/workers/email_worker.py
directory=/www/wwwroot/your-domain.com/backend
user=www
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/email-worker.err.log
stdout_logfile=/var/log/supervisor/email-worker.out.log
```

#### C. Reload Supervisor
```bash
supervisorctl reread
supervisorctl update
supervisorctl start email-backend
supervisorctl start email-worker
```

### 6. Nginx Configuration

#### A. In aaPanel
```
1. Go to "Website" → Select your site → "Configuration"
2. Update Nginx config:
```

```nginx
server {
    listen 80;
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration (aaPanel handles this)
    
    # Frontend - Serve React build
    location / {
        root /www/wwwroot/your-domain.com/frontend/build;
        try_files $uri $uri/ /index.html;
        index index.html;
    }
    
    # Backend API - Proxy to FastAPI
    location /api {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # WebSocket support (if needed)
    location /ws {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 7. SSL Certificate
```
1. In aaPanel Dashboard
2. Go to "Website" → Select your site → "SSL"
3. Choose "Let's Encrypt" and apply
```

### 8. MongoDB Setup

**Option A: Local MongoDB**
```bash
# Install MongoDB via aaPanel
1. Go to "App Store" → Search "MongoDB"
2. Install MongoDB
3. Set authentication if needed
```

**Option B: MongoDB Atlas (Recommended for Production)**
```bash
1. Create account at mongodb.com/cloud/atlas
2. Create cluster
3. Get connection string
4. Update MONGO_URL in .env
```

### 9. Start Application
```bash
# Check supervisor status
supervisorctl status

# Should show:
# email-backend    RUNNING   pid xxxxx
# email-worker     RUNNING   pid xxxxx

# View logs
tail -f /var/log/supervisor/email-backend.out.log
tail -f /var/log/supervisor/email-worker.out.log
```

### 10. Verify Deployment
```bash
# Check backend
curl https://your-domain.com/api/health

# Should return: {"status": "ok"}

# Check frontend
# Open browser: https://your-domain.com
```

---

## 🔍 Monitoring & Logs

### View Logs
```bash
# Backend API logs
tail -f /var/log/supervisor/email-backend.out.log
tail -f /var/log/supervisor/email-backend.err.log

# Email Worker logs
tail -f /var/log/supervisor/email-worker.out.log
tail -f /var/log/supervisor/email-worker.err.log

# Nginx logs (aaPanel)
tail -f /www/wwwlogs/your-domain.com.log
tail -f /www/wwwlogs/your-domain.com.error.log
```

### Service Management
```bash
# Restart services
supervisorctl restart email-backend
supervisorctl restart email-worker

# Stop services
supervisorctl stop email-backend
supervisorctl stop email-worker

# Start services
supervisorctl start email-backend
supervisorctl start email-worker

# View status
supervisorctl status
```

---

## 🧪 Testing After Deployment

### 1. Test Backend API
```bash
curl https://your-domain.com/api/health
```

### 2. Test Email Processing
- Connect an email account via UI
- Send a test email
- Check logs for processing
- Verify draft generation (should NOT be greeting-only)

### 3. Test Validation
Send emails and check that responses:
- ✅ Have substantial content (>50 chars after greeting)
- ✅ Have at least 20 words
- ✅ Have at least 2 sentences
- ✅ Pass AI validation (score >= 70)
- ❌ NOT just "Hi Name,"

---

## 🐛 Troubleshooting

### Issue: Services not starting
```bash
# Check logs
tail -n 50 /var/log/supervisor/email-backend.err.log

# Common issues:
# 1. Python dependencies missing
cd /www/wwwroot/your-domain.com/backend
source venv/bin/activate
pip install -r requirements.txt

# 2. MongoDB not accessible
# Check MONGO_URL in .env
# Test connection: mongosh "your-mongo-url"

# 3. Port 8001 already in use
# Find process: lsof -i :8001
# Kill process: kill -9 <PID>
```

### Issue: Frontend not loading
```bash
# 1. Check if build exists
ls -la /www/wwwroot/your-domain.com/frontend/build/

# 2. Rebuild if needed
cd /www/wwwroot/your-domain.com/frontend
npm run build

# 3. Check Nginx config
nginx -t
```

### Issue: CORS errors
```bash
# Update CORS_ORIGINS in backend/.env
CORS_ORIGINS="https://your-domain.com,http://your-domain.com"

# Restart backend
supervisorctl restart email-backend
```

### Issue: Validation still failing
```bash
# Check GROQ API key
# Verify in backend/.env
# Test API key:
curl -H "Authorization: Bearer gsk_..." https://api.groq.com/openai/v1/models

# Check validation logs
grep "VALIDATION" /var/log/supervisor/email-worker.out.log
```

---

## 📊 Performance Optimization

### 1. Enable Nginx Caching
```nginx
# Add to server block
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m inactive=60m;

location /api {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    # ... rest of proxy config
}
```

### 2. PM2 Alternative (Optional)
```bash
# Instead of supervisor, use PM2
npm install -g pm2
pm2 start backend/server.py --name email-backend --interpreter python3
pm2 start backend/workers/email_worker.py --name email-worker --interpreter python3
pm2 save
pm2 startup
```

---

## 🔐 Security Checklist

- [ ] Change JWT_SECRET to strong random string
- [ ] Change ENCRYPTION_KEY to 32-byte random string
- [ ] Enable MongoDB authentication
- [ ] Enable Redis authentication (if using)
- [ ] Set proper CORS_ORIGINS (not "*")
- [ ] Enable SSL certificate
- [ ] Set proper file permissions (755 for dirs, 644 for files)
- [ ] Enable aaPanel firewall
- [ ] Disable debug mode in production
- [ ] Set up regular backups for MongoDB

---

## 📞 Support & Maintenance

### Regular Maintenance
```bash
# Update dependencies monthly
cd /www/wwwroot/your-domain.com/backend
source venv/bin/activate
pip install --upgrade -r requirements.txt

cd /www/wwwroot/your-domain.com/frontend
npm update

# Restart services after updates
supervisorctl restart all
```

### Backup Strategy
```bash
# MongoDB backup (daily cron)
mongodump --uri="your-mongo-url" --out=/backups/mongodb/$(date +%Y%m%d)

# Code backup
tar -czf /backups/code/app-$(date +%Y%m%d).tar.gz /www/wwwroot/your-domain.com/
```

---

## ✅ Production Checklist

- [ ] Domain configured in aaPanel
- [ ] Code uploaded and dependencies installed
- [ ] Environment variables configured (.env files)
- [ ] MongoDB accessible (local or Atlas)
- [ ] Supervisor services running
- [ ] Nginx configured and SSL enabled
- [ ] OAuth redirect URIs updated
- [ ] Frontend built and accessible
- [ ] Backend API responding to /api/health
- [ ] Email worker processing emails
- [ ] Validation working (no greeting-only responses)
- [ ] Logs rotating properly
- [ ] Backups scheduled
- [ ] Monitoring in place

---

**Deployment Date**: March 12, 2025  
**System Version**: v2.0 (Enhanced Validation)  
**Deployed By**: Production Team
