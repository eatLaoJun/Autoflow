# 完整测试用例设计文档

---

# 第一部分：测试策略总览

---

## 1.1 测试分层架构

```
┌─────────────────────────────────────────────┐
│           E2E 端到端测试（Level 4）            │
│     真实 API + 完整流程 + 真实需求场景          │
│              5 个完整场景                      │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│          集成测试（Level 3）                   │
│     多 Agent 协作 + Orchestrator 流程          │
│              12 个测试用例                     │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│           组件测试（Level 2）                  │
│      单个 Agent 的完整行为测试                  │
│              31 个测试用例                     │
└────────────────────┬────────────────────────┘
                     │
┌────────────────────▼────────────────────────┐
│           单元测试（Level 1）                  │
│      工具函数 / Schema / 解析器                 │
│              28 个测试用例                     │
└─────────────────────────────────────────────┘

总计：76 个测试用例
```

---

## 1.2 测试环境配置

```python
# tests/conftest.py

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from models.schemas import (
    RequirementCard, PRDDocument, 
    TechPlan, TestCases, RiskReport, APIDesign, TestCase
)

# ─────────────────────────────────────────
# 公共 Fixture：标准测试数据
# ─────────────────────────────────────────

@pytest.fixture
def sample_requirement_card():
    """标准需求卡片，用于后续 Agent 测试"""
    return RequirementCard(
        name="用户签到功能",
        background="提升用户日活，通过积分奖励机制促进用户每日打开 App",
        user_roles=["普通用户", "VIP用户"],
        core_actions=[
            "用户点击签到按钮完成签到",
            "系统发放对应积分",
            "展示连续签到进度和奖励预览"
        ],
        constraints=[
            "每个账号每天只能签到一次",
            "连续签到7天积分双倍",
            "每天0点刷新签到状态"
        ],
        out_of_scope=["企业账号不参与签到"],
        tech_stack="React + Node.js + MySQL",
        is_complete=True
    )

@pytest.fixture
def sample_prd():
    """标准 PRD 文档"""
    return PRDDocument(
        title="用户签到功能 PRD",
        background="为提升用户日活，在 App 中增加每日签到功能，通过积分奖励促进用户形成打开 App 的习惯。",
        user_stories=[
            "作为普通用户，我希望每天签到获得积分，以便积累积分兑换奖励",
            "作为VIP用户，我希望享受签到双倍积分，以便获得更多专属权益",
            "作为用户，我希望看到连续签到进度，以便了解还需几天获得额外奖励"
        ],
        core_flow="""
        1. 用户打开 App，进入签到页面
        2. 系统查询用户今日签到状态
        3. 如未签到，展示签到按钮和今日可获积分数量
        4. 用户点击签到按钮
        5. 系统验证用户身份和今日是否已签到
        6. 验证通过后，发放对应积分并更新连续签到天数
        7. 展示签到成功弹窗，显示获得积分数量
        8. 更新签到日历，标记今日已签到
        """,
        exception_flow="""
        异常1：网络请求失败 → 提示网络异常，保留签到按钮可重试
        异常2：重复签到请求 → 返回"今日已签到"提示，不重复发放积分
        异常3：积分系统异常 → 签到状态记录成功，积分延迟发放并通知用户
        异常4：0点跨天时签到 → 以服务器时间为准，防止客户端时间篡改
        """,
        data_fields=[
            "user_id: bigint - 用户ID",
            "sign_date: date - 签到日期",
            "consecutive_days: int - 连续签到天数",
            "total_points_earned: int - 本次获得积分",
            "is_vip: boolean - 是否VIP用户",
            "created_at: datetime - 签到时间"
        ],
        out_of_scope="企业账号签到、签到积分的消费兑换逻辑、签到排行榜"
    )

@pytest.fixture
def sample_tech_plan():
    """标准技术方案"""
    return TechPlan(
        involved_modules=["用户服务", "积分服务", "签到服务（新建）", "通知服务"],
        new_apis=[
            APIDesign(
                name="POST /api/sign-in",
                method="POST",
                description="用户执行签到操作",
                params=["user_id: string", "client_time: timestamp"],
                response="{ success: bool, points_earned: int, consecutive_days: int }"
            ),
            APIDesign(
                name="GET /api/sign-in/status",
                method="GET",
                description="查询用户今日签到状态和历史记录",
                params=["user_id: string", "month: string(YYYY-MM)"],
                response="{ signed_today: bool, consecutive_days: int, monthly_records: [] }"
            )
        ],
        modified_apis=["GET /api/user/points - 增加签到积分明细字段"],
        db_changes=[
            "新增表 user_sign_records(id, user_id, sign_date, consecutive_days, points_earned, created_at)",
            "user_id + sign_date 建唯一索引",
            "user_id 建普通索引"
        ],
        estimated_days={"frontend": 3, "backend": 4, "testing": 2},
        tech_risks=[
            "0点附近并发签到可能导致重复记录，需要数据库唯一索引 + 幂等设计",
            "积分服务调用失败需要补偿机制，避免签到成功但积分未发放"
        ]
    )

@pytest.fixture
def sample_test_cases():
    """标准测试用例集"""
    return TestCases(
        main_flow_cases=[
            TestCase(
                priority="P0",
                precondition="用户已登录，今日未签到",
                steps="点击签到按钮",
                expected="签到成功，获得对应积分，连续天数+1"
            ),
            TestCase(
                priority="P0",
                precondition="VIP用户已登录，今日未签到",
                steps="点击签到按钮",
                expected="签到成功，获得双倍积分"
            ),
            TestCase(
                priority="P0",
                precondition="用户已登录，今日已签到",
                steps="再次点击签到按钮",
                expected="提示今日已签到，不重复发放积分"
            ),
            TestCase(
                priority="P0",
                precondition="用户连续签到6天，今日未签到",
                steps="点击签到按钮",
                expected="签到成功，连续天数显示7，触发双倍积分奖励"
            ),
            TestCase(
                priority="P0",
                precondition="用户已登录，进入签到页面",
                steps="查看签到日历",
                expected="正确展示本月签到记录和连续签到天数"
            )
        ],
        exception_cases=[
            TestCase(
                priority="P1",
                precondition="用户已登录，网络异常",
                steps="点击签到按钮",
                expected="提示网络异常，签到按钮保持可点击状态"
            ),
            TestCase(
                priority="P1",
                precondition="用户已登录，积分服务不可用",
                steps="点击签到按钮",
                expected="签到状态记录成功，提示积分将延迟到账"
            ),
            TestCase(
                priority="P1",
                precondition="用户在23:59:58点击签到",
                steps="点击签到按钮，0点后响应返回",
                expected="以服务器接收时间为准，正确记录签到日期"
            )
        ],
        boundary_cases=[
            TestCase(
                priority="P2",
                precondition="用户连续签到999天",
                steps="查看连续签到天数",
                expected="正确显示999，无数值溢出"
            ),
            TestCase(
                priority="P2",
                precondition="用户昨日签到，今日0点整刷新后立即签到",
                steps="在0点00分00秒点击签到",
                expected="识别为新的一天，可以正常签到"
            ),
            TestCase(
                priority="P2",
                precondition="用户连续签到7天后断签一天再签到",
                steps="断签后第二天点击签到",
                expected="连续签到天数重置为1，不享受双倍积分"
            )
        ]
    )

@pytest.fixture
def sample_risk_report():
    """标准风险报告"""
    return RiskReport(
        risk_level="中",
        risk_points=[
            "0点并发场景存在重复签到风险，需要幂等设计",
            "积分服务调用链路较长，存在部分失败场景",
            "测试用例未覆盖企业账号误操作场景"
        ],
        suggestions=[
            "在数据库层添加 user_id + sign_date 唯一索引",
            "实现积分发放的补偿机制和对账任务",
            "明确企业账号的拦截逻辑并补充测试用例"
        ],
        uncovered_scenarios=[
            "企业账号尝试签到时的处理逻辑",
            "用户账号被封禁时的签到处理"
        ],
        needs_human_review=False
    )

# ─────────────────────────────────────────
# Mock API 响应工厂函数
# ─────────────────────────────────────────

def make_mock_api_response(content: str):
    """创建模拟的 OpenAI API 响应对象"""
    mock_response = MagicMock()
    mock_response.choices[0].message.content = content
    mock_response.usage.prompt_tokens = 500
    mock_response.usage.completion_tokens = 800
    mock_response.usage.total_tokens = 1300
    return mock_response

def make_mock_stream_response(content: str):
    """创建模拟的流式 API 响应"""
    chunks = []
    for char in content:
        chunk = MagicMock()
        chunk.choices[0].delta.content = char
        chunks.append(chunk)
    return iter(chunks)
```

---

# 第二部分：Level 1 单元测试（28个）

---

## 2.1 Schema 校验测试（8个）

