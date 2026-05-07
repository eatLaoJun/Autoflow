# 需求全流程自动化 Agent 系统
## 完整需求文档 & 任务列表

---

# 第一部分：产品需求文档（PRD）

---

## 1. 项目概述

### 1.1 项目背景

在产品研发团队中，一个需求从"业务方口头描述"到"开发可执行的文档"，通常需要经历以下人工环节：

```
业务方描述需求（模糊）
    → PM 反复沟通澄清（1-3天）
    → PM 撰写 PRD（1-2天）
    → 技术评审会议（半天）
    → 开发撰写技术方案（1天）
    → 测试撰写测试用例（1天）
    → 风险评审（半天）
    
总计：4-8 个工作日，大量时间花在文档传递和沟通对齐上
```

这个过程存在三个核心问题：

- **信息损耗**：需求在口头传递过程中容易失真
- **重复劳动**：PRD → 技术方案 → 测试用例的内容高度重叠，却需要三个角色分别撰写
- **变更成本高**：需求变更时，所有下游文档需要手动同步，容易遗漏

### 1.2 项目目标

构建一个由多个 Agent 协同驱动的需求全流程自动化系统，实现：

| 目标 | 当前状态 | 目标状态 |
|------|---------|---------|
| 需求澄清时间 | 1-3 天 | 10-30 分钟 |
| PRD 初稿生成 | 1-2 天 | 自动生成 |
| 技术方案初稿 | 1 天 | 自动生成 |
| 测试用例初稿 | 1 天 | 自动生成 |
| 风险评估 | 半天会议 | 自动输出报告 |

### 1.3 项目范围

**MVP 范围内：**
- 5 个核心 Agent 的实现
- 命令行交互界面
- Streamlit Web UI
- Markdown 格式报告输出
- 本地 JSON 中间状态存储

**MVP 范围外（后续迭代）：**
- Jira / Confluence 真实集成
- 代码仓库扫描
- 变更同步 Agent
- 多用户协作
- 历史需求库检索

---

## 2. 用户画像

### 2.1 主要用户

```
用户 A：产品经理
  痛点：需求澄清和文档撰写耗时太长
  期望：输入粗糙需求，快速得到可用的 PRD 初稿
  使用频率：每周 2-5 次

用户 B：开发负责人
  痛点：技术方案需要从头撰写，与 PRD 内容高度重叠
  期望：基于 PRD 自动得到技术方案框架
  使用频率：每周 1-3 次

用户 C：测试负责人
  痛点：测试用例需要从 PRD 中手动提取场景
  期望：自动生成覆盖全面的测试用例清单
  使用频率：每周 1-3 次
```

### 2.2 典型使用场景

```
场景 1：新功能需求
  输入："老板说要做一个用户邀请好友得积分的功能"
  期望输出：完整的需求文档包（PRD + 技术方案 + 测试用例 + 风险报告）

场景 2：功能改造需求
  输入："现在的支付流程太复杂了，要简化成一步支付"
  期望输出：同上，并重点标注改造涉及的模块风险

场景 3：规则类需求
  输入："要给 VIP 用户加一个专属客服通道"
  期望输出：同上，重点覆盖权限控制和异常场景
```

---

## 3. 系统架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    用户交互层                          │
│         Streamlit UI  /  命令行 CLI                   │
└─────────────────────┬───────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────┐
│                   编排控制层                           │
│              Orchestrator（主控）                      │
│   - 管理 Agent 执行顺序                               │
│   - 传递上下文数据                                     │
│   - 监控执行状态                                       │
│   - 处理异常和重试                                     │
└──────┬──────┬──────┬──────┬──────┬──────────────────┘
       │      │      │      │      │
┌──────▼─┐ ┌──▼───┐ ┌▼────┐ ┌▼────┐ ┌▼──────┐
│Agent 1 │ │Agent │ │Agent│ │Agent│ │Agent  │
│需求澄清│ │  2   │ │  3  │ │  4  │ │   5   │
│        │ │ PRD  │ │技术 │ │测试 │ │风险   │
│        │ │ 生成 │ │方案 │ │用例 │ │评估   │
└────────┘ └──────┘ └─────┘ └─────┘ └───────┘
                              ↑       ↑
                           并行执行（Agent 3 & 4）
┌─────────────────────────────────────────────────────┐
│                    数据存储层                          │
│     本地 JSON（中间状态）  +  Markdown（最终输出）      │
└─────────────────────────────────────────────────────┘
```

### 3.2 Agent 职责与边界

```
┌──────────────────────────────────────────────────────────┐
│  Agent 1：需求澄清 Agent（ClarifyAgent）                   │
│                                                          │
│  输入：用户的一句话需求描述                                 │
│  行为：多轮对话追问，每次最多问 3 个问题                    │
│        最多追问 5 轮，超过则强制生成                        │
│  输出：结构化需求卡片（RequirementCard）                    │
│  失败处理：追问超限 → 标记字段为"待确认"继续推进            │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Agent 2：PRD 生成 Agent（PRDAgent）                      │
│                                                          │
│  输入：RequirementCard                                    │
│  行为：基于需求卡片生成完整 PRD，单次调用                   │
│        输出不完整时自动重试（最多 3 次）                    │
│  输出：PRDDocument                                        │
│  失败处理：重试 3 次失败 → 抛出异常，提示人工介入           │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Agent 3：技术方案 Agent（TechAgent）                     │
│  Agent 4：测试用例 Agent（TestAgent）                     │
│                                                          │
│  输入：RequirementCard + PRDDocument                      │
│  行为：两个 Agent 并行执行，互不依赖                        │
│  输出：TechPlan / TestCases                               │
│  失败处理：单个失败不影响另一个，独立重试                   │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│  Agent 5：风险评估 Agent（RiskAgent）                     │
│                                                          │
│  输入：PRDDocument + TechPlan + TestCases                 │
│  行为：综合分析，识别风险点，进行多步推理                   │
│        对照测试用例和技术方案，找出遗漏场景                 │
│  输出：RiskReport                                         │
│  失败处理：重试 2 次失败 → 输出空报告，标记需人工评估       │
└──────────────────────────────────────────────────────────┘
```

### 3.3 数据流转图

```
用户输入
  │
  ▼
[需求文本: string]
  │
  ▼ Agent 1 处理
[RequirementCard: JSON]
  ├── name: string
  ├── background: string
  ├── user_roles: string[]
  ├── core_actions: string[]
  ├── constraints: string[]
  ├── out_of_scope: string[]
  └── tech_stack: string
  │
  ▼ Agent 2 处理
