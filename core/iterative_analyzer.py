"""
迭代式辩证分析器 V5.1
核心控制器 - 协调双LLM进行分析

V5.1 修复：
- 添加初始化评估阶段（借鉴雪球8主题框架）
- 质疑者有边界约束，聚焦投资决策
- 融合雪球爬虫数据收集
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import re
import json
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime

from core.models import (
    Doubt, DoubtType, DoubtStatus, Priority,
    SearchTarget, Evidence, EvidenceDirection, CredibilityLevel, DataSource,
    Hypothesis, AnalysisScore, IterationResult, AnalysisChain
)
from core.llm_client import LLMClient, SkepticLLM, ResolverLLM
from search.search_engine import SearchEngine


# 8主题评分标准（借鉴雪球分析框架）
SCORING_CRITERIA = {
    "估值分析": {
        "25": "有完整估值模型/DCF分析",
        "15": "有估值讨论（PE/PB对比等）",
        "5": "仅有PE/PB数据",
        "0": "无估值相关内容"
    },
    "商业模式": {
        "25": "深度护城河分析，讨论可持续性",
        "15": "讨论竞争优势和行业地位",
        "5": "仅提及行业地位",
        "0": "无商业模式相关内容"
    },
    "财务质量": {
        "25": "完整财务分析（现金流、ROE趋势等）",
        "15": "部分财务指标讨论",
        "5": "仅有财务数据",
        "0": "无财务相关内容"
    },
    "竞争格局": {
        "25": "深度竞争分析，讨论行业格局演变",
        "15": "提及主要竞争对手和威胁",
        "5": "仅提及竞争",
        "0": "无竞争相关内容"
    },
    "管理层": {
        "25": "深度管理层分析（履历、战略、配置）",
        "15": "提及管理层变动或治理",
        "5": "仅提高管姓名",
        "0": "无管理层相关内容"
    },
    "风险因素": {
        "25": "系统性风险分析，多维度评估",
        "15": "提及主要风险点",
        "5": "仅有负面情绪表达",
        "0": "无风险相关内容"
    },
    "用户价值": {
        "25": "真实用户深度反馈（体验、忠诚度）",
        "15": "有用户评论或反馈",
        "5": "仅提用户数量",
        "0": "无用户相关内容"
    },
    "未来前景": {
        "25": "清晰增长逻辑和催化剂分析",
        "15": "提及增长方向和机会",
        "5": "仅提增长数据",
        "0": "无前景相关内容"
    }
}


class IterativeDialecticalAnalyzer:
    """迭代式辩证分析器 V5.1"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # 初始化LLM
        self.llm_client = LLMClient()
        self.skeptic = SkepticLLM(self.llm_client)
        self.resolver = ResolverLLM(self.llm_client)
        
        # 初始化搜索引擎
        self.search_engine = SearchEngine()
        
        # 配置参数
        self.max_iterations = self.config.get("max_iterations", 15)
        self.min_iterations = self.config.get("min_iterations", 3)
        self.score_threshold = self.config.get("score_threshold", 85)
        
        # 输出目录
        self.output_dir = Path(__file__).parent.parent / "reports" / "v5"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def _save_checkpoint(self, chain: AnalysisChain, iteration: int):
        """保存中间结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_path = self.output_dir / f"{chain.company}_checkpoint_iter{iteration}_{timestamp}.json"
        
        try:
            with open(checkpoint_path, "w", encoding="utf-8") as f:
                json.dump(chain.to_dict(), f, ensure_ascii=False, indent=2)
            print(f"✓ Checkpoint已保存: {checkpoint_path}")
        except Exception as e:
            print(f"⚠ Checkpoint保存失败: {e}")
    
    def _build_initial_evaluation_prompt(self, company: str, initial_data: Dict[str, Any]) -> str:
        """构建初始化评估Prompt（借鉴雪球框架）"""
        
        # 评分标准表格
        criteria_text = "\n| 主题 | 25分标准 | 15分标准 | 5分标准 | 0分 |\n|------|----------|----------|---------|-----|\n"
        for topic, criteria in SCORING_CRITERIA.items():
            criteria_text += f"| {topic} | {criteria['25']} | {criteria['15']} | {criteria['5']} | {criteria['0']} |\n"
        
        prompt = f"""你是一位资深价值投资分析师，现在需要评估当前收集的信息是否足够支撑一份高质量的投资分析报告。

# 分析目标

**公司**: {company}

作为价值投资者，我需要回答以下8个核心问题：