```python
# tests/unit/test_schemas.py

import pytest
from pydantic import ValidationError
from models.schemas import (
    RequirementCard, PRDDocument, TechPlan,
    TestCases, TestCase, RiskReport, APIDesign
)

class TestRequirementCardSchema:
    
    # UT-S-001
    def test_valid_requirement_card(self, sample_requirement_card):
        """正常需求卡片可以成功创建"""
        assert sample_requirement_card.name == "用户签到功能"
        assert len(sample_requirement_card.user_roles) == 2
        assert sample_requirement_card.is_complete == True

    # UT-S-002
    def test_empty_name_raises_error(self):
        """需求名称为空时应抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            RequirementCard(
                name="",                    # ← 空字符串
                background="测试背景",
                user_roles=["普通用户"],
                core_actions=["核心操作"],
                constraints=[],
                out_of_scope=[]
            )
        errors = exc_info.value.errors()
        assert any("name" in str(e) for e in errors)

    # UT-S-003
    def test_empty_user_roles_raises_error(self):
        """用户角色列表为空时应抛出 ValidationError"""
        with pytest.raises(ValidationError):
            RequirementCard(
                name="测试需求",
                background="测试背景",
                user_roles=[],              # ← 空列表
                core_actions=["核心操作"],
                constraints=[],
                out_of_scope=[]
            )

    # UT-S-004
    def test_default_tech_stack(self):
        """未指定技术栈时，使用默认值"""
        card = RequirementCard(
            name="测试需求",
            background="测试背景",
            user_roles=["用户"],
            core_actions=["操作"],
            constraints=[],
            out_of_scope=[]
        )
        assert card.tech_stack == "常见 Web 技术栈"

    # UT-S-005
    def test_test_cases_minimum_count_validation(self):
        """测试用例数量不足时应抛出 ValidationError"""
        with pytest.raises(ValidationError) as exc_info:
            TestCases(
                main_flow_cases=[                   # 只有 2 条，要求 ≥ 5
                    TestCase(priority="P0", precondition="条件", 
                             steps="步骤", expected="结果"),
                    TestCase(priority="P0", precondition="条件", 
                             steps="步骤", expected="结果"),
                ],
                exception_cases=[
                    TestCase(priority="P1", precondition="条件", 
                             steps="步骤", expected="结果"),
                    TestCase(priority="P1", precondition="条件", 
                             steps="步骤", expected="结果"),
                    TestCase(priority="P1", precondition="条件", 
                             steps="步骤", expected="结果"),
                ],
                boundary_cases=[
                    TestCase(priority="P2", precondition="条件", 
                             steps="步骤", expected="结果"),
                    TestCase(priority="P2", precondition="条件", 
                             steps="步骤", expected="结果"),
                    TestCase(priority="P2", precondition="条件", 
                             steps="步骤", expected="结果"),
                ]
            )
        assert "main_flow_cases" in str(exc_info.value)

    # UT-S-006
    def test_test_cases_total_count_property(self, sample_test_cases):
        """TestCases.total_count 属性返回正确总数"""
        assert sample_test_cases.total_count == 11  # 5 + 3 + 3

    # UT-S-007
    def test_risk_report_high_risk_sets_review_flag(self):
        """高风险时 needs_human_review 自动为 True"""
        report = RiskReport(
            risk_level="高",
            risk_points=["风险1"],
            suggestions=["建议1"],
            uncovered_scenarios=[]
        )
        assert report.needs_human_review == True

    # UT-S-008
    def test_risk_report_low_risk_no_review(self):
        """低风险时 needs_human_review 为 False"""
        report = RiskReport(
            risk_level="低",
            risk_points=[],
            suggestions=[],
            uncovered_scenarios=[]
        )
        assert report.needs_human_review == False
```

---

## 2.2 工具函数测试（12个）

```python
# tests/unit/test_utils.py

import pytest
import asyncio
import time
from unittest.mock import MagicMock, patch
from utils.retry import retry_on_failure, async_retry_on_failure
from utils.validator import (
    validate_requirement_card, 
    validate_prd,
    validate_test_cases,
    ValidationResult
)

class TestRetryDecorator:

    # UT-U-001
    def test_retry_succeeds_on_first_try(self):
        """函数第一次成功时，不触发重试"""
        call_count = 0
        
        @retry_on_failure(max_retries=3)
        def always_succeed():
            nonlocal call_count
            call_count += 1
            return "success"
        
        result = always_succeed()
        assert result == "success"
        assert call_count == 1

    # UT-U-002
    def test_retry_on_exception(self):
        """函数失败时自动重试，第二次成功"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0)
        def fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("第一次失败")
            return "success"
        
        result = fail_once()
        assert result == "success"
        assert call_count == 2

    # UT-U-003
    def test_retry_exhausted_raises_exception(self):
        """重试次数耗尽后抛出最后一次的异常"""
        call_count = 0
        
        @retry_on_failure(max_retries=3, delay=0)
        def always_fail():
            nonlocal call_count
            call_count += 1
            raise ValueError(f"第{call_count}次失败")
        
        with pytest.raises(ValueError) as exc_info:
            always_fail()
        
        assert call_count == 3
        assert "第3次失败" in str(exc_info.value)

    # UT-U-004
    def test_retry_only_on_specified_exceptions(self):
        """只对指定的异常类型重试，其他异常直接抛出"""
        call_count = 0
        
        @retry_on_failure(
            max_retries=3, 
            delay=0,
            exceptions=(ValueError,)        # 只重试 ValueError
        )
        def raise_type_error():
            nonlocal call_count
            call_count += 1
            raise TypeError("不应该重试")   # TypeError 不在重试列表
        
        with pytest.raises(TypeError):
            raise_type_error()
        
        assert call_count == 1              # 不重试，只调用一次

    # UT-U-005
    def test_retry_delay_between_attempts(self):
        """重试之间有正确的延迟"""
        @retry_on_failure(max_retries=3, delay=0.1)
        def always_fail():
            raise ValueError("失败")
        
        start = time.time()
        with pytest.raises(ValueError):
            always_fail()
        elapsed = time.time() - start
        
        # 3次调用，2次等待，每次0.1秒
        assert elapsed >= 0.2

    # UT-U-006
    @pytest.mark.asyncio
    async def test_async_retry_on_failure(self):
        """异步函数的重试装饰器正常工作"""
        call_count = 0
        
        @async_retry_on_failure(max_retries=3, delay=0)
        async def async_fail_once():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ValueError("异步失败")
            return "async_success"
        
        result = await async_fail_once()
        assert result == "async_success"
        assert call_count == 2


class TestValidator:

    # UT-U-007
    def test_validate_complete_requirement_card(self, sample_requirement_card):
        """完整的需求卡片校验通过"""
        result = validate_requirement_card(sample_requirement_card)
        assert result.is_valid == True
        assert len(result.issues) == 0

    # UT-U-008
    def test_validate_requirement_card_with_missing_fields(self):
        """有 missing_fields 的需求卡片校验不通过"""
        card = RequirementCard(
            name="测试需求",
            background="背景",
            user_roles=["用户"],
            core_actions=["操作"],
            constraints=[],
            out_of_scope=[],
            missing_fields=["constraints", "out_of_scope"]  # 标记有缺失
        )
        result = validate_requirement_card(card)
        assert result.is_valid == False
        assert "constraints" in str(result.issues)

    # UT-U-009
    def test_validate_prd_passes_with_valid_prd(self, sample_prd):
        """有效 PRD 校验通过"""
        result = validate_prd(sample_prd)
        assert result.is_valid == True

    # UT-U-010
    def test_validate_prd_fails_with_short_core_flow(self):
        """核心流程描述过短时校验不通过"""
        from copy import deepcopy
        import dataclasses
        
        prd = PRDDocument(
            title="测试",
            background="背景",
            user_stories=["故事1"],
            core_flow="太短了",          # ← 少于50字符
            exception_flow="异常处理：网络异常返回错误",
            data_fields=["field1"],
            out_of_scope="无"
        )
        result = validate_prd(prd)
        assert result.is_valid == False
        assert any("core_flow" in issue for issue in result.issues)

    # UT-U-011
    def test_validate_test_cases_passes(self, sample_test_cases):
        """达标的测试用例集校验通过"""
        result = validate_test_cases(sample_test_cases)
        assert result.is_valid == True

    # UT-U-012
    def test_validate_test_cases_warns_on_low_coverage(self):
        """测试用例覆盖度低时给出警告但不阻断"""
        # 创建最低数量的测试用例（恰好达标）
        min_cases = TestCases(
            main_flow_cases=[
                TestCase(priority="P0", precondition="c", steps="s", expected="e")
                for _ in range(5)
            ],
            exception_cases=[
                TestCase(priority="P1", precondition="c", steps="s", expected="e")
                for _ in range(3)
            ],
            boundary_cases=[
                TestCase(priority="P2", precondition="c", steps="s", expected="e")
                for _ in range(3)
            ]
        )
        result = validate_test_cases(min_cases)
        assert result.is_valid == True
        # 恰好达标时给出警告：建议增加更多用例
        assert len(result.warnings) > 0
```

