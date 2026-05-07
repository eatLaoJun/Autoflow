import os
import json
import logging
from typing import Dict, Any, Optional, Type
from openai import OpenAI
from pydantic import BaseModel, ValidationError
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class BaseAgent:
    def __init__(self):
        self.model_name = os.getenv("MODEL_NAME", "gpt-4o")
        self.max_retries = int(os.getenv("MAX_RETRY_TIMES", "3"))
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        if base_url:
            self.client = OpenAI(api_key=api_key, base_url=base_url)
        else:
            self.client = OpenAI(api_key=api_key)

    def _load_prompt(self, prompt_file: str) -> str:
        prompt_path = os.path.join(os.path.dirname(__file__), "..", "prompts", prompt_file)
        try:
            with open(prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        except Exception as e:
            raise Exception(f"Error loading prompt file {prompt_file}: {str(e)}")

    def _call_api(self, messages: list, response_format: Optional[Dict] = None) -> str:
        try:
            params = {
                "model": self.model_name,
                "messages": messages,
                "temperature": 0.7,
            }
            if response_format:
                params["response_format"] = response_format
            response = self.client.chat.completions.create(**params)
            content = response.choices[0].message.content
            return content if content else ""
        except Exception as e:
            logger.error(f"API call failed: {str(e)}")
            raise Exception(f"API call failed: {str(e)}")

    def _parse_json(self, text: str) -> dict:
        if not text:
            raise ValueError("Empty response from API")
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            if end != -1:
                json_str = text[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        if "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            if end != -1:
                json_str = text[start:end].strip()
                try:
                    return json.loads(json_str)
                except json.JSONDecodeError:
                    pass
        try:
            text = text.strip()
            if text.startswith("﻿"):
                text = text[1:]
            return json.loads(text)
        except json.JSONDecodeError:
            import re
            matches = re.findall(r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}", text, re.DOTALL)
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            raise ValueError(f"Unable to parse JSON from text: {text[:200]}...")

    def _validate_output(self, data: dict, schema_class: Type[BaseModel]) -> BaseModel:
        try:
            return schema_class(**data)
        except ValidationError as e:
            logger.error(f"Validation failed: {str(e)}")
            raise
