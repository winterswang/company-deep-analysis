"""
V6.3.1 主分析器

集成分析师和挑战者，实现完整的辩证式分析流程
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.analyst import Analyst
from core.challenger import Challenger, Evaluation
from scripts.data_collector_v63_fixed import IntegratedDataCollectorV63
from core.analyzer_v62 import DataPoint


class DialecticalAnalyzerV631:
    """V6.3.1 辩证式分析器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 5)
        self.score_threshold = self.config.get("score_threshold", 85)
        self.min_valid_data = self.config.get("min_valid_data", 8)
        
        # 初始化组件
        self.llm = LLMClient()
        self.analyst = Analyst(self.llm)
        self.challenger = Challenger(self.llm, self.score_threshold)
        self.collector = IntegratedDataCollectorV63()
        
        # 分析链
        self.iterations: List[Dict] = []
        self.all_evidence: Dict[str, Any] = {}
    
    def analyze_with_data_collection(
        self, 
        company: str, 
        ticker: str = None, 
        market: str = "us"
    ) -> Tuple[str, bool]:
        """完整的分析流程（含数据收集）"""
        
        print("=" * 70)
        print("V6.3.1 辩证式投资分析")
        print("=" * 70)
        print(f"目标公司: {company}")
        print(f"股票代码: {ticker}")
        print(f"最大轮数: {self.max_iterations}")
        print(f"评分阈值: {self.score_threshold}")
        print("=" * 70)
        
        # 阶段1: 数据收集
        print("\n【阶段1: 数据收集】")
        data_points = self.collector.collect_all(company, ticker, market)
        summary = self.collector.get_summary()
        
        print(f"\n数据收集统计:")
        print(f"  总数据: {summary['total']} 条")
        print(f"  有效数据: {summary['valid']} 条 (P2及以上)")
        
        if summary['valid'] < self.min_valid_data:
            return self._generate_insufficient_data_report(company, summary), False
        
        # 阶段2: 数据质量检查
        print("\n【阶段2: 数据质量检查】")
        self.all_evidence = self._organize_evidence(data_points)
        
        # 阶段3: 辩证式分析
        print("\n【阶段3: 辩证式分析】")
        report = self._run_dialectic_analysis(company, self.all_evidence)
        
        # 阶段4: 保存报告
        print("\n【阶段4: 保存报告】")
        report_file = self._save_report(company, report)
        
        return report, True
    
    def _run_dialectic_analysis(self, company: str, evidence: Dict[str, Any]) -> str:
        """运行辩证式分析"""
        
        # 第1轮：生成初始报告
        print("\n【第1轮】分析师生成初始报告...")
        current_report = self.analyst.generate_initial_report(company, evidence)
        
        iteration_record = {
            "round": 1,
            "report": current_report,
            "evaluation": None,
            "todos_executed": []
        }
        
        # 后续轮次：挑战→改进
        for round_num in range(2, self.max_iterations + 1):
            print(f"\n【第{round_num-1}轮】挑战者评估...")
            
            # 挑战者评估
            evaluation = self.challenger.evaluate(current_report, round_num - 1)
            
            print(f"  评分: {evaluation.score}/100")
            print(f"  挑战点数: {len(evaluation.challenges)}")
            print(f"  ToDo数: {len(evaluation.todos)}")
            
            iteration_record["evaluation"] = {
                "score": evaluation.score,
                "scores_by_dimension": evaluation.scores_by_dimension,
                "challenges": [
                    {
                        "content": c.content,
                        "type": c.challenge_type,
                        "severity": c.severity
                    }
                    for c in evaluation.challenges
                ],
                "todos": [
                    {
                        "task": t.task,
                        "type": t.todo_type,
                        "effect": t.expected_effect
                    }
                    for t in evaluation.todos
                ]
            }
            
            # 判断是否终止
            if not evaluation.should_continue:
                print(f"\n✅ 报告质量达标（{evaluation.score}分），分析完成！")
                break
            
            # 执行ToDo
            print(f"\n【第{round_num}轮】执行ToDo...")
            new_evidence = self._execute_todos(evaluation.todos, company)
            
            # 分析师改进报告
            print(f"  分析师改进报告...")
            current_report = self.analyst.improve_report(
                current_report,
                [c.__dict__ for c in evaluation.challenges],
                [t.__dict__ for t in evaluation.todos],
                new_evidence
            )
            
            iteration_record = {
                "round": round_num,
                "report": current_report,
                "evaluation": None,
                "todos_executed": [t.task for t in evaluation.todos]
            }
            
            self.iterations.append(iteration_record)
        
        return current_report
    
    def _execute_todos(self, todos: List, company: str) -> Dict[str, Any]:
        """执行ToDo列表"""
        
        new_evidence = {}
        
        for todo in todos:
            print(f"  执行: {todo.task}")
            
            if todo.todo_type == "数据检索" and todo.search_query:
                # 执行搜索
                results = self._execute_search(todo.search_query, company)
                if results:
                    new_evidence[f"search_{len(new_evidence)}"] = results
            
            elif todo.todo_type == "数据验证":
                # 从现有数据中重新提取
                extracted = self._extract_from_existing(todo.task)
                if extracted:
                    new_evidence[f"extracted_{len(new_evidence)}"] = extracted
            
            elif todo.todo_type == "分析深化":
                # 记录需要深化的方向
                new_evidence[f"deepen_{len(new_evidence)}"] = {
                    "task": todo.task,
                    "expected_effect": todo.expected_effect
                }
        
        return new_evidence
    
    def _execute_search(self, query: str, company: str) -> List[Dict]:
        """执行搜索"""
        
        import requests
        
        results = []
        
        # Tavily搜索
        tavily_key = self.collector.tavily_key if hasattr(self.collector, 'tavily_key') else ""
        if tavily_key:
            try:
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": tavily_key,
                        "query": f"{company} {query}",
                        "max_results": 3
                    },
                    timeout=30
                )
                if response.status_code == 200:
                    data = response.json()
                    for item in data.get("results", []):
                        results.append({
                            "source": "Tavily",
                            "quality": "P2",
                            "title": item.get("title", ""),
                            "content": item.get("content", "")[:500],
                            "url": item.get("url", "")
                        })
            except Exception as e:
                print(f"    Tavily搜索失败: {e}")
        
        return results
    
    def _extract_from_existing(self, task: str) -> Dict[str, Any]:
        """从现有数据中提取"""
        
        # 简化实现：返回现有证据的子集
        extracted = {}
        
        for key, value in self.all_evidence.items():
            if task.lower() in key.lower() or task.lower() in str(value).lower():
                extracted[key] = value
        
        return extracted if extracted else None
    
    def _organize_evidence(self, data_points: List[DataPoint]) -> Dict[str, Any]:
        """组织证据"""
        
        evidence = {
            "by_source": {},
            "by_quality": {"P0": [], "P1": [], "P2": []},
            "all": []
        }
        
        for dp in data_points:
            # 按来源组织
            source = dp.source
            if source not in evidence["by_source"]:
                evidence["by_source"][source] = []
            evidence["by_source"][source].append({
                "name": dp.name,
                "value": dp.value,
                "quality": dp.quality,
                "validity": dp.validity,
                "notes": dp.notes
            })
            
            # 按质量组织
            if dp.quality in evidence["by_quality"]:
                evidence["by_quality"][dp.quality].append(dp.name)
            
            evidence["all"].append({
                "name": dp.name,
                "value": dp.value,
                "source": dp.source,
                "quality": dp.quality
            })
        
        return evidence
    
    def _save_report(self, company: str, report: str) -> Path:
        """保存报告"""
        
        output_dir = Path("reports/v631")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"{company}_v631_report_{timestamp}.md"
        
        # 生成完整报告（含辩证过程）
        full_report = self._generate_full_report(company, report)
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_report)
        
        print(f"  报告已保存: {report_file}")
        
        return report_file
    
    def _generate_full_report(self, company: str, final_report: str) -> str:
        """生成完整报告（含辩证过程）"""
        
        header = f"""# {company} 投资价值分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V6.3.1 辩证式分析（否定之否定）
**迭代轮数**: {len(self.iterations)}

---

## 📊 辩证过程统计

| 轮次 | 评分 | 挑战点数 | ToDo数 |
|------|------|----------|--------|
"""
        
        for i, iteration in enumerate(self.iterations, 1):
            eval_data = iteration.get("evaluation", {})
            score = eval_data.get("score", "N/A")
            challenges = len(eval_data.get("challenges", []))
            todos = len(eval_data.get("todos", []))
            header += f"| {i} | {score} | {challenges} | {todos} |\n"
        
        header += "\n---\n\n"
        
        return header + final_report
    
    def _generate_insufficient_data_report(self, company: str, summary: Dict) -> str:
        """生成数据不足报告"""
        
        return f"""# {company} 分析报告

## ⚠️ 分析终止：数据不足

**终止原因**: 有效数据不足：仅{summary['valid']}条有效数据（需要≥{self.min_valid_data}条）

### 数据收集统计

- 总数据: {summary['total']} 条
- 有效数据: {summary['valid']} 条
- 低质量数据: {summary['invalid']} 条

### 建议补充数据

| 数据项 | 建议来源 | 预期质量 |
|--------|----------|----------|
| 官方财报 | 公司IR网站 | P0 |
| 财务数据 | Bloomberg/S&P | P1 |
| 行业数据 | 行业协会 | P2 |

---

**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析版本**: V6.3.1
"""


# 测试
if __name__ == "__main__":
    analyzer = DialecticalAnalyzerV631({"max_iterations": 3})
    report, success = analyzer.analyze_with_data_collection("Nintendo", "NTDOY", "us")
    print(f"\n状态: {'成功' if success else '终止'}")