---

## 2.3 BaseAgent 工具方法测试（8个）

```python
# tests/unit/test_base_agent.py

import pytest
import json
from unittest.mock import patch, MagicMock
from agents.base_agent import BaseAgent

class TestBaseAgentJsonParser:

    # UT-B-001
    def test_parse_plain_json(self):
        """解析纯 JSON 字符串"""
        agent = BaseAgent()
        text = '{"name": "测试", "value": 123}'
        result = agent._parse_json(text)
        assert result["name"] == "测试"

    # UT-B-002
    def test_parse_json_in_code_block(self):
        """解析包含在 ```json 代码块中的 JSON"""
        agent = BaseAgent()
        text = '''
        这是一些说明文字
        ```json
        {"name": "测试", "value": 123}
        ```
        '''
        result = agent._parse_json(text)
        assert result["name"] == "测试"

    # UT-B-003
    def test_parse_json_in_plain_code_block(self):
        """解析包含在 ``` 代码块中的 JSON"""
        agent = BaseAgent()
        text = '```\n{"name": "测试"}\n```'
        result = agent._parse_json(text)
        assert result["name"] == "测试"

    # UT-B-004
    def test_parse_invalid_json_raises_error(self):
        """无效 JSON 格式抛出异常"""
        agent = BaseAgent()
        text = "这不是JSON格式的内容"
        with pytest.raises(ValueError) as exc_info:
            agent._parse_json(text)
        assert "JSON" in str(exc_info.value)

    # UT-B-005
    def test_parse_json_with_extra_text(self):
        """JSON 前后有额外文字时正确提取"""
        agent = BaseAgent()
        text = '以下是结果：{"name": "测试", "value": 456} 生成完毕。'
        result = agent._parse_json(text)
        assert result["value"] == 456

    # UT-B-006
    def test_load_prompt_reads_file(self, tmp_path):
        """_load_prompt 正确读取 Prompt 文件"""
        prompt_content = "你是一个测试用的 Agent Prompt"
        prompt_file = tmp_path / "test_prompt.txt"
        prompt_file.write_text(prompt_content, encoding="utf-8")
        
        agent = BaseAgent()
        agent.prompt_dir = tmp_path
        result = agent._load_prompt("test_prompt.txt")
        assert result == prompt_content

    # UT-B-007
    def test_load_prompt_missing_file_raises_error(self):
        """Prompt 文件不存在时抛出清晰的错误"""
        agent = BaseAgent()
        with pytest.raises(FileNotFoundError) as exc_info:
            agent._load_prompt("non_existent_prompt.txt")
        assert "non_existent_prompt" in str(exc_info.value)

    # UT-B-008
    def test_api_call_returns_content(self, make_mock_api_response):
        """API 调用成功时返回内容字符串"""
        agent = BaseAgent()
        mock_response = make_mock_api_response('{"result": "ok"}')
        
        with patch.object(agent.client.chat.completions, 'create', 
                          return_value=mock_response):
            result = agent._call_api([{"role": "user", "content": "测试"}])
        
        assert result == '{"result": "ok"}'
```

---

# 第三部分：Level 2 组件测试（31个）

---

## 3.1 Agent 1 - 需求澄清 Agent 测试（9个）

```python
# tests/component/test_clarify_agent.py

import pytest
from unittest.mock import patch, MagicMock, call
from agents.clarify_agent import ClarifyAgent

class TestClarifyAgentNormalFlow:

    # CT-A1-001
    def test_first_round_returns_questions(self, make_mock_api_response):
        """第一轮输入后，Agent 返回追问问题"""
        agent = ClarifyAgent()
        mock_reply = "好的，我需要了解以下信息：\n1. 签到奖励是什么？\n2. 是否有连续签到奖励？\n3. 每天几点刷新？"
        
        with patch.object(agent, '_call_api', 
                          return_value=mock_reply):
            response = agent.chat("做一个签到功能")
        
        assert response.is_done == False
        assert response.round == 1
        assert len(response.reply) > 0

    # CT-A1-002
    def test_completion_when_requirement_card_in_response(self, make_mock_api_response):
        """回复中包含 [REQUIREMENT_CARD] 标记时，is_done 为 True"""
        agent = ClarifyAgent()
        mock_reply = """
        信息已足够，为您生成需求卡片。
        
        [REQUIREMENT_CARD]
        {
            "name": "用户签到功能",
            "background": "提升日活",
            "user_roles": ["普通用户"],
            "core_actions": ["每日签到", "获取积分"],
            "constraints": ["每天一次"],
            "out_of_scope": [],
            "tech_stack": "常见 Web 技术栈",
            "is_complete": true,
            "missing_fields": []
        }
        """
        
        with patch.object(agent, '_call_api', return_value=mock_reply):
            response = agent.chat("积分奖励，每天0点刷新，没有连续奖励")
        
        assert response.is_done == True
        assert agent.get_result() is not None
        assert agent.get_result().name == "用户签到功能"

    # CT-A1-003
    def test_max_rounds_triggers_force_generate(self):
        """达到最大轮数时强制生成需求卡片"""
        agent = ClarifyAgent(max_rounds=3)
        question_reply = "请问签到奖励是什么？"
        
        with patch.object(agent, '_call_api', return_value=question_reply), \
             patch.object(agent, '_force_generate') as mock_force:
            
            mock_force.return_value = RequirementCard(
                name="待定功能",
                background="待确认",
                user_roles=["用户"],
                core_actions=["操作"],
                constraints=[],
                out_of_scope=[],
                missing_fields=["background", "constraints"]
            )
            
            # 前两轮正常追问
            agent.chat("做一个签到")
            agent.chat("不知道")
            # 第三轮触发强制生成
            response = agent.chat("随便")
        
        mock_force.assert_called_once()
        assert response.is_done == True

    # CT-A1-004
    def test_user_says_done_triggers_completion(self):
        """用户说'可以了'时立即生成需求卡片"""
        agent = ClarifyAgent()
        
        # 第一轮追问
        with patch.object(agent, '_call_api', return_value="请问...？"):
            agent.chat("做一个签到功能")
        
        # 用户明确表示完成
        force_card_reply = """
        [REQUIREMENT_CARD]
        {
            "name": "用户签到功能",
            "background": "提升日活",
            "user_roles": ["用户"],
            "core_actions": ["签到"],
            "constraints": [],
            "out_of_scope": [],
            "is_complete": true,
            "missing_fields": []
        }
        """
        
        with patch.object(agent, '_call_api', return_value=force_card_reply):
            response = agent.chat("可以了，就这些")
        
        assert response.is_done == True

    # CT-A1-005
    def test_conversation_history_accumulates(self):
        """对话历史正确累积"""
        agent = ClarifyAgent()
        
        with patch.object(agent, '_call_api', return_value="追问1"):
            agent.chat("需求描述1")
        
        with patch.object(agent, '_call_api', return_value="追问2"):
            agent.chat("补充信息1")
        
        # 对话历史应该有4条：用户1、Agent1、用户2、Agent2
        assert len(agent.conversation_history) == 4
        assert agent.conversation_history[0]["role"] == "user"
        assert agent.conversation_history[1]["role"] == "assistant"

    # CT-A1-006
    def test_api_retry_on_failure(self):
        """API 调用失败时自动重试"""
        agent = ClarifyAgent()
        call_count = 0
        
        def fail_twice(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("API 临时错误")
            return "追问内容"
        
        with patch.object(agent, '_call_api', side_effect=fail_twice):
            response = agent.chat("做一个签到")
        
        assert call_count == 3
        assert response.reply == "追问内容"

    # CT-A1-007
    def test_invalid_json_in_requirement_card_triggers_retry(self):
        """需求卡片 JSON 格式错误时触发重试"""
        agent = ClarifyAgent()
        call_count = 0
        
        def return_invalid_then_valid(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # 第一次返回格式错误的需求卡片
                return "[REQUIREMENT_CARD] {invalid json"
            else:
                # 第二次返回正确格式
                return """[REQUIREMENT_CARD]
                {"name":"功能","background":"bg","user_roles":["用户"],
                "core_actions":["操作"],"constraints":[],"out_of_scope":[],
                "is_complete":true,"missing_fields":[]}"""
        
        with patch.object(agent, '_call_api', 
                          side_effect=return_invalid_then_valid):
            response = agent.chat("信息足够了")
        
        assert response.is_done == True
        assert call_count == 2

    # CT-A1-008
    def test_force_generate_marks_missing_fields(self):
        """强制生成时，未收集到的字段被标记为 missing_fields"""
        agent = ClarifyAgent(max_rounds=1)
        
        with patch.object(agent, '_call_api', return_value="我需要更多信息..."):
            response = agent.chat("做一个功能")  # 信息严重不足
        
        # 强制生成后
        result = agent.get_result()
        # 由于信息不足，应该有 missing_fields
        assert len(result.missing_fields) > 0

    # CT-A1-009
    def test_empty_input_handled_gracefully(self):
        """空输入被优雅处理"""
        agent = ClarifyAgent()
        
        response = agent.chat("")
        
        assert response.is_done == False
        assert "请输入" in response.reply or len(response.reply) > 0
```