[PRDDocument: JSON]
  ├── title: string
  ├── background: string
  ├── user_stories: string[]
  ├── core_flow: string
  ├── exception_flow: string
  ├── data_fields: string[]
  └── out_of_scope: string
  │
  ├──────────────────────┐
  ▼ Agent 3（并行）       ▼ Agent 4（并行）
[TechPlan: JSON]        [TestCases: JSON]
  ├── involved_modules    ├── main_flow_cases
  ├── new_apis            ├── exception_cases
  ├── modified_apis       └── boundary_cases
  ├── estimated_days
  └── tech_risks
  │                       │
  └──────────┬────────────┘
             ▼ Agent 5 处理
        [RiskReport: JSON]
          ├── risk_level
          ├── risk_points
          ├── suggestions
          └── uncovered_scenarios
             │
             ▼
        [最终输出: Markdown 报告]
```

---

## 4. 功能需求详细说明

### 4.1 Agent 1：需求澄清

#### 功能描述
接收用户模糊的需求描述，通过多轮对话的方式澄清关键信息，最终输出结构化需求卡片。

#### 详细行为规则

```
规则 1：追问策略
  - 每次回复最多包含 3 个问题
  - 问题要具体，不问宽泛的"还有什么要补充的吗"
  - 优先追问影响系统设计的关键信息
  - 已经回答过的信息不重复追问

规则 2：信息完整性判断
  必须明确的字段（缺一不可）：
    ✓ 需求名称（能清晰描述这是什么功能）
    ✓ 至少一个用户角色
    ✓ 至少一个核心行为
    ✓ 是否有数量/频率/权限限制
  
  可以有默认值的字段：
    ○ 排除范围（默认为空）
    ○ 技术栈（默认为"常见 Web 技术栈"）

规则 3：强制结束条件
  满足以下任一条件，强制输出需求卡片：
    - 必须明确的字段全部收集完毕
    - 对话轮数达到 5 轮
    - 用户明确说"就这些了"/"可以了"/"开始生成"

规则 4：输出格式
  在回复末尾以特定标记输出 JSON：
  [REQUIREMENT_CARD]
  { ... }
```

#### 追问示例

```
用户："做一个用户签到功能"

Agent 第 1 轮追问：
  1. 签到的奖励机制是什么？（积分/优惠券/其他）
  2. 连续签到是否有额外奖励？
  3. 每天几点刷新签到？

用户："积分奖励，连签有加成，0点刷新"

Agent 第 2 轮追问：
  1. 积分有上限吗？连签加成的具体规则是什么？
  2. 签到记录需要展示多少天的历史？

用户："没有上限，连签7天双倍，展示30天"

Agent 判断：信息已足够 → 输出需求卡片
```

### 4.2 Agent 2：PRD 生成

#### 功能描述
基于结构化需求卡片，自动生成完整的产品需求文档。

#### PRD 必须包含的内容

```
1. 需求背景
   - 业务背景描述
   - 解决的核心问题

2. 用户故事
   - 每个用户角色至少 1 条用户故事
   - 格式：作为[角色]，我希望[行为]，以便[价值]

3. 功能说明
   3.1 核心流程（主流程步骤描述）
   3.2 异常场景（至少覆盖以下类型）
       - 网络异常
       - 数据异常/边界值
       - 权限不足
       - 重复操作

4. 数据说明
   - 涉及的数据字段及类型
   - 关键业务规则

5. 非功能需求
   - 性能要求（如有）
   - 兼容性要求（如有）

6. 排除范围
   - 明确不在本次需求中的内容
```

#### 质量校验规则

```
生成后自动校验：
  ✓ 用户故事数量 ≥ 用户角色数量
  ✓ 异常场景数量 ≥ 3
  ✓ 数据字段列表不为空
  ✓ 核心流程步骤 ≥ 3 步
  
任意校验不通过 → 自动重新生成（最多 3 次）
```

### 4.3 Agent 3：技术方案

#### 功能描述
基于 PRD，生成技术实现框架，帮助开发团队快速了解改动范围。

#### 技术方案必须包含的内容

```
1. 涉及模块
   - 列出需要改动的系统模块
   - 标注是新建还是改造

2. 接口设计
   - 新增接口：接口名称 + 核心参数 + 返回值描述
   - 修改接口：接口名称 + 改动说明

3. 数据库变更
   - 新增表/字段
   - 索引建议

4. 工作量估算
   - 前端工作量（天）
   - 后端工作量（天）
   - 测试工作量（天）

5. 技术风险点
   - 每个风险点说明原因和建议处理方式
```

### 4.4 Agent 4：测试用例

#### 功能描述
基于 PRD 和技术方案，自动生成分级测试用例清单。

#### 测试用例分级规则

```
P0 - 主流程用例（核心功能不能挂）
  - 覆盖 PRD 中每个核心流程步骤
  - 至少 5 条

P1 - 异常用例（异常场景要能处理）
  - 覆盖 PRD 中所有异常场景
  - 至少 3 条

P2 - 边界用例（边界值要处理正确）
  - 数值边界（最大值、最小值、零值）
  - 字符串边界（空、超长）
  - 时间边界（跨天、跨月等）
  - 至少 3 条

用例格式：
  前置条件 | 操作步骤 | 预期结果
```

### 4.5 Agent 5：风险评估

#### 功能描述
综合分析 PRD、技术方案、测试用例，找出潜在风险和遗漏场景。

#### 风险评估维度

```
维度 1：需求完整性
  - PRD 中是否有歧义或未定义的场景？
  - 用户故事是否覆盖所有用户角色？

维度 2：技术风险
  - 改动模块是否涉及核心链路？
  - 是否有跨系统依赖？
  - 工作量估算是否合理？

维度 3：测试覆盖度
  - 测试用例是否覆盖所有异常场景？
  - 是否有明显遗漏的边界用例？

维度 4：交叉风险
  - 技术方案与 PRD 是否存在冲突？
  - 新功能是否可能影响现有功能？
```

#### 风险等级定义

```
🔴 高风险：
  - 涉及支付/账户/核心数据链路
  - 测试用例覆盖度 < 60%
  - 存在明确的技术方案与需求冲突
  → 建议：人工评审后再推进

🟡 中风险：
  - 存在跨系统依赖
  - 有未覆盖的异常场景
  - 工作量估算偏差可能较大
  → 建议：补充相关内容后再推进

🟢 低风险：
  - 改动范围小且独立
  - 覆盖度充分
  - 无明显冲突
  → 建议：可直接推进
```

---

## 5. 非功能需求

### 5.1 性能要求

```
Agent 1（需求澄清）：
  - 每轮响应时间 < 5 秒

Agent 2（PRD 生成）：
  - 生成时间 < 30 秒

Agent 3 & 4（并行执行）：
  - 总耗时 < 40 秒（并行后等于单个最慢的时间）

