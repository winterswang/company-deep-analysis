"""
V6.1 辩证式投资分析器

核心设计：
- 分析师（主链路）：生成投资分析报告
- 挑战者（副链路）：提出改进建议和ToDo
- 迭代改进：评分>=85分终止
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import re

# 添加父目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


@dataclass
class ImprovementSuggestion:
    """改进建议"""
    title: str
    problem: str
    direction: str
    investment_impact: str
    

@dataclass
class ToDoItem:
    """待办事项"""
    id: int
    task: str
    priority: str  # P0, P1, P2
    expected_effect: str
    completed: bool = False


@dataclass
class EvaluationScore:
    """评估评分"""
    financial_depth: int  # 财务分析深度 0-20
    moat_discussion: int  # 护城河讨论 0-20
    valuation_rationality: int  # 估值合理性 0-20
    risk_assessment: int  # 风险评估 0-20
    data_support: int  # 数据支撑 0-20
    
    @property
    def total(self) -> int:
        return (self.financial_depth + self.moat_discussion + 
                self.valuation_rationality + self.risk_assessment + 
                self.data_support)


@dataclass
class ChallengerFeedback:
    """挑战者反馈"""
    score: EvaluationScore
    suggestions: List[ImprovementSuggestion]
    todos: List[ToDoItem]
    should_continue: bool
    round_number: int


@dataclass
class AnalysisIteration:
    """一轮分析"""
    round_number: int
    analyst_report: str
    challenger_feedback: Optional[ChallengerFeedback] = None
    todos_completed: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


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
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def generate_initial_report(self, company: str, data: Dict[str, Any]) -> str:
        """生成初始报告"""
        
        prompt = f"""请为 {company} 生成投资价值分析报告。

## 已收集数据

{self._format_data(data)}

## 输出要求

生成结构化投资分析报告，包含：
1. 执行摘要
2. 业务分析
3. 财务质量分析（必须有ROIC趋势表格）
4. 竞争格局
5. 管理层分析
6. 估值分析
7. 投资决策

重要：
- 每个关键结论都要引用原文（使用 > 📌 引用格式）
- 财务数据要具体讨论，不要抽象表述
- 护城河要分析本质，不要停留在表面"""
        
        return self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
    
    def improve_report(self, company: str, current_report: str, 
                       feedback: ChallengerFeedback, 
                       new_data: Dict[str, Any] = None) -> str:
        """根据挑战者反馈改进报告"""
        
        todos_text = self._format_todos(feedback.todos)
        suggestions_text = self._format_suggestions(feedback.suggestions)
        
        prompt = f"""请根据挑战者的反馈改进 {company} 的投资分析报告。

## 当前报告

{current_report}

## 挑战者评分

总分：{feedback.score.total}/100

| 维度 | 评分 | 说明 |
|------|------|------|
| 财务分析深度 | {feedback.score.financial_depth}/20 | |
| 护城河讨论 | {feedback.score.moat_discussion}/20 | |
| 估值合理性 | {feedback.score.valuation_rationality}/20 | |
| 风险评估 | {feedback.score.risk_assessment}/20 | |
| 数据支撑 | {feedback.score.data_support}/20 | |

## 改进建议

{suggestions_text}

## ToDo 列表

{todos_text}

## 新获取的数据

{self._format_data(new_data) if new_data else "无新数据"}

## 输出要求

1. 生成改进后的报告（保持原有结构）
2. 在报告开头添加"改进说明"部分，说明：
   - 已完成的改进
   - 未采纳的建议及原因
3. 继续使用原文引用格式"""

        return self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
    
    def _format_data(self, data: Dict[str, Any]) -> str:
        """格式化数据"""
        if not data:
            return "暂无数据"
        
        text = ""
        
        # 财务数据
        if "financial_indicators" in data:
            text += "### 财务数据\n"
            for key, value in data["financial_indicators"].items():
                text += f"- {key}: {value}\n"
        
        # 搜索结果
        if "search_results" in data:
            text += "\n### 搜索结果\n"
            for i, result in enumerate(data["search_results"][:10], 1):
                text += f"\n[{i}] {result.get('title', 'N/A')}\n"
                text += f"来源: {result.get('url', 'N/A')}\n"
                text += f"摘要: {result.get('content', result.get('snippet', 'N/A'))[:500]}...\n"
        
        # 雪球数据
        if "xueqiu_data" in data:
            text += "\n### 雪球数据\n"
            text += str(data["xueqiu_data"])[:2000]
        
        return text
    
    def _format_todos(self, todos: List[ToDoItem]) -> str:
        """格式化ToDo"""
        text = "| # | 任务 | 优先级 |\n|---|------|--------|\n"
        for todo in todos:
            text += f"| {todo.id} | {todo.task} | {todo.priority} |\n"
        return text
    
    def _format_suggestions(self, suggestions: List[ImprovementSuggestion]) -> str:
        """格式化建议"""
        text = ""
        for i, s in enumerate(suggestions, 1):
            text += f"\n### 建议{i}：{s.title}\n"
            text += f"- 问题：{s.problem}\n"
            text += f"- 改进方向：{s.direction}\n"
            text += f"- 投资影响：{s.investment_impact}\n"
        return text


class Challenger:
    """挑战者角色 - 副链路"""
    
    SYSTEM_PROMPT = """你是批判性思维专家，帮助分析师发现分析盲点。