1. 这家公司值多少钱？（估值分析）
2. 这门生意好不好？（商业模式）
3. 赚钱能力强吗？（财务质量）
4. 竞争对手怎么样？（竞争格局）
5. 管理层靠得住吗？（管理层）
6. 可能出什么问题？（风险因素）
7. 用户怎么说？（用户价值）
8. 还能增长吗？（未来前景）

# 当前收集的信息

{json.dumps(initial_data, ensure_ascii=False, indent=2) if initial_data else "暂无初始数据"}

# 评分标准

每个主题满分25分，总分200分：

{criteria_text}

# 输出要求

请评估以上信息，输出以下内容：

1. **各主题评分**：对8个主题逐一评分，说明评分理由
2. **内容覆盖分析**：哪些方面充分？哪些缺失？
3. **爬取建议**：
   - 总分 >= 150：信息充分，可以进入分析
   - 总分 100-150：信息基本充分，建议补充
   - 总分 < 100：信息不足，必须继续收集

# 输出格式（JSON）

```json
{{
  "scores": {{
    "估值分析": {{"score": 15, "reason": "..."}},
    "商业模式": {{"score": 10, "reason": "..."}},
    ...
  }},
  "total_score": 120,
  "sufficiency": "基本充分",
  "coverage_analysis": {{
    "strengths": ["商业模式", "竞争格局"],
    "gaps": ["管理层", "用户价值"]
  }},
  "need_more_data": true,
  "data_suggestions": {{
    "priority": ["财务数据", "管理层信息"],
    "focus_topics": ["ROIC趋势", "管理层激励"]
  }}
}}
```
"""
        return prompt
    
    def _evaluate_initial_data(self, company: str, initial_data: Dict[str, Any]) -> Dict[str, Any]:
        """评估初始数据充分性"""
        prompt = self._build_initial_evaluation_prompt(company, initial_data)
        
        try:
            result = self.llm_client.chat([{"role": "user", "content": prompt}])
            
            # 解析JSON
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', result)
            if json_match:
                return json.loads(json_match.group(1))
            else:
                # 尝试直接解析
                return json.loads(result)
        except Exception as e:
            print(f"初始化评估失败: {e}")
            return {
                "total_score": 0,
                "sufficiency": "评估失败",
                "need_more_data": True
            }
    
    def analyze(self, company: str, initial_data: Optional[Dict[str, Any]] = None) -> AnalysisChain:
        """
        执行迭代式辩证分析 V5.1
        
        流程：
        1. 获取初始数据
        2. 初始化评估（雪球框架）
        3. 迭代辩证分析
        4. 生成最终报告
        
        Args:
            company: 公司名称或代码
            initial_data: 初始财务数据（可选）
        
        Returns:
            AnalysisChain: 完整的分析链路
        """
        # 初始化分析链路
        chain = AnalysisChain(company=company)
        
        print(f"\n{'='*60}")
        print(f"V5.1 迭代式辩证分析: {company}")
        print(f"{'='*60}\n")
        
        # === 阶段1: 获取初始财务数据 ===
        print("【阶段1: 数据收集】")
        if initial_data is None:
            initial_data = self._get_initial_data(company)
        
        # === 阶段2: 初始化评估（借鉴雪球框架）===
        print("\n【阶段2: 初始化评估】")
        evaluation = self._evaluate_initial_data(company, initial_data)
        total_score = evaluation.get("total_score", 0)
        sufficiency = evaluation.get("sufficiency", "未知")
        
        print(f"  初始评分: {total_score}/200")
        print(f"  充分性: {sufficiency}")
        
        # 显示各主题评分
        scores = evaluation.get("scores", {})
        if scores:
            print("  各主题评分:")
            for topic, data in scores.items():
                score = data.get("score", 0)
                print(f"    - {topic}: {score}/25")
        
        # === 阶段3: 迭代辩证分析 ===
        print("\n【阶段3: 迭代辩证分析】")
        
        # 创建初始假设（基于评估结果）
        hypothesis = self._create_initial_hypothesis_v2(company, initial_data, evaluation)
        chain.all_doubts = []
        chain.all_evidences = []
        chain.all_searches = []
        
        # 开始迭代
        iteration = 0
        while iteration < self.max_iterations:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"【第 {iteration} 轮】")
            print(f"{'='*60}\n")
            
            # === Step 1: 质疑者识别疑点（聚焦投资决策）===
            print(">>> Step 1: 质疑者识别疑点（投资决策相关）...")
            skeptic_output = self.skeptic.identify_doubts(
                hypothesis.content,
                [e.to_dict() for e in chain.all_evidences],
                [d.to_dict() for d in chain.all_doubts if d.status == DoubtStatus.RESOLVED]
            )
            print(skeptic_output[:500] + "...\n")
            
            # 解析质疑者输出
            doubts, score = self._parse_skeptic_output(skeptic_output)
            
            # 更新疑点状态
            for d in doubts:
                d.id = f"D{iteration}_{d.id}"
                if d not in chain.all_doubts:
                    chain.all_doubts.append(d)
            
            # === Step 2: 判断是否终止 ===
            if score.is_sufficient(self.score_threshold) and iteration >= self.min_iterations:
                print(f"\n✅ 分析充分！评分: {score.total}/100 >= {self.score_threshold}")
                break
            
            if not doubts:
                print(f"\n✅ 无新疑点，分析完成！")
                break
            
            # === Step 3: 解决者设计检索方案 ===
            print(">>> Step 2: 解决者设计检索方案...")
            resolver_output = self.resolver.design_search_plan(
                [d.to_dict() for d in doubts],
                hypothesis.content
            )
            print(resolver_output[:500] + "...\n")
            
            # 解析检索方案
            search_targets = self._parse_search_plan(resolver_output, doubts)
            chain.all_searches.extend(search_targets)
            
            # === Step 4: 执行检索 ===
            print(">>> Step 3: 执行检索...")
            new_evidences = []
            for target in search_targets:
                print(f"  - 搜索: {target.query[:50]}... ({target.data_source.value})")
                evidences = self.search_engine.search(target)
                new_evidences.extend(evidences)
                chain.all_evidences.extend(evidences)
                print(f"    获取 {len(evidences)} 条证据")
            
            # === Step 5: 评估证据 ===
            print("\n>>> Step 4: 评估证据...")
            validation_results = []
            for doubt in doubts:
                relevant_evidences = [e for e in new_evidences if e.doubt_id == doubt.id]
                if not relevant_evidences:
                    relevant_evidences = new_evidences  # 使用所有新证据
                
                if relevant_evidences:
                    eval_output = self.resolver.evaluate_evidence(
                        doubt.to_dict(),
                        [e.to_dict() for e in relevant_evidences]
                    )
                    print(f"  - {doubt.id}: {doubt.description[:30]}...")
                    
                    # 解析评估结果
                    validation = self._parse_evidence_evaluation(eval_output, doubt)
                    validation_results.append(validation)
                    
                    # 更新疑点状态
                    if validation.get("status") == "已解决":
                        doubt.status = DoubtStatus.RESOLVED
                        doubt.resolution = validation.get("conclusion", "")
            
            # === Step 6: 修正假设 ===
            print("\n>>> Step 5: 修正假设...")
            hypothesis_update_output = self.resolver.update_hypothesis(
                hypothesis.content,
                validation_results
            )
            print(hypothesis_update_output[:500] + "...\n")
            
            # 解析新假设
            new_hypothesis_content = self._parse_hypothesis_update(hypothesis_update_output)
            hypothesis = Hypothesis(
                version=iteration + 1,
                content=new_hypothesis_content,
                confidence=score.total / 100,
                open_doubts=[d.id for d in doubts if d.status != DoubtStatus.RESOLVED],
                resolved_doubts=[d.id for d in chain.all_doubts if d.status == DoubtStatus.RESOLVED],
            )
            
            # 记录本轮结果
            iteration_result = IterationResult(
                iteration=iteration,
                hypothesis=hypothesis,
                score=score,
                doubts=doubts,
                search_targets=search_targets,
                evidences=new_evidences,
                skeptic_output=skeptic_output,
                resolver_output=resolver_output,
                should_continue=True,
            )
            chain.iterations.append(iteration_result)
            
            # 保存checkpoint（每轮都保存，防止中断丢失）
            self._save_checkpoint(chain, iteration)
        
        # 分析完成
        chain.end_time = datetime.now()
        chain.final_hypothesis = hypothesis
        chain.final_score = score
        
        print(f"\n{'='*60}")
        print(f"分析完成！")
        print(f"总轮数: {iteration}")
        print(f"最终评分: {score.total}/100")
        print(f"疑点解决率: {chain.resolution_rate:.1%}")
        print(f"{'='*60}\n")
        
        return chain
    
    def _get_initial_data(self, company: str) -> Dict[str, Any]:
        """获取初始财务数据"""
        print(f"获取 {company} 的初始财务数据...")
        
        data = self.search_engine.get_financial_data(company)
        
        # 如果是美股，尝试搜索基本信息
        if not data:
            # 尝试Tavily搜索
            results = self.search_engine.search_multi_source(
                f"{company} financial data revenue profit ROIC",
                [DataSource.TAVILY]
            )
            data["search_results"] = [e.content for e in results]
        
        return data
    
    def _create_initial_hypothesis(self, company: str, data: Dict[str, Any]) -> Hypothesis:
        """创建初始假设"""
        # 简化的初始假设生成
        # 实际应该用LLM生成
        
        if data:
            content = f"对 {company} 的初步分析：\n"
            if "financial_indicators" in data:
                content += "- 财务数据已获取，需要进一步分析\n"
            if "search_results" in data:
                content += "- 搜索到相关信息，需要深入验证\n"
        else:
            content = f"对 {company} 的初步假设：\n- 需要收集基础财务数据\n- 需要分析商业模式\n- 需要评估投资价值"
        
        return Hypothesis(
            version=0,
            content=content,
            confidence=0.3,
        )
    
    def _create_initial_hypothesis_v2(self, company: str, data: Dict[str, Any], evaluation: Dict[str, Any]) -> Hypothesis:
        """创建初始假设 V2（基于评估结果，聚焦投资分析）"""
        
        total_score = evaluation.get("total_score", 0)
        scores = evaluation.get("scores", {})
        gaps = evaluation.get("coverage_analysis", {}).get("gaps", [])
        
        # 构建聚焦于投资分析的假设
        content = f"""# {company} 投资分析初步判断

