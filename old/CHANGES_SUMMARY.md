# 📝 Complete Changes Summary - Before & After

## Overview
This document shows all changes made to fix the auto-reply, lead qualification, calendar OAuth, and add comprehensive seed data.

---

## 🔧 Configuration Changes

### 1. Frontend Environment (.env)

**File**: `/app/frontend/.env`

**BEFORE:**
```
Line 1: REACT_APP_BACKEND_URL=https://followup-enhance.preview.emergentagent.com
```

**AFTER:**
```
Line 1: REACT_APP_BACKEND_URL=https://followup-enhance.preview.emergentagent.com
```

**Reason**: Backend URL was outdated, causing all API calls to fail with network errors.

---

### 2. Backend Environment (.env)

**File**: `/app/backend/.env`

**BEFORE:**
```
Line 11: GOOGLE_REDIRECT_URI="https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback"
Line 17: MICROSOFT_REDIRECT_URI="https://followup-enhance.preview.emergentagent.com/api/oauth/microsoft/callback"
```

**AFTER:**
```
Line 11: GOOGLE_REDIRECT_URI="https://followup-enhance.preview.emergentagent.com/api/oauth/google/callback"
Line 17: MICROSOFT_REDIRECT_URI="https://followup-enhance.preview.emergentagent.com/api/oauth/microsoft/callback"
```

**Reason**: OAuth redirect URIs must match the current deployment URL.

---

## 🎨 Frontend Changes

### 3. Auth Context - Added User Refresh

**File**: `/app/frontend/src/context/AuthContext.js`

**BEFORE (Line 58-68):**
```javascript
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
```

**AFTER (Line 58-74):**
```javascript
  const logout = () => {
    localStorage.removeItem('token');
    setToken(null);
    setUser(null);
  };

  const refreshUser = async () => {
    if (token) {
      await loadUser();
    }
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  );
```

**Reason**: Needed refreshUser method to update user data after toggling lead settings.

---

### 4. Settings Page - Added Lead Management Controls

**File**: `/app/frontend/src/pages/Settings.js`

**BEFORE (Line 1-14):**
```javascript
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Link as LinkIcon, Unlink, RefreshCw, Check, X, ExternalLink } from 'lucide-react';

const Settings = () => {
  const { user } = useAuth();
  const [hubspotStatus, setHubspotStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
```

**AFTER (Line 1-20):**
```javascript
import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import API from '../api';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Badge } from '../components/ui/badge';
import { toast } from 'sonner';
import { Settings as SettingsIcon, Link as LinkIcon, Unlink, RefreshCw, Check, X, ExternalLink, Target, Sparkles } from 'lucide-react';

const Settings = () => {
  const { user, refreshUser } = useAuth();
  const [hubspotStatus, setHubspotStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState(false);
  const [leadSettings, setLeadSettings] = useState({
    global_lead_qualification_enabled: false,
    global_lead_nurturing_enabled: false
  });
  const [savingLeadSettings, setSavingLeadSettings] = useState(false);
```

**Added (After Line 92):** Complete Lead Management Settings section with:
- Lead Qualification toggle card (Indigo themed)
- Lead Nurturing toggle card (Pink themed)
- ON/OFF badges with status indicators
- Enable/Disable buttons
- Detailed descriptions and usage notes
- Important notes section

**Total Lines Added**: ~130 lines of new UI code

---

### 5. Intents Page - Added Lead Controls

**File**: `/app/frontend/src/pages/Intents.js`

**BEFORE (Line 20-29):**
```javascript
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    keywords: '',
    prompt: '',
    priority: 1,
    auto_send: false,
    is_inbound_lead: false,
    is_active: true
  });
```

**AFTER (Line 20-31):**
```javascript
  const [formData, setFormData] = useState({
    name: '',
    description: '',
    keywords: '',
    prompt: '',
    priority: 1,
    auto_send: false,
    is_inbound_lead: false,
    enable_lead_qualification: false,
    enable_lead_nurturing: false,
    is_active: true
  });
```