你的目标不是"推翻分析"，而是"提升分析质量"。

## 你的职责

1. 阅读分析报告
2. 识别分析薄弱环节
3. 提出具体改进建议
4. 给出可执行ToDo
5. 评估报告质量（打分）

## 有效挑战领域 ✅

| 领域 | 具体内容 |
|------|----------|
| 财务分析深度 | ROIC趋势分析是否充分？利润来源是否拆解？ |
| 护城河讨论 | 是否深入本质？有证据支撑吗？变化趋势分析了吗？ |
| 估值合理性 | PE与增长率匹配吗？DCF假设合理吗？ |
| 风险评估 | 债务风险、竞争风险、管理风险是否充分？ |
| 数据支撑 | 关键结论有原文引用吗？ |

## 无效挑战领域 ❌

| 领域 | 说明 |
|------|------|
| 元数据 | CIK编号、EDGAR格式、数据源基础设施等 |
| 已充分讨论 | 不要重复质疑已深入分析的内容 |

## 输出格式

必须严格按照以下JSON格式输出：

```json
{
  "score": {
    "financial_depth": 0-20,
    "moat_discussion": 0-20,
    "valuation_rationality": 0-20,
    "risk_assessment": 0-20,
    "data_support": 0-20
  },
  "suggestions": [
    {
      "title": "建议标题",
      "problem": "当前问题",
      "direction": "改进方向",
      "investment_impact": "为什么重要"
    }
  ],
  "todos": [
    {
      "id": 1,
      "task": "具体任务",
      "priority": "P0/P1/P2",
      "expected_effect": "预期效果"
    }
  ],
  "should_continue": true/false,
  "summary": "一句话总结"
}
```"""

    def __init__(self, llm_client: LLMClient, score_threshold: int = 85):
        self.llm = llm_client
        self.score_threshold = score_threshold
    
    def evaluate_report(self, company: str, report: str, 
                        round_number: int) -> ChallengerFeedback:
        """评估报告并给出反馈"""
        
        prompt = f"""请评估以下 {company} 的投资分析报告（第{round_number}轮）。

## 分析报告

{report}

## 评估要求

1. 对5个维度打分（每个0-20分）
2. 识别2-3个最需要改进的地方
3. 给出具体可执行的ToDo（至少2个）
4. 判断是否达到终止条件（总分>=85）

