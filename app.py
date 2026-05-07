#!/usr/bin/env python3
"""
Streamlit Web UI for the Requirement Flow Automation Agent System
"""
import streamlit as st
import asyncio
import os
import json
import time
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Text dictionary for i18n (must be defined before page config)
TEXTS = {
    'en': {
        'page_title': 'Requirement Flow Automation Agent System',
        'page_icon': '🤖',
        'page_caption': 'From one-sentence requirement to complete documentation package',
        'sidebar_title': '🤖 Agent System',
        'sidebar_caption': 'Requirement Flow Automation',
        'api_key_missing': '⚠️ OPENAI_API_KEY not set!',
        'session_info': 'Session Info',
        'session_id': 'Session: {}',
        'stage': 'Stage: {}',
        'no_active_session': 'No active session',
        'history': 'History',
        'new_requirement': '🔄 New Requirement',
        'requirement_clarification': '💬 Requirement Clarification',
        'enter_requirement': 'Enter your requirement (one sentence is enough)',
        'agent_thinking': '🤔 Agent is thinking...',
        'clarification_complete': 'Clarification complete! Starting document generation...',
        'clarification_round': 'Clarification round {}...',
        'document_generation': '⚙️ Document Generation',
        'starting_prd': 'Starting PRD generation...',
        'prd_complete': 'PRD generation complete!',
        'running_tech_test': 'Running Tech and Test agents in parallel...',
        'tech_test_complete': 'Tech plan and test cases complete!',
        'risk_complete': 'Risk assessment complete!',
        'generating_documents': 'Generating documents...',
        'all_completed': '✅ All tasks completed!',
        'generation_failed': 'Generation failed: {}',
        'retry': 'Retry',
        'generation_results': '📊 Generation Results',
        'requirement_card': '📋 Requirement Card',
        'prd': '📄 PRD',
        'tech_plan': '⚙️ Tech Plan',
        'test_cases': '✅ Test Cases',
        'risk_report': '⚠️ Risk Report',
        'no_requirement_card': 'No requirement card generated',
        'no_prd': 'No PRD generated',
        'no_tech_plan': 'No tech plan generated',
        'no_test_cases': 'No test cases generated',
        'no_risk_report': 'No risk report generated',
        'name': 'Name',
        'background': 'Background',
        'user_roles': 'User Roles',
        'core_actions': 'Core Actions',
        'constraints': 'Constraints',
        'out_of_scope': 'Out of Scope',
        'tech_stack': 'Tech Stack',
        'complete': 'Complete',
        'title': 'Title',
        'user_stories': 'User Stories',
        'core_flow': 'Core Flow',
        'exception_flow': 'Exception Flow',
        'data_fields': 'Data Fields',
        'non_functional': 'Non-functional',
        'involved_modules': 'Involved Modules',
        'new_apis': 'New APIs',
        'modified_apis': 'Modified APIs',
        'database_changes': 'Database Changes',
        'frontend_days': 'Front-end Days',
        'backend_days': 'Back-end Days',
        'testing_days': 'Testing Days',
        'technical_risks': 'Technical Risks',
        'total_cases': 'Total Cases',
        'p0_main_flow': 'P0 Main Flow',
        'p1_exception': 'P1 Exception',
        'p2_boundary': 'P2 Boundary',
        'p0_cases': 'P0 Main Flow Cases',
        'p1_cases': 'P1 Exception Cases',
        'p2_cases': 'P2 Boundary Cases',
        'priority': 'Priority',
        'precondition': 'Precondition',
        'steps': 'Steps',
        'expected': 'Expected',
        'risk_level': 'Risk Level',
        'human_review': 'Human Review Required',
        'risk_points': 'Risk Points',
        'suggestions': 'Suggestions',
        'uncovered_scenarios': 'Uncovered Scenarios',
        'download_files': '📥 Download Files',
        'download_report': '📄 Download Report',
        'download_card': '📋 Card JSON',
        'download_prd': '📄 PRD JSON',
        'download_tech': '⚙️ Tech JSON',
        'download_tests': '✅ Tests JSON',
        'footer': 'Requirement Flow Automation Agent System v1.0 | Powered by OpenAI GPT-4o',
        'none': 'None',
        'description': 'Description',
        'params': 'Params',
        'response': 'Response',
        'case': 'Case {}: {}...',
    },
    'zh': {
        'page_title': '需求流程自动化智能体系统',
        'page_icon': '🤖',
        'page_caption': '从一句话需求到完整文档包',
        'sidebar_title': '🤖 智能体系统',
        'sidebar_caption': '需求流程自动化',
        'api_key_missing': '⚠️ 未设置 OPENAI_API_KEY！',
        'session_info': '会话信息',
        'session_id': '会话: {}',
        'stage': '阶段: {}',
        'no_active_session': '无活动会话',
        'history': '历史记录',
        'new_requirement': '🔄 新建需求',
        'requirement_clarification': '💬 需求澄清',
        'enter_requirement': '输入您的需求（一句话即可）',
        'agent_thinking': '🤔 智能体思考中...',
        'clarification_complete': '澄清完成！开始生成文档...',
        'clarification_round': '澄清轮次 {}...',
        'document_generation': '⚙️ 文档生成',
        'starting_prd': '开始生成PRD...',
        'prd_complete': 'PRD生成完成！',
        'running_tech_test': '并行运行技术方案和测试用例智能体...',
        'tech_test_complete': '技术方案和测试用例生成完成！',
        'risk_complete': '风险评估完成！',
        'generating_documents': '正在生成文档...',
        'all_completed': '✅ 所有任务完成！',
        'generation_failed': '生成失败: {}',
        'retry': '重试',
        'generation_results': '📊 生成结果',
        'requirement_card': '📋 需求卡片',
        'prd': '📄 产品需求文档',
        'tech_plan': '⚙️ 技术方案',
        'test_cases': '✅ 测试用例',
        'risk_report': '⚠️ 风险评估',
        'no_requirement_card': '未生成需求卡片',
        'no_prd': '未生成PRD',
        'no_tech_plan': '未生成技术方案',
        'no_test_cases': '未生成测试用例',
        'no_risk_report': '未生成风险评估',
        'name': '名称',
        'background': '背景',
        'user_roles': '用户角色',
        'core_actions': '核心操作',
        'constraints': '约束条件',
        'out_of_scope': '范围外',
        'tech_stack': '技术栈',
        'complete': '完成',
        'title': '标题',
        'user_stories': '用户故事',
        'core_flow': '核心流程',
        'exception_flow': '异常流程',
        'data_fields': '数据字段',
        'non_functional': '非功能性需求',
        'involved_modules': '涉及模块',
        'new_apis': '新增API',
        'modified_apis': '修改API',
        'database_changes': '数据库变更',
        'frontend_days': '前端天数',
        'backend_days': '后端天数',
        'testing_days': '测试天数',
        'technical_risks': '技术风险',
        'total_cases': '用例总数',
        'p0_main_flow': 'P0 主流程',
        'p1_exception': 'P1 异常场景',
        'p2_boundary': 'P2 边界场景',
        'p0_cases': 'P0 主流程用例',
        'p1_cases': 'P1 异常场景用例',
        'p2_cases': 'P2 边界场景用例',
        'priority': '优先级',
        'precondition': '前置条件',
        'steps': '步骤',
        'expected': '预期结果',
        'risk_level': '风险等级',
        'human_review': '需要人工审核',
        'risk_points': '风险点',
        'suggestions': '改进建议',
        'uncovered_scenarios': '未覆盖场景',
        'download_files': '📥 下载文件',
        'download_report': '📄 下载报告',
        'download_card': '📋 需求卡片JSON',
        'download_prd': '📄 PRD JSON',
        'download_tech': '⚙️ 技术方案JSON',
        'download_tests': '✅ 测试用例JSON',
        'footer': '需求流程自动化智能体系统 v1.0 | 由 OpenAI GPT-4o 驱动',
        'none': '无',
        'description': '描述',
        'params': '参数',
        'response': '返回',
        'case': '用例 {}: {}...',
    }
}