## 已知信息

基于当前数据收集，初步评估：

"""
        
        # 添加各主题评分摘要
        if scores:
            content += "### 信息覆盖情况\n"
            for topic, data in scores.items():
                score = data.get("score", 0)
                reason = data.get("reason", "")
                if score >= 15:
                    content += f"- **{topic}**: {score}/25 ✅ ({reason})\n"
                elif score >= 5:
                    content += f"- **{topic}**: {score}/25 ⚠️ ({reason})\n"
                else:
                    content += f"- **{topic}**: {score}/25 ❌ (缺少相关信息)\n"
        
        # 添加关键问题
        if gaps:
            content += f"\n### 需要深入分析的问题\n"
            for gap in gaps[:5]:
                content += f"- {gap}信息不足，需要补充\n"
        
        # 添加投资决策相关内容
        content += f"""
### 初步投资判断

基于当前信息，需要验证以下投资相关假设：

1. **估值是否合理？** - 需要PE/PB/DCF分析
2. **护城河是否真实？** - 需要竞争分析
3. **财务质量如何？** - 需要ROIC/现金流分析
4. **管理层是否靠谱？** - 需要治理分析
5. **风险是否可控？** - 需要风险评估

**注意**：本假设聚焦于投资决策，不涉及元数据层面的质疑。
"""
        
        return Hypothesis(
            version=1,
            content=content,
            confidence=total_score / 200,
        )
    
    def _parse_skeptic_output(self, output: str) -> Tuple[List[Doubt], AnalysisScore]:
        """解析质疑者输出"""
        doubts = []
        score = AnalysisScore(0, 0, 0, 0, 0)
        
        # 解析疑点
        # 查找表格格式的疑点
        doubt_pattern = r'\|\s*D(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*(P[012])\s*\|'
        matches = re.findall(doubt_pattern, output)
        
        for match in matches:
            doubt_type_str = match[1].strip()
            description = match[2].strip()
            reason = match[3].strip()
            priority_str = match[4].strip()
            
            # 映射疑点类型
            doubt_type_map = {
                "数据矛盾": DoubtType.DATA_CONTRADICTION,
                "逻辑断裂": DoubtType.LOGIC_GAP,
                "反例存在": DoubtType.COUNTEREXAMPLE,
                "信息缺失": DoubtType.MISSING_INFO,
                "假设过强": DoubtType.STRONG_ASSUMPTION,
            }
            doubt_type = doubt_type_map.get(doubt_type_str, DoubtType.MISSING_INFO)
            
            # 映射优先级
            priority_map = {
                "P0": Priority.P0,
                "P1": Priority.P1,
                "P2": Priority.P2,
            }
            priority = priority_map.get(priority_str, Priority.P2)
            
            doubts.append(Doubt(
                id=f"D{match[0]}",
                type=doubt_type,
                description=description,
                priority=priority,
                status=DoubtStatus.PENDING,
                reason=reason,
            ))
        
        # 解析评分
        score_pattern = r'\|\s*\*?\*?总分\*?\*?\s*\|\s*\*?\*?(\d+)/100\*?\*?\s*\|'
        score_match = re.search(score_pattern, output)
        if score_match:
            total = int(score_match.group(1))
            # 简化处理，按比例分配
            score = AnalysisScore(
                hypothesis_completeness=min(25, total // 4),
                evidence_sufficiency=min(25, total // 4),
                doubt_resolution_rate=min(25, total // 4),
                logic_consistency=min(15, total // 7),
                depth_analysis=min(10, total // 10),
            )
        
        # 如果没有解析到疑点，创建默认疑点
        if not doubts:
            doubts.append(Doubt(
                id="D001",
                type=DoubtType.MISSING_INFO,
                description="需要更多财务数据进行验证",
                priority=Priority.P0,
                status=DoubtStatus.PENDING,
                reason="当前分析缺乏足够的数据支撑",
            ))
        
        return doubts, score
    
    def _parse_search_plan(self, output: str, doubts: List[Doubt]) -> List[SearchTarget]:
        """解析检索方案"""
        targets = []
        
        for i, doubt in enumerate(doubts):
            # 简化处理：为每个疑点创建一个默认的搜索目标
            # 实际应该从LLM输出中解析
            
            # 尝试从输出中提取搜索查询
            query_pattern = rf'{doubt.id}.*?搜索[：:]\s*([^\n]+)'
            query_match = re.search(query_pattern, output)
            
            if query_match:
                query = query_match.group(1).strip()
            else:
                # 使用疑点描述作为搜索查询
                query = doubt.description
            
            # 选择数据源
            if doubt.type in [DoubtType.DATA_CONTRADICTION, DoubtType.MISSING_INFO]:
                data_source = DataSource.TAVILY
            elif doubt.type == DoubtType.LOGIC_GAP:
                data_source = DataSource.EXA
            else:
                data_source = DataSource.TAVILY
            
            targets.append(SearchTarget(
                id=f"T{i+1}",
                doubt_id=doubt.id,
                purpose=f"验证疑点: {doubt.description}",
                query=query,
                data_source=data_source,
                expected_result="相关证据",
            ))
        
        return targets
    
    def _parse_evidence_evaluation(self, output: str, doubt: Doubt) -> Dict[str, Any]:
        """解析证据评估结果"""
        result = {
            "doubt_id": doubt.id,
            "status": "需要更多证据",
            "conclusion": "",
            "confidence": 0,
        }
        
        # 解析状态
        if "已解决" in output:
            result["status"] = "已解决"
        elif "无法验证" in output:
            result["status"] = "无法验证"
        
        # 解析结论
        conclusion_pattern = r'\*\*结论\*\*[：:]\s*([^\n]+)'
        conclusion_match = re.search(conclusion_pattern, output)
        if conclusion_match:
            result["conclusion"] = conclusion_match.group(1).strip()
        
        # 解析置信度
        confidence_pattern = r'置信度[：:]\s*(\d+)%?'
        confidence_match = re.search(confidence_pattern, output)
        if confidence_match:
            result["confidence"] = int(confidence_match.group(1))
        
        return result
    
    def _parse_hypothesis_update(self, output: str) -> str:
        """解析假设更新"""
        # 尝试提取新假设
        hypothesis_pattern = r'### 假设修正\s*\n([^\n]+(?:\n[^\n#]+)*)'
        match = re.search(hypothesis_pattern, output)
        
        if match:
            return match.group(1).strip()
        
        # 如果没有找到，返回整个输出
        return output[:500]


def analyze_company(company: str, initial_data: Optional[Dict[str, Any]] = None) -> AnalysisChain:
    """
    分析公司的便捷函数
    
    Args:
        company: 公司名称或代码
        initial_data: 初始财务数据
    
    Returns:
        AnalysisChain: 分析链路
    """
    analyzer = IterativeDialecticalAnalyzer()
    return analyzer.analyze(company, initial_data)


if __name__ == "__main__":
    # 测试
    import sys
    if len(sys.argv) > 1:
        company = sys.argv[1]
        chain = analyze_company(company)
        print(f"\n最终假设:\n{chain.final_hypothesis.content}")
        print(f"\n最终评分: {chain.final_score.total}/100")