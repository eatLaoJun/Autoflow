from typing import Optional
from .base_agent import BaseAgent
from models.schemas import RequirementCard, PRDDocument, TestCases, TestCase
from utils.retry import async_retry_on_failure
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class TestAgent(BaseAgent):
    """Test Case Generation Agent"""

    def __init__(self):
        super().__init__()

    @async_retry_on_failure(max_retries=3, delay=1.0)
    async def generate(self, requirement_card: RequirementCard, prd: PRDDocument) -> TestCases:
        """Generate test cases"""
        input_text = self._format_input(requirement_card, prd)

        system_prompt = self._load_prompt("test_system.txt")

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text}
        ]

        response = self._call_api(messages, response_format={"type": "json_object"})

        try:
            data = json.loads(response)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from response: {response}")
            raise e

        return self._validate_output(data, TestCases)

    def _format_input(self, requirement_card: RequirementCard, prd: PRDDocument) -> str:
        """Format input for test agent"""
        input_parts = [
            "=== Requirement Card ===",
            f"Name: {requirement_card.name}",
            f"Core Actions: {', '.join(requirement_card.core_actions)}",
            "",
            "=== PRD Document ===",
            f"Title: {prd.title}",
            f"User Stories: {'; '.join(prd.user_stories)}",
            f"Core Flow: {prd.core_flow}",
            f"Exception Flow: {prd.exception_flow}",
            f"Data Fields: {', '.join(prd.data_fields)}",
            "",
            "=== Task Description ===",
            "Based on the above PRD, generate comprehensive test cases.",
            "Include:",
            "1. P0 main flow cases (at least 5) - priority 'P0'",
            "2. P1 exception cases (at least 3) - priority 'P1'",
            "3. P2 boundary cases (at least 3) - priority 'P2'",
            "",
            "Each test case must include: priority, precondition, steps, expected result.",
            "Ensure test cases cover all user stories and exception scenarios."
        ]

        return "\n".join(input_parts)
