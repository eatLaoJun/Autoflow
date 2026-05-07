from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Literal
from datetime import datetime

class RequirementCard(BaseModel):
    """Structured requirement card"""
    name: str = Field(..., description="Requirement name, clearly describing what the feature is")
    background: str = Field(..., description="Business background description")
    user_roles: List[str] = Field(..., description="List of user roles")
    core_actions: List[str] = Field(..., description="List of core actions")
    constraints: List[str] = Field(default_factory=list, description="Constraints")
    out_of_scope: List[str] = Field(default_factory=list, description="Out of scope items")
    tech_stack: str = Field(default="Common Web Tech Stack", description="Technology stack")
    is_complete: bool = Field(default=False, description="Whether information is complete")
    missing_fields: List[str] = Field(default_factory=list, description="List of missing fields")
    
    @validator('name')
    def name_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Requirement name cannot be empty')
        return v.strip()
    
    @validator('user_roles')
    def user_roles_at_least_one(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one user role required')
        return v
    
    @validator('core_actions')
    def core_actions_at_least_one(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one core action required')
        return v

class PRDDocument(BaseModel):
    """Product Requirements Document"""
    title: str = Field(..., description="PRD title")
    background: str = Field(..., description="Requirement background")
    user_stories: List[str] = Field(..., description="List of user stories")
    core_flow: str = Field(..., description="Core flow description")
    exception_flow: str = Field(..., description="Exception scenarios description")
    data_fields: List[str] = Field(..., description="Data fields list")
    non_functional: str = Field(default="", description="Non-functional requirements")
    out_of_scope: str = Field(..., description="Out of scope")
    
    @validator('user_stories')
    def user_stories_at_least_one(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one user story required')
        return v
    
    @validator('core_flow')
    def core_flow_min_length(cls, v):
        if not v or len(v.strip()) < 50:
            raise ValueError('Core flow description must be > 50 characters')
        return v.strip()
    
    @validator('exception_flow')
    def exception_flow_min_length(cls, v):
        if not v or len(v.strip()) < 30:
            raise ValueError('Exception flow description must be > 30 characters')
        return v.strip()

class APIDesign(BaseModel):
    """API design model"""
    name: str = Field(..., description="API name")
    method: str = Field(..., description="HTTP method GET/POST/PUT/DELETE")
    description: str = Field(..., description="Function description")
    params: List[str] = Field(default_factory=list, description="Core parameters list")
    response: str = Field(..., description="Return value description")

class TechPlan(BaseModel):
    """Technical solution"""
    involved_modules: List[str] = Field(..., description="List of involved modules")
    new_apis: List[APIDesign] = Field(default_factory=list, description="New APIs")
    modified_apis: List[str] = Field(default_factory=list, description="Modified APIs")
    db_changes: List[str] = Field(default_factory=list, description="Database changes")
    estimated_days: Dict[str, int] = Field(..., description="Workload estimation")
    tech_risks: List[str] = Field(default_factory=list, description="Technical risk points")
    
    @validator('involved_modules')
    def involved_modules_at_least_one(cls, v):
        if not v or len(v) == 0:
            raise ValueError('At least one involved module required')
        return v
    
    @validator('estimated_days')
    def estimated_days_has_required_keys(cls, v):
        required_keys = {'frontend', 'backend', 'testing'}
        if not required_keys.issubset(set(v.keys())):
            raise ValueError(f'Workload estimation must contain {required_keys}')
        return v

class TestCase(BaseModel):
    """Single test case"""
    priority: Literal["P0", "P1", "P2"] = Field(..., description="Test case priority")
    precondition: str = Field(..., description="Precondition")
    steps: str = Field(..., description="Test steps")
    expected: str = Field(..., description="Expected result")

class TestCases(BaseModel):
    """Test cases collection"""
    main_flow_cases: List[TestCase] = Field(..., description="P0 main flow cases")
    exception_cases: List[TestCase] = Field(..., description="P1 exception cases")
    boundary_cases: List[TestCase] = Field(..., description="P2 boundary cases")
    
    @validator('main_flow_cases')
    def main_flow_cases_min_count(cls, v):
        if not v or len(v) < 5:
            raise ValueError('At least 5 P0 main flow cases required')
        return v
    
    @validator('exception_cases')
    def exception_cases_min_count(cls, v):
        if not v or len(v) < 3:
            raise ValueError('At least 3 P1 exception cases required')
        return v
    
    @validator('boundary_cases')
    def boundary_cases_min_count(cls, v):
        if not v or len(v) < 3:
            raise ValueError('At least 3 P2 boundary cases required')
        return v
    
    @property
    def total_count(self) -> int:
        """Return total test case count"""
        return len(self.main_flow_cases) + len(self.exception_cases) + len(self.boundary_cases)

class RiskReport(BaseModel):
    """Risk assessment report"""
    risk_level: Literal["High", "Medium", "Low"] = Field(..., description="Risk level")
    risk_points: List[str] = Field(..., description="List of risk points")
    suggestions: List[str] = Field(..., description="List of improvement suggestions")
    uncovered_scenarios: List[str] = Field(default_factory=list, description="Uncovered scenarios")
    needs_human_review: bool = Field(default=False, description="Whether human review is needed")

# Export all models
__all__ = [
    "RequirementCard",
    "PRDDocument", 
    "APIDesign",
    "TechPlan",
    "TestCase",
    "TestCases",
    "RiskReport"
]