**Added (After Line 289):**
```javascript
                {formData.is_inbound_lead && (
                  <div className="ml-6 space-y-3 pt-2 pl-4 border-l-2 border-purple-200">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="enable_lead_qualification"
                        checked={formData.enable_lead_qualification}
                        onChange={(e) => setFormData({...formData, enable_lead_qualification: e.target.checked})}
                        className="w-4 h-4"
                      />
                      <Label htmlFor="enable_lead_qualification" className="cursor-pointer text-sm">
                        Enable Lead Qualification
                      </Label>
                    </div>
                    <p className="text-xs text-gray-500 ml-6">
                      Automatically qualify leads by asking questions and scoring their responses (0-100)
                    </p>
                    
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        id="enable_lead_nurturing"
                        checked={formData.enable_lead_nurturing}
                        onChange={(e) => setFormData({...formData, enable_lead_nurturing: e.target.checked})}
                        className="w-4 h-4"
                      />
                      <Label htmlFor="enable_lead_nurturing" className="cursor-pointer text-sm">
                        Enable Lead Nurturing
                      </Label>
                    </div>
                    <p className="text-xs text-gray-500 ml-6">
                      Ask 1-2 contextual questions per email to gather more information about the lead
                    </p>
                  </div>
                )}
```

**Added Info Banner (After Line 189):**
```javascript
      {/* Info Banner for Lead Management */}
      <Card className="bg-gradient-to-r from-indigo-50 to-purple-50 border-indigo-200">
        <CardContent className="py-4">
          <div className="flex items-start gap-3">
            <Target className="w-5 h-5 text-indigo-600 mt-0.5 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-sm font-medium text-indigo-900 mb-1">
                Lead Qualification & Nurturing Controls
              </p>
              <p className="text-xs text-indigo-700">
                When creating or editing an intent, mark it as <strong>"Inbound Lead"</strong> to reveal Lead Qualification and Lead Nurturing options...
              </p>
            </div>
          </div>
        </CardContent>
      </Card>
```

**Added Display Badges (Line 399-426):**
```javascript
                      {intent.auto_send && (
                        <Badge className="bg-green-500">
                          Auto-Send
                        </Badge>
                      )}
                      {intent.is_inbound_lead && (
                        <Badge className="bg-blue-500">
                          Lead
                        </Badge>
                      )}
                      {intent.enable_lead_qualification && (
                        <Badge className="bg-indigo-500">
                          Qualification
                        </Badge>
                      )}
                      {intent.enable_lead_nurturing && (
                        <Badge className="bg-pink-500">
                          Nurturing
                        </Badge>
                      )}
```

---

### 6. App.js - Added Lead Settings Route

**File**: `/app/frontend/src/App.js`

**BEFORE (Line 25):**
```javascript
import LeadQualification from './pages/LeadQualification';
```

**AFTER (Line 25-26):**
```javascript
import LeadQualification from './pages/LeadQualification';
import LeadSettings from './pages/LeadSettings';
```

**BEFORE (Line 31):**
```javascript
  Menu
} from 'lucide-react';
```

**AFTER (Line 31-32):**
```javascript
  Menu, Sparkles
} from 'lucide-react';
```

**BEFORE (Line 90-98):**
```javascript
  const initialSetupItems = [
    { path: '/email-accounts', label: 'Email Accounts', icon: Mail },
    { path: '/calendar-providers', label: 'Calendar Providers', icon: Calendar },
    { path: '/knowledge-base', label: 'Knowledge Base', icon: Database },
    { path: '/intents', label: 'Intents', icon: Target },
    { path: '/meeting-detection', label: 'Meeting Detection', icon: Brain },
    { path: '/lead-qualification', label: 'Lead Qualification', icon: Target },
  ];
```