Agent 5（风险评估）：
  - 生成时间 < 20 秒

端到端总时间目标：
  - 需求澄清（用户交互）：10-30 分钟
  - 文档自动生成：< 2 分钟
```

### 5.2 稳定性要求

```
- 单个 Agent 失败自动重试，最多 3 次
- 重试全部失败时给出明确错误提示
- 不因单个 Agent 失败导致整个流程中断
- 中间状态实时保存，支持断点恢复
```

### 5.3 输出质量要求

```
- 所有输出必须通过 Pydantic Schema 校验
- PRD 字数 > 800 字
- 测试用例总数 ≥ 11 条（P0≥5 + P1≥3 + P2≥3）
- 风险报告必须给出明确的风险等级
```

---

## 6. 技术选型说明

```
类别          选型              理由
─────────────────────────────────────────────
语言          Python 3.10+     生态成熟，异步支持好
模型调用      OpenAI API       GPT-4o，支持 JSON Mode
Agent 编排    自实现 Orchestrator  MVP 阶段无需重框架
并行执行      asyncio          原生支持，无额外依赖
数据校验      Pydantic v2      Schema 定义和校验一体
Web UI        Streamlit        快速搭建，无需前端开发
存储          本地 JSON 文件   MVP 阶段够用
输出格式      Markdown         通用，可直接粘贴使用
环境管理      python-dotenv    管理 API Key
```

---

# 第二部分：完整任务列表

---

## 任务总览

```
总任务数：47 个
预计工期：15 个工作日（3 周）

分布：
  P0 核心任务：22 个（必须完成，MVP 可跑通）
  P1 完善任务：16 个（质量保障）
  P2 优化任务：9 个（体验提升）
```

---

## TASK-001 ～ TASK-008：项目基础搭建

---

### TASK-001
```
标题：初始化项目结构
优先级：P0
预计耗时：1 小时
依赖：无

详细描述：
  创建完整的项目目录结构，包含所有必要的目录和初始文件。

需要创建的结构：
  requirement-agent/
  ├── main.py
  ├── app.py
  ├── .env.example
  ├── requirements.txt
  ├── README.md
  ├── agents/
  │   ├── __init__.py
  │   ├── base_agent.py
  │   ├── clarify_agent.py
  │   ├── prd_agent.py
  │   ├── tech_agent.py
  │   ├── test_agent.py
  │   └── risk_agent.py
  ├── models/
  │   ├── __init__.py
  │   └── schemas.py
  ├── prompts/
  │   ├── clarify_system.txt
  │   ├── prd_system.txt
  │   ├── tech_system.txt
  │   ├── test_system.txt
  │   └── risk_system.txt
  ├── core/
  │   ├── __init__.py
  │   ├── orchestrator.py
  │   └── output_generator.py
  ├── utils/
  │   ├── __init__.py
  │   ├── retry.py
  │   └── validator.py
  └── output/              ← gitignore 此目录

验收标准：
  ✓ 目录结构完整
  ✓ 所有 __init__.py 已创建
  ✓ .gitignore 已配置（忽略 .env, output/, __pycache__）
```

---

### TASK-002
```
标题：配置 requirements.txt 和环境变量
优先级：P0
预计耗时：30 分钟
依赖：TASK-001

需要安装的依赖：
  openai>=1.0.0
  pydantic>=2.0.0
  streamlit>=1.28.0
  python-dotenv>=1.0.0
  asyncio（标准库，无需安装）

.env.example 内容：
  OPENAI_API_KEY=your_key_here
  MODEL_NAME=gpt-4o
  MAX_RETRY_TIMES=3
  MAX_CLARIFY_ROUNDS=5

验收标准：
  ✓ pip install -r requirements.txt 无报错
  ✓ .env.example 包含所有必要配置项
  ✓ README 中有环境配置说明
```

---

### TASK-003
```
标题：实现 Pydantic Schema 数据模型
优先级：P0
预计耗时：2 小时
依赖：TASK-001

文件：models/schemas.py

需要实现的 Schema：

1. RequirementCard
   字段：
     name: str                    # 需求名称
     background: str              # 业务背景
     user_roles: List[str]        # 用户角色列表
     core_actions: List[str]      # 核心行为列表
     constraints: List[str]       # 限制条件
     out_of_scope: List[str]      # 排除范围
     tech_stack: str = "常见 Web 技术栈"
     is_complete: bool = False
     missing_fields: List[str] = []  # 标记缺失字段
   
   验证器：
     - name 不能为空字符串
     - user_roles 至少 1 个元素
     - core_actions 至少 1 个元素

2. PRDDocument
   字段：
     title: str
     background: str
     user_stories: List[str]
     core_flow: str
     exception_flow: str
     data_fields: List[str]
     non_functional: str = ""
     out_of_scope: str
   
   验证器：
     - user_stories 至少 1 条
     - core_flow 长度 > 50 字符
     - exception_flow 长度 > 30 字符

3. APIDesign（嵌套模型）
   字段：
     name: str           # 接口名称
     method: str         # GET/POST/PUT/DELETE
     description: str    # 功能描述
     params: List[str]   # 核心参数
     response: str       # 返回值描述

4. TechPlan
   字段：
     involved_modules: List[str]
     new_apis: List[APIDesign]
     modified_apis: List[str]
     db_changes: List[str]          # 数据库变更
     estimated_days: Dict[str, int] # {"frontend":x, "backend":x, "testing":x}
     tech_risks: List[str]
   
   验证器：
     - involved_modules 至少 1 个
     - estimated_days 必须包含 frontend/backend/testing 三个 key

5. TestCase（嵌套模型）
   字段：
     priority: str       # P0/P1/P2
     precondition: str   # 前置条件
     steps: str          # 操作步骤
     expected: str       # 预期结果

6. TestCases
   字段：
     main_flow_cases: List[TestCase]    # P0
     exception_cases: List[TestCase]    # P1
     boundary_cases: List[TestCase]     # P2
   
   验证器：
     - main_flow_cases 至少 5 条
     - exception_cases 至少 3 条
     - boundary_cases 至少 3 条
   
   属性方法：
     total_count -> int   # 返回总用例数

7. RiskReport
   字段：
     risk_level: Literal["高", "中", "低"]
     risk_points: List[str]
     suggestions: List[str]
     uncovered_scenarios: List[str]
     needs_human_review: bool   # 高风险时自动为 True

验收标准：
  ✓ 所有 Schema 可以正常实例化
  ✓ 验证器在输入不合法时正确抛出 ValidationError
  ✓ 写一个简单的单元测试验证每个 Schema
```

---

### TASK-004
```
标题：实现 BaseAgent 基类
优先级：P0
预计耗时：2 小时
依赖：TASK-002, TASK-003

文件：agents/base_agent.py

