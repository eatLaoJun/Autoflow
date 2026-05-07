from typing import Optional
from .base_agent import BaseAgent
from models.schemas import RequirementCard, PRDDocument
from utils.retry import async_retry_on_failure
import asyncio
import json
import logging

logger = logging.getLogger(__name__)

class PRDAgent(BaseAgent):
    """PRD Generation Agent"""

    def __init__(self):
        super().__init__()

    @async_retry_on_failure(max_retries=3, delay=1.0)
    async def generate(self, requirement_card: RequirementCard) -> PRDDocument:
        """Generate PRD document"""
        input_text = self._format_input(requirement_card)

        system_prompt = self._load_prompt("prd_system.txt")

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

        return self._validate_output(data, PRDDocument)

    def _format_input(self, requirement_card: RequirementCard) -> str:
        """Format requirement card as input for PRD agent"""
        input_parts = [
            "=== Requirement Card Information ===",
            f"Name: {requirement_card.name}",
            f"Background: {requirement_card.background}",
            f"User Roles: {", ".join(requirement_card.user_roles)}",
            f"Core Actions: {", ".join(requirement_card.core_actions)}",
            f"Constraints: {", ".join(requirement_card.constraints) if requirement_card.constraints else "None"}",
            f"Out of Scope: {", ".join(requirement_card.out_of_scope) if requirement_card.out_of_scope else "None"}",
            f"Tech Stack: {requirement_card.tech_stack}",
            "",
            "=== Clarification Conversation History ===",
        ]

        if hasattr(self, "conversation_history") and self.conversation_history:
            for msg in self.conversation_history[-6:]:  # Last 6 messages.
                role = "User" if msg["role"] == "user" else "Assistant"
                content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
                input_parts.append(f"{role}: {content}")
        else:
            input_parts.append("No conversation history")

        input_parts.extend([
            "",
            "=== Task Description ===",
            "Based on the above requirement card information, generate a complete Product Requirements Document (PRD).",
            "Ensure all necessary sections are included: background, user stories, functional description (core flow and exception scenarios), data description, non-functional requirements, and exclusions.",
            "Special Notes:",
            "1. User stories should follow the format: As a [role], I want [action], so that [value]",
            "2. Core flow should describe the complete steps for users to use the feature",
            "3. Exception scenarios should cover at least: network exceptions, data exceptions/boundary values, insufficient permissions, repeated operations",
            "4. Data fields should accurately describe data structures and types",
            "5. If there are fields marked as TBD in the requirement card, explain this in the corresponding section"
        ])

        return "\n".join(input_parts)