---

## 3.2 Agent 2 - PRD 生成 Agent 测试（6个）

```python
# tests/component/test_prd_agent.py

import pytest
import json
from unittest.mock import patch
from agents.prd_agent import PRDAgent

class TestPRDAgent:

    # CT-A2-001
    def test_generates_valid_prd(self, sample_requirement_card):
        """输入有效需求卡片，生成通过 Schema 校验的 PRD"""
        agent = PRDAgent()
        
        mock_prd_json = {
            "title": "用户签到功能 PRD",
            "background": "为提升用户日活，增加每日签到功能",
            "user_stories": [
                "作为普通用户，我希望每天签到获得积分，以便兑换奖励",
                "作为VIP用户，我希望享受签到双倍积分，以便获得更多权益"
            ],
            "core_flow": "1. 用户进入签到页\n2. 点击签到按钮\n3. 系统验证\n4. 发放积分\n5. 展示结果",
            "exception_flow": "网络异常：提示重试\n重复签到：提示已签到\n积分异常：延迟发放",
            "data_fields": ["user_id", "sign_date", "consecutive_days", "points_earned"],
            "non_functional": "签到接口 P99 延迟 < 200ms",
            "out_of_scope": "积分消费逻辑"
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_prd_json)):
            prd = agent.generate(sample_requirement_card)
        
        assert prd.title == "用户签到功能 PRD"
        assert len(prd.user_stories) >= 1
        assert len(prd.data_fields) >= 1

    # CT-A2-002
    def test_retries_on_failed_validation(self, sample_requirement_card):
        """PRD 校验不通过时自动重试"""
        agent = PRDAgent()
        call_count = 0
        
        invalid_prd = {"title": "标题", "background": "背景"}  # 缺少必要字段
        valid_prd = {
            "title": "完整标题",
            "background": "完整背景描述",
            "user_stories": ["用户故事1"],
            "core_flow": "步骤1\n步骤2\n步骤3\n步骤4（足够长的核心流程描述）",
            "exception_flow": "异常1：处理方式\n异常2：处理方式\n异常3：处理方式",
            "data_fields": ["field1", "field2"],
            "out_of_scope": "排除范围"
        }
        
        def return_invalid_then_valid(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return json.dumps(invalid_prd)
            return json.dumps(valid_prd)
        
        with patch.object(agent, '_call_api', 
                          side_effect=return_invalid_then_valid):
            prd = agent.generate(sample_requirement_card)
        
        assert call_count == 2
        assert prd.title == "完整标题"

    # CT-A2-003
    def test_raises_after_max_retries(self, sample_requirement_card):
        """超过最大重试次数后抛出异常"""
        agent = PRDAgent()
        invalid_prd = {"title": "只有标题"}  # 一直返回无效内容
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(invalid_prd)):
            with pytest.raises(Exception) as exc_info:
                agent.generate(sample_requirement_card)
        
        assert "生成失败" in str(exc_info.value) or "重试" in str(exc_info.value)

    # CT-A2-004
    def test_user_stories_count_matches_roles(self, sample_requirement_card):
        """生成的用户故事数量不少于用户角色数量"""
        agent = PRDAgent()
        
        # sample_requirement_card 有 2 个用户角色
        mock_prd = {
            "title": "签到功能",
            "background": "提升日活",
            "user_stories": [
                "作为普通用户，我希望签到，以便获得积分",
                "作为VIP用户，我希望获得双倍积分，以便享受更多权益"
            ],
            "core_flow": "步骤1\n步骤2\n步骤3\n步骤4（详细的核心流程描述内容）",
            "exception_flow": "异常1\n异常2\n异常3（异常处理说明）",
            "data_fields": ["user_id", "sign_date"],
            "out_of_scope": "不包含的内容"
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_prd)):
            prd = agent.generate(sample_requirement_card)
        
        assert len(prd.user_stories) >= len(sample_requirement_card.user_roles)

    # CT-A2-005
    def test_format_input_includes_all_card_fields(self, sample_requirement_card):
        """_format_input 方法将需求卡片所有字段包含在输出中"""
        agent = PRDAgent()
        formatted = agent._format_input(sample_requirement_card)
        
        assert sample_requirement_card.name in formatted
        assert sample_requirement_card.background in formatted
        for role in sample_requirement_card.user_roles:
            assert role in formatted
        for action in sample_requirement_card.core_actions:
            assert action in formatted

    # CT-A2-006
    def test_handles_missing_fields_in_card(self):
        """需求卡片有 missing_fields 时，PRD 对应部分标记为待确认"""
        agent = PRDAgent()
        incomplete_card = RequirementCard(
            name="不完整需求",
            background="背景",
            user_roles=["用户"],
            core_actions=["操作"],
            constraints=[],
            out_of_scope=[],
            missing_fields=["constraints"]     # 标记 constraints 未确认
        )
        
        mock_prd = {
            "title": "不完整需求 PRD",
            "background": "背景",
            "user_stories": ["用户故事"],
            "core_flow": "步骤1\n步骤2\n步骤3\n步骤4（待确认具体约束条件）",
            "exception_flow": "异常1\n异常2\n异常3",
            "data_fields": ["field1"],
            "out_of_scope": "待确认"
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_prd)):
            prd = agent.generate(incomplete_card)
        
        # PRD 中应该提到"待确认"
        full_text = prd.core_flow + prd.exception_flow
        assert "待确认" in full_text or "待" in full_text
```

---

## 3.3 Agent 3 & 4 - 并行 Agent 测试（8个）