需要实现的内容：

class BaseAgent:
  属性：
    model_name: str         # 从环境变量读取
    max_retries: int        # 从环境变量读取
    client: OpenAI          # OpenAI 客户端
  
  方法：
    1. _load_prompt(prompt_file: str) -> str
       从 prompts/ 目录读取对应的 Prompt 文件
    
    2. _call_api(messages, response_format=None) -> str
       调用 OpenAI API
       统一处理：超时、限速、网络错误
       失败时抛出自定义异常
    
    3. _parse_json(text: str) -> dict
       从文本中提取 JSON 内容
       处理 ```json ``` 代码块的情况
       处理纯 JSON 字符串的情况
    
    4. _validate_output(data: dict, schema_class) -> BaseModel
       用 Pydantic 校验输出
       校验失败抛出 ValidationError

验收标准：
  ✓ BaseAgent 可以正常初始化
  ✓ API 调用失败时正确抛出异常
  ✓ JSON 解析能处理带代码块的情况
```

---

### TASK-005
```
标题：实现重试工具函数
优先级：P0
预计耗时：1 小时
依赖：TASK-001

文件：utils/retry.py

需要实现：

1. retry_on_failure 装饰器
   参数：
     max_retries: int = 3
     delay: float = 1.0        # 每次重试间隔（秒）
     exceptions: tuple         # 哪些异常触发重试
   
   行为：
     - 被装饰函数失败时自动重试
     - 每次重试前打印日志
     - 超过最大次数后重新抛出异常

2. async_retry_on_failure 装饰器
   - 与上面相同，但支持 async 函数

示例用法：
  @retry_on_failure(max_retries=3, delay=1.0)
  def generate_prd(self, ...):
      ...

验收标准：
  ✓ 同步和异步版本都正常工作
  ✓ 重试日志格式清晰（第 x 次重试...）
  ✓ 超过最大次数后正确抛出异常
```

---

### TASK-006
```
标题：实现输出校验工具
优先级：P1
预计耗时：1 小时
依赖：TASK-003

文件：utils/validator.py

需要实现：

1. validate_requirement_card(card: RequirementCard) -> ValidationResult
   检查：
     - 必要字段是否完整
     - 返回缺失字段列表

2. validate_prd(prd: PRDDocument) -> ValidationResult
   检查：
     - 用户故事数量是否足够
     - 核心流程是否完整
     - 异常场景是否覆盖

3. validate_test_cases(cases: TestCases) -> ValidationResult
   检查：
     - 各优先级用例数量是否达标

class ValidationResult:
  is_valid: bool
  issues: List[str]    # 问题列表
  warnings: List[str]  # 警告列表（不影响继续，但值得注意）

验收标准：
  ✓ 每个校验函数返回 ValidationResult
  ✓ issues 和 warnings 区分清晰
```

---

### TASK-007
```
标题：编写所有 Agent 的 Prompt 模板
优先级：P0
预计耗时：3 小时
依赖：TASK-001

这是整个项目最重要的任务之一，Prompt 质量直接决定输出质量。

文件：prompts/ 目录下 5 个文件

1. clarify_system.txt（需求澄清 Agent）
   要点：
     - 明确追问策略（每次最多 3 问）
     - 明确什么时候停止追问
     - 明确输出格式（[REQUIREMENT_CARD] 标记）
     - 给出追问的优先级（业务规则 > 用户角色 > 技术细节）

2. prd_system.txt（PRD 生成 Agent）
   要点：
     - 明确 PRD 各部分的写作要求
     - 用户故事格式要求
     - 异常场景必须覆盖的类型
     - 输出 JSON 格式定义

3. tech_system.txt（技术方案 Agent）
   要点：
     - 明确技术方案各部分内容
     - 接口设计的格式要求
     - 工作量估算的参考标准
     - 输出 JSON 格式定义

4. test_system.txt（测试用例 Agent）
   要点：
     - P0/P1/P2 用例的定义和数量要求
     - 每条用例的格式（前置条件/步骤/预期结果）
     - 输出 JSON 格式定义

5. risk_system.txt（风险评估 Agent）
   要点：
     - 风险评估的维度（需求/技术/测试/交叉）
     - 风险等级的判断标准
     - 输出 JSON 格式定义

验收标准：
  ✓ 每个 Prompt 包含清晰的角色定义
  ✓ 每个 Prompt 包含明确的输出格式要求
  ✓ 每个 Prompt 经过至少 3 个真实需求的测试
  ✓ 输出质量稳定（重复调用结果基本一致）
```

---

### TASK-008
```
标题：实现状态持久化（中间结果保存）
优先级：P1
预计耗时：1.5 小时
依赖：TASK-003

文件：core/state_manager.py

需要实现：

class SessionState:
  属性：
    session_id: str          # 时间戳生成
    raw_input: str           # 用户原始输入
    requirement_card: Optional[RequirementCard]
    prd: Optional[PRDDocument]
    tech_plan: Optional[TechPlan]
    test_cases: Optional[TestCases]
    risk_report: Optional[RiskReport]
    current_stage: str       # clarifying/generating/done
    created_at: str

  方法：
    save() -> None           # 保存到 output/{session_id}/state.json
    load(session_id) -> SessionState   # 从文件加载
    get_progress() -> dict   # 返回各阶段完成状态

验收标准：
  ✓ 每个 Agent 执行完自动保存状态
  ✓ 程序中断后可以从上次状态继续
  ✓ state.json 格式可读
```

---

## TASK-009 ～ TASK-018：Agent 核心实现

---

### TASK-009
```
标题：实现 Agent 1 - 需求澄清 Agent
优先级：P0
预计耗时：4 小时
依赖：TASK-004, TASK-007

文件：agents/clarify_agent.py

class ClarifyAgent(BaseAgent):
  
  属性：
    conversation_history: List[dict]    # 对话历史
    round_count: int                    # 当前追问轮数
    max_rounds: int                     # 最大轮数（默认5）
    requirement_card: Optional[RequirementCard]
  
  方法：
    1. chat(user_input: str) -> ClarifyResponse
       返回：
         ClarifyResponse:
           reply: str          # Agent 的回复文本
           is_done: bool       # 是否完成澄清
           round: int          # 当前轮数
       
       内部逻辑：
         a. 将用户输入加入对话历史
         b. 调用 API 获取回复
         c. 检查回复是否包含 [REQUIREMENT_CARD]
         d. 如果包含，解析并校验需求卡片
         e. 如果不包含且轮数达上限，强制触发生成
         f. 返回 ClarifyResponse
    
    2. _force_generate() -> RequirementCard
       当轮数达上限时，强制要求 Agent 输出需求卡片
       对于未收集到的字段，标记为"待确认"
    
    3. _parse_requirement_card(text: str) -> RequirementCard
       从回复文本中提取并解析需求卡片 JSON
    
    4. get_result() -> RequirementCard
       返回最终的需求卡片

