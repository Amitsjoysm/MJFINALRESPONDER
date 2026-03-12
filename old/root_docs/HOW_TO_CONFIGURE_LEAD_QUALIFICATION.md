# 🎯 How to Configure Lead Qualification - Complete User Guide

## Table of Contents
1. [Where to Define Qualifying/Disqualifying Answers](#where-to-define-qualifyingdisqualifying-answers)
2. [Step-by-Step Configuration](#step-by-step-configuration)
3. [Understanding Each Field](#understanding-each-field)
4. [Configuration Examples](#configuration-examples)
5. [Best Practices](#best-practices)

---

## 📍 Where to Define Qualifying/Disqualifying Answers

### **Primary Location: Lead Qualification Page**

**URL:** `/lead-qualification`  
**Navigation:** Dashboard → Lead Qualification (in sidebar under "Initial Setup")

This is where users configure **EVERYTHING** related to lead qualification:
- ✅ Qualification criteria name
- ✅ Scoring threshold (min score)
- ✅ Max email exchanges
- ✅ Auto-disqualify settings
- ✅ **ALL QUESTIONS** with their properties
- ✅ **QUALIFYING ANSWERS** for each question
- ✅ **DISQUALIFYING ANSWERS** for each question

---

## 🛠️ Step-by-Step Configuration

### **Step 1: Access Lead Qualification Page**

1. Login to the application (demo@example.com / demo123)
2. Click **"Lead Qualification"** in the left sidebar
3. Click **"New Criteria"** button (purple button in top-right)

---

### **Step 2: Fill Basic Information**

```
┌────────────────────────────────────────────────────────┐
│  Create Criteria                                       │
├────────────────────────────────────────────────────────┤
│                                                        │
│  [Criteria Name_____________________]                 │
│  Example: "B2B SaaS Lead Qualification"               │
│                                                        │
│  [Description (optional)____________]                 │
│  [Standard qualification for B2B SaaS leads__]        │
│                                                        │
└────────────────────────────────────────────────────────┘
```

**Fields:**
- **Criteria Name** (Required): Give your criteria a descriptive name
- **Description** (Optional): Explain the purpose

---

### **Step 3: Configure Scoring Settings**

```
┌─────────────────────────────────────────────────────────┐
│  Min Score        Max Exchanges      Auto-disqualify   │
│  [60___]          [3___]             [✓] ON            │
└─────────────────────────────────────────────────────────┘
```

**Fields:**
- **Min Score** (0-100): Minimum score needed to qualify (default: 60)
- **Max Exchanges** (1-10): Maximum email attempts before giving up (default: 3)
- **Auto-disqualify**: Toggle ON to automatically mark as unqualified after max exchanges

---

### **Step 4: Add Questions**

Click **"+ Add Question"** button for each question you want to ask leads.

---

### **Step 5: Configure Each Question**

For each question, you'll see this form:

```
┌─────────────────────────────────────────────────────────────┐
│  Question 1                                            [X]   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Question Text                                              │
│  [What is your company size?_________________________]     │
│                                                             │
│  Question Key              Weight (0.0-1.0)                │
│  [company_size____]        [0.25_____]                     │
│                                                             │
│  [✓] Required Question                                     │
│                                                             │
│  ─────────────────────────────────────────────────         │
│                                                             │
│  ✅ Qualifying Answers (Optional)                          │
│  Comma-separated answers that qualify the lead             │
│  [51-200, 201-500, 501+, enterprise____________]          │
│                                                             │
│  ❌ Disqualifying Answers (Optional)                       │
│  Comma-separated answers that disqualify the lead          │
│  [1-10, self-employed, freelancer_______________]          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Understanding Each Field

### **Question-Level Fields**

#### **1. Question Text** (Required)
- **What it is:** The actual question that will be asked to the lead
- **Example:** "What is your company size?"
- **Purpose:** This is what the AI will look for in the lead's email response

#### **2. Question Key** (Required)
- **What it is:** A unique identifier for this question (no spaces, use underscores)
- **Example:** `company_size`, `monthly_budget`, `industry`
- **Purpose:** Used internally to map answers to questions
- **Format:** lowercase, underscores only (e.g., `company_size` not `Company Size`)

#### **3. Weight** (Required, 0.0-1.0)
- **What it is:** How much this question contributes to the final score
- **Example:** 
  - 0.25 = 25% of total score
  - 0.30 = 30% of total score
  - 0.20 = 20% of total score
- **Purpose:** Determines importance of each question
- **Best Practice:** All required questions should add up to ~0.70-1.00

**Weight Examples:**
```
Question 1: company_size (weight: 0.25) = 25%
Question 2: budget (weight: 0.30) = 30%
Question 3: industry (weight: 0.20) = 20%
─────────────────────────────────────────────
Total required weight = 0.75 = 75%
```

#### **4. Required Question** (Toggle)
- **What it is:** Whether this question MUST be answered for qualification
- **Options:**
  - ✓ **ON (Required):** Must be answered, included in score calculation
  - ○ **OFF (Optional):** Bonus question, adds extra points if answered
- **Purpose:** Separates must-have information from nice-to-have

---

### **Answer Validation Fields**

#### **5. ✅ Qualifying Answers** (Optional)

**What it is:** A comma-separated list of answers that are considered "good" and fully qualify the lead.

**Format:** `answer1, answer2, answer3`

**How it works:**
- If the lead's answer **matches** one of these, full question weight is added to score
- If the lead's answer **doesn't match** but is provided, question is still answered (may get partial or full weight depending on configuration)
- If left **empty**, any answer counts

**Examples:**

**For "What is your company size?"**
```
Qualifying Answers:
51-200, 201-500, 501+, enterprise, mid-sized, large company

Result:
Lead says "We have 150 employees" → AI matches to "51-200" → ✅ QUALIFIED ANSWER
Lead says "We're a 20-person team" → No match but answered → ⚠️ NEUTRAL (still counts)
```

**For "What is your role?"**
```
Qualifying Answers:
CEO, CTO, VP, Director, C-level, decision maker, founder

Result:
Lead says "I'm the CEO" → Matches → ✅ QUALIFIED ANSWER
Lead says "I'm a developer" → No match → ⚠️ NEUTRAL (still counts but not ideal)
```

**When to use:**
- ✅ When you want to identify ideal leads (e.g., company size, decision-maker roles)
- ✅ When certain answers indicate high intent (e.g., "urgent", "this quarter")
- ❌ Don't use for open-ended questions (e.g., budget - any number is fine)

---

#### **6. ❌ Disqualifying Answers** (Optional)

**What it is:** A comma-separated list of answers that instantly disqualify the lead.

**Format:** `bad_answer1, bad_answer2, bad_answer3`

**How it works:**
- If the lead's answer **matches** one of these, **NO weight is added** (0 points)
- If auto-disqualify is enabled, lead may be immediately marked as unqualified
- These are "deal-breakers" that indicate the lead is not a good fit

**Examples:**

**For "What is your company size?"**
```
Disqualifying Answers:
1-10, self-employed, freelancer, just me, solo, individual

Result:
Lead says "I'm a freelancer" → Matches → ❌ DISQUALIFIED (0 points)
Lead says "Just me" → Matches → ❌ DISQUALIFIED (0 points)
Lead says "We have 5 people" → No exact match but similar → AI may catch it
```

**For "What is your budget?"**
```
Disqualifying Answers:
no budget, free only, can't pay, $0, looking for free

Result:
Lead says "Looking for a free solution" → Matches "free only" → ❌ DISQUALIFIED
Lead says "We have $5k budget" → No match → ✅ COUNTS
```

**For "What industry?"**
```
Disqualifying Answers:
gambling, adult, illegal, cannabis (if you don't serve these)

Result:
Lead says "We're in the gambling industry" → ❌ DISQUALIFIED
```

**When to use:**
- ✅ When you have clear non-fit criteria (e.g., too small, no budget, wrong industry)
- ✅ When you want to auto-reject certain types of leads
- ✅ When compliance/legal restrictions exist
- ❌ Don't overuse - be careful not to reject good leads by accident

---

### **Special Case: No Qualifying/Disqualifying Answers**

If you leave **BOTH fields empty**:
- ✅ **Any answer counts** toward qualification
- The lead gets full weight just for responding
- Best for open-ended questions like "What is your budget?" or "What are your goals?"

**Example:**
```
Question: "What is your monthly budget?"
Qualifying Answers: [empty]
Disqualifying Answers: [empty]

Result:
→ "$5k" ✅ Counts (full weight)
→ "$50k" ✅ Counts (full weight)
→ "Not sure yet" ✅ Counts (full weight)
→ "Need to discuss with team" ✅ Counts (full weight)
```

---

## 💡 Configuration Examples

### **Example 1: B2B SaaS Lead Qualification**

**Goal:** Qualify leads with medium-to-large companies who have budget

**Configuration:**

```
Criteria Name: B2B SaaS Lead Qualification
Description: Standard qualification for B2B SaaS leads
Min Score: 60
Max Exchanges: 3
Auto-disqualify: ✓ ON

Questions:

1. What is your company size?
   Key: company_size
   Weight: 0.25 (25%)
   Required: ✓ Yes
   ✅ Qualifying: 51-200, 201-500, 501+, enterprise, mid-sized, large
   ❌ Disqualifying: 1-10, self-employed, freelancer, solo

2. What is your monthly budget for this solution?
   Key: budget
   Weight: 0.30 (30%)
   Required: ✓ Yes
   ✅ Qualifying: [empty - any answer]
   ❌ Disqualifying: no budget, free only, $0, can't afford

3. What industry are you in?
   Key: industry
   Weight: 0.20 (20%)
   Required: ✓ Yes
   ✅ Qualifying: [empty - any answer]
   ❌ Disqualifying: [empty - none]

4. What is your role in the company?
   Key: job_title
   Weight: 0.25 (25%)
   Required: ○ No (OPTIONAL - bonus points)
   ✅ Qualifying: CEO, CTO, VP, Director, C-level, founder, decision maker
   ❌ Disqualifying: [empty]
```

**How it works:**
- Required weight: 75% (25% + 30% + 20%)
- Lead must score ≥60% to qualify
- Freelancers and solo operators automatically rejected
- Decision-maker roles get bonus points

**Scoring Scenarios:**
- Company: 100 employees, Budget: $10k → Score: 73% ✅ QUALIFIED
- Company: 5 people → Score: 30% ❌ DISQUALIFIED (company too small)
- Company: 75 employees, Budget: $8k, Role: CEO → Score: 100% ✅ QUALIFIED (urgent)

---

### **Example 2: Enterprise-Only Qualification**

**Goal:** Only qualify large enterprises with significant budget

**Configuration:**

```
Criteria Name: Enterprise Lead Qualification
Min Score: 70 (stricter!)
Max Exchanges: 2
Auto-disqualify: ✓ ON

Questions:

1. What is your company size?
   Key: company_size
   Weight: 0.40 (40%) - HIGH IMPORTANCE
   Required: ✓ Yes
   ✅ Qualifying: 501+, enterprise, 500+, Fortune 500
   ❌ Disqualifying: 1-50, startup, small business, freelancer

2. What is your annual budget for enterprise solutions?
   Key: budget
   Weight: 0.40 (40%) - HIGH IMPORTANCE
   Required: ✓ Yes
   ✅ Qualifying: $100k+, $50k+, six figures, significant budget
   ❌ Disqualifying: under $10k, small budget, limited funds

3. Are you evaluating for a company-wide deployment?
   Key: deployment_scope
   Weight: 0.20 (20%)
   Required: ✓ Yes
   ✅ Qualifying: yes, company-wide, enterprise-wide, full deployment
   ❌ Disqualifying: no, single user, pilot only, trial
```

**How it works:**
- Very strict (70% threshold instead of 60%)
- Only 2 attempts (don't waste time)
- Focuses on company size and budget (40% each)
- Automatically rejects small businesses and pilots

---

### **Example 3: Lenient Qualification (Any Lead)**

**Goal:** Capture all leads, just gather information

**Configuration:**

```
Criteria Name: General Lead Information
Min Score: 30 (lenient!)
Max Exchanges: 5
Auto-disqualify: ○ OFF (manual review)

Questions:

1. What is your company size?
   Key: company_size
   Weight: 0.33 (33%)
   Required: ✓ Yes
   ✅ Qualifying: [empty - any answer]
   ❌ Disqualifying: [empty - none]

2. What is your budget range?
   Key: budget
   Weight: 0.33 (33%)
   Required: ✓ Yes
   ✅ Qualifying: [empty - any answer]
   ❌ Disqualifying: [empty - none]

3. What industry are you in?
   Key: industry
   Weight: 0.34 (34%)
   Required: ✓ Yes
   ✅ Qualifying: [empty - any answer]
   ❌ Disqualifying: [empty - none]
```

**How it works:**
- Low threshold (30% = any 1 question answered qualifies)
- More attempts (5 exchanges)
- No auto-disqualify (manual review)
- No qualifying/disqualifying lists (all answers welcome)

---

## ✅ Best Practices

### **For Question Design**

1. **Use 3-5 required questions** (not too many)
   - More questions = more friction = lower response rate
   - Focus on critical information only

2. **Weight questions by importance**
   - Budget/company size: 25-30% each
   - Industry/role: 15-20% each
   - Total required weight: 70-85%

3. **Add 1-2 optional questions** for bonus insights
   - Decision-maker role (25% bonus)
   - Timeline (15% bonus)
   - Use case (10% bonus)

4. **Keep question text conversational**
   - ✅ "What is your company size?"
   - ❌ "Enter number of employees in company"

### **For Qualifying Answers**

1. **Use for critical criteria only**
   - Company size (to filter enterprise vs SMB)
   - Decision-maker roles (to prioritize)
   - Timeline urgency (to prioritize)

2. **Include variations**
   - Not just "501+" but also "enterprise, 500+, large company"
   - AI matches intelligently but more variations help

3. **Don't overuse**
   - Leave budget/industry open (any answer is good)
   - Only use when you need to distinguish ideal leads

### **For Disqualifying Answers**

1. **Use sparingly** - only for clear non-fits
   - ✅ Freelancers (if you only serve companies)
   - ✅ No budget (if you're not free)
   - ✅ Competitor industries (if restricted)

2. **Be specific**
   - Include common phrases: "self-employed, freelancer, solo, just me"
   - Include clear indicators: "no budget, free only, can't pay"

3. **Test first**
   - Don't set disqualifying answers until you see patterns
   - Review manually for a week, then add common rejections

### **For Scoring Thresholds**

| Business Type | Min Score | Reasoning |
|--------------|-----------|-----------|
| Enterprise-only | 70-80% | Strict, only perfect fits |
| B2B SaaS | 60-70% | Balanced, good leads |
| SMB/General | 40-50% | Lenient, capture all |
| Information gathering | 20-30% | Very lenient, any response |

### **For Max Exchanges**

| Strategy | Max Exchanges | When to Use |
|----------|---------------|-------------|
| Aggressive | 1-2 | High-value enterprise, don't chase |
| Standard | 3 | Most B2B SaaS products |
| Persistent | 4-5 | Long sales cycles, complex products |
| Nurturing | 6+ | Relationship-building, education |

---

## 🎯 Quick Reference: Field Descriptions

| Field | Required? | Format | Purpose | Example |
|-------|-----------|--------|---------|---------|
| Question Text | ✓ Yes | Natural language | What to ask | "What is your company size?" |
| Question Key | ✓ Yes | `lowercase_with_underscores` | Internal identifier | `company_size` |
| Weight | ✓ Yes | 0.0-1.0 (decimal) | Importance (% of total score) | `0.25` (25%) |
| Required | ✓ Yes | Toggle ON/OFF | Must answer to qualify? | ✓ ON |
| Qualifying Answers | ○ Optional | Comma-separated | Good answers | `51-200, enterprise, 500+` |
| Disqualifying Answers | ○ Optional | Comma-separated | Bad answers | `1-10, freelancer, solo` |

---

## 📊 Testing Your Configuration

### **Test Scenario Checklist**

After configuring, test these scenarios:

1. **Ideal Lead:**
   - Answers all required questions
   - Matches qualifying criteria
   - Expected: Score 90-100%, Status: Qualified

2. **Good Lead:**
   - Answers 2/3 required questions
   - No disqualifying answers
   - Expected: Score 60-75%, Status: Qualified

3. **Marginal Lead:**
   - Answers 1-2 required questions
   - Borderline information
   - Expected: Score 40-59%, Status: Unqualified

4. **Bad Fit:**
   - Provides disqualifying answer
   - Expected: Score <40%, Status: Unqualified

5. **No Response:**
   - Doesn't reply to emails
   - Expected: After max exchanges → Unqualified

---

## 🔍 Common Mistakes to Avoid

❌ **Setting threshold too high** (e.g., 90%)
   - Fix: Use 60-70% for most cases

❌ **Too many required questions** (e.g., 8 questions)
   - Fix: Stick to 3-5 essential questions

❌ **All questions have qualifying/disqualifying lists**
   - Fix: Leave most open, only restrict critical ones

❌ **Weights don't add up** (e.g., 3 questions at 0.5 each = 150%)
   - Fix: Ensure required weights sum to 0.70-1.00

❌ **Disqualifying answers too broad** (e.g., "small" catches "small enterprise")
   - Fix: Be specific: "1-10, small business, freelancer"

❌ **Not testing** before going live
   - Fix: Test with sample leads first

---

## 📱 User Interface Guide

### **What You'll See:**

**1. Lead Qualification Page:**
```
┌─────────────────────────────────────────────────────┐
│ Lead Qualification                    [New Criteria] │
│ Define criteria to qualify/disqualify leads          │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ╔═══════════════════════════════════════════════╗  │
│ ║ B2B SaaS Lead Qualification          [✏️] [🗑️] ║  │
│ ║ Standard qualification for B2B SaaS leads     ║  │
│ ║                                               ║  │
│ ║ Type: question_based | Min Score: 60/100     ║  │
│ ║ Questions: 4 | Enabled: Yes                  ║  │
│ ║                                               ║  │
│ ║ Questions:                                    ║  │
│ ║ • What is your company size?                 ║  │
│ ║   Key: company_size | Weight: 25% | Required ║  │
│ ║   ✅ Qualifying: 51-200, 201-500, 501+       ║  │
│ ║   ❌ Disqualifying: 1-10, freelancer         ║  │
│ ║                                               ║  │
│ ║ • What is your monthly budget?               ║  │
│ ║   Key: budget | Weight: 30% | Required       ║  │
│ ║   ℹ️ Any answer accepted                     ║  │
│ ╚═══════════════════════════════════════════════╝  │
└─────────────────────────────────────────────────────┘
```

---

## 🎉 Summary

### **Where to Configure:**
✅ **Lead Qualification Page** (`/lead-qualification`) - ONE place for everything!

### **What You Can Configure:**
✅ Criteria name and description  
✅ Min score threshold (60 by default)  
✅ Max email exchanges (3 by default)  
✅ Auto-disqualify on/off  
✅ Questions with text, key, weight  
✅ **Qualifying answers** (good answers)  
✅ **Disqualifying answers** (bad answers)  

### **How It Works:**
1. User fills form with questions and answer criteria
2. System stores in database
3. When lead replies, AI extracts answers
4. System checks if answers match qualifying/disqualifying lists
5. Calculates score based on weights
6. Qualifies or disqualifies based on threshold

---

**Updated:** January 7, 2026  
**UI Enhancement:** Added qualifying/disqualifying answer fields  
**Status:** ✅ Fully functional and ready to use