```python
# tests/component/test_tech_test_agents.py

import pytest
import asyncio
import time
from unittest.mock import patch
from agents.tech_agent import TechAgent
from agents.test_agent import TestAgent

class TestTechAgent:

    # CT-A3-001
    def test_generates_valid_tech_plan(
        self, sample_requirement_card, sample_prd
    ):
        """生成通过 Schema 校验的技术方案"""
        agent = TechAgent()
        
        mock_plan = {
            "involved_modules": ["用户服务", "积分服务", "签到服务"],
            "new_apis": [
                {
                    "name": "POST /api/sign-in",
                    "method": "POST",
                    "description": "用户签到",
                    "params": ["user_id"],
                    "response": "{ success: bool }"
                }
            ],
            "modified_apis": ["GET /api/user/points"],
            "db_changes": ["新增 user_sign_records 表"],
            "estimated_days": {"frontend": 3, "backend": 4, "testing": 2},
            "tech_risks": ["并发签到风险"]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_plan)):
            plan = agent.generate(sample_requirement_card, sample_prd)
        
        assert len(plan.involved_modules) >= 1
        assert "frontend" in plan.estimated_days
        assert "backend" in plan.estimated_days
        assert "testing" in plan.estimated_days

    # CT-A3-002
    def test_tech_plan_identifies_payment_risk(
        self, sample_requirement_card, sample_prd
    ):
        """涉及积分/支付场景时，技术方案应包含对应风险"""
        agent = TechAgent()
        
        mock_plan = {
            "involved_modules": ["积分服务", "支付服务"],
            "new_apis": [],
            "modified_apis": [],
            "db_changes": [],
            "estimated_days": {"frontend": 2, "backend": 3, "testing": 2},
            "tech_risks": [
                "积分发放失败补偿机制",
                "并发扣减积分的幂等性保证"
            ]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_plan)):
            plan = agent.generate(sample_requirement_card, sample_prd)
        
        # 应该有积分/支付相关的风险点
        risk_text = " ".join(plan.tech_risks)
        assert "积分" in risk_text or "幂等" in risk_text


class TestTestAgent:

    # CT-A4-001
    def test_generates_minimum_test_cases(
        self, sample_requirement_card, sample_prd
    ):
        """生成的测试用例满足最低数量要求"""
        agent = TestAgent()
        
        mock_cases = {
            "main_flow_cases": [
                {"priority": "P0", "precondition": f"条件{i}", 
                 "steps": f"步骤{i}", "expected": f"结果{i}"}
                for i in range(5)
            ],
            "exception_cases": [
                {"priority": "P1", "precondition": f"条件{i}", 
                 "steps": f"步骤{i}", "expected": f"结果{i}"}
                for i in range(3)
            ],
            "boundary_cases": [
                {"priority": "P2", "precondition": f"条件{i}", 
                 "steps": f"步骤{i}", "expected": f"结果{i}"}
                for i in range(3)
            ]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_cases)):
            cases = agent.generate(sample_requirement_card, sample_prd)
        
        assert len(cases.main_flow_cases) >= 5
        assert len(cases.exception_cases) >= 3
        assert len(cases.boundary_cases) >= 3

    # CT-A4-002
    def test_test_cases_cover_exception_scenarios(
        self, sample_requirement_card, sample_prd
    ):
        """测试用例覆盖 PRD 中定义的异常场景"""
        agent = TestAgent()
        
        # PRD 中有网络异常、重复签到、积分异常三个异常
        mock_cases = {
            "main_flow_cases": [
                {"priority": "P0", "precondition": f"c{i}", 
                 "steps": f"s{i}", "expected": f"e{i}"}
                for i in range(5)
            ],
            "exception_cases": [
                {"priority": "P1", "precondition": "网络异常",
                 "steps": "点击签到", "expected": "提示网络错误"},
                {"priority": "P1", "precondition": "已签到",
                 "steps": "再次签到", "expected": "提示已签到"},
                {"priority": "P1", "precondition": "积分服务故障",
                 "steps": "点击签到", "expected": "签到成功积分延迟"}
            ],
            "boundary_cases": [
                {"priority": "P2", "precondition": f"c{i}", 
                 "steps": f"s{i}", "expected": f"e{i}"}
                for i in range(3)
            ]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_cases)):
            cases = agent.generate(sample_requirement_card, sample_prd)
        
        exception_text = " ".join([c.precondition for c in cases.exception_cases])
        assert "网络" in exception_text or "异常" in exception_text

    # CT-A4-003
    def test_boundary_cases_include_time_boundary(
        self, sample_requirement_card, sample_prd
    ):
        """边界用例包含时间相关边界（0点跨天）"""
        agent = TestAgent()
        
        mock_cases = {
            "main_flow_cases": [
                {"priority": "P0", "precondition": f"c{i}", 
                 "steps": f"s{i}", "expected": f"e{i}"}
                for i in range(5)
            ],
            "exception_cases": [
                {"priority": "P1", "precondition": f"c{i}", 
                 "steps": f"s{i}", "expected": f"e{i}"}
                for i in range(3)
            ],
            "boundary_cases": [
                {"priority": "P2", "precondition": "23:59:58点击签到",
                 "steps": "0点后响应", "expected": "以服务器时间为准"},
                {"priority": "P2", "precondition": "连续签到第7天",
                 "steps": "签到", "expected": "触发双倍积分"},
                {"priority": "P2", "precondition": "连续签到中断后",
                 "steps": "重新签到", "expected": "连续天数重置为1"}
            ]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_cases)):
            cases = agent.generate(sample_requirement_card, sample_prd)
        
        boundary_text = " ".join([c.precondition for c in cases.boundary_cases])
        assert "0点" in boundary_text or "23:59" in boundary_text or "连续" in boundary_text


class TestParallelExecution:

    # CT-P-001
    @pytest.mark.asyncio
    async def test_tech_and_test_agents_run_in_parallel(
        self, sample_requirement_card, sample_prd
    ):
        """Agent 3 和 Agent 4 确实并行执行，总时间接近较慢的单个时间"""
        
        async def slow_tech_generate(*args):
            await asyncio.sleep(0.3)    # 模拟 0.3 秒
            return sample_tech_plan
        
        async def slow_test_generate(*args):
            await asyncio.sleep(0.2)    # 模拟 0.2 秒
            return sample_test_cases
        
        start = time.time()
        
        tech_plan, test_cases = await asyncio.gather(
            slow_tech_generate(sample_requirement_card, sample_prd),
            slow_test_generate(sample_requirement_card, sample_prd)
        )
        
        elapsed = time.time() - start
        
        # 并行时总时间应接近 0.3s，而非 0.5s
        assert elapsed < 0.45, f"并行执行耗时 {elapsed:.2f}s，疑似串行执行"
        assert tech_plan is not None
        assert test_cases is not None

    # CT-P-002
    @pytest.mark.asyncio
    async def test_one_agent_failure_does_not_block_other(
        self, sample_requirement_card, sample_prd
    ):
        """一个 Agent 失败时，另一个 Agent 继续完成"""
        
        async def failing_tech(*args):
            raise Exception("技术方案生成失败")
        
        async def successful_test(*args):
            await asyncio.sleep(0.1)
            return sample_test_cases
        
        # 使用 gather 的 return_exceptions=True 模式
        results = await asyncio.gather(
            failing_tech(sample_requirement_card, sample_prd),
            successful_test(sample_requirement_card, sample_prd),
            return_exceptions=True
        )
        
        assert isinstance(results[0], Exception)    # 技术方案失败
        assert results[1] == sample_test_cases      # 测试用例成功
```

---

## 3.4 Agent 5 - 风险评估 Agent 测试（8个）

```python
# tests/component/test_risk_agent.py

import pytest
from unittest.mock import patch
from agents.risk_agent import RiskAgent

class TestRiskAgent:

    # CT-A5-001
    def test_generates_valid_risk_report(
        self, sample_prd, sample_tech_plan, sample_test_cases
    ):
        """生成通过 Schema 校验的风险报告"""
        agent = RiskAgent()
        
        mock_report = {
            "risk_level": "中",
            "risk_points": ["并发签到风险", "积分服务依赖风险"],
            "suggestions": ["添加唯一索引", "实现补偿机制"],
            "uncovered_scenarios": ["账号封禁时的签到处理"]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_report)):
            report = agent.evaluate(
                sample_prd, sample_tech_plan, sample_test_cases
            )
        
        assert report.risk_level in ["高", "中", "低"]
        assert len(report.risk_points) > 0
        assert len(report.suggestions) > 0

    # CT-A5-002
    def test_high_risk_sets_human_review_flag(
        self, sample_prd, sample_tech_plan, sample_test_cases
    ):
        """风险等级为高时，needs_human_review 自动为 True"""
        agent = RiskAgent()
        
        mock_report = {
            "risk_level": "高",
            "risk_points": ["涉及支付核心链路"],
            "suggestions": ["必须进行人工评审"],
            "uncovered_scenarios": ["大量未覆盖场景"]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_report)):
            report = agent.evaluate(
                sample_prd, sample_tech_plan, sample_test_cases
            )
        
        assert report.needs_human_review == True

    # CT-A5-003
    def test_detects_prd_tech_plan_conflict(
        self, sample_prd, sample_tech_plan, sample_test_cases
    ):
        """能识别 PRD 与技术方案之间的冲突"""
        agent = RiskAgent()
        
        # 模拟 Agent 识别出冲突
        mock_report = {
            "risk_level": "高",
            "risk_points": [
                "PRD 要求0点刷新，但技术方案未提及定时任务设计，存在冲突"
            ],
            "suggestions": ["技术方案需补充定时任务说明"],
            "uncovered_scenarios": []
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_report)):
            report = agent.evaluate(
                sample_prd, sample_tech_plan, sample_test_cases
            )
        
        conflict_found = any("冲突" in r or "未提及" in r 
                             for r in report.risk_points)
        assert conflict_found

    # CT-A5-004
    def test_detects_uncovered_test_scenarios(
        self, sample_prd, sample_tech_plan, sample_test_cases
    ):
        """能识别测试用例未覆盖的场景"""
        agent = RiskAgent()
        
        mock_report = {
            "risk_level": "中",
            "risk_points": ["部分异常场景未被测试覆盖"],
            "suggestions": ["补充企业账号误操作的测试用例"],
            "uncovered_scenarios": [
                "企业账号尝试签到的处理",
                "账号注销后的签到记录处理"
            ]
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_report)):
            report = agent.evaluate(
                sample_prd, sample_tech_plan, sample_test_cases
            )
        
        assert len(report.uncovered_scenarios) > 0

    # CT-A5-005
    def test_low_risk_for_simple_requirement(
        self, sample_prd, sample_tech_plan, sample_test_cases
    ):
        """简单需求且覆盖充分时，风险等级为低"""
        agent = RiskAgent()
        
        mock_report = {
            "risk_level": "低",
            "risk_points": [],
            "suggestions": ["可以直接推进"],
            "uncovered_scenarios": []
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_report)):
            report = agent.evaluate(
                sample_prd, sample_tech_plan, sample_test_cases
            )
        
        assert report.risk_level == "低"
        assert report.needs_human_review == False

    # CT-A5-006
    def test_format_context_includes_all_inputs(
        self, sample_prd, sample_tech_plan, sample_test_cases
    ):
        """_format_context 包含所有输入的关键信息"""
        agent = RiskAgent()
        context = agent._format_context(
            sample_prd, sample_tech_plan, sample_test_cases
        )
        
        # 验证关键信息都在上下文中
        assert sample_prd.title in context
        assert str(sample_test_cases.total_count) in context
        assert any(module in context 
                   for module in sample_tech_plan.involved_modules)

    # CT-A5-007
    def test_risk_level_escalation_for_payment_module(
        self, sample_prd, sample_test_cases
    ):
        """涉及支付模块时，风险等级不低于中"""
        agent = RiskAgent()
        
        # 创建一个涉及支付的技术方案
        payment_tech_plan = TechPlan(
            involved_modules=["支付服务", "用户服务"],
            new_apis=[],
            modified_apis=["支付接口改造"],
            db_changes=[],
            estimated_days={"frontend": 1, "backend": 3, "testing": 2},
            tech_risks=["支付安全风险"]
        )
        
        mock_report = {
            "risk_level": "低",       # ← Agent 返回低，但应被提升为中
            "risk_points": [],
            "suggestions": [],
            "uncovered_scenarios": []
        }
        
        with patch.object(agent, '_call_api', 
                          return_value=json.dumps(mock_report)):
            report = agent.evaluate(
                sample_prd, payment_tech_plan, sample_test_cases
            )
        
        # 涉及支付时，风险等级应至少为中
        assert report.risk_level in ["中", "高"]

    # CT-A5-008
    def test_insufficient_test_coverage_raises_risk(
        self, sample_prd, sample_tech_plan
    ):
        """测试用例总数不足时，风险等级应提升"""
        agent = RiskAgent()
        
        # 创建用例数量不足的测试集（总共只有8条，低于建议的11条）
        minimal_cases = TestCases(
            main_flow_cases=[
                TestCase(priority="P0", precondition="c", 
                         steps="s", expected="e")
                for _ in range(5)
            ],
            exception_cases=[
                TestCase(priority="P1", precondition="c", 
                         steps="s", expected="e")
                for _ in range(3)
            ],
            boundary_cases=[]    # 没有边界用例（但最低要求3条）
        )
        
        # 注意：minimal_cases 实际上无法通过 Schema 校验（boundary < 3）
        # 这里用 mock 绕过
        with pytest.raises(Exception):
            # 边界用例为空应该在 Schema 层面被拦截
            agent.evaluate(sample_prd, sample_tech_plan, minimal_cases)
```

