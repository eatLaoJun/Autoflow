import json
import os
from typing import Optional
from datetime import datetime
from models.schemas import RequirementCard, PRDDocument, TechPlan, TestCases, RiskReport

class SessionState:
    """Session state management for persisting intermediate results"""
    
    def __init__(self):
        self.session_id: str = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.raw_input: str = ""
        self.requirement_card: Optional[RequirementCard] = None
        self.prd: Optional[PRDDocument] = None
        self.tech_plan: Optional[TechPlan] = None
        self.test_cases: Optional[TestCases] = None
        self.risk_report: Optional[RiskReport] = None
        self.current_stage: str = "initialized"  # clarifying/generating/done
        self.created_at: str = datetime.now().isoformat()
    
    def save(self, output_dir: str = "output") -> None:
        """Save session state to output/{session_id}/state.json"""
        # Create session directory
        session_dir = os.path.join(output_dir, self.session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save state.json
        state_file = os.path.join(session_dir, "state.json")
        state_data = {
            "session_id": self.session_id,
            "raw_input": self.raw_input,
            "requirement_card": self.requirement_card.dict() if self.requirement_card else None,
            "prd": self.prd.dict() if self.prd else None,
            "tech_plan": self.tech_plan.dict() if self.tech_plan else None,
            "test_cases": self.test_cases.dict() if self.test_cases else None,
            "risk_report": self.risk_report.dict() if self.risk_report else None,
            "current_stage": self.current_stage,
            "created_at": self.created_at
        }
        
        with open(state_file, 'w', encoding='utf-8') as f:
            json.dump(state_data, f, ensure_ascii=False, indent=2)
    
    @classmethod
    def load(cls, session_id: str, output_dir: str = "output") -> Optional['SessionState']:
        """Load session state from output/{session_id}/state.json"""
        state_file = os.path.join(output_dir, session_id, "state.json")
        
        if not os.path.exists(state_file):
            return None
        
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)
            
            # Create instance
            session = cls()
            session.session_id = state_data["session_id"]
            session.raw_input = state_data["raw_input"]
            session.current_stage = state_data["current_stage"]
            session.created_at = state_data["created_at"]
            
            # Load nested objects if they exist
            if state_data["requirement_card"]:
                session.requirement_card = RequirementCard(**state_data["requirement_card"])
            if state_data["prd"]:
                session.prd = PRDDocument(**state_data["prd"])
            if state_data["tech_plan"]:
                session.tech_plan = TechPlan(**state_data["tech_plan"])
            if state_data["test_cases"]:
                session.test_cases = TestCases(**state_data["test_cases"])
            if state_data["risk_report"]:
                session.risk_report = RiskReport(**state_data["risk_report"])
            
            return session
        except Exception as e:
            print(f"Error loading session state: {str(e)}")
            return None
    
    def get_progress(self) -> dict:
        """Return completion status of each stage"""
        progress = {
            "clarifying": self.requirement_card is not None,
            "prd_generated": self.prd is not None,
            "tech_generated": self.tech_plan is not None,
            "test_generated": self.test_cases is not None,
            "risk_generated": self.risk_report is not None,
            "completed": self.current_stage == "done"
        }
        return progress