关键边界处理：
  - 用户输入为空时：提示重新输入
  - API 返回格式不正确时：重试
  - 轮数达上限时：强制生成并在 missing_fields 中记录

验收标准：
  ✓ 正常流程：能在 3-5 轮内完成需求澄清
  ✓ 边界测试：用户一直不提供信息，5轮后强制输出
  ✓ 格式测试：输出的 RequirementCard 通过 Pydantic 校验
  ✓ 用户说"可以了"时立即生成需求卡片
```

---

### TASK-010
```
标题：实现 Agent 2 - PRD 生成 Agent
优先级：P0
预计耗时：3 小时
依赖：TASK-004, TASK-007

文件：agents/prd_agent.py

class PRDAgent(BaseAgent):
  
  方法：
    1. generate(requirement_card: RequirementCard) -> PRDDocument
       内部逻辑：
         a. 将需求卡片格式化为 Prompt
         b. 调用 API（使用 JSON Mode）
         c. 解析返回的 JSON
         d. 用 Pydantic 校验
         e. 校验不通过则重试（最多 3 次）
         f. 3 次失败则抛出异常
    
    2. _format_input(requirement_card) -> str
       将需求卡片格式化为清晰的文本，供 Prompt 使用
    
    3. _validate_prd_quality(prd: PRDDocument) -> bool
       检查 PRD 质量：
         - 用户故事数量 ≥ 用户角色数量
         - 异常场景数量 ≥ 3
         - 字段列表不为空

验收标准：
  ✓ 输入有效需求卡片，输出完整 PRD
  ✓ PRD 包含所有必要章节
  ✓ Pydantic 校验通过
  ✓ 重试机制正常工作
```

---

### TASK-011
```
标题：实现 Agent 3 - 技术方案 Agent
优先级：P0
预计耗时：3 小时
依赖：TASK-004, TASK-007

文件：agents/tech_agent.py

class TechAgent(BaseAgent):
  
  方法：
    1. generate(requirement_card, prd) -> TechPlan
       内部逻辑：
         a. 组合需求卡片和 PRD 内容作为输入
         b. 调用 API（JSON Mode）
         c. 解析并校验 TechPlan
         d. 失败重试（最多 3 次）
    
    2. _format_input(requirement_card, prd) -> str
       将两个输入格式化为技术方案 Prompt 的输入部分

验收标准：
  ✓ 输出 TechPlan 通过 Pydantic 校验
  ✓ 涉及模块不为空
  ✓ 工作量估算包含三个维度
```

---

### TASK-012
```
标题：实现 Agent 4 - 测试用例 Agent
优先级：P0
预计耗时：3 小时
依赖：TASK-004, TASK-007

文件：agents/test_agent.py

class TestAgent(BaseAgent):
  
  方法：
    1. generate(requirement_card, prd) -> TestCases
       内部逻辑：
         a. 提取 PRD 中的核心流程和异常场景
         b. 调用 API 生成分级测试用例
         c. 校验各优先级数量是否达标
         d. 不达标则重试
    
    2. _count_cases(cases: TestCases) -> dict
       返回各优先级用例数量统计

验收标准：
  ✓ P0 用例 ≥ 5 条
  ✓ P1 用例 ≥ 3 条
  ✓ P2 用例 ≥ 3 条
  ✓ 每条用例包含前置条件/步骤/预期结果
```

---

### TASK-013
```
标题：实现 Agent 5 - 风险评估 Agent
优先级：P0
预计耗时：3 小时
依赖：TASK-004, TASK-007

文件：agents/risk_agent.py

class RiskAgent(BaseAgent):
  
  方法：
    1. evaluate(prd, tech_plan, test_cases) -> RiskReport
       内部逻辑：
         a. 将三个输入合并为综合上下文
         b. 调用 API 进行多维度风险分析
         c. 解析风险报告
         d. 根据风险等级设置 needs_human_review
    
    2. _format_context(prd, tech_plan, test_cases) -> str
       将三个输入合并，突出关键信息用于风险分析
    
    3. _determine_risk_level(report_data: dict) -> str
       根据规则判断风险等级：
         有支付/账户关键词 → 至少中风险
         测试用例总数 < 11 → 至少中风险
         技术风险点 > 3 → 至少中风险

验收标准：
  ✓ 风险等级在 高/中/低 中取值
  ✓ 高风险时 needs_human_review = True
  ✓ 风险点列表不为空
  ✓ 改进建议具有可操作性
```

---

### TASK-014
```
标题：实现 Orchestrator 主编排器
优先级：P0
预计耗时：4 小时
依赖：TASK-009, TASK-010, TASK-011, TASK-012, TASK-013

文件：core/orchestrator.py

class Orchestrator:
  
  属性：
    session: SessionState
    clarify_agent: ClarifyAgent
    prd_agent: PRDAgent
    tech_agent: TechAgent
    test_agent: TestAgent
    risk_agent: RiskAgent
    on_progress: Callable    # 进度回调函数
  
  方法：
    1. async run_clarify_stage(user_input: str) -> ClarifyResponse
       执行需求澄清（支持多轮）
       更新 session 状态
    
    2. async run_generation_stage() -> GenerationResult
       执行文档生成阶段：
         a. 串行：PRD 生成
         b. 并行：技术方案 + 测试用例
         c. 串行：风险评估
       每步完成后更新 session 并触发进度回调
    
    3. async run(initial_input: str) -> SessionState
       完整流程入口
       返回最终的 session 状态
    
    4. _notify_progress(stage: str, progress: int, message: str)
       触发进度回调，供 UI 层展示进度

  进度定义：
    需求澄清完成：20%
    PRD 生成完成：40%
    技术方案完成：60%
    测试用例完成：60%（与技术方案并行，同时完成）
    风险评估完成：80%
    报告生成完成：100%

验收标准：
  ✓ 完整流程可以端到端跑通
  ✓ Agent 3 和 Agent 4 确实是并行执行
  ✓ 进度回调在每个阶段正确触发
  ✓ 任一 Agent 失败时给出清晰错误信息
```

---

### TASK-015
```
标题：实现 Markdown 报告生成器
优先级：P0
预计耗时：2 小时
依赖：TASK-003, TASK-008

文件：core/output_generator.py

