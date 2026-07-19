#!/usr/bin/env python3
"""
Audio-Localizing AI Monitor - Brain Module
Cloud LLM + prompt handling
"""

import json
import base64
import time
from typing import Optional, Dict, Any
import anthropic
from config import (
    ANTHROPIC_API_KEY, LLM_MODEL, LLM_SYSTEM_PROMPT, LLM_USER_PROMPT_TEMPLATE,
    LLM_TIMEOUT_SEC, OFFLINE_MODE, DEMO_MODE, SERIAL_DEBUG, CANNED_RESPONSES
)

class Brain:
    """Analyzes events via multimodal LLM."""
    
    def __init__(self):
        self.client = None
        if ANTHROPIC_API_KEY:
            self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        self.fallback_responses = CANNED_RESPONSES
    
    def analyze_event(self, photo_path: Optional[str] = None, 
                      audio_path: Optional[str] = None,
                      audio_description: str = "") -> Dict[str, Any]:
        """
        Send photo + audio to LLM for event classification.
        
        Returns: {
            "event_type": str,
            "severity": str,
            "response": str,
            "action": str
        }
        """
        
        # Fallback if offline or demo mode
        if OFFLINE_MODE or not self.client:
            return self._fallback_response()
        
        try:
            # Build multimodal message
            content = self._build_message(photo_path, audio_description)
            
            # Call LLM
            message = self.client.messages.create(
                model=LLM_MODEL,
                max_tokens=256,
                system=LLM_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": content}],
                timeout=LLM_TIMEOUT_SEC
            )
            
            # Parse response
            response_text = message.content[0].text
            return self._parse_response(response_text)
        
        except json.JSONDecodeError as e:
            if SERIAL_DEBUG:
                print(f"[BRAIN] JSON parse error: {e}")
            return self._fallback_response()
        
        except Exception as e:
            print(f"[BRAIN] LLM call failed: {e}")
            return self._fallback_response()
    
    def _build_message(self, photo_path: Optional[str], 
                       audio_description: str) -> list:
        """Build multimodal message for Claude."""
        content = []
        
        # Add image if provided
        if photo_path:
            try:
                with open(photo_path, "rb") as f:
                    image_data = base64.standard_b64encode(f.read()).decode("utf-8")
                
                # Detect format
                fmt = "jpeg" if photo_path.endswith(".jpg") else "png"
                
                content.append({
                    "type": "image",
                    "source": {
                        "type": "base64",
                        "media_type": f"image/{fmt}",
                        "data": image_data
                    }
                })
            except Exception as e:
                print(f"[BRAIN] Image encode failed: {e}")
        
        # Add text prompt
        prompt = LLM_USER_PROMPT_TEMPLATE.format(audio_description=audio_description)
        content.append({
            "type": "text",
            "text": prompt
        })
        
        return content
    
    def _parse_response(self, text: str) -> Dict[str, Any]:
        """Extract JSON from LLM response."""
        # Try to find JSON object in response
        start = text.find('{')
        end = text.rfind('}')
        
        if start != -1 and end != -1:
            json_str = text[start:end+1]
            obj = json.loads(json_str)
            
            # Validate required keys
            required = ["event_type", "severity", "response", "action"]
            if all(key in obj for key in required):
                return obj
        
        # Fallback if parsing failed
        return self._fallback_response()
    
    def _fallback_response(self) -> Dict[str, Any]:
        """Return canned response on error."""
        if SERIAL_DEBUG:
            print("[BRAIN] Using fallback response")
        
        return {
            "event_type": "unknown",
            "severity": "benign",
            "response": self.fallback_responses.get("unknown", "Heard something interesting"),
            "action": "log"
        }
    
    def get_canned(self, key: str, default: str = "") -> str:
        """Retrieve pre-recorded canned response."""
        return self.fallback_responses.get(key, default)
