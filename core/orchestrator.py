import asyncio
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from models.schemas import RequirementCard, PRDDocument, TechPlan, TestCases, RiskReport
from .state_manager import SessionState
from agents.clarify_agent import ClarifyAgent
from agents.prd_agent import PRDAgent
from agents.tech_agent import TechAgent
from agents.test_agent import TestAgent
from agents.risk_agent import RiskAgent
from core.output_generator import OutputGenerator

class Orchestrator:
    """Main orchestrator for the multi-agent system"""
    
    def __init__(self, output_dir: str = "output"):
        self.session = SessionState()
        self.clarify_agent = ClarifyAgent()
        self.prd_agent = PRDAgent()
        self.tech_agent = TechAgent()
        self.test_agent = TestAgent()
        self.risk_agent = RiskAgent()
        self.output_generator = OutputGenerator(self.output_dir)
        self.on_progress: Optional[Callable[[str, int, str], None]] = None
        self.output_dir = output_dir
        
        # Ensure output directory exists
        import os
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _notify_progress(self, stage: str, progress: int, message: str):
        """Notify progress callback if set"""
        if self.on_progress:
            try:
                self.on_progress(stage, progress, message)
            except Exception as e:
                # Don't let progress callback errors break the flow
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Progress callback failed: {str(e)}")
    
    async def run_clarify_stage(self, user_input: str) -> Dict[str, Any]:
        """Execute clarification stage with multi-turn dialogue"""
        self._notify_progress("clarifying", 10, "开始需求澄清...")
        
        # Add user input to conversation history
        self.clarify_agent.conversation_history.append({
            "role": "user",
            "content": user_input
        })
        
        # Get agent response
        response = await self.clarify_agent.chat(user_input)
        
        # Add agent response to conversation history
        self.clarify_agent.conversation_history.append({
            "role": "assistant",
            "content": response.reply
        })
        
        # Update session state
        self.session.raw_input = user_input
        self.session.current_stage = "clarifying"
        
        if response.is_done:
            self.session.requirement_card = self.clarify_agent.get_result()
            self.session.current_stage = "generated"
            self._notify_progress("clarifying", 20, "需求澄清完成！")
        else:
            self.session.current_stage = "clarifying"
            self._notify_progress("clarifying", 10 + (response.round * 2), f"需求澄清中... (第{response.round}/5轮)")
        
        # Save state
        self.session.save()
        
        return {
            "response": response.reply,
            "is_done": response.is_done,
            "round": response.round,
            "requirement_card": self.session.requirement_card
        }
    
    async def run_generation_stage(self) -> Dict[str, Any]:
        """Execute document generation stage"""
        if not self.session.requirement_card:
            raise ValueError("Requirement card not generated. Please run clarification stage first.")
        
        self._notify_progress("generating", 30, "开始生成PRD...")
        
        # Generate PRD
        try:
            self.session.prd = await self.prd_agent.generate(self.session.requirement_card)
            self._notify_progress("generating", 40, "PRD生成完成！")
        except Exception as e:
            self._notify_progress("generating", 40, f"PRD生成失败: {str(e)}")
            raise
        
        # Save state after PRD
        self.session.save()
        
        # Execute Tech Agent and Test Agent in parallel
        self._notify_progress("generating", 50, "并发生成技术方案和测试用例...")
        
        try:
            # Run tech agent and test agent concurrently
            tech_task = asyncio.create_task(
                self.tech_agent.generate(self.session.requirement_card, self.session.prd)
            )
            test_task = asyncio.create_task(
                self.test_agent.generate(self.session.requirement_card, self.session.prd)
            )
            
            # Wait for both to complete
            self.session.tech_plan, self.session.test_cases = await asyncio.gather(
                tech_task, test_task
            )
            
            self._notify_progress("generating", 70, "技术方案和测试用例生成完成！")
        except Exception as e:
            self._notify_progress("generating", 70, f"并行生成失败: {str(e)}")
            raise
        
        # Save state after parallel execution
        self.session.save()
        
        # Generate Risk Report
        self._notify_progress("generating", 80, "进行风险评估...")
        
        try:
            self.session.risk_report = await self.risk_agent.evaluate(
                self.session.prd, 
                self.session.tech_plan, 
                self.session.test_cases
            )
            self._notify_progress("generating", 90, "风险评估完成！")
        except Exception as e:
            self._notify_progress("generating", 90, f"风险评估失败: {str(e)}")
            # Create a default risk report on failure
            from models.schemas import RiskReport
            self.session.risk_report = RiskReport(
                risk_level="未知",
                risk_points=["风险评估过程中出现错误"],
                suggestions=["请检查系统配置并重试"],
                uncovered_scenarios=[],
                needs_human_review=True
            )
        
        # Save final state
        self.session.save()
        
        # Generate final output
        self._notify_progress("generating", 95, "生成最终报告...")
        
        try:
            output_path = self.output_generator.save(self.session)
            self._notify_progress("generating", 100, f"报告生成完成！保存至: {output_path}")
        except Exception as e:
            self._notify_progress("generating", 100, f"报告生成失败: {str(e)}")
            raise
        
        self.session.current_stage = "done"
        
        return {
            "prd": self.session.prd,
            "tech_plan": self.session.tech_plan,
            "test_cases": self.session.test_cases,
            "risk_report": self.session.risk_report,
            "output_path": output_path
        }
    
    async def run(self, initial_input: str) -> SessionState:
        """Run the complete pipeline"""
        # Reset session for new run
        self.session = SessionState()
        
        # Stage 1: Clarification (multi-turn)
        clarify_done = False
        while not clarify_done:
            user_input = initial_input if not self.clarify_agent.conversation_history else ""
            result = await self.run_clarify_stage(user_input if user_input else "继续")
            clarify_done = result["is_done"]
            
            if not clarify_done and not user_input:
                # If we're continuing conversation but got no new input, break to avoid infinite loop
                break
        
        # Stage 2: Generation (if clarification succeeded)
        if self.session.requirement_card and self.session.requirement_card.is_complete:
            await self.run_generation_stage()
        elif self.session.requirement_card:
            # Even if incomplete, proceed with generation (missing fields will be marked)
            await self.run_generation_stage()
        
        return self.session