class OutputGenerator:
  
  方法：
    1. generate(session: SessionState) -> str
       生成完整的 Markdown 报告文本
    
    2. save(session: SessionState) -> Path
       保存报告到 output/{session_id}/full_report.md
       同时保存各 Agent 输出的 JSON 文件：
         - requirement_card.json
         - prd.json
         - tech_plan.json
         - test_cases.json
         - risk_report.json
    
    3. _generate_header(session) -> str
    4. _generate_requirement_section(card) -> str
    5. _generate_prd_section(prd) -> str
    6. _generate_tech_section(plan) -> str
    7. _generate_test_section(cases) -> str
    8. _generate_risk_section(report) -> str

报告结构：
  # {需求名称} - 完整需求分析报告
  生成时间：{timestamp}
  风险等级：{level}
  
  ## 目录
  ## 一、结构化需求卡片
  ## 二、产品需求文档（PRD）
  ## 三、技术方案
  ## 四、测试用例
  ## 五、风险评估报告

验收标准：
  ✓ 生成的 Markdown 格式正确，可正常渲染
  ✓ 所有章节内容完整
  ✓ JSON 文件同步保存
  ✓ 文件路径清晰，包含时间戳
```

---

## TASK-016 ～ TASK-022：主入口与 CLI

---

### TASK-016
```
标题：实现命令行主入口
优先级：P0
预计耗时：2 小时
依赖：TASK-014, TASK-015

文件：main.py

功能：
  - 命令行交互式运行
  - 清晰的阶段提示（Step 1/5, Step 2/5...）
  - 进度条显示（简单的文字进度即可）
  - 最终输出报告路径

交互示例：
  ════════════════════════════════════
    需求全流程自动化 Agent 系统 v1.0
  ════════════════════════════════════

  📋 第一步：需求澄清
  请输入您的需求（一句话即可）：
  > 做一个用户签到功能

  🤖 Agent：
  [追问内容...]

  您：
  > [用户回答]

  ✅ 需求澄清完成！开始生成文档...

  ⚡ 正在生成 PRD...        完成 ✓  (用时 12s)
  ⚡ 并行生成技术方案...    完成 ✓  (用时 18s)
  ⚡ 并行生成测试用例...    完成 ✓  (用时 15s)
  ⚡ 正在进行风险评估...    完成 ✓  (用时 10s)

  🎉 全部完成！

  风险等级：🟡 中风险
  测试用例：共 14 条（P0: 6条 P1: 5条 P2: 3条）
  
  📄 报告已保存至：output/20241201_143022/full_report.md

验收标准：
  ✓ 完整流程可以通过命令行运行
  ✓ 每个阶段有明确的状态提示
  ✓ 最终显示报告路径
```

---

### TASK-017 ～ TASK-022：Streamlit UI 实现

---

### TASK-017
```
标题：实现 Streamlit 应用基础框架
优先级：P1
预计耗时：2 小时
依赖：TASK-016

文件：app.py

页面结构：
  - 左侧边栏：会话历史、配置项
  - 主区域：当前会话的交互和结果展示
  - 顶部：进度指示器

Session State 管理：
  st.session_state 中维护：
    - orchestrator: Orchestrator 实例
    - stage: 当前阶段
    - messages: 对话历史
    - results: 各 Agent 的输出结果

验收标准：
  ✓ 页面可以正常启动（streamlit run app.py）
  ✓ Session State 正确初始化
  ✓ 页面布局符合设计
```

---

### TASK-018
```
标题：实现需求澄清对话界面
优先级：P1
预计耗时：2 小时
依赖：TASK-017

功能：
  - 类似聊天界面的对话展示
  - 用户输入框在底部
  - Agent 回复带有图标区分
  - 需求澄清完成后显示"生成文档"按钮
  - 展示当前追问轮数（第 x/5 轮）

验收标准：
  ✓ 对话界面正常显示
  ✓ 用户和 Agent 的消息视觉区分明显
  ✓ 完成后"生成文档"按钮出现
```

---

### TASK-019
```
标题：实现文档生成进度展示
优先级：P1
预计耗时：2 小时
依赖：TASK-018

功能：
  - 点击"生成文档"后显示实时进度
  - 每个 Agent 有单独的状态展示：
    ○ 等待中 → ⚡ 生成中 → ✅ 完成 / ❌ 失败
  - 进度条显示整体进度
  - 生成完成后自动跳转到结果展示

验收标准：
  ✓ 进度实时更新（不是等全部完成后刷新）
  ✓ 并行的 Agent 3 和 Agent 4 同时显示进行中状态
  ✓ 任一失败时有错误提示
```

---

### TASK-020
```
标题：实现结果分 Tab 展示
优先级：P1
预计耗时：2 小时
依赖：TASK-019

功能：
  5个 Tab 对应 5 个 Agent 的输出：
  
  Tab 1 - 需求卡片：
    以卡片形式展示结构化需求
    每个字段单独一行，清晰可读
  
  Tab 2 - PRD：
    Markdown 渲染展示
    支持展开/折叠各章节
  
  Tab 3 - 技术方案：
    涉及模块以标签形式展示
    接口列表以表格展示
    工作量以进度条形式展示
  
  Tab 4 - 测试用例：
    按 P0/P1/P2 分组展示
    以可勾选的清单形式展示（方便测试时对照）
  
  Tab 5 - 风险评估：
    风险等级大字展示（带颜色）
    风险点和建议分列展示

验收标准：
  ✓ 5 个 Tab 内容完整
  ✓ 测试用例可勾选
  ✓ 风险等级颜色正确（红/黄/绿）
```

---

### TASK-021
```
标题：实现报告下载功能
优先级：P1
预计耗时：1 小时
依赖：TASK-020

功能：
  - "下载完整报告（Markdown）"按钮
  - "下载原始数据（JSON）"按钮（打包下载所有 JSON）
  - 显示报告保存路径

验收标准：
  ✓ 点击下载按钮可以下载文件
  ✓ Markdown 文件格式正确
```

---

### TASK-022
```
标题：实现历史会话查看
优先级：P2
预计耗时：2 小时
依赖：TASK-021

功能：
  左侧边栏显示历史会话列表：
  - 显示需求名称和生成时间
  - 点击可查看历史结果
  - 支持删除历史会话

验收标准：
  ✓ 历史会话正确加载
  ✓ 点击历史会话可以查看结果
```

---

## TASK-023 ～ TASK-035：质量保障

---

### TASK-023
```
标题：编写 Agent 1 单元测试
优先级：P1
预计耗时：2 小时
依赖：TASK-009

测试用例：
  1. test_normal_clarification
     输入一个完整需求，验证 3 轮内完成
  
  2. test_force_generation
     模拟用户一直不提供信息，验证第 5 轮强制生成
  
  3. test_user_says_done
     用户说"可以了"，验证立即生成需求卡片
  
  4. test_output_schema_validation
     验证输出的需求卡片通过 Pydantic 校验
  
  5. test_parse_requirement_card
     测试从包含 [REQUIREMENT_CARD] 的文本中正确解析 JSON

