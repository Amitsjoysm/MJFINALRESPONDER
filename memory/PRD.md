# PRD - AI Email Assistant (MJFINALRESPONDER)

## Original Problem Statement
Clone https://github.com/Amitsjoysm/MJFINALRESPONDER branch FixedCleaned. Check how agent is working in case User ask for Follow up next month or next quarter or next year or next summer or after 10-15 days. Ensure follow up tasks are generated and automatically sent and draft agent generate correct follow up using context of previous conversations without failures. While Working Ensure working features/functions don't get affected.

## Architecture
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: React.js on port 3000
- **Database**: MongoDB (email_assistant_db)
- **AI Provider**: Groq (llama-3.3-70b-versatile)
- **Email**: OAuth Gmail/Outlook + SMTP

## What's Been Implemented (March 12, 2026)

### 1. Enhanced DateParserService
- **Seasons**: next summer/winter/spring/fall/autumn
- **Day ranges**: after 10-15 days, in 10-15 days
- **Simple days**: after 30 days, in 7 days
- **Vague days**: couple of days, few days
- **Named days**: next Monday/Tuesday etc.
- **Year boundaries**: beginning of next year, end of year
- **Fiscal year**: next fiscal year
- **Week ranges**: after 2-3 weeks (fixed 'after' support)
- **Week simple**: after 4 weeks, in 2 weeks
- **Quarters**: next quarter, Q2, 3rd quarter
- **Months**: next month, in 3 months
- **Specific dates**: after 20th November, after December 15
- **Availability**: out of office till, will be free after
- **Deduplication**: removes duplicate date matches

### 2. Enhanced Follow-up Draft Generation (email_worker.py)
- Full thread history included in context
- KB entries pulled for relevant follow-up content
- Sender email history across all threads
- Previous follow-up history (avoids repetition)
- Original email body + our response included
- Reply detection before sending (cancels if replied)
- Better error handling with specific cancellation reasons

### 3. Enhanced AI Prompt for Follow-ups (ai_agent_service.py)
- Sender history section in prompt
- Previous follow-ups section (with "don't repeat" instruction)
- Original email + response context
- KB summary for value-add content

### 4. Fixed SignatureHandler
- Only checks last 5 lines for signature patterns
- No longer strips body content with "thank you"
- Standalone closing phrase detection only

### 5. Configuration
- Updated GROQ_API_KEY
- Cleared EMERGENT_LLM_KEY
- Added /api/test/parse-dates test endpoint

## User Personas
- **Sales Teams**: Auto-follow-up on leads who say "contact me next quarter"
- **Account Managers**: Long-term nurturing with "follow up next year"
- **Support Teams**: Short-term follow-ups "after 10-15 days"

## Core Requirements (Static)
- Email processing pipeline (intent → draft → validate → send)
- Follow-up scheduling (time-based + standard)
- Lead qualification & nurturing
- Calendar integration
- Meeting detection

## Prioritized Backlog
### P0 (Critical) - DONE
- [x] Long-term follow-up date parsing (all patterns)
- [x] Follow-up draft generation with full context
- [x] SignatureHandler fix

### P1 (Important)
- [ ] LLM-powered fallback for ambiguous time references
- [ ] Follow-up escalation (if no response after multiple follow-ups)
- [ ] Follow-up analytics dashboard

### P2 (Nice to have)
- [ ] Multi-timezone support for follow-up scheduling
- [ ] Custom follow-up templates per intent
- [ ] A/B testing for follow-up messages

## Next Tasks
1. Monitor follow-up delivery in production
2. Add follow-up performance metrics
3. Test with real email accounts
