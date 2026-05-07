# Autoflow - 需求流程自动化智能体系统

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.30+-red.svg)](https://streamlit.io/)

从一句话需求到完整文档包 - 由 OpenAI GPT-4o 驱动的智能体系统。

---

## 🌟 项目简介

Autoflow 是一个**需求流程自动化智能体系统**，能够通过多轮对话澄清需求，自动生成：

- 📋 **需求卡片** - 结构化需求信息
- 📄 **产品需求文档（PRD）** - 完整的产品需求说明\
- ⚙️ **技术方案** - 架构设计、API设计、工作量估算\
- ✅ **测试用例** - P0/P1/P2 三级测试用例\
- ⚠️ **风险评估报告** - 量化风险评分与改进建议\

---

## ✨ 核心特性

| 特性 | 说明 |
|------|------|
| 🤖 **多智能体协作** | ClarifyAgent、PRDAgent、TechAgent、TestAgent、RiskAgent 协同工作 |
| 💬 **智能澄清对话** | 借鉴 YC Office Hours 六问，挑战需求真实性 |
| 📊 **中英文双语** | 侧边栏一键切换，支持中文/English |
| 🔄 **并行生成** | TechAgent 和 TestAgent 并行执行，提速50% |
| 📈 **架构审查** | 输出ASCII架构图、状态转换图、依赖清单 |
| 📉 **量化风险评估** | 1-10分评分，含触发条件、概率、影响范围 |
| 📥 **多格式下载** | 支持 Markdown 和 JSON 两种格式 |

---

## 🚀 快速开始

### 1. 克隆项目

```bash
git clone https://github.com/xuan599/Autoflow.git
cd Autoflow
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填入你的 OpenAI API Key
# OPENAI_API_KEY=your_api_key_here
# OPENAI_BASE_URL=https://api.openai.com/v1
# MODEL_NAME=gpt-4o
```

### 3. 安装依赖

```bash
# 创建虚拟环境（可选）
python -m venv venv

# 安装依赖
venv/Scripts/pip install -r requirements.txt
# 或
pip install -r requirements.txt
```

### 4. 启动应用

```bash
venv/Scripts/streamlit run app.py
# 或
streamlit run app.py
```

### 5. 访问应用

打开浏览器访问：**http://localhost:8501**

---

## 📖 使用流程

```
┌─────────────────┐
│  用户输入一句话需求（如："我想做一个用户积分兑换商品的功能"）  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────┐
│  多轮澄清对话（3-5轮）                              │
│  - 用户角色、业务背景、核心操作、约束条件              │
│  - 借鉴 YC Office Hours 六问，挑战需求真实性            │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────┐
│  自动生成全套文档（并行执行）                        │
│  ✅ PRD 文档（含用户故事、核心流程、异常流程）          │
│  ✅ 技术方案（含API设计、数据库变更、工作量估算）       │
│  ✅ 测试用例（P0×5 + P1×3 + P2×3）               │
│  ✅ 风险评估（量化评分 + 改进建议）                  │
└──────────────┬──────────────┘
               │
               ▼
┌─────────────────┐
│  查看结果 & 下载文档                                │
│  - Web界面查看（5个标签页）                         │
│  - 下载 Markdown 报告                              │
│  - 下载 JSON 文件（便于二次开发）                    │
└─────────────────┘
```

---

## 📂 项目结构

```
Autoflow/
├── agents/              # 智能体实现
│   ├── base_agent.py         # 基础智能体类
│   ├── clarify_agent.py     # 需求澄清智能体
│   ├── prd_agent.py         # PRD生成智能体
│   ├── tech_agent.py        # 技术方案智能体
│   ├── test_agent.py        # 测试用例智能体
│   └── risk_agent.py        # 风险评估智能体
├── core/                # 核心逻辑
│   ├── orchestrator.py     # 流程编排器
│   ├── output_generator.py # 输出生成器
│   └── state_manager.py   # 状态管理
├── models/              # 数据模型（Pydantic）
│   └── schemas.py
├── utils/               # 工具函数
│   ├── retry.py           # 重试装饰器
│   └── validator.py       # 输出验证
├── prompts/             # 提示词模板
│   ├── clarify_system.txt   # 澄清提示词（含YC六问）
│   ├── prd_system.txt      # PRD生成提示词
│   ├── tech_system.txt     # 技术方案提示词（含架构审查）
│   ├── test_system.txt     # 测试用例提示词
│   └── risk_system.txt    # 风险评估提示词（含量化评分）
├── docs/                # 项目文档
│   ├── PRD.md             # 产品需求文档
│   ├── 使用场景.md
│   ├── 闭环流程示例.md
│   └── 问题修复记录.md
├── app.py               # Streamlit Web UI
├── requirements.txt      # Python 依赖
├── .env.example         # 环境变量示例
└── README.md            # 本文件
```

---

## 🎯 使用场景

### 场景一：产品经理快速出PRD
**用户**：产品经理小王  
**需求**："做个用户积分兑换功能"  
**结果**：30分钟内生成完整PRD文档（原本需要2-3天）

### 场景二：技术负责人评估工作量
**用户**：技术Leader小李  
**需求**："开发社区团购团长管理后台"  
**结果**：自动生成技术方案 + 工作量估算（前端5天、后端8天、测试3天）

### 场景三：测试人员获取测试用例
**用户**：测试工程师小张  
**需求**：加载已有需求  
**结果**：自动生成P0/P1/P2三级测试用例（共15+个）

### 场景四：项目经理风险评估
**用户**：项目经理小赵  
**需求**：新功能上线前评估  
**结果**：量化风险评分（中风险7分）+ 改进建议

### 场景五：新人接手项目
**用户**：刚入职的开发小陈  
**需求**：快速理解需求和技术方案  
**结果**：通过历史会话快速了解项目全貌

---

## 🔧 技术栈

| 类别 | 技术 |
|------|------|
| **后端** | Python 3.12+ |
| **Web框架** | Streamlit 1.30+ |
| **AI模型** | OpenAI GPT-4o（支持自定义Base URL） |
| **数据验证** | Pydantic v2.13+ |
| **异步处理** | asyncio |
| **提示词工程** | 借鉴 GStack / Superpowers 方法论 |

---

## 📊 系统要求

| 要求 | 说明 |
|------|------|
| Python | 3.12 或更高版本 |
| OpenAI API Key | 有效且余额充足 |
| 内存 | 建议 4GB+ |
| 网络 | 能够访问 OpenAI API（或配置代理） |

---

## 🛠️ 已知问题 & 修复记录

详见 [问题修复记录.md](docs/问题修复记录.md)

**主要修复**：
- ✅ ClarifyAgent 状态重置问题
- ✅ OutputGenerator 硬编码目录问题
- ✅ 中英文切换功能
- ✅ 对话界面JSON显示问题

---

## 🤝 贡献指南

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📧 联系方式

- **项目地址**：https://github.com/xuan599/Autoflow
- **Issues**：https://github.com/xuan599/Autoflow/issues
- **作者**：Xuan (2717485102@qq.com)

---

## 🙏 致谢

- 提示词方法论借鉴自 [GStack](https://github.com/garrytan/gstack) 和 [Superpowers](https://github.com/obra/superpowers)
- UI框架使用 [Streamlit](https://streamlit.io/)
- AI模型由 [OpenAI](https://openai.com/) 提供