使用 Mock 替代真实 API 调用
```

---

### TASK-024 ～ TASK-027
```
标题：编写 Agent 2-5 单元测试
优先级：P1
预计耗时：各 1.5 小时
依赖：对应 Agent 实现完成

每个 Agent 至少测试：
  1. 正常输入 → 正确输出
  2. 输出格式错误 → 触发重试
  3. 重试 3 次失败 → 正确抛出异常
  4. 输出通过 Schema 校验

均使用 Mock 替代真实 API 调用
```

---

### TASK-028
```
标题：编写 Orchestrator 集成测试
优先级：P1
预计耗时：3 小时
依赖：TASK-014

测试用例：
  1. test_full_flow_success
     Mock 所有 Agent，验证完整流程跑通
  
  2. test_parallel_execution
     验证 Agent 3 和 Agent 4 确实并行执行
     （通过计时验证总时间接近最慢的单个 Agent 时间）
  
  3. test_agent3_failure
     Agent 3 失败，验证 Agent 4 仍然执行
     验证错误信息正确传递
  
  4. test_progress_callbacks
     验证进度回调在正确的时机触发
     验证进度百分比正确
```

---

### TASK-029
```
标题：端到端真实测试（3 个真实需求场景）
优先级：P0
预计耗时：3 小时
依赖：TASK-016

使用真实 API 调用测试以下场景：

场景 1：简单功能需求
  输入："做一个用户签到功能"
  验证：能完成完整流程，输出质量可接受

场景 2：复杂业务需求
  输入："实现一个邀请好友得积分的裂变功能"
  验证：能识别复杂的业务规则，风险评估合理

场景 3：改造类需求
  输入："把现有的短信验证码登录改成支持微信一键登录"
  验证：能识别这是改造需求，技术方案中有模块改动描述

每个场景验收：
  ✓ 流程完整跑通
  ✓ 输出文档可读性强
  ✓ 测试用例数量达标
  ✓ 风险等级判断合理
```

---

### TASK-030 ～ TASK-035：Prompt 调优

---

### TASK-030
```
标题：Agent 1 Prompt 调优
优先级：P1
预计耗时：2 小时
依赖：TASK-029

调优目标：
  - 追问的问题更精准，不问废话
  - 能识别用户"已经回答过"的信息，不重复追问
  - 3 轮内完成简单需求的澄清
  - 强制生成时，"待确认"字段标记清晰

调优方式：
  - 运行 5 个不同类型的需求，记录追问质量
  - 针对问题修改 Prompt
  - 重复测试直到达标
```

---

### TASK-031 ～ TASK-035
```
标题：Agent 2-5 Prompt 调优
优先级：P1
预计耗时：各 1.5 小时

各 Agent 调优重点：

Agent 2（PRD）：
  - 用户故事表达是否自然
  - 异常场景覆盖是否全面
  - 数据字段描述是否准确

Agent 3（技术方案）：
  - 接口设计是否合理
  - 工作量估算是否靠谱
  - 技术风险点是否切实

Agent 4（测试用例）：
  - P0/P1/P2 分级是否准确
  - 边界用例是否覆盖关键边界
  - 用例描述是否可直接执行

Agent 5（风险评估）：
  - 风险等级判断是否合理
  - 是否能识别 PRD 与技术方案的冲突
  - 改进建议是否具有可操作性
```

---

## TASK-036 ～ TASK-047：完善与优化

---

### TASK-036
```
标题：异常处理完善
优先级：P1
预计耗时：2 小时

需要处理的异常场景：
  1. API Key 无效或额度不足
     → 给出明确提示，不显示技术错误

  2. 网络超时
     → 自动重试，超过次数后提示检查网络

  3. API 返回非 JSON 格式
     → 触发重试，记录原始返回用于 Debug

  4. Pydantic 校验失败
     → 记录具体失败字段，带字段信息重试

  5. 用户 Ctrl+C 中断
     → 优雅退出，保存当前会话状态

所有异常统一通过：
  CustomError 类封装，包含：
    - 错误类型
    - 用户友好的错误信息
    - 是否可重试
    - 原始错误（用于 Debug）
```

---

### TASK-037
```
标题：日志系统实现
优先级：P2
预计耗时：1.5 小时

需要记录的信息：
  - 每个 Agent 的调用时间和耗时
  - Token 消耗量（prompt_tokens / completion_tokens）
  - 重试次数和原因
  - 最终各 Agent 输出的摘要

日志文件：
  output/{session_id}/run.log

日志格式：
  2024-12-01 14:30:22 [INFO] Agent1.ClarifyAgent - 第 1 轮追问开始
  2024-12-01 14:30:25 [INFO] Agent1.ClarifyAgent - 第 1 轮完成 (耗时3s, 消耗512 tokens)
  2024-12-01 14:31:05 [INFO] Agent2.PRDAgent - PRD生成开始
  2024-12-01 14:31:22 [INFO] Agent2.PRDAgent - PRD生成完成 (耗时17s, 消耗2048 tokens)
```

---

### TASK-038
```
标题：Token 消耗统计
优先级：P2
预计耗时：1 小时

在每次 API 调用后记录 Token 消耗：
  - prompt_tokens
  - completion_tokens
  - total_tokens
  - 估算费用（基于 GPT-4o 定价）

在报告末尾追加统计信息：
  ## 生成统计
  | Agent | 耗时 | Token 消耗 | 估算费用 |
  |-------|------|-----------|---------|
  | 需求澄清 | 3m 20s | 3,200 | $0.016 |
  | PRD 生成 | 18s | 2,100 | $0.011 |
  | 技术方案 | 22s | 1,800 | $0.009 |
  | 测试用例 | 19s | 1,600 | $0.008 |
  | 风险评估 | 14s | 1,400 | $0.007 |
  | **合计** | **~5 分钟** | **10,100** | **$0.051** |
```

---

### TASK-039
```
标题：编写 README 文档
优先级：P1
预计耗时：2 小时

README 包含：
  1. 项目介绍（一句话 + 核心流程图）
  2. 快速开始
     - 环境要求
     - 安装步骤
     - 配置 API Key
     - 运行方式（CLI + Web UI）
  3. 使用示例（含截图或 GIF）
  4. 输出示例（展示一个真实需求的输出）
  5. 项目结构说明
  6. 配置项说明
  7. 常见问题 FAQ
```

---

### TASK-040
```
标题：配置项支持
优先级：P2
预计耗时：1 小时

支持通过 .env 配置：
  OPENAI_API_KEY=           # 必填
  MODEL_NAME=gpt-4o         # 可选，默认 gpt-4o
  MAX_RETRY_TIMES=3         # 可选，默认 3
  MAX_CLARIFY_ROUNDS=5      # 可选，默认 5
  OUTPUT_DIR=output         # 可选，默认 output
  LOG_LEVEL=INFO            # 可选，默认 INFO