请严格按照JSON格式输出，不要添加其他内容。"""

        response = self.llm.chat_with_system(self.SYSTEM_PROMPT, prompt)
        
        # 解析JSON
        try:
            # 提取JSON部分
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                data = json.loads(json_match.group())
            else:
                data = json.loads(response)
            
            # 构建评分
            score = EvaluationScore(
                financial_depth=data["score"]["financial_depth"],
                moat_discussion=data["score"]["moat_discussion"],
                valuation_rationality=data["score"]["valuation_rationality"],
                risk_assessment=data["score"]["risk_assessment"],
                data_support=data["score"]["data_support"]
            )
            
            # 构建建议
            suggestions = [
                ImprovementSuggestion(**s) for s in data.get("suggestions", [])
            ]
            
            # 构建ToDo
            todos = [
                ToDoItem(**t) for t in data.get("todos", [])
            ]
            
            # 判断是否继续
            should_continue = score.total < self.score_threshold
            
            return ChallengerFeedback(
                score=score,
                suggestions=suggestions,
                todos=todos,
                should_continue=should_continue,
                round_number=round_number
            )
            
        except Exception as e:
            print(f"解析挑战者反馈失败: {e}")
            # 返回默认反馈
            return ChallengerFeedback(
                score=EvaluationScore(10, 10, 10, 10, 10),
                suggestions=[],
                todos=[],
                should_continue=True,
                round_number=round_number
            )


class DialecticalAnalyzerV61:
    """V6.1 辩证式分析器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 5)
        self.score_threshold = self.config.get("score_threshold", 85)
        
        # 初始化LLM
        self.llm = LLMClient()
        
        # 初始化角色
        self.analyst = Analyst(self.llm)
        self.challenger = Challenger(self.llm, self.score_threshold)
        
        # 分析链
        self.iterations: List[AnalysisIteration] = []
        
        # 数据
        self.data: Dict[str, Any] = {}
    
    def analyze(self, company: str, initial_data: Dict[str, Any] = None) -> str:
        """执行辩证式分析"""
        
        print("=" * 70)
        print("V6.1 辩证式投资分析")
        print("=" * 70)
        print(f"目标公司: {company}")
        print(f"最大轮数: {self.max_iterations}")
        print(f"评分阈值: {self.score_threshold}")
        print("=" * 70)
        
        # 设置初始数据
        self.data = initial_data or {}
        
        # 第1轮：生成初始报告
        print("\n【第 1 轮】分析师生成初始报告...")
        report = self.analyst.generate_initial_report(company, self.data)
        
        iteration = AnalysisIteration(round_number=1, analyst_report=report)
        self.iterations.append(iteration)
        
        # 保存checkpoint
        self._save_checkpoint(company)
        
        # 迭代改进
        for round_num in range(2, self.max_iterations + 1):
            print(f"\n【第 {round_num - 1} 轮】挑战者评估报告...")
            
            # 挑战者评估
            feedback = self.challenger.evaluate_report(
                company, report, round_num - 1
            )
            
            iteration.challenger_feedback = feedback
            
            print(f"  评分: {feedback.score.total}/100")
            
            # 判断是否终止
            if not feedback.should_continue:
                print(f"\n✅ 报告质量达标（{feedback.score.total}分），分析完成！")
                break
            
            print(f"\n【第 {round_num} 轮】分析师改进报告...")
            print(f" ToDo数量: {len(feedback.todos)}")
            
            # 执行ToDo（搜索新数据）
            new_data = self._execute_todos(company, feedback.todos)
            
            # 分析师改进报告
            report = self.analyst.improve_report(
                company, report, feedback, new_data
            )
            
            # 记录完成的ToDo
            iteration.todos_completed = [
                t.task for t in feedback.todos if t.completed
            ]
            
            # 新一轮迭代
            iteration = AnalysisIteration(
                round_number=round_num,
                analyst_report=report
            )
            self.iterations.append(iteration)
            
            # 保存checkpoint
            self._save_checkpoint(company)
        
        print("\n" + "=" * 70)
        print("分析完成！")
        print("=" * 70)
        
        return report
    
    def _execute_todos(self, company: str, todos: List[ToDoItem]) -> Dict[str, Any]:
        """执行ToDo（搜索新数据）"""
        
        new_data = {}
        search_queries = []
        
        for todo in todos:
            if todo.priority == "P0":
                # 根据ToDo任务生成搜索查询
                query = f"{company} {todo.task}"
                search_queries.append(query)
        
        if search_queries:
            print(f"  执行搜索: {len(search_queries)} 个查询")
            # 这里可以调用搜索引擎
            # new_data["search_results"] = self.search_engine.search(...)
        
        return new_data
    
    def _save_checkpoint(self, company: str):
        """保存checkpoint"""
        
        reports_dir = Path("reports/v61")
        reports_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{company}_v61_iter{len(self.iterations)}_{timestamp}.json"
        
        checkpoint = {
            "company": company,
            "iterations": [asdict(i) for i in self.iterations],
            "config": self.config,
            "timestamp": datetime.now().isoformat()
        }
        
        # 处理不可序列化的对象
        for iter_data in checkpoint["iterations"]:
            if iter_data.get("challenger_feedback"):
                cf = iter_data["challenger_feedback"]
                if cf and "score" in cf and hasattr(cf["score"], "__dict__"):
                    cf["score"] = asdict(cf["score"])
        
        with open(reports_dir / filename, "w", encoding="utf-8") as f:
            json.dump(checkpoint, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"  Checkpoint已保存: {filename}")


def main():
    """测试入口"""
    
    # 测试数据
    test_data = {
        "financial_indicators": {
            "营收": "$21.2B",
            "净利润": "$2.2B",
            "ROIC": "8.74%",
            "毛利率": "60.48%"
        }
    }
    
    analyzer = DialecticalAnalyzerV61({
        "max_iterations": 3,
        "score_threshold": 85
    })
    
    report = analyzer.analyze("FISV", test_data)
    print("\n最终报告:")
    print(report[:2000])


if __name__ == "__main__":
    main()