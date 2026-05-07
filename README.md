# 需求全流程自动化 Agent 系统

## 项目概述

这是一个由多个 Agent 协同驱动的需求全流程自动化系统，旨在将用户的模糊需求描述自动转换为完整的需求文档包（PRD + 技术方案 + 测试用例 + 风险报告）。

## 系统架构

```
用户交互层
    ↓
编排控制层 (Orchestrator)
    ↓
┌─────────────┬─────────────┬─────────────┬─────────────┬─────────────┐
│ 需求澄清 Agent │ PRD 生成 Agent │ 技术方案 Agent │ 测试用例 Agent │ 风险评估 Agent │
└─────────────┴─────────────┴─────────────┴─────────────┴─────────────┘
    ↓                           ↓
              数据存储层 (本地 JSON + Markdown)
```

## 快速开始

### 环境要求

- Python 3.10+
- OpenAI API Key

### 安装步骤

1. 克隆项目到本地
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 配置环境变量：
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填入您的 OpenAI API Key
   ```

### 运行方式

#### 命令行界面 (CLI)
```bash
python main.py
```

#### Web 界面 (Streamlit)
```bash
streamlit run app.py
```

## 核心功能

### 5 个核心 Agent

1. **需求澄清 Agent (ClarifyAgent)**：通过多轮对话澄清用户模糊需求，输出结构化需求卡片
2. **PRD 生成 Agent (PRDAgent)**：基于需求卡片生成完整产品需求文档
3. **技术方案 Agent (TechAgent)**：基于 PRD 生成技术实现方案
4. **测试用例 Agent (TestAgent)**：基于 PRD 和技术方案生成分级测试用例
5. **风险评估 Agent (RiskAgent)**：综合分析所有文档，输出风险评估报告

### 输出格式

- 结构化需求卡片 (JSON)
- 产品需求文档 (PRD) (JSON)
- 技术方案 (JSON)
- 测试用例 (JSON)
- 风险评估报告 (JSON)
- 完整需求分析报告 (Markdown)

## 项目结构

```
requirement-agent/
├── main.py                 # CLI 主入口
├── app.py                  # Streamlit Web UI
├── requirements.txt        # 项目依赖
├── .env.example            # 环境变量模板
├── README.md               # 本文件
├── agents/                 # Agent 实现
│   ├── __init__.py
│   ├── base_agent.py       # BaseAgent 基类
│   ├── clarify_agent.py    # 需求澄清 Agent
│   ├── prd_agent.py        # PRD 生成 Agent
│   ├── tech_agent.py       # 技术方案 Agent
│   ├── test_agent.py       # 测试用例 Agent
│   └── risk_agent.py       # 风险评估 Agent
├── models/                 # 数据模型
│   ├── __init__.py
│   └── schemas.py          # Pydantic Schema 定义
├── prompts/                # Prompt 模板
│   ├── __init__.py
│   ├── clarify_system.txt
│   ├── prd_system.txt
│   ├── tech_system.txt
│   ├── test_system.txt
│   └── risk_system.txt
├── core/                   # 核心组件
│   ├── __init__.py
│   ├── orchestrator.py     # 主编排器
│   ├── state_manager.py    # 状态持久化
│   └── output_generator.py # 报告生成器
├── utils/                  # 工具函数
│   ├── __init__.py
│   ├── retry.py            # 重试装饰器
│   └── validator.py        # 输出校验工具
└── output/                 # 输出目录（ gitignore 中）
```

## 配置说明

系统支持通过 `.env` 文件进行配置：

- `OPENAI_API_KEY`：OpenAI API 密钥（**必填**）
- `MODEL_NAME`：使用的模型名称（默认：`gpt-4o`）
- `MAX_RETRY_TIMES`：最大重试次数（默认：`3`）
- `MAX_CLARIFY_ROUNDS`：最大澄清轮数（默认：`5`）
- `OUTPUT_DIR`：输出目录（默认：`output`）

## 测试

项目包含完整的测试套件：

```bash
# 运行所有非 E2E 测试（快速）
pytest -m "not e2e"

# 运行单元测试
pytest tests/unit/

# 运行组件测试
pytest tests/component/

# 运行集成测试
pytest tests/integration/

# 运行 E2E 测试（需要 API Key）
pytest tests/e2e/ -m e2e -s
```

## 质量保障

- 所有输出必须通过 Pydantic Schema 校验
- PRD 字数 > 800 字
- 测试用例总数 ≥ 11 条（P0≥5 + P1≥3 + P2≥3）
- 风险报告必须给出明确的风险等级
- 单个 Agent 失败自动重试，最多 3 次
- 中间状态实时保存，支持断点恢复

## 许可证

MIT License