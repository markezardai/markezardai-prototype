"""
Gemini AI service with key rotation and structured output parsing
"""

import os
import json
import random
import time
import logging
import pathlib
from typing import Dict, Any, List, Optional, Union
import asyncio
from dataclasses import dataclass
from dotenv import load_dotenv

import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# Ensure environment variables are loaded
project_root = pathlib.Path(__file__).parent.parent.parent.parent
load_dotenv(project_root / '.env')

logger = logging.getLogger(__name__)

@dataclass
class GeminiConfig:
    model: str = "gemini-pro"
    max_tokens: int = 2048
    temperature: float = 0.7
    top_p: float = 0.8
    top_k: int = 40

class GeminiService:
    def __init__(self):
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.key_usage_count = {}
        self.failed_keys = set()
        self._configure_safety_settings()
    
    def _load_api_keys(self) -> List[str]:
        """Load Gemini API keys from environment - PRODUCTION MODE ONLY"""
        keys = []
        for i in range(1, 5):  # Support up to 4 keys
            key = os.getenv(f'GEMINI_API_KEY_{i}')
            if key:
                keys.append(key)
                logger.info(f"✅ Loaded Gemini API key {i}")
        
        if not keys:
            raise ValueError("No Gemini API keys found. At least GEMINI_API_KEY_1 is required for production mode.")
        
        logger.info(f"✅ Gemini AI service initialized with {len(keys)} API keys")
        return keys
    
    def _configure_safety_settings(self):
        """Configure safety settings for Gemini"""
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
    
    def _get_next_api_key(self) -> Optional[str]:
        """Get next available API key using round-robin"""
        if not self.api_keys:
            return None
        
        # Get available keys (not failed)
        available_indices = [i for i in range(len(self.api_keys)) if i not in self.failed_keys]
        if not available_indices:
            # Reset failed keys if all have failed
            logger.warning("All API keys failed, resetting failed keys list")
            self.failed_keys.clear()
            available_indices = list(range(len(self.api_keys)))
        
        # Round-robin selection from available indices
        selected_index = available_indices[self.current_key_index % len(available_indices)]
        self.current_key_index = (self.current_key_index + 1) % len(available_indices)
        
        key = self.api_keys[selected_index]
        
        # Track usage
        self.key_usage_count[selected_index] = self.key_usage_count.get(selected_index, 0) + 1
        
        logger.info(f"Using Gemini API key {selected_index + 1} (usage: {self.key_usage_count[selected_index]})")
        return key
    
    def _mark_key_failed(self, api_key: str):
        """Mark an API key as failed"""
        try:
            key_index = self.api_keys.index(api_key)
            self.failed_keys.add(key_index)
            logger.warning(f"Marked Gemini API key {key_index + 1} as failed")
        except ValueError:
            pass
    
    async def call_gemini(
        self,
        prompt: str,
        config: Optional[GeminiConfig] = None,
        structured_output: bool = False,
        retry_count: int = 3
    ) -> Union[str, Dict[str, Any]]:
        """
        Call Gemini API with key rotation and retry logic - PRODUCTION MODE ONLY
        
        Args:
            prompt: The prompt to send to Gemini
            config: Configuration for the model
            structured_output: Whether to parse response as JSON
            retry_count: Number of retries on failure
        
        Returns:
            String response or parsed JSON dict
        """
        if config is None:
            config = GeminiConfig()
        
        last_error = None
        
        for attempt in range(retry_count):
            api_key = self._get_next_api_key()
            if not api_key:
                raise RuntimeError("No available Gemini API keys")
            
            try:
                # Configure the API key
                genai.configure(api_key=api_key)
                
                # Create model
                model = genai.GenerativeModel(
                    model_name=config.model,
                    safety_settings=self.safety_settings
                )
                
                # Generate content
                response = await asyncio.to_thread(
                    model.generate_content,
                    prompt,
                    generation_config=genai.types.GenerationConfig(
                        max_output_tokens=config.max_tokens,
                        temperature=config.temperature,
                        top_p=config.top_p,
                        top_k=config.top_k,
                    )
                )
                
                if response.text:
                    result = response.text.strip()
                    logger.info("✅ Gemini AI response generated successfully")
                    
                    if structured_output:
                        return self._parse_structured_output(result)
                    return result
                else:
                    raise Exception("Empty response from Gemini")
                
            except Exception as e:
                last_error = e
                error_msg = str(e).lower()
                
                # Check for quota/rate limit errors
                if "quota" in error_msg or "429" in error_msg or "rate limit" in error_msg:
                    self._mark_key_failed(api_key)
                    logger.warning(f"Quota/rate limit hit for key, trying next key: {str(e)}")
                    continue
                
                # Exponential backoff for transient errors
                if attempt < retry_count - 1:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"Gemini API error (attempt {attempt + 1}), retrying in {wait_time:.2f}s: {str(e)}")
                    await asyncio.sleep(wait_time)
                    continue
                
                logger.error(f"Gemini API call failed: {str(e)}")
                break
        
        # If all retries failed, raise error instead of mock response
        logger.error(f"All Gemini API attempts failed. Last error: {last_error}")
        raise RuntimeError(f"Gemini AI service failed after {retry_count} attempts: {last_error}")
    
    def _parse_structured_output(self, response: str) -> Dict[str, Any]:
        """Parse structured JSON output from Gemini response"""
        try:
            # Try to find JSON in the response
            response = response.strip()
            
            # Remove markdown code blocks if present
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Find JSON object
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                # Try parsing the entire response
                return json.loads(response)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse structured output: {str(e)}")
            logger.error(f"Response was: {response[:500]}...")
            
            # Return a basic structure
            return {
                "error": "Failed to parse structured output",
                "raw_response": response[:500]
            }
    

# Global instance
gemini_service = GeminiService()

# Convenience functions
async def call_gemini(prompt: str, **kwargs) -> Union[str, Dict[str, Any]]:
    """Convenience function for calling Gemini"""
    return await gemini_service.call_gemini(prompt, **kwargs)
