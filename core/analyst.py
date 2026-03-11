"""
V6.3.1 分析师角色

职责：
1. 生成投资分析报告
2. 响应挑战者的质疑
3. 执行改进ToDo
4. 输出最终报告
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class Analyst:
    """分析师角色 - 主链路"""
    
    SYSTEM_PROMPT = """你是资深投资分析师，擅长深度价值投资分析。

你的分析风格：
- 聚焦企业本身，不纠结元数据
- 财务数据要具体讨论，不抽象表述
- 护城河要深入本质，不停留在表面
- 每个结论都有证据支撑
- 最终给出明确的投资建议

你的报告结构：
1. 执行摘要（估值判断、投资建议、核心逻辑、关键风险）
2. 业务分析（商业模式、护城河）
3. 财务质量分析（ROIC/ROE趋势、现金流、债务）
4. 竞争格局
5. 管理层分析
6. 估值分析
7. 投资决策"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
    
    def generate_initial_report(self, company: str, data: Dict[str, Any]) -> str:
        """生成初始报告（V1）"""
        
        prompt = f"""请为 {company} 生成投资价值分析报告。

## 已收集数据

{self._format_data(data)}

## 输出要求

生成结构化投资分析报告，包含：
1. 执行摘要
2. 业务分析
3. 财务质量分析
4. 竞争格局
5. 管理层分析
6. 估值分析
7. 投资决策

重要：
- 每个关键结论都要引用原文（使用 > 📌 引用格式）
- 财务数据要具体讨论，不要抽象表述
- 护城河要分析本质，不要停留在表面"""
        
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
    
    def improve_report(
        self, 
        current_report: str, 
        challenges: List[Dict], 
        todos: List[Dict],
        new_evidence: Dict[str, Any] = None
    ) -> str:
        """根据挑战和ToDo改进报告"""
        
        challenges_text = self._format_challenges(challenges)
        todos_text = self._format_todos(todos)
        evidence_text = self._format_evidence(new_evidence) if new_evidence else "无新证据"
        
        prompt = f"""请根据挑战者的反馈改进投资分析报告。

## 当前报告

{current_report}

## 挑战者的挑战点

{challenges_text}

## 改进ToDo

{todos_text}

## 新获取的证据

{evidence_text}

## 输出要求

1. 生成改进后的报告（保持原有结构）
2. 针对每个挑战点给出具体解答
3. 引用新获取的证据
4. 保持分析的深度和具体性"""
        
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """格式化数据"""
        if not data:
            return "暂无数据"
        
        text = ""
        
        # 按来源分组
        by_source = {}
        for key, value in data.items():
            if isinstance(value, dict):
                source = value.get('source', 'unknown')
                if source not in by_source:
                    by_source[source] = []
                by_source[source].append((key, value))
        
        for source, items in by_source.items():
            text += f"\n### {source}\n"
            for key, value in items:
                if isinstance(value, dict):
                    val = value.get('value', value.get('name', str(value)))
                    quality = value.get('quality', 'N/A')
                    text += f"- {key}: {val} [{quality}]\n"
                else:
                    text += f"- {key}: {value}\n"
        
        return text
    
    def _format_challenges(self, challenges: List[Dict]) -> str:
        """格式化挑战点"""
        text = "| # | 挑战内容 | 问题类型 | 严重程度 |\n|---|----------|----------|----------|\n"
        for i, c in enumerate(challenges, 1):
            content = c.get('content', c.get('challenge', ''))
            challenge_type = c.get('type', c.get('challenge_type', ''))
            severity = c.get('severity', '中')
            text += f"| {i} | {content} | {challenge_type} | {severity} |\n"
        return text
    
    def _format_todos(self, todos: List[Dict]) -> str:
        """格式化ToDo"""
        text = "| # | ToDo任务 | 类型 | 预期效果 |\n|---|----------|------|----------|\n"
        for i, t in enumerate(todos, 1):
            task = t.get('task', t.get('description', ''))
            todo_type = t.get('type', '')
            effect = t.get('expected_effect', t.get('effect', ''))
            text += f"| {i} | {task} | {todo_type} | {effect} |\n"
        return text
    
    def _format_evidence(self, evidence: Dict[str, Any]) -> str:
        """格式化证据"""
        if not evidence:
            return "无新证据"
        
        text = ""
        for key, value in evidence.items():
            text += f"\n### {key}\n"
            if isinstance(value, list):
                for item in value[:5]:
                    if isinstance(item, dict):
                        name = item.get('name', item.get('title', ''))
                        val = item.get('value', item.get('content', ''))
                        source = item.get('source', '')
                        quality = item.get('quality', 'P2')
                        text += f"- {name}: {val[:200]}... [{quality}] {source}\n"
            else:
                text += f"{value}\n"
        
        return text