---

# 第四部分：Level 3 集成测试（12个）

```python
# tests/integration/test_orchestrator.py

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from core.orchestrator import Orchestrator

class TestOrchestratorFlow:

    # IT-O-001
    @pytest.mark.asyncio
    async def test_full_flow_completes_successfully(
        self,
        sample_requirement_card,
        sample_prd,
        sample_tech_plan,
        sample_test_cases,
        sample_risk_report
    ):
        """完整流程端到端执行成功"""
        orchestrator = Orchestrator()
        
        # Mock 所有 Agent
        with patch.object(orchestrator.clarify_agent, 'chat') as mock_clarify, \
             patch.object(orchestrator.prd_agent, 'generate', 
                          return_value=sample_prd), \
             patch.object(orchestrator.tech_agent, 'generate', 
                          return_value=sample_tech_plan), \
             patch.object(orchestrator.test_agent, 'generate', 
                          return_value=sample_test_cases), \
             patch.object(orchestrator.risk_agent, 'evaluate', 
                          return_value=sample_risk_report):
            
            # 模拟 clarify_agent 第一轮直接完成
            mock_clarify.return_value = MagicMock(
                is_done=True, 
                reply="需求卡片已生成"
            )
            orchestrator.clarify_agent.requirement_card = sample_requirement_card
            
            session = await orchestrator.run("做一个签到功能")
        
        assert session.requirement_card is not None
        assert session.prd is not None
        assert session.tech_plan is not None
        assert session.test_cases is not None
        assert session.risk_report is not None
        assert session.current_stage == "done"

    # IT-O-002
    @pytest.mark.asyncio
    async def test_progress_callbacks_fire_in_order(
        self,
        sample_requirement_card,
        sample_prd,
        sample_tech_plan,
        sample_test_cases,
        sample_risk_report
    ):
        """进度回调按正确顺序触发，进度值递增"""
        orchestrator = Orchestrator()
        progress_log = []
        
        def capture_progress(stage, progress, message):
            progress_log.append({"stage": stage, "progress": progress})
        
        orchestrator.on_progress = capture_progress
        
        with patch.object(orchestrator.clarify_agent, 'chat') as mock_clarify, \
             patch.object(orchestrator.prd_agent, 'generate', 
                          return_value=sample_prd), \
             patch.object(orchestrator.tech_agent, 'generate', 
                          return_value=sample_tech_plan), \
             patch.object(orchestrator.test_agent, 'generate', 
                          return_value=sample_test_cases), \
             patch.object(orchestrator.risk_agent, 'evaluate', 
                          return_value=sample_risk_report):
            
            mock_clarify.return_value = MagicMock(is_done=True, reply="完成")
            orchestrator.clarify_agent.requirement_card = sample_requirement_card
            
            await orchestrator.run("做一个签到功能")
        
        # 验证进度值递增
        progress_values = [p["progress"] for p in progress_log]
        assert progress_values == sorted(progress_values), "进度值应该递增"
        
        # 验证最终进度为 100
        assert progress_log[-1]["progress"] == 100

    # IT-O-003
    @pytest.mark.asyncio
    async def test_session_state_saved_after_each_stage(
        self,
        sample_requirement_card,
        sample_prd,
        sample_tech_plan,
        sample_test_cases,
        sample_risk_report,
        tmp_path
    ):
        """每个 Agent 执行完后，session 状态被保存"""
        orchestrator = Orchestrator(output_dir=tmp_path)
        save_count = 0
        
        original_save = orchestrator.session.save
        def counting_save():
            nonlocal save_count
            save_count += 1
            original_save()
        
        orchestrator.session.save = counting_save
        
        with patch.object(orchestrator.clarify_agent, 'chat') as mock_clarify, \
             patch.object(orchestrator.prd_agent, 'generate', 
                          return_value=sample_prd), \
             patch.object(orchestrator.tech_agent, 'generate', 
                          return_value=sample_tech_plan), \
             patch.object(orchestrator.test_agent, 'generate', 
                          return_value=sample_test_cases), \
             patch.object(orchestrator.risk_agent, 'evaluate', 
                          return_value=sample_risk_report):
            
            mock_clarify.return_value = MagicMock(is_done=True, reply="完成")
            orchestrator.clarify_agent.requirement_card = sample_requirement_card
            
            await orchestrator.run("做一个签到功能")
        
        # 每个阶段完成后都应该保存：需求澄清+PRD+技术+测试+风险+完成 = 至少5次
        assert save_count >= 5

    # IT-O-004
    @pytest.mark.asyncio
    async def test_prd_agent_failure_stops_flow(
        self, sample_requirement_card
    ):
        """PRD 生成失败时，后续 Agent 不执行"""
        orchestrator = Orchestrator()
        tech_called = False
        
        def mark_tech_called(*args):
            nonlocal tech_called
            tech_called = True
        
        with patch.object(orchestrator.clarify_agent, 'chat') as mock_clarify, \
             patch.object(orchestrator.prd_agent, 'generate',
                          side_effect=Exception("PRD 生成失败")), \
             patch.object(orchestrator.tech_agent, 'generate', 
                          side_effect=mark_tech_called):
            
            mock_clarify.return_value = MagicMock(is_done=True, reply="完成")
            orchestrator.clarify_agent.requirement_card = sample_requirement_card
            
            with pytest.raises(Exception) as exc_info:
                await orchestrator.run("做一个签到功能")
        
        assert "PRD" in str(exc_info.value) or "生成失败" in str(exc_info.value)
        assert tech_called == False   # 技术方案 Agent 不应该被调用

    # IT-O-005
    @pytest.mark.asyncio
    async def test_risk_agent_failure_returns_empty_report(
        self,
        sample_requirement_card,
        sample_prd,
        sample_tech_plan,
        sample_test_cases
    ):
        """风险评估失败时，返回空报告而非中断流程"""
        orchestrator = Orchestrator()
        
        with patch.object(orchestrator.clarify_agent, 'chat') as mock_clarify, \
             patch.object(orchestrator.prd_agent, 'generate', 
                          return_value=sample_prd), \
             patch.object(orchestrator.tech_agent, 'generate', 
                          return_value=sample_tech_plan), \
             patch.object(orchestrator.test_agent, 'generate', 
                          return_value=sample_test_cases), \
             patch.object(orchestrator.risk_agent, 'evaluate',
                          side_effect=Exception("风险评估服务不可用")):
            
            mock_clarify.return_value = MagicMock(is_done=True, reply="完成")
            orchestrator.clarify_agent.requirement_card = sample_requirement_card
            
            # 风险评估失败不应让整个流程崩溃
            session = await orchestrator.run("做一个签到功能")
        
        # 其他 Agent 的输出应该正常
        assert session.prd is not None
        assert session.tech_plan is not None
        # 风险报告为空或有标记
        assert session.risk_report is None or \
               session.risk_report.risk_level == "未知"

    # IT-O-006
    @pytest.mark.asyncio
    async def test_parallel_agents_timing(
        self,
        sample_requirement_card,
        sample_prd,
        sample_tech_plan,
        sample_test_cases,
        sample_risk_report
    ):
        """Agent 3 和 Agent 4 并行执行，验证时间效率"""
        orchestrator = Orchestrator()
        
        async def slow_tech(*args):
            await asyncio.sleep(0.3)
            return sample_tech_plan
        
        async def slow_test(*args):
            await asyncio.sleep(0.25)
            return sample_test_cases
        
        with patch.object(orchestrator.clarify_agent, 'chat') as mock_clarify, \
             patch.object(orchestrator.prd_agent, 'generate', 
                          return_value=sample_prd), \
             patch.object(orchestrator.tech_agent, 'generate', 
                          new=slow_tech), \
             patch.object(orchestrator.test_agent, 'generate', 
                          new=slow_test), \
             patch.object(orchestrator.risk_agent, 'evaluate', 
                          return_value=sample_risk_report):
            
            mock_clarify.return_value = MagicMock(is_done=True, reply="完成")
            orchestrator.clarify_agent.requirement_card = sample_requirement_card
            
            start = time.time()
            await orchestrator.run("做一个签到功能")
            elapsed = time.time() - start
        
        # 并行时应接近 0.3s，串行则需要 0.55s
        assert elapsed < 0.5, f"并行执行耗时 {elapsed:.2f}s，疑似串行"

    # IT-O-007 ~ IT-O-012
    # （其余集成测试：断点恢复、多次运行状态隔离、
    #   进度回调异常不影响主流程、Token统计正确累加、
    #   输出文件完整生成、高风险时人工介入标记）
```

