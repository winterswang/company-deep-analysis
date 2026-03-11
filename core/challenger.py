"""
V6.3.1 挑战者角色

职责：
1. 阅读分析报告
2. 识别分析薄弱环节
3. 提出具体挑战点
4. 给出改进ToDo
5. 评估报告质量（打分）
"""

import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


@dataclass
class Challenge:
    """挑战点"""
    content: str
    challenge_type: str  # 财务/护城河/估值/风险/数据
    severity: str  # 高/中/低
    suggestion: str  # 改进建议


@dataclass
class ToDo:
    """改进任务"""
    task: str
    todo_type: str  # 数据验证/数据检索/分析深化/证据补充
    expected_effect: str
    search_query: str = ""  # 如果是检索类，提供搜索关键词


@dataclass
class Evaluation:
    """评估结果"""
    score: int  # 0-100
    scores_by_dimension: Dict[str, int]
    challenges: List[Challenge]
    todos: List[ToDo]
    should_continue: bool


class Challenger:
    """挑战者角色 - 副链路"""
    
    SYSTEM_PROMPT = """你是批判性思维专家，帮助分析师提升报告质量。

## 你的职责

1. 阅读分析报告
2. 识别分析薄弱环节
3. 提出具体挑战点
4. 给出改进ToDo
5. 评估报告质量

## 有效挑战领域 ✅

| 领域 | 具体内容 |
|------|----------|
| 财务分析深度 | ROIC趋势、利润来源拆解、现金流质量 |
| 护城河讨论 | 本质分析、证据支撑、变化趋势 |
| 估值合理性 | 方法合理、假设清晰、对比充分 |
| 风险评估 | 风险识别充分、量化分析 |
| 数据支撑 | 有原文引用、来源可靠 |

## 无效挑战领域 ❌

| 领域 | 说明 |
|------|------|
| 元数据 | CIK编号、文件格式、数据源基础设施 |
| 已充分讨论 | 不重复质疑已深入分析的内容 |

## ToDo类型

| 类型 | 说明 | 示例 |
|------|------|------|
| 数据验证 | 从现有数据重新提取依据 | 重新审视已收集数据 |
| 数据检索 | 获取新数据 | Tavily搜索、Exa深度搜索 |
| 分析深化 | 深入分析特定领域 | 财务拆解、护城河本质 |
| 证据补充 | 补充证据链 | 搜索+验证+标注 |

## 输出格式

必须输出JSON格式：
```json
{
  "score": {
    "financial_depth": 0-20,
    "moat_discussion": 0-20,
    "valuation_rationality": 0-20,
    "risk_assessment": 0-20,
    "data_support": 0-20
  },
  "challenges": [
    {
      "content": "具体挑战内容",
      "challenge_type": "财务/护城河/估值/风险/数据",
      "severity": "高/中/低",
      "suggestion": "改进建议"
    }
  ],
  "todos": [
    {
      "task": "具体任务",
      "todo_type": "数据验证/数据检索/分析深化/证据补充",
      "expected_effect": "预期效果",
      "search_query": "如果是检索类，提供搜索关键词"
    }
  ],
  "should_continue": true/false
}
```"""
    
    def __init__(self, llm_client: LLMClient = None, score_threshold: int = 85):
        self.llm = llm_client or LLMClient()
        self.score_threshold = score_threshold
    
    def evaluate(self, report: str, round_number: int) -> Evaluation:
        """评估分析报告"""
        
        prompt = f"""请评估以下投资分析报告（第{round_number}轮）。

## 分析报告

{report}

## 评估要求

1. 对5个维度打分（每个0-20分）
2. 识别2-5个最需要改进的挑战点
3. 给出具体的改进ToDo（包含数据检索需求）
4. 判断是否达到终止条件（总分>=85）

请严格按照JSON格式输出。"""
        
        response = self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
        
        return self._parse_evaluation(response, round_number)
    
    def _parse_evaluation(self, response: str, round_number: int) -> Evaluation:
        """解析评估结果"""
        
        try:
            # 提取JSON
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            # 解析评分
            score_data = data.get("score", {})
            scores_by_dimension = {
                "financial_depth": score_data.get("financial_depth", 10),
                "moat_discussion": score_data.get("moat_discussion", 10),
                "valuation_rationality": score_data.get("valuation_rationality", 10),
                "risk_assessment": score_data.get("risk_assessment", 10),
                "data_support": score_data.get("data_support", 10)
            }
            total_score = sum(scores_by_dimension.values())
            
            # 解析挑战点
            challenges = []
            for c in data.get("challenges", []):
                challenges.append(Challenge(
                    content=c.get("content", ""),
                    challenge_type=c.get("challenge_type", c.get("type", "财务")),
                    severity=c.get("severity", "中"),
                    suggestion=c.get("suggestion", "")
                ))
            
            # 解析ToDo
            todos = []
            for t in data.get("todos", []):
                todos.append(ToDo(
                    task=t.get("task", t.get("description", "")),
                    todo_type=t.get("todo_type", t.get("type", "数据检索")),
                    expected_effect=t.get("expected_effect", t.get("effect", "")),
                    search_query=t.get("search_query", "")
                ))
            
            # 判断是否继续
            should_continue = total_score < self.score_threshold
            
            return Evaluation(
                score=total_score,
                scores_by_dimension=scores_by_dimension,
                challenges=challenges,
                todos=todos,
                should_continue=should_continue
            )
            
        except Exception as e:
            print(f"解析评估结果失败: {e}")
            # 返回默认评估
            return Evaluation(
                score=50,
                scores_by_dimension={
                    "financial_depth": 10,
                    "moat_discussion": 10,
                    "valuation_rationality": 10,
                    "risk_assessment": 10,
                    "data_support": 10
                },
                challenges=[],
                todos=[],
                should_continue=True
            )