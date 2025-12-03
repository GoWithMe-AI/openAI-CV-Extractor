"""
AI service for CV summarization using OpenAI or Gemini.
"""
import json
import re
import logging
from typing import Dict, Any
from app.config import settings

logger = logging.getLogger(__name__)


class AIService:
    """Service for interacting with AI providers to summarize CVs."""
    
    def __init__(self):
        self.provider = settings.AI_PROVIDER.lower()
        self._validate_config()
    
    def _validate_config(self):
        """Validate that required API keys are configured."""
        if self.provider == "openai":
            if not settings.OPENAI_API_KEY:
                raise ValueError("OPENAI_API_KEY is required when using OpenAI")
        elif self.provider == "gemini":
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY is required when using Gemini")
        else:
            raise ValueError(f"Unsupported AI provider: {self.provider}")
    
    async def summarize_cv(self, cv_text: str) -> Dict[str, Any]:
        """
        Summarize CV text and extract structured information.
        
        Args:
            cv_text: Extracted text from CV PDF
            
        Returns:
            Dictionary with summary, skills, and experience_years
        """
        if self.provider == "openai":
            return await self._summarize_with_openai(cv_text)
        elif self.provider == "gemini":
            return await self._summarize_with_gemini(cv_text)
    
    async def _summarize_with_openai(self, cv_text: str) -> Dict[str, Any]:
        """Summarize using OpenAI API."""
        try:
            from openai import AsyncOpenAI
            
            client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
            
            prompt = self._build_prompt(cv_text)
            
            response = await client.chat.completions.create(
                model=settings.OPENAI_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert at analyzing CVs and resumes. Extract key information and return structured JSON."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                response_format={"type": "json_object"}
                # Note: temperature parameter removed - using model default
                # Some models only support default temperature value
            )
            
            result_text = response.choices[0].message.content
            return self._parse_ai_response(result_text)
            
        except ImportError:
            raise ValueError("openai package is required. Install it with: pip install openai")
        except Exception as e:
            raise ValueError(f"OpenAI API error: {str(e)}")
    
    async def _summarize_with_gemini(self, cv_text: str) -> Dict[str, Any]:
        """Summarize using Google Gemini API."""
        try:
            import google.generativeai as genai
            
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)
            
            prompt = self._build_prompt(cv_text)
            
            response = await model.generate_content_async(prompt)
            result_text = response.text
            
            return self._parse_ai_response(result_text)
            
        except ImportError:
            raise ValueError("google-generativeai package is required. Install it with: pip install google-generativeai")
        except Exception as e:
            raise ValueError(f"Gemini API error: {str(e)}")
    
    def _build_prompt(self, cv_text: str) -> str:
        """Build the prompt for AI summarization."""
        # Increase limit to ensure all experience sections are captured
        # Most CVs are under 15000 chars, but we want to capture all work history
        limited_text = cv_text[:15000] if len(cv_text) > 15000 else cv_text
        logger.debug(f"Building prompt with CV text length: {len(cv_text)} (limited to: {len(limited_text)})")
        
        return f"""Analyze the following CV/resume text and extract key information.

CV Text:
{limited_text}

Please provide a JSON response with the following structure:
{{
    "summary": "A concise 2-3 sentence summary of the candidate's background, experience, and key strengths",
    "skills": ["skill1", "skill2", "skill3", ...],
    "experience_years": <number>
}}

Instructions:
- summary: Write a professional summary highlighting the candidate's experience and expertise
- skills: Extract all technical and professional skills mentioned. Include programming languages, frameworks, tools, methodologies, etc.
-   experience_years: Calculate total years of professional experience. 
  
  CRITICAL INSTRUCTIONS:
  1. You MUST find ALL work experience positions in the CV. Look carefully through the entire document.
  2. Search for sections titled: "Professional Experience", "Work Experience", "Employment History", "Experience", or similar.
  3. Also look for job titles followed by company names and dates anywhere in the document.
  4. Each position should have: Job Title, Company Name, and Date Range (start date - end date).
  
  Date format handling:
  - Dates may appear in various formats: "Jan 2015 - Dec 2017", "2015-2017", "01/2015 - 12/2017", "04/2023 – Present", "June 2019 - March 2023", "08/2008 – 05/2012", etc.
  - Date separators can be: "-", "–", "to", "/"
  - Month formats: "Jan", "January", "01", "1", etc.
  - Year formats: "2015", "15" (assume 2000s if 2-digit)
  - If the end date is "Present", "Current", "Now", or similar, calculate from start date to today's date (calculate current date first - assume current year is 2024 or 2025).
  - If dates are unclear or corrupted due to PDF extraction issues (e.g., "201 9" should be "2019", "06/201 9" should be "06/2019"), try to infer reasonable dates from context.
  - Only count WORK/PROFESSIONAL experience, NOT education, internships (unless explicitly stated as work), or volunteer work.
  
  Calculation method (VERY IMPORTANT):
  - FIRST: List ALL positions you found with their date ranges. Make sure you didn't miss any!
  - For each position, identify the start date and end date (or "Present").
  - Convert all dates to a consistent format (MM/YYYY) for calculation.
  - CRITICAL: Calculate from the EARLIEST start date to the LATEST end date (or Present).
  - If positions are consecutive (no gaps or small gaps of 1-2 months), count the entire period from earliest start to latest end.
  - If positions overlap, merge them and count the overlapping period only once.
  - If there are gaps between positions, you can still count them as separate periods and sum them, OR count from earliest to latest (whichever gives the total professional experience time).
  - Calculate total years including partial years as decimals (e.g., 08/2008 to 05/2012 = 3 years 9 months = 3.75 years).
  - Return as a decimal number (e.g., 16.5 for 16 years and 6 months).
  
  Example calculation:
  If you find these positions:
  - Position 1: 08/2008 - 05/2012 (3.75 years)
  - Position 2: 08/2012 - 02/2015 (2.5 years)
  - Position 3: 03/2015 - 05/2019 (4.17 years)
  - Position 4: 06/2019 - 03/2023 (3.75 years)
  - Position 5: 04/2023 - Present (1.67 years as of Dec 2024)
  
  Calculation method: Count from EARLIEST start (08/2008) to LATEST end (Present = Dec 2024)
  Total = 08/2008 to Present = approximately 16.5 years
  
  VALIDATION CHECK: Before finalizing your calculation, verify:
  - If the CV shows positions starting from 2008 or earlier and ending at Present, the total should be 15-17 years (not 10-12 years).
  - If you calculated less than expected, you likely missed some positions - go back and find ALL of them!
  - There is NO maximum limit - calculate the actual total years based on ALL positions found.
  - Double-check that you found ALL positions in the "Professional Experience" section before calculating!
  
  Step-by-step process:
  1. Scan the ENTIRE CV text carefully for ALL work experience entries
  2. List each position with its date range
  3. Convert all dates to MM/YYYY format
  4. Identify the earliest start date and latest end date (or Present)
  5. Calculate the total time span in years (earliest start to latest end/Present)
  6. Return the total as a decimal number

Return ONLY valid JSON, no additional text."""
    
    def _parse_ai_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse AI response and extract structured data.
        
        Handles JSON wrapped in markdown code blocks or plain JSON.
        """
        # Remove markdown code blocks if present
        response_text = response_text.strip()
        
        # Try to extract JSON from markdown code blocks
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
        
        # Try to find JSON object in the text
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(0)
        
        try:
            data = json.loads(response_text)
            
            # Validate and normalize response
            result = {
                "summary": str(data.get("summary", "")).strip(),
                "skills": self._normalize_skills(data.get("skills", [])),
                "experience_years": self._normalize_experience(data.get("experience_years", 0))
            }
            
            # Validate required fields
            if not result["summary"]:
                raise ValueError("AI response missing 'summary' field")
            if not result["skills"]:
                raise ValueError("AI response missing 'skills' field")
            
            return result
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error processing AI response: {str(e)}")
    
    def _normalize_skills(self, skills: Any) -> list:
        """Normalize skills to a list of strings."""
        if isinstance(skills, list):
            return [str(skill).strip() for skill in skills if str(skill).strip()]
        elif isinstance(skills, str):
            # Try to parse comma-separated or newline-separated skills
            return [s.strip() for s in re.split(r'[,;\n]', skills) if s.strip()]
        return []
    
    def _normalize_experience(self, experience: Any) -> float:
        """Normalize experience years to a float."""
        try:
            if isinstance(experience, (int, float)):
                return float(experience)
            elif isinstance(experience, str):
                # Extract number from string
                match = re.search(r'(\d+\.?\d*)', experience)
                if match:
                    return float(match.group(1))
            return 0.0
        except (ValueError, TypeError):
            return 0.0

