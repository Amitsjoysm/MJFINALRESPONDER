"""
Lead AI Service
AI-powered features for lead nurturing and qualification
- Answer extraction from emails
- Question rephrasing
- Natural language criteria parsing
"""
import json
import logging
from typing import Dict, List, Optional, Any
import httpx

from config import config

logger = logging.getLogger(__name__)

class LeadAIService:
    """AI service for lead qualification and nurturing"""
    
    def __init__(self):
        self.groq_api_key = config.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        
        if not self.groq_api_key:
            logger.warning("GROQ_API_KEY not configured. AI features will be limited.")
    
    async def extract_answers_from_email(
        self,
        email_content: str,
        questions_asked: List[Dict[str, Any]]
    ) -> Dict[str, str]:
        """
        Use AI to extract answers to specific questions from email content
        
        Args:
            email_content: The email body text
            questions_asked: List of questions that were asked
            
        Returns:
            Dict mapping question_key to extracted answer
        """
        if not self.groq_api_key or not questions_asked:
            return {}
        
        try:
            # Prepare questions list
            questions_text = "\n".join([
                f"{i+1}. {q.get('question_text')} (key: {q.get('question_key')})"
                for i, q in enumerate(questions_asked)
            ])
            
            prompt = f"""Extract answers to these questions from the email below.
Return ONLY valid JSON with question keys mapped to answers.

Questions:
{questions_text}

Email Content:
{email_content[:2000]}

Return format:
{{
  "question_key_1": "extracted answer or 'not answered'",
  "question_key_2": "extracted answer or 'not answered'"
}}

Return ONLY the JSON object, no explanations."""

            response = await self._call_groq_api(prompt, temperature=0.1)
            
            if not response:
                return {}
            
            # Parse JSON response
            try:
                answers = json.loads(response)
                # Filter out "not answered" responses
                return {k: v for k, v in answers.items() if v and v.lower() != 'not answered'}
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse JSON from AI response: {response}")
                return {}
                
        except Exception as e:
            logger.error(f"Error extracting answers with AI: {e}")
            return {}
    
    async def rephrase_questions(
        self,
        questions: List[Dict[str, Any]],
        previous_versions: List[str],
        attempt_number: int
    ) -> List[Dict[str, Any]]:
        """
        Rephrase questions in a different, more natural way
        
        Args:
            questions: Original questions to rephrase
            previous_versions: Previously asked versions (to avoid repetition)
            attempt_number: Which attempt this is (1, 2, or 3)
            
        Returns:
            Questions with rephrased text
        """
        if not self.groq_api_key or not questions:
            return questions
        
        try:
            questions_list = []
            for q in questions:
                original = q.get('question_text', '')
                questions_list.append(f"- {original}")
            
            questions_text = "\n".join(questions_list)
            previous_text = "\n".join([f"- {v}" for v in previous_versions]) if previous_versions else "None"
            
            tone_guide = {
                1: "friendly and curious",
                2: "more casual and conversational",
                3: "gentle and understanding"
            }
            
            tone = tone_guide.get(attempt_number, "professional")
            
            prompt = f"""Rephrase these questions in a {tone} tone while keeping the same intent.
Make them sound natural and different from previous versions.

Original Questions:
{questions_text}

Previous Versions (DO NOT repeat these):
{previous_text}

Guidelines:
- Keep questions clear and concise
- Make them feel natural, not scripted
- Vary sentence structure
- This is attempt #{attempt_number}, so adjust formality accordingly
- Return as JSON array

Return format:
[
  {{"original": "original question", "rephrased": "new version"}},
  {{"original": "original question", "rephrased": "new version"}}
]

Return ONLY the JSON array."""

            response = await self._call_groq_api(prompt, temperature=0.7)
            
            if not response:
                return questions
            
            # Parse JSON response
            try:
                rephrased_list = json.loads(response)
                
                # Map rephrased questions back to original structure
                rephrased_questions = []
                for q in questions:
                    original_text = q.get('question_text', '')
                    # Find matching rephrased version
                    rephrased_text = original_text
                    for item in rephrased_list:
                        if item.get('original', '').lower() in original_text.lower():
                            rephrased_text = item.get('rephrased', original_text)
                            break
                    
                    rephrased_q = q.copy()
                    rephrased_q['question_text'] = rephrased_text
                    rephrased_questions.append(rephrased_q)
                
                return rephrased_questions
                
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse rephrased questions: {response}")
                return questions
                
        except Exception as e:
            logger.error(f"Error rephrasing questions: {e}")
            return questions
    
    async def parse_natural_language_criteria(
        self,
        criteria_text: str
    ) -> Dict[str, Any]:
        """
        Parse natural language criteria into structured format
        
        Args:
            criteria_text: Natural language description of qualification criteria
            
        Returns:
            Structured criteria with rules and questions
        """
        if not self.groq_api_key or not criteria_text:
            return {"rules": [], "questions": []}
        
        try:
            prompt = f"""Parse this lead qualification criteria into structured format.

Criteria Description:
{criteria_text}

Extract:
1. Rules (company size, budget, industry, etc.)
2. Questions to ask the lead
3. Qualifying/disqualifying answers

Return as JSON:
{{
  "rules": [
    {{"field": "company_size", "operator": "greater_than", "value": 50, "weight": 1.0}},
    {{"field": "industry", "operator": "in_list", "value": ["tech", "saas"], "weight": 0.8}}
  ],
  "questions": [
    {{
      "question_text": "What's your company size?",
      "question_key": "company_size",
      "expected_answer_type": "number",
      "qualifying_answers": null,
      "disqualifying_answers": ["less than 10"],
      "weight": 1.0,
      "is_required": true,
      "priority": 1
    }}
  ]
}}

Return ONLY the JSON object."""

            response = await self._call_groq_api(prompt, temperature=0.2)
            
            if not response:
                return {"rules": [], "questions": []}
            
            # Parse JSON response
            try:
                parsed = json.loads(response)
                return parsed
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse criteria: {response}")
                return {"rules": [], "questions": []}
                
        except Exception as e:
            logger.error(f"Error parsing natural language criteria: {e}")
            return {"rules": [], "questions": []}
    
    async def evaluate_answer_quality(
        self,
        question: str,
        answer: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Use AI to evaluate the quality and relevance of an answer
        
        Returns:
            Dict with score (0-100), is_complete, and reasoning
        """
        if not self.groq_api_key:
            return {"score": 50, "is_complete": True, "reasoning": "AI not available"}
        
        try:
            prompt = f"""Evaluate this answer to a qualification question.

Question: {question}
Answer: {answer}
Context: {context}

Evaluate:
1. Is the answer complete? (yes/no)
2. Quality score (0-100)
3. Does it qualify or disqualify the lead?
4. Brief reasoning

Return as JSON:
{{
  "score": 75,
  "is_complete": true,
  "qualifies": true,
  "reasoning": "Clear and detailed answer showing good fit"
}}

Return ONLY the JSON object."""

            response = await self._call_groq_api(prompt, temperature=0.1)
            
            if not response:
                return {"score": 50, "is_complete": True, "reasoning": "Evaluation failed"}
            
            try:
                evaluation = json.loads(response)
                return evaluation
            except json.JSONDecodeError:
                return {"score": 50, "is_complete": True, "reasoning": "Parse error"}
                
        except Exception as e:
            logger.error(f"Error evaluating answer: {e}")
            return {"score": 50, "is_complete": True, "reasoning": f"Error: {str(e)}"}
    
    async def _call_groq_api(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ) -> Optional[str]:
        """Call Groq API"""
        if not self.groq_api_key:
            return None
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.groq_api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "llama-3.3-70b-versatile",
                        "messages": [
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": temperature,
                        "max_tokens": max_tokens
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Groq API error: {response.status_code} - {response.text}")
                    return None
                
                data = response.json()
                return data['choices'][0]['message']['content'].strip()
                
        except Exception as e:
            logger.error(f"Error calling Groq API: {e}")
            return None
