from typing import Optional
from .base_agent import BaseAgent
from models.schemas import RequirementCard, PRDDocument, TechPlan, APIDesign
from utils.retry import async_retry_on_failure
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class TechAgent(BaseAgent):
    """Technical Solution Generation Agent"""

    def __init__(self):
        super().__init__()

    @async_retry_on_failure(max_retries=3, delay=1.0)
    async def generate(self, requirement_card: RequirementCard, prd: PRDDocument) -> TechPlan:
        """Generate technical solution plan"""
        input_text = self._format_input(requirement_card, prd)

        system_prompt = self._load_prompt("tech_system.txt")

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

        return self._validate_output(data, TechPlan)

    def _format_input(self, requirement_card: RequirementCard, prd: PRDDocument) -> str:
        """Format input for tech agent"""
        input_parts = [
            "=== Requirement Card ===",
            f"Name: {requirement_card.name}",
            f"Background: {requirement_card.background}",
            f"User Roles: {', '.join(requirement_card.user_roles)}",
            f"Core Actions: {', '.join(requirement_card.core_actions)}",
            f"Tech Stack: {requirement_card.tech_stack}",
            "",
            "=== PRD Document ===",
            f"Title: {prd.title}",
            f"Background: {prd.background}",
            f"User Stories: {'; '.join(prd.user_stories)}",
            f"Core Flow: {prd.core_flow}",
            f"Exception Flow: {prd.exception_flow}",
            f"Data Fields: {', '.join(prd.data_fields)}",
            f"Non-Functional: {prd.non_functional}",
            f"Out of Scope: {prd.out_of_scope}",
            "",
            "=== Task Description ===",
            "Based on the above requirement and PRD, generate a complete technical solution plan.",
            "Include: involved modules, new/modified APIs, database changes, workload estimation, and technical risks.",
            "Ensure workload estimation includes frontend, backend, and testing days."
        ]

        return "\n".join(input_parts)
