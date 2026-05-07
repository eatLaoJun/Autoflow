from typing import List, Tuple
from models.schemas import RequirementCard, PRDDocument, TestCases
from pydantic import BaseModel

class ValidationResult:
    """Validation result container"""
    def __init__(self):
        self.is_valid: bool = True
        self.issues: List[str] = []    # Problems that block continuation
        self.warnings: List[str] = []  # Issues that don't block but should be noted
    
    def add_issue(self, issue: str):
        self.is_valid = False
        self.issues.append(issue)
    
    def add_warning(self, warning: str):
        self.warnings.append(warning)


def validate_requirement_card(card: RequirementCard) -> ValidationResult:
    """
    Validate requirement card completeness
    
    Args:
        card: RequirementCard instance to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    # Check if essential fields are filled
    if not card.name or not card.name.strip():
        result.add_issue("需求名称未填写")
    
    if not card.user_roles or len(card.user_roles) == 0:
        result.add_issue("未识别用户角色")
    
    if not card.core_actions or len(card.core_actions) == 0:
        result.add_issue("未识别核心行为")
    
    # Check for missing fields marked during clarification
    if card.missing_fields and len(card.missing_fields) > 0:
        missing_str = ", ".join(card.missing_fields)
        result.add_warning(f"以下字段信息不完整，标记为待确认: {missing_str}")
    
    return result


def validate_prd(prd: PRDDocument) -> ValidationResult:
    """
    Validate PRD quality according to rules
    
    Args:
        prd: PRDDocument instance to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    # Rule: 用户故事数量 ≥ 用户角色数量
    # Note: We don't have user_roles here, so we check minimum 1
    if not prd.user_stories or len(prd.user_stories) < 1:
        result.add_issue("用户故事数量不足，至少需要1条")
    
    # Rule: 异常场景数量 ≥ 3
    # Since exception_flow is a text field, we check if it contains multiple scenarios
    exception_text = prd.exception_flow.lower()
    exception_indicators = ["异常", "错误", "失败", "异常1", "异常2", "异常3", 
                          "场景1", "场景2", "场景3", "情况1", "情况2", "情况3"]
    exception_count = sum(1 for indicator in exception_indicators if indicator in exception_text)
    
    # Alternative approach: count sentences or bullet points
    if exception_count < 3:
        # Try counting by lines that look like exceptions
        lines = [line.strip() for line in prd.exception_flow.split('\n') if line.strip()]
        exception_lines = [line for line in lines if 
                          any(keyword in line.lower() for keyword in 
                              ['异常', '错误', '失败', '网络', '权限', '重复', '数据'])]
        if len(exception_lines) < 3:
            result.add_issue("异常场景描述不足，建议至少覆盖3种异常类型")
    
    # Rule: 数据字段列表不为空
    if not prd.data_fields or len(prd.data_fields) == 0:
        result.add_issue("数据字段列表为空")
    
    # Rule: 核心流程步骤 ≥ 3 步
    # Check if core_flow contains multiple steps
    core_text = prd.core_flow.lower()
    step_indicators = ["步骤", "第一", "第二", "第三", "1.", "2.", "3.", "首先", "然后", "最后"]
    step_count = sum(1 for indicator in step_indicators if indicator in core_text)
    
    if step_count < 3:
        # Alternative: count by lines or sentences
        lines = [line.strip() for line in prd.core_flow.split('\n') if line.strip()]
        if len(lines) < 3:
            result.add_issue("核心流程描述不足，建议至少描述3个步骤")
    
    return result


def validate_test_cases(cases: TestCases) -> ValidationResult:
    """
    Validate test cases quantity and quality
    
    Args:
        cases: TestCases instance to validate
        
    Returns:
        ValidationResult with validation status
    """
    result = ValidationResult()
    
    # Check minimum quantities (these are already validated by Pydantic, but double-check)
    if len(cases.main_flow_cases) < 5:
        result.add_issue(f"P0主流程用例数量不足，当前{len(cases.main_flow_cases)}条，需要至少5条")
    
    if len(cases.exception_cases) < 3:
        result.add_issue(f"P1异常用例数量不足，当前{len(cases.exception_cases)}条，需要至少3条")
    
    if len(cases.boundary_cases) < 3:
        result.add_issue(f"P2边界用例数量不足，当前{len(cases.boundary_cases)}条，需要至少3条")
    
    # Check if each test case has required fields
    for i, case in enumerate(cases.main_flow_cases):
        if not case.precondition or not case.precondition.strip():
            result.add_issue(f"P0用例#{i+1}前置条件为空")
        if not case.steps or not case.steps.strip():
            result.add_issue(f"P0用例#{i+1}操作步骤为空")
        if not case.expected or not case.expected.strip():
            result.add_issue(f"P0用例#{i+1}预期结果为空")
    
    for i, case in enumerate(cases.exception_cases):
        if not case.precondition or not case.precondition.strip():
            result.add_issue(f"P1用例#{i+1}前置条件为空")
        if not case.steps or not case.steps.strip():
            result.add_issue(f"P1用例#{i+1}操作步骤为空")
        if not case.expected or not case.expected.strip():
            result.add_issue(f"P1用例#{i+1}预期结果为空")
    
    for i, case in enumerate(cases.boundary_cases):
        if not case.precondition or not case.precondition.strip():
            result.add_issue(f"P2用例#{i+1}前置条件为空")
        if not case.steps or not case.steps.strip():
            result.add_issue(f"P2用例#{i+1}操作步骤为空")
        if not case.expected or not case.expected.strip():
            result.add_issue(f"P2用例#{i+1}预期结果为空")
    
    # Warning if exactly at minimum (suggest adding more for better coverage)
    if len(cases.main_flow_cases) == 5:
        result.add_warning("P0用例恰好达到最低要求，建议增加更多主流程用例以提高覆盖度")
    
    if len(cases.exception_cases) == 3:
        result.add_warning("P1用例恰好达到最低要求，建议增加更多异常场景用例")
    
    if len(cases.boundary_cases) == 3:
        result.add_warning("P2用例恰好达到最低要求，建议增加更多边界值用例")
    
    return result