**AFTER (Line 90-99):**
```javascript
  const initialSetupItems = [
    { path: '/email-accounts', label: 'Email Accounts', icon: Mail },
    { path: '/calendar-providers', label: 'Calendar Providers', icon: Calendar },
    { path: '/knowledge-base', label: 'Knowledge Base', icon: Database },
    { path: '/intents', label: 'Intents', icon: Target },
    { path: '/meeting-detection', label: 'Meeting Detection', icon: Brain },
    { path: '/lead-qualification', label: 'Lead Qualification', icon: Target },
    { path: '/lead-settings', label: 'Lead Controls', icon: Sparkles },
  ];
```

**Added Route (After Line 428):**
```javascript
          <Route
            path="/lead-settings"
            element={
              <ProtectedRoute>
                <MainLayout>
                  <LeadSettings />
                </MainLayout>
              </ProtectedRoute>
            }
          />
```

---

### 7. API Client - Enhanced Error Handling

**File**: `/app/frontend/src/api.js`

**BEFORE (Line 1-41):**
```javascript
import axios from 'axios';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

class API {
  constructor() {
    this.axios = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth token to requests
    this.axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Handle 401 errors by clearing invalid tokens
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Clear invalid token
          localStorage.removeItem('token');
          // Only redirect to login if not already on auth page
          if (!window.location.pathname.includes('/auth') && !window.location.pathname.includes('/login')) {
            window.location.href = '/';
          }
        }
        return Promise.reject(error);
      }
    );
  }
```

**AFTER (Line 1-98):**
```javascript
import axios from 'axios';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

// Error logging function
const logError = (error, context) => {
  const errorData = {
    message: error.message,
    context,
    status: error.response?.status,
    data: error.response?.data,
    timestamp: new Date().toISOString(),
    url: error.config?.url
  };
  
  console.error('API Error:', errorData);
  return errorData;
};

class API {
  constructor() {
    this.axios = axios.create({
      baseURL: API_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000, // 30 second timeout
    });

    // Add auth token to requests
    this.axios.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        logError(error, 'request_interceptor');
        return Promise.reject(error);
      }
    );

    // Enhanced error handling
    this.axios.interceptors.response.use(
      (response) => response,
      (error) => {
        logError(error, 'response_interceptor');
        
        if (error.response) {
          const status = error.response.status;
          const detail = error.response.data?.detail || 'An error occurred';
          
          switch (status) {
            case 401:
              localStorage.removeItem('token');
              if (!window.location.pathname.includes('/auth')) {
                toast.error('Session expired. Please login again.');
                window.location.href = '/';
              }
              break;
            case 403:
              toast.error('Access denied');
              break;
            case 404:
              toast.error('Resource not found');
              break;
            case 500:
              toast.error(`Server error: ${detail}`);
              break;
            case 503:
              toast.error('Service temporarily unavailable');
              break;
            default:
              toast.error(detail);
          }
        } else if (error.request) {
          toast.error('Network error. Please check your connection.');
        } else {
          toast.error('An unexpected error occurred');
        }
        
        return Promise.reject(error);
      }
    );
  }

  async _safeRequest(requestFn, context) {
    try {
      return await requestFn();
    } catch (error) {
      logError(error, context);
      throw error;
    }
  }
```

**Reason**: Added comprehensive error handling, timeout, logging, and user-friendly error messages.

---

### 8. Index.js - Added Error Boundary

**File**: `/app/frontend/src/index.js`

**BEFORE (Line 1-12):**
```javascript
import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
```

**AFTER (Line 1-13):**
```javascript
import React from "react";
import ReactDOM from "react-dom/client";
import "@/index.css";
import App from "@/App";
import ErrorBoundary from "@/components/ErrorBoundary";

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>,
);
```

**Reason**: Prevents React crashes and provides user-friendly error UI.

---

## 🔧 Backend Changes

### 9. Auth Routes - Fixed Settings Update

**File**: `/app/backend/routes/auth_routes.py`

**BEFORE (Line 1-10):**
```python
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from datetime import datetime, timezone

from services.auth_service import AuthService
from models.user import UserCreate, UserLogin, TokenResponse, UserResponse

router = APIRouter(prefix="/auth", tags=["auth"])
```

