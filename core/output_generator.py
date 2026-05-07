import os
import json
from datetime import datetime
from pathlib import Path
from models.schemas import RequirementCard, PRDDocument, TechPlan, TestCases, RiskReport
from .state_manager import SessionState

class OutputGenerator:
    """Generates Markdown reports and saves JSON outputs"""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
    
    def save(self, session: SessionState) -> str:
        """Save all generated documents and return output path"""
        # Create session directory
        session_dir = os.path.join(self.output_dir, session.session_id)
        os.makedirs(session_dir, exist_ok=True)
        
        # Save JSON files
        if session.requirement_card:
            self._save_json(session_dir, "requirement_card.json", session.requirement_card.dict())
        
        if session.prd:
            self._save_json(session_dir, "prd.json", session.prd.dict())
        
        if session.tech_plan:
            self._save_json(session_dir, "tech_plan.json", session.tech_plan.dict())
        
        if session.test_cases:
            self._save_json(session_dir, "test_cases.json", session.test_cases.dict())
        
        if session.risk_report:
            self._save_json(session_dir, "risk_report.json", session.risk_report.dict())
        
        # Generate and save full report
        report_path = self._generate_markdown_report(session, session_dir)
        
        return report_path
    
    def _save_json(self, session_dir: str, filename: str, data: dict):
        """Save data as JSON file"""
        filepath = os.path.join(session_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _generate_markdown_report(self, session: SessionState, session_dir: str) -> str:
        """Generate full Markdown report"""
        lines = [
            "# 需求流程自动化报告",
            "",
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"会话ID: {session.session_id}",
            "",
            "---",
            ""
        ]
        
        # Requirement Card
        if session.requirement_card:
            lines.extend([
                "## 📋 需求卡片",
                "",
                f"**名称**: {session.requirement_card.name}",
                f"**背景**: {session.requirement_card.background}",
                f"**用户角色**: {', '.join(session.requirement_card.user_roles)}",
                f"**核心操作**: {'; '.join(session.requirement_card.core_actions)}",
                f"**约束条件**: {', '.join(session.requirement_card.constraints) if session.requirement_card.constraints else '无'}",
                f"**范围外**: {', '.join(session.requirement_card.out_of_scope) if session.requirement_card.out_of_scope else '无'}",
                f"**技术栈**: {session.requirement_card.tech_stack}",
                ""
            ])
        
        # PRD
        if session.prd:
            lines.extend([
                "## 📄 产品需求文档",
                "",
                f"**标题**: {session.prd.title}",
                f"**背景**: {session.prd.background}",
                "",
                "**用户故事**:",
                *[f"- {story}" for story in session.prd.user_stories],
                "",
                f"**核心流程**: {session.prd.core_flow}",
                "",
                f"**异常流程**: {session.prd.exception_flow}",
                "",
                f"**数据字段**: {', '.join(session.prd.data_fields)}",
                f"**非功能性需求**: {session.prd.non_functional}",
                f"**范围外**: {session.prd.out_of_scope}",
                ""
            ])
        
        # Tech Plan
        if session.tech_plan:
            lines.extend([
                "## ⚙️ 技术方案",
                "",
                f"**涉及模块**: {', '.join(session.tech_plan.involved_modules)}",
                "",
            ])
            if session.tech_plan.new_apis:
                lines.append("**新增API**:")
                for api in session.tech_plan.new_apis:
                    lines.append(f"- {api.name} ({api.method}): {api.description}")
                lines.append("")
            if session.tech_plan.modified_apis:
                lines.append(f"**修改API**: {', '.join(session.tech_plan.modified_apis)}")
                lines.append("")
            if session.tech_plan.db_changes:
                lines.append(f"**数据库变更**: {', '.join(session.tech_plan.db_changes)}")
                lines.append("")
            lines.extend([
                f"**工作量估算**: 前端{session.tech_plan.estimated_days.get('frontend', 0)}天, 后端{session.tech_plan.estimated_days.get('backend', 0)}天, 测试{session.tech_plan.estimated_days.get('testing', 0)}天",
                ""
            ])
            if session.tech_plan.tech_risks:
                lines.append("**技术风险**:")
                for risk in session.tech_plan.tech_risks:
                    lines.append(f"- {risk}")
                lines.append("")
        
        # Test Cases
        if session.test_cases:
            lines.extend([
                "## ✅ 测试用例",
                "",
                f"**用例总数**: {session.test_cases.total_count}",
                "",
                "### P0 主流程用例",
                *[f"- {case.precondition}" for case in session.test_cases.main_flow_cases[:3]],
                "",
                "### P1 异常场景用例",
                *[f"- {case.precondition}" for case in session.test_cases.exception_cases[:3]],
                "",
                "### P2 边界场景用例",
                *[f"- {case.precondition}" for case in session.test_cases.boundary_cases[:3]],
                ""
            ])
        
        # Risk Report
        if session.risk_report:
            lines.extend([
                "## ⚠️ 风险评估",
                "",
                f"**风险等级**: {session.risk_report.risk_level}",
                f"**需要人工审核**: {'是' if session.risk_report.needs_human_review else '否'}",
                "",
            ])
            if session.risk_report.risk_points:
                lines.append("**风险点**:")
                for point in session.risk_report.risk_points:
                    lines.append(f"- {point}")
                lines.append("")
            if session.risk_report.suggestions:
                lines.append("**改进建议**:")
                for suggestion in session.risk_report.suggestions:
                    lines.append(f"- {suggestion}")
                lines.append("")
        
        # Save report
        report_path = os.path.join(session_dir, "full_report.md")
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        return report_path
    