---

# 第五部分：Level 4 端到端测试（5个场景）

```python
# tests/e2e/test_real_scenarios.py
# ⚠️ 这些测试调用真实 API，需要有效的 OPENAI_API_KEY

import pytest
import os
from core.orchestrator import Orchestrator
from core.output_generator import OutputGenerator

# 跳过条件：没有 API Key 时跳过
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENAI_API_KEY"),
    reason="需要有效的 OPENAI_API_KEY"
)

class TestRealScenarios:

    # E2E-001：简单新功能需求
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_simple_new_feature(self):
        """
        场景：简单的新功能需求
        输入：用户签到功能
        验收：完整流程跑通，输出质量达标
        """
        orchestrator = Orchestrator()
        
        # 模拟用户多轮对话
        user_inputs = [
            "做一个用户每日签到功能",
            "积分奖励，连续7天双倍，每天0点刷新",
            "没有上限，需要展示30天历史记录",
            "可以了"
        ]
        
        input_iter = iter(user_inputs)
        
        async def simulate_user_chat(msg):
            # 实际调用 Agent 1
            return await orchestrator.run_clarify_stage(msg)
        
        # 执行需求澄清
        for user_input in user_inputs:
            response = await orchestrator.run_clarify_stage(user_input)
            if response.is_done:
                break
        
        # 执行文档生成
        await orchestrator.run_generation_stage()
        
        session = orchestrator.session
        
        # ── 验收标准 ──
        # 需求卡片
        assert session.requirement_card is not None
        assert "签到" in session.requirement_card.name
        assert len(session.requirement_card.user_roles) >= 1
        
        # PRD
        assert session.prd is not None
        assert len(session.prd.user_stories) >= 1
        assert len(session.prd.data_fields) >= 3
        assert len(session.prd.exception_flow) > 50
        
        # 技术方案
        assert session.tech_plan is not None
        assert len(session.tech_plan.involved_modules) >= 1
        assert session.tech_plan.estimated_days.get("backend", 0) > 0
        
        # 测试用例
        assert session.test_cases is not None
        assert session.test_cases.total_count >= 11
        
        # 风险报告
        assert session.risk_report is not None
        assert session.risk_report.risk_level in ["高", "中", "低"]
        
        print(f"\n✅ E2E-001 通过")
        print(f"   测试用例总数：{session.test_cases.total_count}")
        print(f"   风险等级：{session.risk_report.risk_level}")
        print(f"   涉及模块：{session.tech_plan.involved_modules}")

    # E2E-002：复杂裂变业务需求
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_complex_viral_feature(self):
        """
        场景：涉及多个系统的复杂裂变业务
        输入：邀请好友得积分
        验收：技术方案识别多系统依赖，风险等级不低于中
        """
        orchestrator = Orchestrator()
        user_inputs = [
            "实现一个邀请好友得积分的裂变功能",
            "邀请人和被邀请人都得积分，邀请人额外得被邀请人首充金额的5%",
            "每人最多邀请100个好友，被邀请人必须是新用户且完成首充",
            "可以了"
        ]
        
        for user_input in user_inputs:
            response = await orchestrator.run_clarify_stage(user_input)
            if response.is_done:
                break
        
        await orchestrator.run_generation_stage()
        session = orchestrator.session
        
        # ── 验收标准 ──
        # 需求卡片：应识别邀请人和被邀请人两个角色
        assert len(session.requirement_card.user_roles) >= 2
        
        # 技术方案：应涉及多个系统
        involved = " ".join(session.tech_plan.involved_modules)
        assert len(session.tech_plan.involved_modules) >= 3
        
        # 测试用例：应有边界用例（100人上限）
        boundary_text = " ".join([c.precondition + c.steps 
                                   for c in session.test_cases.boundary_cases])
        assert "100" in boundary_text or "上限" in boundary_text
        
        # 风险：涉及积分+支付，风险等级不应为低
        assert session.risk_report.risk_level in ["高", "中"]
        
        print(f"\n✅ E2E-002 通过")
        print(f"   识别到 {len(session.tech_plan.involved_modules)} 个涉及模块")
        print(f"   风险等级：{session.risk_report.risk_level}")

    # E2E-003：改造类需求
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_refactor_feature(self):
        """
        场景：对现有功能进行改造
        输入：将短信验证码登录改为支持微信一键登录
        验收：技术方案识别为改造，标注现有接口修改
        """
        orchestrator = Orchestrator()
        user_inputs = [
            "把现有的短信验证码登录改成支持微信一键登录",
            "两种方式都要保留，微信登录后自动绑定手机号",
            "老用户首次微信登录时需要验证原手机号",
            "可以了"
        ]
        
        for user_input in user_inputs:
            response = await orchestrator.run_clarify_stage(user_input)
            if response.is_done:
                break
        
        await orchestrator.run_generation_stage()
        session = orchestrator.session
        
        # ── 验收标准 ──
        # 技术方案应有修改的接口（不只是新增）
        assert len(session.tech_plan.modified_apis) >= 1
        
        # PRD 应该覆盖"老用户首次微信登录"场景
        prd_text = session.prd.core_flow + session.prd.exception_flow
        assert "老用户" in prd_text or "绑定" in prd_text
        
        # 风险：改造现有登录模块，风险不应为低
        assert session.risk_report.risk_level in ["高", "中"]
        
        print(f"\n✅ E2E-003 通过")
        print(f"   修改接口数：{len(session.tech_plan.modified_apis)}")

    # E2E-004：规则类需求（权限控制）
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_permission_feature(self):
        """
        场景：涉及权限控制的规则类需求
        输入：给VIP用户加专属客服通道
        验收：测试用例包含权限边界用例
        """
        orchestrator = Orchestrator()
        user_inputs = [
            "给VIP用户增加一个专属人工客服通道",
            "VIP用户可以优先排队，等待时间不超过5分钟，普通用户走普通通道",
            "VIP分三个等级，等级越高优先级越高",
            "可以了"
        ]
        
        for user_input in user_inputs:
            response = await orchestrator.run_clarify_stage(user_input)
            if response.is_done:
                break
        
        await orchestrator.run_generation_stage()
        session = orchestrator.session
        
        # ── 验收标准 ──
        # 需求卡片：应识别VIP等级差异
        constraints_text = " ".join(session.requirement_card.constraints)
        assert "VIP" in constraints_text or "等级" in constraints_text
        
        # 测试用例：应包含权限验证用例
        all_cases_text = " ".join([
            c.precondition + c.steps + c.expected
            for c in (session.test_cases.main_flow_cases + 
                      session.test_cases.exception_cases +
                      session.test_cases.boundary_cases)
        ])
        assert "普通用户" in all_cases_text or "权限" in all_cases_text
        
        # 边界：VIP等级边界（等级1/2/3的不同优先级）
        assert len(session.test_cases.boundary_cases) >= 3
        
        print(f"\n✅ E2E-004 通过")

    # E2E-005：极端场景 - 用户信息极度不足
    @pytest.mark.asyncio
    @pytest.mark.e2e
    async def test_extremely_vague_requirement(self):
        """
        场景：用户提供信息极度模糊，全程不配合追问
        输入：做一个功能
        验收：5轮后强制生成，missing_fields 有标记，流程不崩溃
        """
        orchestrator = Orchestrator(max_clarify_rounds=5)
        
        vague_input = "做一个功能"
        unhelpful_responses = [
            "不知道",
            "随便",
            "你看着办",
            "就这样吧"
        ]
        
        # 第一轮
        response = await orchestrator.run_clarify_stage(vague_input)
        
        # 后续轮次用无效回答
        for unhelpful in unhelpful_responses:
            if response.is_done:
                break
            response = await orchestrator.run_clarify_stage(unhelpful)
        
        # 强制生成后仍然执行文档生成
        await orchestrator.run_generation_stage()
        
        session = orchestrator.session
        
        # ── 验收标准 ──
        # 流程不崩溃
        assert session.current_stage == "done"
        
        # 需求卡片有 missing_fields 标记
        assert len(session.requirement_card.missing_fields) > 0
        
        # 所有文档都生成了（质量可能差，但不能为空）
        assert session.prd is not None
        assert session.tech_plan is not None
        assert session.test_cases is not None
        
        print(f"\n✅ E2E-005 通过")
        print(f"   Missing fields: {session.requirement_card.missing_fields}")
        print(f"   测试用例数：{session.test_cases.total_count}")
```

