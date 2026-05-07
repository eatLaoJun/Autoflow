from typing import Optional
from .base_agent import BaseAgent
from models.schemas import RequirementCard
from utils.retry import async_retry_on_failure
import asyncio
import json
import logging
import re

logger = logging.getLogger(__name__)

class ClarifyResponse:
    """Response from clarification agent"""
    def __init__(self, reply, is_done, round):
        self.reply = reply
        self.is_done = is_done
        self.round = round

class ClarifyAgent(BaseAgent):
    """Requirement clarification Agent"""
    
    def __init__(self, max_rounds=5):
        super().__init__()
        self.max_rounds = max_rounds
        self.conversation_history = []
        self.round_count = 0
        self.requirement_card = None
    
    @async_retry_on_failure(max_retries=3, delay=1.0)
    async def chat(self, user_input):
        """Multi-turn chat for requirement clarification"""
        if user_input.strip():
            self.conversation_history.append({"role": "user", "content": user_input})
        self.round_count += 1
        if self.round_count >= self.max_rounds:
            return await self._force_generate()
        
        system_prompt = self._load_prompt("clarify_system.txt")
        messages = [{"role": "system", "content": system_prompt}] + self.conversation_history
        response = self._call_api(messages)
        self.conversation_history.append({"role": "assistant", "content": response})
        # 检测是否包含需求卡片标记（支持多种格式）
        card_markers = ["[REQUIREMENT_CARD]", "[当前进展]", "[需求卡片]"]
        marker_found = None
        for marker in card_markers:
            if marker in response:
                marker_found = marker
                break
        
        if marker_found:
            try:
                requirement_card = self._parse_requirement_card(response)
                self.requirement_card = requirement_card
            except Exception as e:
                logger.warning(f"Failed to parse requirement card: {str(e)}")
            
            # 无论解析成功与否，都返回友好提示，不显示JSON
            return ClarifyResponse(
                "✅ 信息已收集完整，需求卡片已生成完成！系统将自动进入文档生成阶段。",
                is_done=True,
                round=self.round_count
            )
        
        # 正常对话，返回清理后的回复（过滤掉可能的JSON片段）
        clean_response = self._clean_response(response)
        return ClarifyResponse(clean_response, is_done=False, round=self.round_count)
    
    async def _force_generate(self):
        """Force generate requirement card from conversation history"""
        # Build prompt from conversation history
        history_text = "\n".join([
            f"{msg['role']}: {msg['content']}" 
            for msg in self.conversation_history
        ])
        
        system_prompt = self._load_prompt("clarify_system.txt")
        
        # Add force generate instruction
        force_prompt = f"""{system_prompt}

Conversation History:
{history_text}

Based on the above conversation, force generate the requirement card now.
You must output the requirement card in the format:
[REQUIREMENT_CARD]
{{
    "name": "...",
    "background": "...",
    "user_roles": [...],
    "core_actions": [...],
    "constraints": [...],
    "out_of_scope": [...],
    "tech_stack": "..."
}}
"""
        
        messages = [
            {"role": "system", "content": force_prompt},
            {"role": "user", "content": "Please generate the requirement card based on our conversation."}
        ]
        
        response = self._call_api(messages, response_format={"type": "json_object"})        
        
        try:
            requirement_card = self._parse_requirement_card(response)
            self.requirement_card = requirement_card
            return ClarifyResponse(response, is_done=True, round=self.round_count)
        except Exception as e:
            logger.error(f"Force generate failed: {str(e)}")
            # Return a basic response
            return ClarifyResponse(
                "已达到最大轮次，但生成需求卡片失败。请重新开始对话。",
                is_done=True,
                round=self.round_count
            )
    
    def _parse_requirement_card(self, text):
        """Parse requirement card from response, supports multiple formats"""
        # Try different markers
        markers = ["[REQUIREMENT_CARD]", "[当前进展]", "[需求卡片]"]
        json_start = -1
        
        for marker in markers:
            if marker in text:
                # Find JSON after marker
                idx = text.find(marker) + len(marker)
                # Find the start of JSON (first '{')
                brace_idx = text.find("{", idx)
                if brace_idx != -1:
                    json_start = brace_idx
                    break
        
        if json_start != -1:
            # Find matching closing brace
            depth = 0
            json_end = json_start
            for i in range(json_start, len(text)):
                if text[i] == "{":
                    depth += 1
                elif text[i] == "}":
                    depth -= 1
                    if depth == 0:
                        json_end = i + 1
                        break
            json_str = text[json_start:json_end]
            try:
                data = json.loads(json_str)
                return self._validate_output(data, RequirementCard)
            except (json.JSONDecodeError, Exception) as e:
                logger.warning(f"Failed to parse JSON after marker: {str(e)}")
        
        # Try to parse as pure JSON
        try:
            data = json.loads(text)
            return self._validate_output(data, RequirementCard)
        except json.JSONDecodeError:
            # Try to extract JSON from code blocks
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                if end != -1:
                    json_str = text[start:end].strip()
                    try:
                        data = json.loads(json_str)
                        return self._validate_output(data, RequirementCard)
                    except json.JSONDecodeError:
                        pass
        
        # If all parsing fails, create a basic card from conversation
        logger.warning("Failed to parse requirement card, creating from conversation")
        return RequirementCard(
            name="需求卡片",
            background="从对话中自动提取",
            user_roles=["用户"],
            core_actions=["待补充"],
            constraints=[],
            out_of_scope=[],
            tech_stack="常见Web技术栈",
            is_complete=False,
            missing_fields=["详细信息待补充"]
        )
    
    def _clean_response(self, text):
        """Remove JSON and markers from response for clean display"""
        # Remove common JSON markers
        markers = ["[REQUIREMENT_CARD]", "[当前进展]", "[需求卡片]", "```json", "```"]
        clean = text
        for marker in markers:
            if marker in clean:
                # Find the marker and remove everything from there
                if marker in ["```json", "```"]:
                    # Remove code blocks
                    while "```" in clean:
                        start = clean.find("```")
                        end = clean.find("```", start + 3)
                        if end == -1:
                            clean = clean[:start].strip()
                            break
                        clean = clean[:start] + clean[end+3:]
                else:
                    # Remove marker and following JSON
                    idx = clean.find(marker)
                    if idx != -1:
                        # Keep text before marker
                        clean = clean[:idx].strip()
        return clean.strip() or "请继续提供信息。"
    
    def get_result(self):
        """Get the generated requirement card"""
        return self.requirement_card
