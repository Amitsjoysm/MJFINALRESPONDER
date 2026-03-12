# 🚀 Quick Start Guide

## Login Credentials
- **URL**: https://followup-enhance.preview.emergentagent.com
- **Email**: demo@example.com
- **Password**: demo123

## 🎯 Where to Find Lead Qualification & Nurturing Controls

### Option 1: Lead Controls Page (Recommended)
**Navigation**: Sidebar → Initial Setup → **Lead Controls**

**What You'll See:**
- 🟢 Large ON/OFF toggle cards for:
  - Lead Qualification (Indigo card)
  - Lead Nurturing (Pink card)
- 📊 Statistics showing:
  - Total Lead Intents
  - Intents with Qualification enabled
  - Intents with Nurturing enabled
- 📋 List of all lead intents with their configuration
- ℹ️ "How It Works" guide

**Actions You Can Take:**
- Click "Disable Qualification" or "Disable Nurturing" to turn OFF globally
- Click "Enable Qualification" or "Enable Nurturing" to turn ON globally
- Click "Configure" on any intent to edit its settings

---

### Option 2: Intents Page
**Navigation**: Sidebar → Initial Setup → **Intents**

**What You'll See:**
- ℹ️ Blue info banner at top explaining lead controls
- 📋 List of all intents with color-coded badges:
  - 🟢 Green = Auto-Send
  - 🔵 Blue = Lead
  - 🟣 Indigo = Qualification
  - 🟠 Pink = Nurturing

**Creating/Editing Intent:**
1. Click "Create Intent" or "Edit" on existing intent
2. Fill in Name, Keywords, Prompt
3. ✅ Check "Mark as Inbound Lead intent"
4. **Two new options appear with purple border:**
   - ✅ "Enable Lead Qualification"
   - ✅ "Enable Lead Nurturing"
5. Click "Create Intent" or "Update Intent"

**Visual Indicator:**
- When "Inbound Lead" is checked, qualification and nurturing options appear indented with a purple left border

---

### Option 3: Settings Page
**Navigation**: Profile Icon (top right) → **Settings**

**What You'll See:**
- 📊 Lead Management Settings section (large card)
- Two toggle sections:
  - Lead Qualification (Indigo background)
  - Lead Nurturing (Purple background)
- Each shows ON/OFF status with green or gray badge
- Click "Disable" or "Enable" buttons to toggle

---

## 📊 Pre-Populated Data

### Intents with Lead Controls:
1. ✅ **Pricing Inquiry (Lead)** - Qualification + Nurturing
2. ✅ **Demo Request (Lead)** - Qualification + Nurturing  
3. ✅ **Partnership Inquiry (Lead)** - Qualification only

### Sample Leads to Explore:
- Sarah Johnson - **Qualified** (Score: 85)
- David Kim - **Qualified** (Score: 95)
- Michael Chen - **Awaiting Info** (Score: 45)
- Emily Rodriguez - **New** (Score: 0)
- Lisa Anderson - **Unqualified** (Score: 25)

### Sample Campaigns:
- Q4 Product Launch - **Completed** (66.67% open rate, 1 conversion)
- Enterprise Outreach - **Running** (100% open rate)

---

## 🎮 Testing the Flow

### Test Lead Qualification:
1. Go to **Test Email** page (in sidebar)
2. Send a pricing inquiry email
3. Check **Inbound Leads** - new lead should appear
4. Send reply with qualification answers
5. Lead should update with score and stage

### Test Campaign Analytics:
1. Go to **Campaigns** page
2. Click on "Q4 Product Launch"
3. View comprehensive analytics:
   - Open/Click/Reply rates
   - Sentiment breakdown
   - Lead generation metrics
   - Conversion tracking

---

## ⚙️ How Lead Controls Work

### Two-Level Control System:

**Level 1: Global Settings** (Lead Controls page)
- Controls overall availability of features
- Must be ON for features to work anywhere

**Level 2: Per-Intent Settings** (Intents page)
- Controls which intents use the features
- Appears when intent is marked as "Inbound Lead"

**Both must be enabled** for lead qualification/nurturing to activate.

---

## 📈 Campaign Analytics Available

For any campaign, you'll see:
- 📧 Open Rate, Click Rate, Reply Rate
- 📬 Delivery Rate, Inbox Rate, Bounce Rate
- 😊 Sentiment Analysis (Positive, Neutral, Negative)
- 🎯 Lead Rate, Opportunities Rate, Conversion Rate
- 💡 Smart Recommendations for improvement
- 📊 Performance Score (0-100)

---

## 🔄 Running Seed Script Again

To reset and recreate all data:
```bash
cd /app
python3 seed_data_comprehensive.py
```

This will:
- Delete existing demo@example.com user data
- Recreate everything from scratch
- Safe to run multiple times

---

**Need Help?** All features are now visible with clear labels and instructions in the UI!