在启动时打印当前配置（隐藏 API Key）：
  当前配置：
    模型：gpt-4o
    最大重试次数：3
    最大澄清轮数：5
    输出目录：./output
```

---

### TASK-041 ～ TASK-043：性能优化

---

### TASK-041
```
标题：Agent 3 & 4 并行执行验证与优化
优先级：P1
预计耗时：1.5 小时

验证并行执行的效果：
  - 记录串行执行时间（基准）
  - 记录并行执行时间
  - 验证并行时间接近 max(Agent3时间, Agent4时间)

如果并行不生效，检查：
  - asyncio.gather 使用是否正确
  - 是否在同步函数中调用了 async 函数
  - 线程池大小是否足够
```

---

### TASK-042
```
标题：Prompt 长度优化
优先级：P2
预计耗时：1 小时

随着流程推进，输入给后续 Agent 的 Prompt 会越来越长。
需要做适当截断/摘要：

  Agent 3 & 4 的输入：
    不需要完整的 PRD 文本
    只需要 PRD 的关键信息（核心流程、数据字段、异常场景）
    可以减少约 30% 的 Token 消耗

  Agent 5 的输入：
    不需要完整的 PRD + 技术方案 + 测试用例
    需要提炼关键风险相关信息
    可以减少约 40% 的 Token 消耗
```

---

### TASK-043
```
标题：流式输出支持（Streaming）
优先级：P2
预计耗时：2 小时

对 PRD 生成这种耗时较长的 Agent，支持流式输出：
  - API 调用时设置 stream=True
  - 在 Streamlit UI 中实时展示生成内容
  - 用户不需要等待全部生成完成才能看到内容

注意：
  使用流式输出时，无法直接用 JSON Mode
  需要等流式输出完成后再进行 JSON 解析
```

---

### TASK-044 ～ TASK-047：最终验收

---

### TASK-044
```
标题：完整功能验收测试
优先级：P0
预计耗时：4 小时

验收清单：

基础功能：
  □ CLI 模式完整流程跑通
  □ Streamlit UI 完整流程跑通
  □ 5 个 Agent 均正常输出
  □ 输出报告格式正确

质量要求：
  □ PRD 包含所有必要章节
  □ 测试用例 ≥ 11 条
  □ 风险报告包含等级和建议
  □ 输出 Markdown 可正常渲染

异常处理：
  □ API 调用失败时有重试
  □ 重试失败时有友好提示
  □ 中断后状态已保存

性能要求：
  □ 文档生成阶段 < 2 分钟
  □ 并行执行生效

使用 3 个不同类型的需求完成验收测试
```

---

### TASK-045
```
标题：输出质量人工评审
优先级：P0
预计耗时：2 小时

邀请目标用户（PM/开发/测试）各一人：
  - 使用系统处理一个真实需求
  - 对输出质量打分（1-5分）：
    PRD 可用性：__/5
    技术方案合理性：__/5
    测试用例覆盖度：__/5
    风险识别准确度：__/5
  - 记录反馈意见
  - 基于反馈调整 Prompt

目标分数：各项 ≥ 3.5 分
```

---

### TASK-046
```
标题：性能基准测试
优先级：P2
预计耗时：1 小时

测试内容：
  对同一个需求运行 5 次，记录：
  - 每次各 Agent 的耗时
  - Token 消耗量
  - 输出质量（字数、用例数量）

验证：
  - 耗时稳定（标准差 < 20%）
  - Token 消耗在预期范围内（< 15000 tokens/次）
  - 输出质量稳定（不同次运行差异不大）
```

---

### TASK-047
```
标题：项目打包与发布准备
优先级：P2
预计耗时：1 小时

  □ requirements.txt 版本锁定
  □ README 完整
  □ .env.example 完整
  □ .gitignore 配置正确（不包含 .env 和 output/）
  □ 在一个干净的 Python 环境中重新安装并验证可运行
```

---

# 第三部分：里程碑计划

```
Week 1（Day 1-5）：核心跑通
  Day 1  TASK-001, 002, 003（项目初始化 + Schema）
  Day 2  TASK-004, 005, 006, 007（基础工具 + Prompt）
  Day 3  TASK-009, 010（Agent 1 + Agent 2）
  Day 4  TASK-011, 012, 013（Agent 3 + 4 + 5）
  Day 5  TASK-014, 015, 016（Orchestrator + 报告 + CLI）
  
  ✅ Week 1 里程碑：CLI 完整流程可跑通

Week 2（Day 6-10）：质量保障
  Day 6  TASK-008（状态持久化）+ TASK-028（集成测试）
  Day 7  TASK-023 ～ 027（Agent 单元测试）
  Day 8  TASK-029（端到端真实测试）
  Day 9  TASK-030 ～ 035（Prompt 调优）
  Day 10 TASK-036, 037（异常处理 + 日志）
  
  ✅ Week 2 里程碑：CLI 版本质量稳定，可给真实用户试用

Week 3（Day 11-15）：UI + 完善
  Day 11 TASK-017, 018（Streamlit 基础 + 对话界面）
  Day 12 TASK-019, 020（进度展示 + 结果展示）
  Day 13 TASK-021, 039, 040（下载 + README + 配置）
  Day 14 TASK-044, 045（完整验收 + 用户评审）
  Day 15 TASK-038, 046, 047（统计 + 性能测试 + 打包）
  
  ✅ Week 3 里程碑：MVP 完整版本发布
```

---

# 第四部分：快速参考

## 任务优先级汇总

```
P0 必须完成（22个）：
  TASK-001 ~ 005, 007, 009 ~ 016, 029, 044, 045

P1 质量保障（16个）：
  TASK-006, 008, 017 ~ 021, 023 ~ 028, 030 ~ 036, 039, 041

P2 体验优化（9个）：
  TASK-022, 037, 038, 040, 042, 043, 046, 047
```

## 关键依赖链

```
TASK-001（项目结构）
  └── TASK-002（依赖配置）
        └── TASK-004（BaseAgent）
  └── TASK-003（Schema）
        └── TASK-009（Agent1）
              └── TASK-014（Orchestrator）
                    └── TASK-016（CLI 入口）
  └── TASK-007（Prompt 模板）
        └── 所有 Agent 实现
```

---

这份文档可以直接作为开发基础，按照里程碑计划推进，**Week 1 结束就能看到完整的可运行版本**。

如果需要，我可以继续帮你：
1. **把某个具体 Task 的代码直接写出来**
2. **深化某个 Agent 的 Prompt 模板设计**
3. **设计更详细的测试用例**