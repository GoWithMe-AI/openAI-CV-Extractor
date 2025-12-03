"""
AI service for CV summarization using OpenAI or Gemini.
"""
import json
import re
from typing import Dict, Any
from app.config import settings


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
                response_format={"type": "json_object"},
                temperature=0.3
            )
            
            result_text = response.choices[0].message.content
            return self._parse_ai_response(result_text)
            
        except ImportError:
            raise ValueError("openai package is required. Install it with: pip install openai")
        except Exception as e:
            error_msg = str(e)
            # Provide more specific error messages
            if "Connection" in error_msg or "connect" in error_msg.lower():
                raise ValueError(
                    f"OpenAI API connection error: {error_msg}. "
                    "Please check your internet connection, firewall settings, or try again later."
                )
            elif "api key" in error_msg.lower() or "authentication" in error_msg.lower():
                raise ValueError(
                    f"OpenAI API authentication error: {error_msg}. "
                    "Please check your OPENAI_API_KEY in the .env file."
                )
            else:
                raise ValueError(f"OpenAI API error: {error_msg}")
    
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
        # Limit text to avoid token limits
        limited_text = cv_text[:8000] if len(cv_text) > 8000 else cv_text
        
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
- experience_years: Calculate total years of professional experience. If multiple positions, sum them up. Return as a decimal number (e.g., 5.5 for 5 years and 6 months)

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

