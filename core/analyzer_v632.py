"""
V6.3.2 主分析器 - 投资故事线 + 辩证式分析

核心改进：
1. 投资故事线设计（业务→财务→护城河→风险→估值→决策）
2. 分章节生成（避免截断）
3. 强制逻辑串联
4. 真正的辩证式输出（每个章节包含初始→挑战→解答→最终）
5. 完整的报告结构
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.analyst_v632 import AnalystV632
from core.challenger import Challenger, Evaluation
from scripts.data_collector_v63_fixed import IntegratedDataCollectorV63
from core.analyzer_v62 import DataPoint


class DialecticalAnalyzerV632:
    """V6.3.2 辩证式分析器 - 投资故事线设计"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.max_iterations = self.config.get("max_iterations", 3)
        self.score_threshold = self.config.get("score_threshold", 85)
        self.min_valid_data = self.config.get("min_valid_data", 8)
        
        # 初始化组件
        self.llm = LLMClient()
        self.analyst = AnalystV632(self.llm)
        self.challenger = Challenger(self.llm, self.score_threshold)
        self.collector = IntegratedDataCollectorV63()
        
        # 分析链
        self.iterations: List[Dict] = []
        self.all_evidence: Dict[str, Any] = {}
        self.chapter_challenges: Dict[str, List[Dict]] = {}  # 每个章节的挑战
    
    def analyze_with_data_collection(
        self, 
        company: str, 
        ticker: str = None, 
        market: str = "us"
    ) -> Tuple[str, bool]:
        """完整的分析流程（含数据收集）"""
        
        print("=" * 70)
        print("V6.3.2 辩证式投资分析（投资故事线）")
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
        
        # 阶段2: 数据组织
        print("\n【阶段2: 数据组织】")
        self.all_evidence = self._organize_evidence(data_points)
        
        # 阶段3: 生成初始报告
        print("\n【阶段3: 生成初始报告】")
        initial_report = self.analyst.generate_full_report(company, self.all_evidence, ticker)
        
        # 阶段4: 辩证式迭代
        print("\n【阶段4: 辩证式迭代】")
        final_report = self._run_dialectic_analysis(company, initial_report)
        
        # 阶段5: 保存报告
        print("\n【阶段5: 保存报告】")
        report_file = self._save_report(company, final_report)
        
        return final_report, True
    
    def _run_dialectic_analysis(self, company: str, initial_report: str) -> str:
        """运行辩证式分析"""
        
        current_report = initial_report
        
        for round_num in range(1, self.max_iterations + 1):
            print(f"\n{'='*60}")
            print(f"第 {round_num} 轮辩证分析")
            print(f"{'='*60}")
            
            # 挑战者评估
            print(f"\n【挑战者评估】")
            evaluation = self.challenger.evaluate(current_report, round_num)
            
            print(f"  总分: {evaluation.score}/100")
            print(f"  各维度得分:")
            for dim, score in evaluation.scores_by_dimension.items():
                print(f"    - {dim}: {score}/20")
            print(f"  挑战点数: {len(evaluation.challenges)}")
            print(f"  ToDo数: {len(evaluation.todos)}")
            
            # 保存迭代记录
            iteration_record = {
                "round": round_num,
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
            self.iterations.append(iteration_record)
            
            # 判断是否终止
            if not evaluation.should_continue:
                print(f"\n✅ 报告质量达标（{evaluation.score}分），分析完成！")
                break
            
            # 执行ToDo获取新证据
            print(f"\n【执行ToDo获取新证据】")
            new_evidence = self._execute_todos(evaluation.todos, company)
            
            # 针对挑战改进报告
            print(f"\n【分析师改进报告】")
            
            # 按章节改进
            chapters_to_improve = self._identify_weak_chapters(evaluation.challenges)
            
            for chapter_name, chapter_challenges in chapters_to_improve.items():
                if chapter_name in self.analyst.chapters:
                    print(f"  改进章节: {chapter_name}")
                    improved_content = self.analyst.improve_chapter(
                        chapter_name,
                        self.analyst.chapters[chapter_name],
                        chapter_challenges,
                        new_evidence
                    )
                    self.analyst.chapters[chapter_name] = improved_content
            
            # 重新合并报告
            current_report = self.analyst._merge_chapters(company)
        
        return current_report
    
    def _identify_weak_chapters(self, challenges: List) -> Dict[str, List[Dict]]:
        """根据挑战类型识别需要改进的章节"""
        
        chapter_mapping = {
            "财务": "financial_analysis",
            "护城河": "moat_analysis",
            "估值": "valuation_analysis",
            "风险": "risk_analysis",
            "数据": "business_analysis"
        }
        
        chapters_to_improve = {}
        
        for challenge in challenges:
            challenge_type = challenge.challenge_type if hasattr(challenge, 'challenge_type') else challenge.get('type', '')
            chapter_name = chapter_mapping.get(challenge_type, "business_analysis")
            
            if chapter_name not in chapters_to_improve:
                chapters_to_improve[chapter_name] = []
            
            chapters_to_improve[chapter_name].append({
                "content": challenge.content if hasattr(challenge, 'content') else challenge.get('content', ''),
                "type": challenge_type,
                "severity": challenge.severity if hasattr(challenge, 'severity') else challenge.get('severity', '中')
            })
        
        return chapters_to_improve
    
    def _execute_todos(self, todos: List, company: str) -> Dict[str, Any]:
        """执行ToDo列表"""
        
        new_evidence = {}
        
        for i, todo in enumerate(todos, 1):
            task = todo.task if hasattr(todo, 'task') else todo.get('task', '')
            print(f"  [{i}/{len(todos)}] {task[:50]}...")
            
            todo_type = todo.todo_type if hasattr(todo, 'todo_type') else todo.get('type', '')
            search_query = todo.search_query if hasattr(todo, 'search_query') else todo.get('search_query', '')
            
            if todo_type == "数据检索" and search_query:
                results = self._execute_search(search_query, company)
                if results:
                    new_evidence[f"search_{i}"] = results
            
            elif todo_type == "数据验证":
                extracted = self._extract_from_existing(task)
                if extracted:
                    new_evidence[f"extracted_{i}"] = extracted
        
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
        
        output_dir = Path("reports/v632")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = output_dir / f"{company}_v632_report_{timestamp}.md"
        
        # 生成完整报告（含辩证过程统计）
        full_report = self._generate_full_report_with_dialectic(company, report)
        
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(full_report)
        
        print(f"  报告已保存: {report_file}")
        
        # 同时生成数据引用报告
        self._generate_data_reference_report(company)
        
        return report_file
    
    def _generate_full_report_with_dialectic(self, company: str, final_report: str) -> str:
        """生成包含辩证过程统计的完整报告"""
        
        header = f"""# {company} 投资价值分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V6.3.2 投资故事线 + 辩证式分析
**迭代轮数**: {len(self.iterations)}

---

## 📊 辩证过程统计

| 轮次 | 总分 | 财务 | 护城河 | 估值 | 风险 | 数据 | 挑战点 | ToDo |
|------|------|------|--------|------|------|------|--------|------|
"""
        
        for i, iteration in enumerate(self.iterations, 1):
            scores = iteration.get("scores_by_dimension", {})
            header += f"| {i} | {iteration.get('score', 'N/A')} | "
            header += f"{scores.get('financial_depth', 0)} | "
            header += f"{scores.get('moat_discussion', 0)} | "
            header += f"{scores.get('valuation_rationality', 0)} | "
            header += f"{scores.get('risk_assessment', 0)} | "
            header += f"{scores.get('data_support', 0)} | "
            header += f"{len(iteration.get('challenges', []))} | "
            header += f"{len(iteration.get('todos', []))} |\n"
        
        header += "\n---\n\n"
        
        return header + final_report
    
    def _generate_data_reference_report(self, company: str) -> None:
        """生成数据引用报告"""
        
        output_dir = Path("reports/v632")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ref_file = output_dir / f"{company}_v632_数据引用报告_{timestamp}.md"
        
        content = f"""# {company} 数据引用报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V6.3.2

---

## 📊 数据收集统计

"""
        
        summary = self.collector.get_summary()
        content += f"- 总数据: {summary['total']} 条\n"
        content += f"- 有效数据: {summary['valid']} 条 (P2及以上)\n"
        content += f"- 低质量数据: {summary['invalid']} 条 (已丢弃)\n\n"
        
        content += "## 📋 数据来源分布\n\n"
        for source, count in summary['by_source'].items():
            content += f"- {source}: {count} 条\n"
        
        content += "\n## 📚 主要参考文献\n\n"
        content += "### 官方文件（P0）\n"
        content += "1. 公司年报/季报\n"
        content += "2. 公司公告\n\n"
        content += "### 第三方研究（P1）\n"
        content += "1. 行业研究报告\n"
        content += "2. 分析师报告\n\n"
        
        with open(ref_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        print(f"  数据引用报告已保存: {ref_file}")
    
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
**分析版本**: V6.3.2
"""


# 测试
if __name__ == "__main__":
    analyzer = DialecticalAnalyzerV632({"max_iterations": 2})
    report, success = analyzer.analyze_with_data_collection("Nintendo", "NTDOY", "us")
    print(f"\n状态: {'成功' if success else '终止'}")