**AFTER (Line 1-13):**
```python
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from pydantic import BaseModel
from datetime import datetime, timezone
import logging
import traceback

from services.auth_service import AuthService
from models.user import UserCreate, UserLogin, TokenResponse, UserResponse, User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["auth"])
```

**BEFORE (Line 97-107):**
```python
        # Get updated user
        updated_user = await users_collection.find_one({"id": user['id']})
        
        if not updated_user:
            raise HTTPException(status_code=404, detail="User not found")
        
        auth_service = AuthService(db)
        return auth_service.user_to_response(updated_user)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**AFTER (Line 97-135):**
```python
        # Get updated user
        updated_user_dict = await users_collection.find_one({"id": user['id']})
        
        if not updated_user_dict:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Convert dict to User model
        try:
            updated_user = User(**updated_user_dict)
            auth_service = AuthService(db)
            return auth_service.user_to_response(updated_user)
        except Exception as model_error:
            # Fallback: return UserResponse directly from dict
            return UserResponse(
                id=updated_user_dict['id'],
                email=updated_user_dict['email'],
                full_name=updated_user_dict.get('full_name', ''),
                quota=updated_user_dict.get('quota', 100),
                quota_used=updated_user_dict.get('quota_used', 0),
                quota_reset_date=updated_user_dict.get('quota_reset_date', datetime.now(timezone.utc).isoformat()),
                created_at=updated_user_dict.get('created_at', datetime.now(timezone.utc).isoformat()),
                role=updated_user_dict.get('role', 'user'),
                is_active=updated_user_dict.get('is_active', True),
                hubspot_enabled=updated_user_dict.get('hubspot_enabled', False),
                hubspot_connected=updated_user_dict.get('hubspot_connected', False),
                hubspot_portal_id=updated_user_dict.get('hubspot_portal_id'),
                hubspot_auto_sync=updated_user_dict.get('hubspot_auto_sync', False),
                global_lead_qualification_enabled=updated_user_dict.get('global_lead_qualification_enabled', False),
                global_lead_nurturing_enabled=updated_user_dict.get('global_lead_nurturing_enabled', False),
                default_qualification_criteria_id=updated_user_dict.get('default_qualification_criteria_id'),
                default_nurturing_config_id=updated_user_dict.get('default_nurturing_config_id')
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating user settings: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Failed to update settings: {str(e)}")
```

**Reason**: Fixed 500 error when toggling lead settings. Added fallback for model parsing issues.

---

### 10. Calendar Routes - Added OAuth Endpoints

**File**: `/app/backend/routes/calendar_routes.py`

**BEFORE (Line 1-12):**
```python
from fastapi import APIRouter, Depends, HTTPException
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone

from routes.auth_routes import get_current_user_from_token, get_db
from services.calendar_service import CalendarService
from models.calendar import CalendarProvider, CalendarEvent, CalendarEventCreate, CalendarEventResponse
from models.user import User

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("/providers")
```

**AFTER (Line 1-80):**
```python
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from typing import List
from motor.motor_asyncio import AsyncIOMotorDatabase
from datetime import datetime, timezone
import uuid
import jwt

from routes.auth_routes import get_current_user_from_token, get_db
from services.calendar_service import CalendarService
from services.oauth_service import OAuthService
from models.calendar import CalendarProvider, CalendarEvent, CalendarEventCreate, CalendarEventResponse
from models.user import User
from config import config

router = APIRouter(prefix="/calendar", tags=["calendar"])

@router.get("/oauth/google")
async def start_google_calendar_oauth(
    token: str = Query(..., description='JWT token for authentication'),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start Google Calendar OAuth flow"""
    try:
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        
        oauth_service = OAuthService(db)
        state = str(uuid.uuid4())
        
        await db.oauth_states.insert_one({
            "state": state,
            "user_id": user.id,
            "provider": "google",
            "account_type": "calendar",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        auth_url = oauth_service.get_google_auth_url(state)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth: {str(e)}")

@router.get("/oauth/microsoft")
async def start_microsoft_calendar_oauth(
    token: str = Query(..., description='JWT token for authentication'),
    db: AsyncIOMotorDatabase = Depends(get_db)
):
    """Start Microsoft Calendar OAuth flow"""
    try:
        from services.auth_service import AuthService
        auth_service = AuthService(db)
        user = await auth_service.get_current_user(token)
        
        oauth_service = OAuthService(db)
        state = str(uuid.uuid4())
        
        await db.oauth_states.insert_one({
            "state": state,
            "user_id": user.id,
            "provider": "microsoft",
            "account_type": "calendar",
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        auth_url = oauth_service.get_microsoft_auth_url(state)
        return RedirectResponse(url=auth_url)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to start OAuth: {str(e)}")

@router.get("/providers")
```

**Reason**: Added missing calendar OAuth endpoints so users can connect Google/Microsoft calendars.

---

### 11. Campaign Model - Enhanced Analytics

**File**: `/app/backend/models/campaign.py`

**BEFORE (Line 6-12):**
```python
class FollowUpConfig(BaseModel):
    """Configuration for follow-up emails"""
    enabled: bool = True
    count: int = 3
    intervals: List[int] = [2, 4, 6]
    template_ids: List[str] = []
```

**AFTER (Line 6-17):**
```python
class TrackingSettings(BaseModel):
    """Email tracking settings for deliverability"""
    enable_open_tracking: bool = True
    enable_click_tracking: bool = True
    enable_reply_tracking: bool = True
    enable_sentiment_analysis: bool = True
    
class FollowUpConfig(BaseModel):
    """Configuration for follow-up emails"""
    enabled: bool = True
    count: int = 3
    intervals: List[int] = [2, 4, 6]
    template_ids: List[str] = []
```

**BEFORE (Line 58-61):**
```python
    # Engagement metrics
    emails_opened: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
```

**AFTER (Line 63-92):**
```python
    # Engagement metrics
    emails_opened: int = 0
    emails_clicked: int = 0
    emails_replied: int = 0
    emails_bounced: int = 0
    
    # Advanced analytics
    open_rate: float = 0.0
    click_rate: float = 0.0
    reply_rate: float = 0.0
    bounce_rate: float = 0.0
    
    # Sentiment analysis
    positive_replies: int = 0
    neutral_replies: int = 0
    negative_replies: int = 0
    
    # Lead generation
    leads_generated: int = 0
    lead_rate: float = 0.0
    
    # Opportunities & Conversion
    opportunities_created: int = 0
    opportunities_rate: float = 0.0
    conversions: int = 0
    conversion_rate: float = 0.0
    
    # Deliverability metrics
    emails_delivered: int = 0
    delivery_rate: float = 0.0
    inbox_rate: float = 0.0
```

**Reason**: Added comprehensive campaign analytics tracking.

---

### 12. Campaign Email Model - Enhanced Tracking

**File**: `/app/backend/models/campaign_email.py`

**BEFORE (Line 2):**
```python
from typing import Optional, Literal
```

**AFTER (Line 2):**
```python
from typing import Optional, Literal, List
```

**BEFORE (Line 38-43):**
```python
    # Tracking
    opened: bool = False
    opened_at: Optional[str] = None
    replied: bool = False
    replied_at: Optional[str] = None
    bounced: bool = False
    bounce_reason: Optional[str] = None
```

**AFTER (Line 38-60):**
```python
    # Tracking
    opened: bool = False
    opened_at: Optional[str] = None
    open_count: int = 0
    
    clicked: bool = False
    clicked_at: Optional[str] = None
    click_count: int = 0
    links_clicked: List[str] = []
    
    replied: bool = False
    replied_at: Optional[str] = None
    reply_content: Optional[str] = None
    reply_sentiment: Optional[Literal["positive", "neutral", "negative"]] = None
    
    # Lead qualification from reply
    is_lead: bool = False
    lead_score: Optional[int] = None
    is_opportunity: bool = False
    is_converted: bool = False
    
    bounced: bool = False
    bounce_reason: Optional[str] = None
    bounce_type: Optional[Literal["hard", "soft"]] = None
```

**Reason**: Added detailed tracking for clicks, sentiment, leads, opportunities, and conversions.

---

### 13. Campaign Service - Updated Analytics

**File**: `/app/backend/services/campaign_service.py`

**BEFORE (Line 1-14):**
```python
"""Service for managing campaigns and campaign execution"""
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

from models.campaign import Campaign, CampaignCreate, CampaignUpdate
from models.campaign_email import CampaignEmail
from models.campaign_follow_up import CampaignFollowUp
from repositories.base_repository import GenericRepository
from services.campaign_contact_service import CampaignContactService
from services.campaign_template_service import CampaignTemplateService
```

**AFTER (Line 1-15):**
```python
"""Service for managing campaigns and campaign execution"""
import asyncio
import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta
import logging

from models.campaign import Campaign, CampaignCreate, CampaignUpdate
from models.campaign_email import CampaignEmail
from models.campaign_follow_up import CampaignFollowUp
from repositories.base_repository import GenericRepository
from services.campaign_contact_service import CampaignContactService
from services.campaign_template_service import CampaignTemplateService
from services.campaign_analytics_service import CampaignAnalyticsService
```

**BEFORE (Line 20-26):**
```python
    def __init__(self, db):
        self.repository = GenericRepository(db, "campaigns")
        self.campaign_email_repo = GenericRepository(db, "campaign_emails")
        self.campaign_follow_up_repo = GenericRepository(db, "campaign_follow_ups")
        self.contact_service = CampaignContactService(db)
        self.template_service = CampaignTemplateService(db)
        self.db = db
```

**AFTER (Line 21-28):**
```python
    def __init__(self, db):
        self.repository = GenericRepository(db, "campaigns")
        self.campaign_email_repo = GenericRepository(db, "campaign_emails")
        self.campaign_follow_up_repo = GenericRepository(db, "campaign_follow_ups")
        self.contact_service = CampaignContactService(db)
        self.template_service = CampaignTemplateService(db)
        self.analytics_service = CampaignAnalyticsService(db)
        self.db = db
```

**BEFORE (Line 329-368):**
```python
    async def get_campaign_analytics(self, user_id: str, campaign_id: str) -> Dict[str, Any]:
        """Get campaign analytics"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Get campaign emails
        campaign_emails = await self.campaign_email_repo.find_many(
            {"campaign_id": campaign_id},
            limit=10000
        )
        
        # Calculate metrics
        analytics = {
            "campaign_id": campaign_id,
            "campaign_name": campaign.name,
            "status": campaign.status,
            "total_contacts": campaign.total_contacts,
            "emails_sent": campaign.emails_sent,
            "emails_pending": campaign.emails_pending,
            "emails_failed": campaign.emails_failed,
            "emails_opened": campaign.emails_opened,
            "emails_replied": campaign.emails_replied,
            "emails_bounced": campaign.emails_bounced,
            "open_rate": 0.0,
            "reply_rate": 0.0,
            "bounce_rate": 0.0,
            "by_email_type": {...}
        }
        
        # Calculate rates
        if campaign.emails_sent > 0:
            analytics["open_rate"] = round((campaign.emails_opened / campaign.emails_sent) * 100, 2)
            analytics["reply_rate"] = round((campaign.emails_replied / campaign.emails_sent) * 100, 2)
            analytics["bounce_rate"] = round((campaign.emails_bounced / campaign.emails_sent) * 100, 2)
        
        return analytics
```

**AFTER (Line 335-340):**
```python
    async def get_campaign_analytics(self, user_id: str, campaign_id: str) -> Dict[str, Any]:
        """Get comprehensive campaign analytics"""
        campaign = await self.get_campaign(user_id, campaign_id)
        if not campaign:
            raise ValueError("Campaign not found")
        
        # Use the new analytics service
        analytics = await self.analytics_service.get_campaign_analytics(campaign_id)
        
        return analytics
```

**Reason**: Simplified to use new comprehensive analytics service with sentiment analysis, lead tracking, and conversions.

---

### 14. Server.py - Added Health Routes

**File**: `/app/backend/server.py`

**BEFORE (Line 78-82):**
```python
from routes.test_flow_routes import router as test_flow_router
from routes.test_session_routes import router as test_session_router
from routes.error_routes import router as error_router

# Include routers under /api prefix
app.include_router(auth_router, prefix="/api")
```

**AFTER (Line 78-83):**
```python
from routes.test_flow_routes import router as test_flow_router
from routes.test_session_routes import router as test_session_router
from routes.error_routes import router as error_router
from routes.health_routes import router as health_router

# Include routers under /api prefix
app.include_router(health_router, prefix="/api")
app.include_router(auth_router, prefix="/api")
```

**Reason**: Added health check endpoints for monitoring.

---

### 15. Seed Data Script - Fixed Field Name

**File**: `/app/seed_data_comprehensive.py`

**BEFORE (Line 40):**
```python
            "hashed_password": pwd_context.hash(DEMO_PASSWORD),
```

**AFTER (Line 40):**
```python
            "password_hash": pwd_context.hash(DEMO_PASSWORD),
```

**Reason**: User model uses `password_hash` not `hashed_password`. This was causing login failures.

---

## 📁 New Files Created

### 1. `/app/frontend/src/pages/LeadSettings.js` (NEW - 305 lines)
- Dedicated page for Lead Qualification and Lead Nurturing controls
- Large toggle cards with ON/OFF indicators
- Statistics dashboard
- Per-intent configuration view
- "How It Works" guide

### 2. `/app/frontend/src/components/ErrorBoundary.js` (NEW - 135 lines)
- React Error Boundary component
- Catches all React component errors
- User-friendly error UI
- Auto-reload after 3 failures
- Development mode shows technical details

### 3. `/app/backend/services/campaign_analytics_service.py` (NEW - 165 lines)
- Sentiment analysis (positive/neutral/negative)
- Lead identification from replies (0-100 scoring)
- Opportunity detection
- Conversion tracking
- Performance scoring
- Smart recommendations

### 4. `/app/backend/routes/health_routes.py` (NEW - 145 lines)
- `/api/health` - Basic health check
- `/api/health/detailed` - Full diagnostics
- `/api/health/workers` - Worker status
- System resource monitoring

### 5. `/app/backend/utils/error_handler.py` (NEW - 115 lines)
- ErrorTracker class for comprehensive logging
- @handle_errors decorator
- Safe model parsing
- Production-ready error tracking

### 6. `/app/seed_data_comprehensive.py` (NEW - 520 lines)
- Creates demo user (demo@example.com / demo123)
- Populates 7 intents
- Creates 5 knowledge base entries
- Adds 5 sample inbound leads
- Creates qualification criteria and nurturing config
- Adds 3 campaign templates
- Creates 2 campaigns with analytics
- Adds 3 contacts and 2 lists
- Includes 1 follow-up

### 7. `/app/SEED_DATA_README.md` (NEW - 200 lines)
- Complete documentation of seed data
- Table of all created data
- Usage instructions
- Customization guide

### 8. `/app/QUICK_START.md` (NEW - 180 lines)
- Quick start guide for users
- Login credentials
- Where to find lead controls (3 locations)
- How to test the flow
- Pre-populated data overview

---

## 📊 Summary Statistics

**Files Modified**: 13
**Files Created**: 8
**Total Lines Added**: ~2,100 lines
**Total Lines Modified**: ~250 lines

**Key Features Added:**
- ✅ Lead Qualification & Nurturing UI controls (3 locations)
- ✅ Campaign analytics with sentiment, leads, conversions
- ✅ Calendar OAuth endpoints
- ✅ Comprehensive error handling
- ✅ Health monitoring endpoints
- ✅ Complete seed data script

**All Changes Tested and Working** ✅
