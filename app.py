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

def update_progress(progress, status):
    """Update progress bar and status"""
    st.session_state.progress = progress
    st.session_state.status = status
    progress_bar.progress(progress / 100)
    status_text.text(status)

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
        
        # Tab 1: Requirement Card
        with tab1:
            if session.requirement_card:
                card = session.requirement_card
                st.text_input(t('name'), value=card.name, disabled=True)
                st.text_area(t('background'), value=card.background, height=100, disabled=True)
                st.text_input(t('user_roles'), value=", ".join(card.user_roles), disabled=True)
                st.text_area(t('core_actions'), value="\n".join(card.core_actions), height=100, disabled=True)
                st.text_area(t('constraints'), value="\n".join(card.constraints) if card.constraints else t('none'), height=100, disabled=True)
                st.text_area(t('out_of_scope'), value="\n".join(card.out_of_scope) if card.out_of_scope else t('none'), height=100, disabled=True)
                st.text_input(t('tech_stack'), value=card.tech_stack, disabled=True)
                st.checkbox(t('complete'), value=card.is_complete, disabled=True)
            else:
                st.warning(t('no_requirement_card'))
        
        # Tab 2: PRD
        with tab2:
            if session.prd:
                prd = session.prd
                st.text_input(t('title'), value=prd.title, disabled=True)
                st.text_area(t('background'), value=prd.background, height=100, disabled=True)
                st.text_area(t('user_stories'), value="\n".join(prd.user_stories), height=150, disabled=True)
                st.text_area(t('core_flow'), value=prd.core_flow, height=150, disabled=True)
                st.text_area(t('exception_flow'), value=prd.exception_flow, height=150, disabled=True)
                st.text_area(t('data_fields'), value="\n".join(prd.data_fields), height=100, disabled=True)
                st.text_area(t('non_functional'), value=prd.non_functional, height=100, disabled=True)
                st.text_area(t('out_of_scope'), value=prd.out_of_scope, height=100, disabled=True)
            else:
                st.warning(t('no_prd'))
        
        # Tab 3: Tech Plan
        with tab3:
            if session.tech_plan:
                plan = session.tech_plan
                st.text_area(t('involved_modules'), value="\n".join(plan.involved_modules), height=100, disabled=True)
                
                if plan.new_apis:  
                    st.subheader(t('new_apis'))
                    for api in plan.new_apis:  
                        with st.expander(f"{api.name} ({api.method})"):  
                            st.text(f"{t('description')}: {api.description}")  
                            st.text(f"{t('params')}: {', '.join(api.params) if api.params else t('none')}")  
                            st.text(f"{t('response')}: {api.response}")  
                
                if plan.modified_apis:  
                    st.subheader(t('modified_apis'))  
                    for api in plan.modified_apis:  
                        st.text(f"- {api}")  
                
                st.text_area(t('database_changes'), value="\n".join(plan.db_changes) if plan.db_changes else t('none'), height=100, disabled=True)  
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric(t('frontend_days'), plan.estimated_days.get('frontend', 0))  
                with col2:
                    st.metric(t('backend_days'), plan.estimated_days.get('backend', 0))  
                with col3:  
                    st.metric(t('testing_days'), plan.estimated_days.get('testing', 0))  
                
                st.text_area(t('technical_risks'), value="\n".join(plan.tech_risks) if plan.tech_risks else t('none'), height=100, disabled=True)  
            else:  
                st.warning(t('no_tech_plan'))  
        
        # Tab 4: Test Cases  
        with tab4:  
            if session.test_cases:  
                cases = session.test_cases  
                st.metric(t('total_cases'), cases.total_count)  
                
                col1, col2, col3 = st.columns(3)  
                with col1:  
                    st.metric(t('p0_main_flow'), len(cases.main_flow_cases))  
                with col2:  
                    st.metric(t('p1_exception'), len(cases.exception_cases))  
                with col3:  
                    st.metric(t('p2_boundary'), len(cases.boundary_cases))  
                
                st.subheader(t('p0_cases'))  
                for i, case in enumerate(cases.main_flow_cases, 1):  
                    with st.expander(t('case', i, case.precondition[:30])):  
                        st.text(f"{t('priority')}: {case.priority}")  
                        st.text(f"{t('precondition')}: {case.precondition}")  
                        st.text(f"{t('steps')}: {case.steps}")  
                        st.text(f"{t('expected')}: {case.expected}")  
                
                st.subheader(t('p1_cases'))  
                for i, case in enumerate(cases.exception_cases, 1):  
                    with st.expander(t('case', i, case.precondition[:30])):  
                        st.text(f"{t('priority')}: {case.priority}")  
                        st.text(f"{t('precondition')}: {case.precondition}")  
                        st.text(f"{t('steps')}: {case.steps}")  
                        st.text(f"{t('expected')}: {case.expected}")  
                
                st.subheader(t('p2_cases'))  
                for i, case in enumerate(cases.boundary_cases, 1):  
                    with st.expander(t('case', i, case.precondition[:30])):  
                        st.text(f"{t('priority')}: {case.priority}")  
                        st.text(f"{t('precondition')}: {case.precondition}")  
                        st.text(f"{t('steps')}: {case.steps}")  
                        st.text(f"{t('expected')}: {case.expected}")  
            else:  
                st.warning(t('no_test_cases'))  
        
        # Tab 5: Risk Report  
        with tab5:  
            if session.risk_report:  
                report = session.risk_report  
                risk_emoji = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(report.risk_level, "⚪")  
                st.metric(t('risk_level'), f"{risk_emoji} {report.risk_level}")  
                st.checkbox(t('human_review'), value=report.needs_human_review, disabled=True)  
                
                st.text_area(t('risk_points'), value="\n".join(report.risk_points) if report.risk_points else t('none'), height=100, disabled=True)  
                st.text_area(t('suggestions'), value="\n".join(report.suggestions) if report.suggestions else t('none'), height=100, disabled=True)  
                st.text_area(t('uncovered_scenarios'), value="\n".join(report.uncovered_scenarios) if report.uncovered_scenarios else t('none'), height=100, disabled=True)  
            else:  
                st.warning(t('no_risk_report'))  
        
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