def t(key, *args):
    """Get text for current language"""
    lang = st.session_state.get('lang', 'zh')
    text = TEXTS[lang].get(key, key)
    if args:
        return text.format(*args)
    return text

# Page config (must be after t() function is defined)
st.set_page_config(
    page_title=t('page_title'),
    page_icon=t('page_icon'),
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    /* Main container */
    .main .block-container {
        padding-top: 2rem;
        padding-left: 5%;
        padding-right: 5%;
    }
    
    /* Chat messages */
    .stChatMessage {
        border-radius: 10px;
        padding: 0.5rem;
        margin-bottom: 0.5rem;
    }
    
    /* User message */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #f0f2f6;
    }
    
    /* Assistant message */
    .stChatMessage[data-testid="stChatMessage"]:nth-child(even) {
        background-color: #e8f4fd;
    }
    
    /* Progress bar */
    .stProgress > div > div > div {
        background-color: #4CAF50;
    }
    
    /* Metric cards */
    .stMetric {
        background-color: #f9f9f9;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #333;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background-color: #4CAF50;
        color: white;
        border-radius: 6px;
        border: none;
        padding: 0.5rem 1rem;
    }
    
    .stDownloadButton > button:hover {
        background-color: #45a049;
    }
    
    /* Sidebar */
    .css-1d391kg {
        background-color: #f8f9fa;
    }
    
    /* Tabs */
    .stTabs [data-baseweb-tabs-list] {
        background-color: #f0f2f6;
        border-radius: 8px;
        padding: 0.5rem;
    }
    
    .stTabs [data-baseweb-tabs-tab] {
        border-radius: 6px;
        padding: 0.5rem 1rem;
    }
    
    .stTabs [data-baseweb-tabs-tab][aria-selected="true"] {
        background-color: #4CAF50;
        color: white;
    }
    
    /* Status text */
    .element-container [data-testid="stText"] {
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize Streamlit session state"""
    if 'lang' not in st.session_state:
        st.session_state.lang = 'zh'  # Default: Chinese
    if 'orchestrator' not in st.session_state:
        from core.orchestrator import Orchestrator
        st.session_state.orchestrator = Orchestrator()
    if 'stage' not in st.session_state:
        st.session_state.stage = 'initialized'  # initialized/clarifying/generating/done
    if 'messages' not in st.session_state:
        st.session_state.messages = []  # Chat history for clarification
    if 'session' not in st.session_state:
        st.session_state.session = None  # Final session results
    if 'progress' not in st.session_state:
        st.session_state.progress = 0
    if 'status' not in st.session_state:
        st.session_state.status = ""

init_session_state()

# Sidebar
with st.sidebar:
    # Language selector
    lang = st.selectbox('Language / 语言', options=['zh', 'en'], format_func=lambda x: '中文' if x == 'zh' else 'English', index=0 if st.session_state.lang == 'zh' else 1)
    if lang != st.session_state.lang:
        st.session_state.lang = lang
        st.rerun()
    
    st.title(t('sidebar_title'))
    st.caption(t('sidebar_caption'))
    
    st.divider()
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        st.error(t('api_key_missing'))
        st.stop()
    
    # Session info
    st.subheader(t('session_info'))
    if st.session_state.session:
        st.text(t('session_id', st.session_state.session.session_id))
        st.text(t('stage', st.session_state.stage))
    else:
        st.text(t('no_active_session'))
    
    st.divider()
    
    # History
    st.subheader(t('history'))
    output_dir = "output"
    if os.path.exists(output_dir):
        sessions = sorted([d for d in os.listdir(output_dir) if os.path.isdir(os.path.join(output_dir, d))], reverse=True)
        for session_id in sessions[:5]:
            if st.button(f"📄 {session_id}", key=f"session_{session_id}"):
                from core.state_manager import SessionState
                session = SessionState.load(session_id, output_dir)
                if session:
                    st.session_state.session = session
                    st.session_state.stage = session.current_stage
                    st.rerun()
    
    st.divider()
    
    # New requirement button
    if st.button(t('new_requirement'), use_container_width=True):
        # 重新创建 Orchestrator，重置所有agent状态
        from core.orchestrator import Orchestrator
        st.session_state.orchestrator = Orchestrator()
        st.session_state.stage = 'initialized'
        st.session_state.messages = []
        st.session_state.session = None
        st.session_state.progress = 0
        st.session_state.status = ""
        st.rerun()

# Main area
st.title(f"{t('page_icon')} {t('page_title')}")
st.caption(t('page_caption'))

# Progress bar and status
progress_bar = st.empty()
status_text = st.empty()
progress_container = st.container()

def update_progress(progress, status):
    """Update progress bar and status with visual indicators"""
    st.session_state.progress = progress
    st.session_state.status = status
    
    with progress_container:
        # Progress bar
        progress_bar.progress(progress / 100)
        
        # Status with icons
        if progress < 30:
            icon = "💬"
            stage_name = t('requirement_clarification')
        elif progress < 50:
            icon = "📄"
            stage_name = t('starting_prd')
        elif progress < 70:
            icon = "⚙️"
            stage_name = t('running_tech_test')
        elif progress < 90:
            icon = "✅"
            stage_name = t('tech_test_complete')
        elif progress < 100:
            icon = "⚠️"
            stage_name = t('risk_complete')
        else:
            icon = "✅"
            stage_name = t('all_completed')
        
        status_text.markdown(f"{icon} **{stage_name}** - {status}")

# Clarification stage
if st.session_state.stage in ['initialized', 'clarifying']:
    st.subheader(t('requirement_clarification'))
    
    # Display chat messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    
    # User input
    if prompt := st.chat_input(t('enter_requirement')):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        with st.chat_message("user"):
            st.write(prompt)
        
        # Show agent thinking
        with st.chat_message("assistant"):
            thinking = st.empty()
            thinking.text(t('agent_thinking'))
            
            # Run clarification
            async def run_clarify():
                orchestrator = st.session_state.orchestrator
                
                # Set up progress callback
                def on_progress(stage, progress, message):
                    update_progress(progress, message)
                
                orchestrator.on_progress = on_progress
                
                # Run clarification
                result = await orchestrator.run_clarify_stage(prompt if len(st.session_state.messages) <= 2 else "")
                return result
            
            # Run async function
            result = asyncio.run(run_clarify())
            
            # Display response
            thinking.text(result["response"])
            st.session_state.messages.append({"role": "assistant", "content": result["response"]})
            
            # Check if done
            if result["is_done"]:
                st.session_state.stage = 'generating'
                update_progress(20, t('clarification_complete'))
                st.rerun()
            else:
                update_progress(10 + result["round"] * 2, t('clarification_round', result['round']))

# Generation stage
elif st.session_state.stage == 'generating':
    st.subheader(t('document_generation'))
    
    # Progress bar
    if st.session_state.progress < 30:
        update_progress(30, t('starting_prd'))
    elif st.session_state.progress < 50:
        update_progress(40, t('prd_complete'))
    elif st.session_state.progress < 70:
        update_progress(50, t('running_tech_test'))
    elif st.session_state.progress < 90:
        update_progress(70, t('tech_test_complete'))
    elif st.session_state.progress < 100:
        update_progress(90, t('risk_complete'))
    
    # Run generation
    if not st.session_state.session or st.session_state.session.current_stage != 'done':
        async def run_generation():
            orchestrator = st.session_state.orchestrator
            
            # Set up progress callback 
            def on_progress(stage, progress, message):
                update_progress(progress, message)
            
            orchestrator.on_progress = on_progress
            
            # Run generation stage
            result = await orchestrator.run_generation_stage()
            return result
        
        with st.spinner(t('generating_documents')):
            try:
                result = asyncio.run(run_generation())
                st.session_state.session = st.session_state.orchestrator.session
                st.session_state.stage = 'done'
                update_progress(100, t('all_completed'))
                st.success(t('all_completed'))
                time.sleep(1)
                st.rerun()
            except Exception as e:
                st.error(t('generation_failed', str(e)))
                if st.button(t('retry')):
                    st.rerun()

# Results display
elif st.session_state.stage == 'done':
    st.subheader(t('generation_results'))
    
    session = st.session_state.session
    
    if session:
        # Tabs for different sections
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            t('requirement_card'), 
            t('prd'),  
            t('tech_plan'),  
            t('test_cases'),  
            t('risk_report')  
        ])
        
        # Tab 1: Requirement Card (美化版）
        with tab1:
            if session.requirement_card:
                card = session.requirement_card
                # 使用容器和图标美化
                with st.container():
                    st.markdown(f"### 📋 {card.name}")
                    st.markdown("---")
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{t('background')}**：{card.background}")
                    with col2:
                        status = "✅ 完整" if card.is_complete else "⚠️ 待完善"
                        st.markdown(f"**状态**：{status}")
                    
                    st.markdown(f"**{t('user_roles')}**：{', '.join(card.user_roles)}")
                    
                    st.markdown(f"**{t('core_actions')}**：")
                    for action in card.core_actions:
                        st.markdown(f"- {action}")
                    
                    if card.constraints:
                        st.markdown(f"**{t('constraints')}**：")
                        for c in card.constraints:
                            st.markdown(f"- {c}")
                    else:
                        st.markdown(f"**{t('constraints')}**：{t('none')}")
                    
                    if card.out_of_scope:
                        st.markdown(f"**{t('out_of_scope')}**：")
                        for o in card.out_of_scope:
                            st.markdown(f"- {o}")
                    else:
                        st.markdown(f"**{t('out_of_scope')}**：{t('none')}")
                    
                    st.markdown(f"**{t('tech_stack')}**：{card.tech_stack}")
            else:
                st.warning(t('no_requirement_card'))
                st.info("请先通过对话生成需求卡片")
        
        # Tab 2: PRD (美化版）
        with tab2:
            if session.prd:
                prd = session.prd
                with st.container():
                    st.markdown(f"### 📄 {prd.title}")
                    st.markdown("---")
                    
                    st.markdown(f"**{t('background')}**：{prd.background}")
                    
                    st.markdown(f"**{t('user_stories')}**：")
                    for story in prd.user_stories:
                        st.markdown(f"- {story}")
                    
                    st.markdown(f"**{t('core_flow')}**：")
                    st.markdown(prd.core_flow)
                    
                    st.markdown(f"**{t('exception_flow')}**：")
                    st.markdown(prd.exception_flow)
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"**{t('data_fields')}**：")
                        for field in prd.data_fields:
                            st.markdown(f"- {field}")
                    with col2:
                        st.markdown(f"**{t('non_functional')}**：")
                        st.markdown(prd.non_functional)
                    
                    st.markdown(f"**{t('out_of_scope')}**：{prd.out_of_scope}")
            else:
                st.warning(t('no_prd'))
                st.info("请先完成需求澄清，系统将自动生成PRD文档")
        
        # Tab 3: Tech Plan (美化版）
        with tab3:
            if session.tech_plan:
                plan = session.tech_plan
                with st.container():
                    st.markdown(f"### ⚙️ {t('tech_plan')}")
                    st.markdown("---")
                    
                    # 涉及模块
                    st.markdown(f"**{t('involved_modules')}**：")
                    for mod in plan.involved_modules:
                        st.markdown(f"🔹 {mod}")
                    
                    # 新增API
                    if plan.new_apis:  
                        st.markdown(f"**{t('new_apis')}**：")
                        for api in plan.new_apis:  
                            with st.expander(f"🔌 {api.name} ({api.method})"):  
                                st.markdown(f"**{t('description')}**：{api.description}")  
                                st.markdown(f"**{t('params')}**：{', '.join(api.params) if api.params else t('none')}")  
                                st.markdown(f"**{t('response')}**：{api.response}")  
                    
                    # 修改API
                    if plan.modified_apis:  
                        st.markdown(f"**{t('modified_apis')}**：")  
                        for api in plan.modified_apis:  
                            st.markdown(f"✏️ {api}")  
                    
                    # 数据库变更
                    if plan.db_changes:
                        st.markdown(f"**{t('database_changes')}**：")
                        for change in plan.db_changes:
                            st.markdown(f"🗄️ {change}")
                    else:
                        st.markdown(f"**{t('database_changes')}**：{t('none')}")
                    
                    # 工作量估算
                    st.markdown(f"**{t('estimated_days')}**：")
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric(label=t('frontend_days'), value=plan.estimated_days.get('frontend', 0), help="前端开发天数")
                    with col2:
                        st.metric(label=t('backend_days'), value=plan.estimated_days.get('backend', 0), help="后端开发天数")
                    with col3:  
                        st.metric(label=t('testing_days'), value=plan.estimated_days.get('testing', 0), help="测试验证天数")
                    
                    # 技术风险
                    if plan.tech_risks:
                        st.markdown(f"**{t('technical_risks')}**：")
                        for risk in plan.tech_risks:
                            st.markdown(f"⚠️ {risk}")
                    else:
                        st.markdown(f"**{t('technical_risks')}**：{t('none')}")
            else:  
                st.warning(t('no_tech_plan'))
                st.info("请先完成需求澄清，系统将自动生成技术方案")
        
        # Tab 4: Test Cases (美化版）
        with tab4:  
            if session.test_cases:  
                cases = session.test_cases  
                
                # 统计卡片
                st.markdown("### ✅ 测试用例总览")
                col1, col2, col3 = st.columns(3)  
                with col1:  
                    st.metric(label="🔹 P0 主流程", value=len(cases.main_flow_cases), help="核心流程用例，必须全部通过")
                with col2:  
                    st.metric(label="⚠️ P1 异常场景", value=len(cases.exception_cases), help="异常处理用例，验证系统健壮性")
                with col3:  
                    st.metric(label="🎯 P2 边界场景", value=len(cases.boundary_cases), help="边界条件用例，验证极值处理")
                
                # P0 主流程用例
                if cases.main_flow_cases:
                    st.markdown("#### 🔹 P0 主流程用例")
                    for i, case in enumerate(cases.main_flow_cases, 1):  
                        with st.expander(f"💎 用例 {i}: {case.precondition[:30]}..."):  
                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                st.markdown(f"**优先级**\nP0")
                            with col_b:
                                st.markdown(f"**前置条件**\n{case.precondition}")
                            st.markdown(f"**步骤**\n{case.steps}")
                            st.success(f"**预期结果**: {case.expected}")
                
                # P1 异常场景用例
                if cases.exception_cases:
                    st.markdown("#### ⚠️ P1 异常场景用例")
                    for i, case in enumerate(cases.exception_cases, 1):  
                        with st.expander(f"⚠️ 用例 {i}: {case.precondition[:30]}..."):  
                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                st.markdown(f"**优先级**\nP1")
                            with col_b:
                                st.markdown(f"**前置条件**\n{case.precondition}")
                            st.markdown(f"**步骤**\n{case.steps}")
                            st.warning(f"**预期结果**: {case.expected}")
                
                # P2 边界场景用例
                if cases.boundary_cases:
                    st.markdown("#### 🎯 P2 边界场景用例")
                    for i, case in enumerate(cases.boundary_cases, 1):  
                        with st.expander(f"🎯 用例 {i}: {case.precondition[:30]}..."):  
                            col_a, col_b = st.columns([1, 3])
                            with col_a:
                                st.markdown(f"**优先级**\nP2")
                            with col_b:
                                st.markdown(f"**前置条件**\n{case.precondition}")
                            st.markdown(f"**步骤**\n{case.steps}")
                            st.info(f"**预期结果**: {case.expected}")
            else:  
                st.warning(t('no_test_cases'))
                st.info("请先完成需求澄清，系统将自动生成测试用例")
        
        # Tab 5: Risk Report (美化版）
        with tab5:  
            if session.risk_report:  
                report = session.risk_report  
                
                # 风险等级显示（带颜色）
                risk_color = {"High": "#ff4444", "Medium": "#ffa500", "Low": "#00cc00"}.get(report.risk_level, "#666666")
                risk_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(report.risk_level, "⚪")
                
                st.markdown(f"### ⚠️ {t('risk_report')}")
                st.markdown("---")
                
                # 风险等级卡片
                col1, col2 = st.columns([1, 3])
                with col1:
                    st.metric(label="风险等级", value=f"{risk_emoji} {report.risk_level}", 
                             help="High: 需立即处理 | Medium: 需补充内容 | Low: 可直接进行")
                with col2:
                    human_review = "✅ 需要" if report.needs_human_review else "❌ 不需要"
                    st.metric(label=t('human_review'), value=human_review)
                
                # 风险点
                if report.risk_points:
                    st.markdown(f"**{t('risk_points')}**：")
                    for i, point in enumerate(report.risk_points, 1):
                        st.markdown(f"🔹 **{i}.** {point}")
                else:
                    st.markdown(f"**{t('risk_points')}**：{t('none')}")
                
                # 改进建议
                if report.suggestions:
                    st.markdown(f"**{t('suggestions')}**：")
                    for i, sug in enumerate(report.suggestions, 1):
                        st.markdown(f"💡 **{i}.** {sug}")
                else:
                    st.markdown(f"**{t('suggestions')}**：{t('none')}")
                
                # 未覆盖场景
                if report.uncovered_scenarios:
                    st.markdown(f"**{t('uncovered_scenarios')}**：")
                    for i, scene in enumerate(report.uncovered_scenarios, 1):
                        st.markdown(f"🎯 **{i}.** {scene}")
                else:
                    st.markdown(f"**{t('uncovered_scenarios')}**：{t('none')}")
            else:  
                st.warning(t('no_risk_report'))
                st.info("请先完成需求澄清，系统将自动生成风险评估报告")
        
        # Download buttons  
        st.divider()  
        st.subheader(t('download_files'))  
        
        session_dir = Path("output") / session.session_id  
        if session_dir.exists():  
            col1, col2, col3, col4, col5 = st.columns(5)  
            
            with col1:  
                report_file = session_dir / "full_report.md"  
                if report_file.exists():  
                    with open(report_file, 'r', encoding='utf-8') as f:  
                        st.download_button(t('download_report'), f.read(), file_name="full_report.md")  
            
            with col2:  
                card_file = session_dir / "requirement_card.json"  
                if card_file.exists():  
                    with open(card_file, 'r', encoding='utf-8') as f:  
                        st.download_button(t('download_card'), f.read(), file_name="requirement_card.json")  
            
            with col3:  
                prd_file = session_dir / "prd.json"  
                if prd_file.exists():  
                    with open(prd_file, 'r', encoding='utf-8') as f:  
                        st.download_button(t('download_prd'), f.read(), file_name="prd.json")  
            
            with col4:  
                tech_file = session_dir / "tech_plan.json"  
                if tech_file.exists():  
                    with open(tech_file, 'r', encoding='utf-8') as f:  
                        st.download_button(t('download_tech'), f.read(), file_name="tech_plan.json")  
            
            with col5:  
                test_file = session_dir / "test_cases.json"  
                if test_file.exists():  
                    with open(test_file, 'r', encoding='utf-8') as f:  
                        st.download_button(t('download_tests'), f.read(), file_name="test_cases.json")  

# Footer
st.divider()
st.caption(t('footer'))

# Streamlit runs this file directly, no main() needed
