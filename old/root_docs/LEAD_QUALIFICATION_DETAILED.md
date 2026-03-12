# 🎯 Lead Qualification - How Answers Work & Lead Acceptance/Rejection

## Table of Contents
1. [How Answers Work](#how-answers-work)
2. [How Leads Qualify](#how-leads-qualify)
3. [How Leads Get Rejected](#how-leads-get-rejected)
4. [Scoring Calculation](#scoring-calculation)
5. [Real Examples](#real-examples)

---

## 📝 How Answers Work

### **1. Answer Format**

Answers can be in **any natural text format**. The AI extracts the information intelligently:

**Examples of Valid Answers:**
```
✅ "We have 75 employees"
✅ "Our company size is 50-100 people"
✅ "75"
✅ "Small team of 20"
✅ "We're a startup with 10 people"

✅ "Budget is $10,000 per month"
✅ "We can spend around $5k monthly"
✅ "10k"
✅ "$5,000-$10,000 range"
✅ "We have allocated $15,000 for this"
```

**The AI doesn't require exact formats** - it understands context!

### **2. Answer Extraction Process**

When a lead replies to an email:

```
Step 1: Email received
   ↓
Step 2: AI (Groq LLM) reads the entire email
   ↓
Step 3: Matches content to previously asked questions
   ↓
Step 4: Extracts answers in natural language
   ↓
Step 5: Stores answers with question keys
```

**Example:**
```
Email Reply:
"Hi, thanks for reaching out! We're a technology company with 
75 employees. Our budget for this kind of solution is around 
$10,000 per month. We're looking to implement ASAP."

Extracted Answers:
{
  "company_size": "75 employees",
  "budget": "$10,000 per month",
  "industry": "technology",
  "timeline": "ASAP"
}
```

### **3. Types of Answer Validation**

#### **A. No Specific Requirements (Any Answer Counts)**
Most questions accept any answer:

**Question:** "What is your monthly budget?"
- ✅ Any response counts as answered
- Example: "$5k", "Not sure yet", "Need to discuss with team"
- **All count toward qualification score**

#### **B. Qualifying Answers (Preferred Responses)**
Some questions have specific qualifying answers:

**Question:** "What is your company size?"
- ✅ **Qualifying Answers:** `51-200`, `201-500`, `501+`, `enterprise`
- ⚠️ **Neutral Answers:** `11-50`, `25 people`, `small team`
- ❌ **Disqualifying Answers:** `1-10`, `self-employed`, `just me`

**How It Works:**
```
If answer matches qualifying list:
   → Full weight added to score
   → Reason: "✓ company_size: Qualifying answer - 75 employees"

If answer doesn't match but is provided:
   → Partial or no weight (depending on configuration)
   → Reason: "⚠ company_size: Neutral answer - 5 people"

If answer matches disqualifying list:
   → No weight added
   → Reason: "✗ company_size: Disqualifying answer - self-employed"
```

#### **C. Disqualifying Answers (Instant Rejection)**
Certain answers immediately disqualify:

**Question:** "What is your company size?"
- ❌ **Disqualifying:** `1-10`, `self-employed`, `freelancer`, `just me`

**What Happens:**
- Lead score does NOT include this question's weight
- If auto-disqualify is enabled, lead is marked as unqualified immediately
- Reason logged: "✗ company_size: Disqualifying answer - freelancer"

---

## ✅ How Leads Qualify

### **Qualification Formula**

```
Score = (Sum of Answered Question Weights / Sum of Required Question Weights) × 100

Qualification Status:
- Score ≥ 60 → ✅ QUALIFIED
- Score < 60 → ❌ UNQUALIFIED
- Score = 0  → ⏳ AWAITING INFO
```

### **Current Configuration**

**Required Questions & Weights:**
1. **Company Size** - 25% weight (has qualifying/disqualifying answers)
2. **Monthly Budget** - 30% weight (any answer counts)
3. **Industry** - 20% weight (any answer counts)

**Optional Questions:**
4. **Job Title** - 25% weight (bonus points, not required)

**Total Required Weight:** 75%  
**Qualification Threshold:** 60%

### **Qualification Scenarios**

#### **Scenario 1: All Required Questions Answered** ✅
```
Lead Reply:
"We have 75 employees, budget is $10k/month, we're in Technology"

Extracted Answers:
✓ company_size: "75 employees" (25% weight)
✓ budget: "$10k/month" (30% weight)
✓ industry: "Technology" (20% weight)

Calculation:
Score = (25% + 30% + 20%) / 75% × 100
Score = 75% / 75% × 100
Score = 100/100

Result: ✅ QUALIFIED
Stage: qualified
Priority: high
```

#### **Scenario 2: 2 out of 3 Required Answered** ✅
```
Lead Reply:
"We have 50 employees and our budget is around $5,000 monthly"

Extracted Answers:
✓ company_size: "50 employees" (25% weight)
✓ budget: "$5,000 monthly" (30% weight)
✗ industry: No answer (20% weight)

Calculation:
Score = (25% + 30%) / 75% × 100
Score = 55% / 75% × 100
Score = 73/100

Result: ✅ QUALIFIED (73 ≥ 60)
Stage: qualified
Priority: high
```

#### **Scenario 3: Includes Optional Question** ✅
```
Lead Reply:
"I'm the CTO of a 100-person company, budget is $15k"

Extracted Answers:
✓ company_size: "100-person company" (25% weight)
✓ budget: "$15k" (30% weight)
✗ industry: No answer (20% weight)
✓ job_title: "CTO" (25% weight - OPTIONAL)

Calculation:
Score = (25% + 30% + 25%) / 75% × 100
      = 80% / 75% × 100
      = 107/100 (capped at 100)

Result: ✅ QUALIFIED
Stage: qualified
Priority: urgent (optional question adds bonus)
```

---

## ❌ How Leads Get Rejected

### **Rejection Methods**

#### **Method 1: Low Score (Below Threshold)**
```
Lead Reply:
"We have 30 employees"

Extracted Answers:
✓ company_size: "30 employees" (25% weight)
✗ budget: No answer (30% weight)
✗ industry: No answer (20% weight)

Calculation:
Score = 25% / 75% × 100
Score = 33/100

Result: ❌ UNQUALIFIED (33 < 60)
Stage: unqualified
Priority: low
Action: Stop sending follow-ups
```

#### **Method 2: Disqualifying Answers**
```
Lead Reply:
"I'm a freelancer working solo, budget is $100/month"

Extracted Answers:
✗ company_size: "freelancer working solo" 
   → Matches disqualifying answer "self-employed"
   → NO weight added (0%)
✓ budget: "$100/month" (30% weight)
✗ industry: No answer (20% weight)

Calculation:
Score = 30% / 75% × 100
Score = 40/100

Result: ❌ UNQUALIFIED (40 < 60)
Stage: unqualified
Priority: low
Reason: "Disqualifying answer: freelancer (company_size)"
```

#### **Method 3: No Response After Max Exchanges**
```
Initial Email: 2 questions sent
   ↓ No reply
Follow-up #1 (Day 2): 2 questions sent
   ↓ No reply
Follow-up #2 (Day 4): 2 questions sent
   ↓ No reply
Follow-up #3 (Day 6): Final attempt
   ↓ No reply

Max Exchanges Reached (3)
Auto Disqualify: TRUE

Result: ❌ UNQUALIFIED
Stage: unqualified
Priority: low
Reason: "No response after 3 attempts"
Action: Stop all follow-ups
```

#### **Method 4: Partial Answers - Not Enough Info**
```
Lead Reply:
"Thanks for the info!"

Extracted Answers:
✗ company_size: No answer
✗ budget: No answer
✗ industry: No answer

Score = 0/100

Result: ⏳ AWAITING INFO (not rejected yet)
Stage: awaiting_info
Action: Send next follow-up with questions
Attempt: 2/3
```

### **Auto-Disqualification Rules**

When `auto_disqualify_on_fail: true`:

1. **Max exchanges reached** → Automatic unqualified
2. **Disqualifying answer provided** → Immediate unqualified
3. **Score below threshold after 3 attempts** → Automatic unqualified

When `auto_disqualify_on_fail: false`:

- Leads remain in `awaiting_info` stage indefinitely
- Manual review required
- No automatic rejection

---

## 🧮 Scoring Calculation Examples

### **Example 1: Startup Lead** ✅

**Email Reply:**
```
"We're a startup in the SaaS space with 45 people. 
We have a monthly budget of $7,500 for tools like this."
```

**Extraction:**
```json
{
  "company_size": "45 people",
  "budget": "$7,500",
  "industry": "SaaS"
}
```

**Scoring:**
```
Question 1: company_size (25% weight)
  Answer: "45 people"
  Qualifying answers: [51-200, 201-500, 501+, enterprise]
  Disqualifying answers: [1-10, self-employed]
  Result: Neutral (not in qualifying list, not disqualifying)
  → Any answer counts: ✓ 25% added

Question 2: budget (30% weight)
  Answer: "$7,500"
  Result: ✓ 30% added

Question 3: industry (20% weight)
  Answer: "SaaS"
  Result: ✓ 20% added

Total: (25% + 30% + 20%) / 75% × 100 = 100/100
Status: ✅ QUALIFIED
```

### **Example 2: Solo Freelancer** ❌

**Email Reply:**
```
"I'm a freelance consultant looking for a good deal. 
My budget is pretty tight, maybe $50/month."
```

**Extraction:**
```json
{
  "company_size": "freelance consultant",
  "budget": "$50/month"
}
```

**Scoring:**
```
Question 1: company_size (25% weight)
  Answer: "freelance consultant"
  Qualifying answers: [51-200, 201-500, 501+, enterprise]
  Disqualifying answers: [1-10, self-employed, freelancer]
  Result: ❌ DISQUALIFYING MATCH
  → 0% added (no weight)

Question 2: budget (30% weight)
  Answer: "$50/month"
  Result: ✓ 30% added (any answer counts)

Question 3: industry (20% weight)
  Answer: No answer
  Result: ✗ 0% added

Total: (0% + 30% + 0%) / 75% × 100 = 40/100
Status: ❌ UNQUALIFIED
Reason: "Disqualifying answer + low score"
```

### **Example 3: Enterprise Lead** ✅

**Email Reply:**
```
"We're an enterprise company with 500+ employees. 
I'm the VP of Engineering and we have $50k monthly budget 
allocated for this type of solution."
```

**Extraction:**
```json
{
  "company_size": "500+ employees",
  "budget": "$50k monthly",
  "job_title": "VP of Engineering"
}
```

**Scoring:**
```
Question 1: company_size (25% weight)
  Answer: "500+ employees"
  Qualifying answers: [51-200, 201-500, 501+, enterprise]
  Result: ✅ QUALIFYING MATCH
  → ✓ 25% added (full weight)

Question 2: budget (30% weight)
  Answer: "$50k monthly"
  Result: ✓ 30% added

Question 3: industry (20% weight)
  Answer: No answer
  Result: ✗ 0% added

Question 4: job_title (25% weight - OPTIONAL)
  Answer: "VP of Engineering"
  Result: ✓ 25% added (bonus points!)

Total: (25% + 30% + 0% + 25%) / 75% × 100 = 107/100 → 100/100
Status: ✅ QUALIFIED
Priority: URGENT (high-value lead)
```

### **Example 4: Vague Response** ⏳

**Email Reply:**
```
"Sounds interesting, tell me more."
```

**Extraction:**
```json
{}
```

**Scoring:**
```
Question 1: company_size (25% weight)
  Answer: No answer
  Result: ✗ 0% added

Question 2: budget (30% weight)
  Answer: No answer
  Result: ✗ 0% added

Question 3: industry (20% weight)
  Answer: No answer
  Result: ✗ 0% added

Total: 0 / 75% × 100 = 0/100
Status: ⏳ AWAITING INFO
Stage: awaiting_info
Action: Send follow-up with questions
Attempt: 2/3
```

---

## 🎯 Lead Stage Transitions

```
┌─────────────────────────────────────────────────────────────┐
│                    EMAIL ARRIVES                             │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
               ┌─────────────────┐
               │   NEW LEAD      │
               │   Score: 0      │
               └────────┬────────┘
                        │
                        ▼
               ┌─────────────────┐
               │ AWAITING INFO   │  ← Initial stage
               │ Score: 0        │
               │ Attempt: 1/3    │
               └────────┬────────┘
                        │
            ┌───────────┴───────────┐
            │                       │
    Lead Replies              No Reply (Day 2)
            │                       │
            ▼                       ▼
      ┌──────────┐          ┌─────────────────┐
      │ EXTRACT  │          │ FOLLOW-UP #1    │
      │ ANSWERS  │          │ Attempt: 2/3    │
      └────┬─────┘          └────────┬────────┘
           │                         │
           ▼                   No Reply (Day 4)
      ┌─────────┐                    │
      │ SCORE   │                    ▼
      │ LEAD    │            ┌─────────────────┐
      └────┬────┘            │ FOLLOW-UP #2    │
           │                 │ Attempt: 3/3    │
           │                 └────────┬────────┘
    ┌──────┴──────┐                  │
    │             │            No Reply (Day 6)
    ▼             ▼                  │
Score ≥ 60    Score < 60             ▼
    │             │          ┌─────────────────┐
    ▼             ▼          │ MAX EXCHANGES   │
┌─────────┐  ┌──────────┐   │ REACHED         │
│QUALIFIED│  │UNQUALIFIED│   └────────┬────────┘
│Score:73 │  │Score: 40  │            │
│Priority:│  │Priority:  │            ▼
│  high   │  │   low     │   ┌──────────────┐
└─────────┘  └───────────┘   │ UNQUALIFIED  │
                              │ Reason: No   │
                              │ response     │
                              └──────────────┘
```

---

## 📊 Summary Table

| Scenario | Answers Provided | Score | Status | Action |
|----------|-----------------|-------|--------|--------|
| All required answered | 3/3 required | 100/100 | ✅ Qualified | Route to sales |
| 2 out of 3 required | 2/3 required | 73/100 | ✅ Qualified | Route to sales |
| 1 out of 3 required | 1/3 required | 33/100 | ❌ Unqualified | Stop follow-ups |
| Disqualifying answer | 1 disqualifying | 40/100 | ❌ Unqualified | Stop follow-ups |
| No answers | 0/3 required | 0/100 | ⏳ Awaiting Info | Send follow-up |
| Vague/incomplete | Partial info | 25/100 | ⏳ Awaiting Info | Send follow-up |
| No reply after 3 attempts | 0/3 required | 0/100 | ❌ Unqualified | Stop follow-ups |
| Optional question + required | 2/3 + 1 optional | 100/100 | ✅ Qualified (Urgent) | Priority routing |

---

## 🔧 Configuration Options

### **For Users to Configure:**

1. **Qualification Threshold** (Min Score)
   - Default: 60%
   - Range: 0-100%
   - Example: Set to 70% for stricter qualification

2. **Max Exchanges**
   - Default: 3 attempts
   - Range: 1-10
   - Controls how many follow-ups before giving up

3. **Auto Disqualify**
   - Default: TRUE
   - If TRUE: Automatically mark as unqualified after max exchanges
   - If FALSE: Keep in awaiting_info for manual review

4. **Question Weights**
   - Customize importance of each question
   - Required questions: Must add up to ≤100%
   - Optional questions: Bonus points

5. **Qualifying/Disqualifying Answers**
   - Define specific acceptable answers
   - Define instant rejection answers
   - Leave empty for "any answer counts"

---

## ✅ Best Practices

### **For Question Design:**

1. **Use 3-5 required questions** (not too many)
2. **Weight critical questions higher** (e.g., budget 30%)
3. **Add 1-2 optional questions** for bonus insight
4. **Define disqualifying answers** for obvious non-fits (e.g., "freelancer")
5. **Keep threshold at 60-70%** (not too strict)

### **For Answer Validation:**

1. **Leave most questions open** (any answer counts)
2. **Only use qualifying lists** for critical criteria (e.g., company size)
3. **Use disqualifying lists sparingly** (only for clear non-fits)
4. **Let AI handle extraction** (it understands context well)

### **For Lead Management:**

1. **Auto-disqualify after 3 attempts** (don't waste time)
2. **Route qualified leads immediately** (score ≥60)
3. **Manual review for edge cases** (score 50-59)
4. **Stop follow-ups for unqualified** (score <50)

---

**Last Updated:** January 7, 2026  
**Current Configuration:** B2B SaaS Lead Qualification (60% threshold, 3 max exchanges)