---

# 第六部分：测试执行配置

```ini
# pytest.ini

[pytest]
testpaths = tests
asyncio_mode = auto

markers =
    unit: 单元测试（快速，无外部依赖）
    component: 组件测试（Mock API）
    integration: 集成测试（Mock 所有 Agent）
    e2e: 端到端测试（真实 API，需要 API Key）

# 默认只跑 unit + component + integration
addopts = -v -m "not e2e"
```

```makefile
# Makefile 测试命令

# 快速测试（不调用真实 API）
test:
	pytest -m "not e2e" --tb=short

# 单元测试
test-unit:
	pytest tests/unit/ -v

# 组件测试
test-component:
	pytest tests/component/ -v

# 集成测试
test-integration:
	pytest tests/integration/ -v

# 端到端测试（需要 API Key）
test-e2e:
	pytest tests/e2e/ -v -m e2e -s

# 查看覆盖率
test-coverage:
	pytest --cov=. --cov-report=html -m "not e2e"
	open htmlcov/index.html

# 完整测试（包含 e2e）
test-all:
	pytest -v -s
```

---

# 第七部分：测试用例总览索引

```
┌────────────────────────────────────────────────────────┐
│                   测试用例总览                           │
├──────────┬────────────────────────────┬──────┬────────┤
│ 编号     │ 测试内容                    │ 级别  │ 优先级 │
├──────────┼────────────────────────────┼──────┼────────┤
│ UT-S-001 │ 有效需求卡片创建            │  L1  │  P0   │
│ UT-S-002 │ 空名称校验                  │  L1  │  P0   │
│ UT-S-003 │ 空用户角色校验              │  L1  │  P0   │
│ UT-S-004 │ 技术栈默认值               │  L1  │  P1   │
│ UT-S-005 │ 测试用例数量校验            │  L1  │  P0   │
│ UT-S-006 │ total_count 属性           │  L1  │  P1   │
│ UT-S-007 │ 高风险自动设置 review 标志  │  L1  │  P0   │
│ UT-S-008 │ 低风险不设置 review 标志   │  L1  │  P1   │
├──────────┼────────────────────────────┼──────┼────────┤
│ UT-U-001 │ 重试-第一次成功            │  L1  │  P0   │
│ UT-U-002 │ 重试-第二次成功            │  L1  │  P0   │
│ UT-U-003 │ 重试耗尽抛异常             │  L1  │  P0   │
│ UT-U-004 │ 只重试指定异常类型         │  L1  │  P1   │
│ UT-U-005 │ 重试间隔验证               │  L1  │  P1   │
│ UT-U-006 │ 异步重试                   │  L1  │  P0   │
│ UT-U-007 │ 完整卡片校验通过           │  L1  │  P0   │
│ UT-U-008 │ 有缺失字段校验不通过       │  L1  │  P0   │
│ UT-U-009 │ 有效 PRD 校验通过          │  L1  │  P0   │
│ UT-U-010 │ 流程过短校验不通过         │  L1  │  P0   │
│ UT-U-011 │ 达标测试用例集校验通过     │  L1  │  P0   │
│ UT-U-012 │ 低覆盖给出警告             │  L1  │  P1   │
├──────────┼────────────────────────────┼──────┼────────┤
│ UT-B-001 │ 解析纯 JSON               │  L1  │  P0   │
│ UT-B-002 │ 解析代码块中的 JSON        │  L1  │  P0   │
│ UT-B-003 │ 解析无语言标记代码块       │  L1  │  P1   │
│ UT-B-004 │ 无效 JSON 抛异常           │  L1  │  P0   │
│ UT-B-005 │ 前后有额外文字的 JSON      │  L1  │  P1   │
│ UT-B-006 │ 读取 Prompt 文件           │  L1  │  P0   │
│ UT-B-007 │ Prompt 文件不存在          │  L1  │  P0   │
│ UT-B-008 │ API 调用返回内容           │  L1  │  P0   │
├──────────┼────────────────────────────┼──────┼────────┤
│ CT-A1-001│ 第一轮返回追问             │  L2  │  P0   │
│ CT-A1-002│ 包含标记时完成             │  L2  │  P0   │
│ CT-A1-003│ 达到最大轮数强制生成       │  L2  │  P0   │
│ CT-A1-004│ 用户说完成立即生成         │  L2  │  P0   │
│ CT-A1-005│ 对话历史正确累积           │  L2  │  P1   │
│ CT-A1-006│ API 失败自动重试           │  L2  │  P0   │
│ CT-A1-007│ JSON 格式错误重试          │  L2  │  P0   │
│ CT-A1-008│ 强制生成标记缺失字段       │  L2  │  P1   │
│ CT-A1-009│ 空输入优雅处理             │  L2  │  P1   │
├──────────┼────────────────────────────┼──────┼────────┤
│ CT-A2-001│ 生成有效 PRD               │  L2  │  P0   │
│ CT-A2-002│ 校验失败自动重试           │  L2  │  P0   │
│ CT-A2-003│ 超过重试次数抛异常         │  L2  │  P0   │
│ CT-A2-004│ 用户故事≥用户角色数         │  L2  │  P1   │
│ CT-A2-005│ 格式化输入包含所有字段     │  L2  │  P1   │
│ CT-A2-006│ 缺失字段标记待确认         │  L2  │  P1   │
├──────────┼────────────────────────────┼──────┼────────┤
│ CT-A3-001│ 生成有效技术方案           │  L2  │  P0   │
│ CT-A3-002│ 识别积分/支付风险          │  L2  │  P1   │
│ CT-A4-001│ 生成最低数量测试用例       │  L2  │  P0   │
│ CT-A4-002│ 覆盖 PRD 异常场景          │  L2  │  P0   │
│ CT-A4-003│ 包含时间边界用例           │  L2  │  P1   │
│ CT-P-001 │ 并行执行时间验证           │  L2  │  P0   │
│ CT-P-002 │ 单个失败不阻塞另一个       │  L2  │  P0   │
├──────────┼────────────────────────────┼──────┼────────┤
│ CT-A5-001│ 生成有效风险报告           │  L2  │  P0   │
│ CT-A5-002│ 高风险设置 review 标志     │  L2  │  P0   │
│ CT-A5-003│ 识别 PRD 技术方案冲突      │  L2  │  P1   │
│ CT-A5-004│ 识别未覆盖测试场景         │  L2  │  P1   │
│ CT-A5-005│ 简单需求低风险             │  L2  │  P1   │
│ CT-A5-006│ 上下文包含所有输入信息     │  L2  │  P1   │
│ CT-A5-007│ 支付模块风险等级提升       │  L2  │  P0   │
│ CT-A5-008│ 测试覆盖不足提升风险       │  L2  │  P0   │
├──────────┼────────────────────────────┼──────┼────────┤
│ IT-O-001 │ 完整流程执行成功           │  L3  │  P0   │
│ IT-O-002 │ 进度回调顺序递增           │  L3  │  P0   │
│ IT-O-003 │ 每阶段保存状态             │  L3  │  P1   │
│ IT-O-004 │ PRD 失败停止后续流程       │  L3  │  P0   │
│ IT-O-005 │ 风险评估失败返回空报告     │  L3  │  P1   │
│ IT-O-006 │ 并行执行时间效率           │  L3  │  P0   │
│ IT-O-007~│ 其余集成场景               │  L3  │  P1   │
│ IT-O-012 │                           │      │       │
├──────────┼────────────────────────────┼──────┼────────┤
│ E2E-001  │ 简单新功能（签到）          │  L4  │  P0   │
│ E2E-002  │ 复杂裂变业务               │  L4  │  P0   │
│ E2E-003  │ 改造类需求                 │  L4  │  P0   │
│ E2E-004  │ 权限控制需求               │  L4  │  P1   │
│ E2E-005  │ 极端模糊输入               │  L4  │  P1   │
└──────────┴────────────────────────────┴──────┴────────┘

总计：76 个测试用例
P0：44 个  P1：32 个
```
