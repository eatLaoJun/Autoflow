from typing import Optional
from .base_agent import BaseAgent
from models.schemas import PRDDocument, TechPlan, TestCases, RiskReport
from utils.retry import async_retry_on_failure
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class RiskAgent(BaseAgent):
    """Risk Assessment Agent"""

    def __init__(self):
        super().__init__()

    @async_retry_on_failure(max_retries=3, delay=1.0)
    async def evaluate(self, prd: PRDDocument, tech_plan: TechPlan, test_cases: TestCases) -> RiskReport:
        """Evaluate risks based on PRD, tech plan, and test cases"""
        input_text = self._format_input(prd, tech_plan, test_cases)

        system_prompt = self._load_prompt("risk_system.txt")

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

        return self._validate_output(data, RiskReport)

    def _format_input(self, prd: PRDDocument, tech_plan: TechPlan, test_cases: TestCases) -> str:
        """Format input for risk agent"""
        input_parts = [
            "=== PRD Document ===",
            f"Title: {prd.title}",
            f"Background: {prd.background}",
            f"User Stories: {'; '.join(prd.user_stories)}",
            f"Core Flow: {prd.core_flow}",
            f"Exception Flow: {prd.exception_flow}",
            "",
            "=== Technical Plan ===",
            f"Involved Modules: {', '.join(tech_plan.involved_modules)}",
            f"New APIs: {len(tech_plan.new_apis)} APIs",
            f"Modified APIs: {', '.join(tech_plan.modified_apis)}",
            f"DB Changes: {', '.join(tech_plan.db_changes)}",
            f"Estimated Days: {tech_plan.estimated_days}",
            f"Tech Risks: {', '.join(tech_plan.tech_risks)}",
            "",
            "=== Test Cases ===",
            f"Total Test Cases: {test_cases.total_count}",
            f"P0 Cases: {len(test_cases.main_flow_cases)}",
            f"P1 Cases: {len(test_cases.exception_cases)}",
            f"P2 Cases: {len(test_cases.boundary_cases)}",
            "",
            "=== Task Description ===",
            "Based on the above documents, perform a comprehensive risk assessment.",
            "Determine risk level (High/Medium/Low) and provide:",
            "1. List of risk points",
            "2. Improvement suggestions",
            "3. Uncovered scenarios",
            "4. Whether human review is needed",
            "",
            "Consider: technical complexity, test coverage, exception handling, and business impact."
        ]

        return "\n".join(input_parts)
