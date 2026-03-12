# 🎯 Comprehensive Seed Data Script

## Overview
This script populates the entire AI Email Assistant application with realistic demo data for testing, demonstration, and development purposes.

## Usage

```bash
cd /app
python3 seed_data_comprehensive.py
```

## What Gets Created

### 1. Demo User Account
- **Email**: `demo@example.com`
- **Password**: `demo123`
- **Quota**: 1000 emails/day (45 used)
- **Global Lead Qualification**: ENABLED
- **Global Lead Nurturing**: ENABLED
- **Role**: User
- **HubSpot**: Enabled but not connected

### 2. Lead Qualification Criteria (1)
- **Name**: "B2B SaaS Lead Qualification"
- **Type**: Question-based
- **Questions**: 4 qualification questions
  - Company size (25% weight)
  - Monthly budget (30% weight)
  - Industry (20% weight)
  - Job title (25% weight)
- **Threshold**: 60% minimum score
- **Max Exchanges**: 3 attempts

### 3. Lead Nurturing Configuration (1)
- **Name**: "Standard B2B Nurturing"
- **Questions**: 5 contextual questions
  - Features interested in
  - Company size
  - Budget range
  - Implementation timeline
  - Industry
- **Questions per Email**: 2
- **Max Exchanges**: 3
- **Natural Integration**: Enabled

### 4. Email Intents (7)

| Intent Name | Priority | Auto-Send | Is Lead | Qualification | Nurturing |
|------------|----------|-----------|---------|---------------|-----------|
| Pricing Inquiry (Lead) | 10 | ✅ | ✅ | ✅ | ✅ |
| Demo Request (Lead) | 9 | ✅ | ✅ | ✅ | ✅ |
| Meeting Request | 8 | ✅ | ❌ | ❌ | ❌ |
| Support Request | 7 | ✅ | ❌ | ❌ | ❌ |
| Partnership Inquiry (Lead) | 6 | ✅ | ✅ | ✅ | ❌ |
| General Inquiry | 3 | ✅ | ❌ | ❌ | ❌ |
| Default Intent | 1 | ❌ | ❌ | ❌ | ❌ |

**Keywords Included**: Each intent has 5-9 relevant keywords for accurate classification

### 5. Knowledge Base Entries (5)

1. **Product Overview** - Comprehensive product description
2. **Pricing Plans** - All pricing tiers (Starter, Professional, Enterprise)
3. **Getting Started Guide** - 5-step onboarding guide
4. **Support & Contact** - All support channels and contacts
5. **AI Capabilities** - Technical details about AI features

### 6. Sample Inbound Leads (5)

| Name | Company | Stage | Score | Priority | Meeting |
|------|---------|-------|-------|----------|---------|
| Sarah Johnson | TechCorp Solutions | Qualified | 85 | High | ✅ |
| Michael Chen | Startup Ventures | Awaiting Info | 45 | Medium | ❌ |
| Emily Rodriguez | Marketing Pro Agency | New | 0 | Medium | ❌ |
| David Kim | Global Enterprise Inc | Qualified | 95 | Urgent | ✅ |
| Lisa Anderson | Anderson Consulting | Unqualified | 25 | Low | ❌ |

**Lead Distribution:**
- Qualified: 2 (40%)
- Awaiting Info: 1 (20%)
- New: 1 (20%)
- Unqualified: 1 (20%)

### 7. Campaign Templates (3)

1. **Product Launch - Initial** - Introduction email with value prop
2. **Product Launch - Follow-up 1** - First follow-up with social proof
3. **Customer Success Story** - Case study and results

**Features**: All templates include variables for personalization ({{first_name}}, {{company}}, etc.)

### 8. Contact Lists (2)

1. **Enterprise Prospects** - Large companies (high-value)
2. **SaaS Startups** - Early stage SaaS companies

### 9. Campaign Contacts (3)

1. **John Smith** - Acme Corp (Sales Director)
2. **Jane Doe** - Innovate Inc (CEO, Founder)
3. **Robert Brown** - Enterprise Solutions (CTO, Enterprise)

**All contacts include**: Email verified, company size, industry, job title

### 10. Sample Campaigns (2)

#### Campaign 1: "Q4 Product Launch" (Completed)
- **Status**: Completed
- **Contacts**: 3
- **Metrics**:
  - Emails Sent: 3
  - Open Rate: 66.67%
  - Click Rate: 33.33%
  - Reply Rate: 66.67%
  - Delivery Rate: 100%
  - Inbox Rate: 66.67%
- **Lead Metrics**:
  - Leads Generated: 2
  - Lead Rate: 100%
  - Opportunities: 1
  - Conversions: 1
- **Sentiment**: 1 positive, 1 neutral, 0 negative

#### Campaign 2: "Enterprise Outreach" (Running)
- **Status**: Running
- **Contacts**: 1
- **Metrics**:
  - Emails Sent: 1
  - Open Rate: 100%
  - Delivery Rate: 100%

### 11. Follow-ups (1)

- 1 pending follow-up scheduled for 2 days from now

## Data Relationships

All data is properly linked:
- Intents → User
- Knowledge Base → User
- Leads → User
- Qualification Criteria → User → Leads
- Nurturing Config → User → Intents
- Templates → User → Campaigns
- Contacts → Lists → Campaigns
- Follow-ups → User

## Features Demonstrated

✅ **Lead Management**
- Lead qualification with scoring
- Lead nurturing with questions
- Multiple lead stages
- Priority tracking

✅ **Campaign Management**
- Complete campaigns with analytics
- Template system with variables
- Contact list management
- Advanced tracking metrics

✅ **Intent Classification**
- Multiple intent types
- Priority-based matching
- Lead vs non-lead intents
- Auto-send configuration

✅ **Analytics**
- Open/click/reply rates
- Sentiment analysis
- Lead generation metrics
- Conversion tracking
- Deliverability metrics

## Customization

To create seed data for a different user:

1. Change `DEMO_EMAIL` and `DEMO_PASSWORD` variables at top of script
2. Run the script
3. All data will be linked to the new user

## Notes

- Script is idempotent - can run multiple times (deletes existing demo user data first)
- All dates are realistic (campaigns from 15 days ago, leads from various times)
- Metrics are realistic percentages
- Bcrypt warning is harmless (version detection issue)

## Testing the Data

After running the script:

1. **Login**: Use demo@example.com / demo123
2. **Dashboard**: See overview with statistics
3. **Intents**: View all 7 intents with different configurations
4. **Knowledge Base**: Browse 5 knowledge articles
5. **Inbound Leads**: See 5 leads in different stages
6. **Campaigns**: View 2 campaigns with analytics
7. **Lead Controls**: Toggle qualification and nurturing
8. **Settings**: View and modify lead management settings

## Production Use

For production environments:
- Create separate seed scripts per environment
- Use environment variables for credentials
- Add data validation
- Include database backup before seeding
- Log all data creation with IDs

---

**Created**: December 19, 2025
**Version**: 1.0
**Database**: email_assistant_db
