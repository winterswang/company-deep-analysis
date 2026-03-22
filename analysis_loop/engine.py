"""
Analysis Engine V2.0 - 深度思考分析引擎
单Agent架构，支持多轮深度讨论，挖掘深层逻辑
"""

import json
import os
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

# 添加路径
sys.path.insert(0, '/root/.openclaw/workspace/akshare_docs')

try:
    from akshare_service.skills.finance import (
        calculate_roic_a_share,  # A股ROIC计算
        calculate_roic_us,       # 美股ROIC计算
    )
    _has_akshare = True
except ImportError:
    calculate_roic_a_share = None
    calculate_roic_us = None
    _has_akshare = False


@dataclass
class ThinkingRound:
    """单轮思考"""
    round: int
    reflection: str  # 反思
    action: str  # 行动（工具调用）
    reasoning: str  # 推理
    conclusion: str  # 结论
    new_insights: List[str] = field(default_factory=list)  # 新发现
    data_used: List[str] = field(default_factory=list)  # 使用的数据
    self_score: Dict[str, int] = field(default_factory=dict)  # 自评分


@dataclass
class DimensionAnalysis:
    """单个分析维度"""
    dimension: str
    status: str = "pending"
    rounds: int = 0
    final_score: int = 0
    thinking_chain: List[ThinkingRound] = field(default_factory=list)
    final_insights: List[str] = field(default_factory=list)
    conclusion: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "dimension": self.dimension,
            "status": self.status,
            "rounds": self.rounds,
            "final_score": self.final_score,
            "thinking_chain": [
                {
                    "round": t.round,
                    "reflection": t.reflection,
                    "action": t.action,
                    "reasoning": t.reasoning,
                    "conclusion": t.conclusion,
                    "new_insights": t.new_insights,
                    "data_used": t.data_used,
                    "self_score": t.self_score
                }
                for t in self.thinking_chain
            ],
            "final_insights": self.final_insights,
            "conclusion": self.conclusion
        }


@dataclass
class AnalysisEngineResult:
    """分析引擎输出结果"""
    skill: str = "analysis-engine"
    version: str = "2.0"
    company: str = ""
    stock_code: str = ""
    analysis_date: str = ""
    dimensions: List[DimensionAnalysis] = field(default_factory=list)
    summary_insights: List[str] = field(default_factory=list)
    overall_score: int = 0
    total_rounds: int = 0
    total_tokens: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skill": self.skill,
            "version": self.version,
            "company": self.company,
            "stock_code": self.stock_code,
            "analysis_date": self.analysis_date,
            "dimensions": [d.to_dict() for d in self.dimensions],
            "summary_insights": self.summary_insights,
            "overall_score": self.overall_score,
            "total_rounds": self.total_rounds,
            "total_tokens": self.total_tokens
        }


class AnalysisEngine:
    """深度思考分析引擎 V2.0"""

    # 分析维度常量
    DIMENSION_FINANCIAL_ANOMALY = "financial_anomaly"
    DIMENSION_BUSINESS_INSIGHT = "business_insight"
    DIMENSION_MOAT_IDENTIFICATION = "moat_identification"
    DIMENSION_SUSTAINABILITY = "sustainability"

    ALL_DIMENSIONS = [
        DIMENSION_FINANCIAL_ANOMALY,
        DIMENSION_BUSINESS_INSIGHT,
        DIMENSION_MOAT_IDENTIFICATION,
        DIMENSION_SUSTAINABILITY
    ]

    def __init__(
        self,
        data_collector_output_dir: str,
        max_rounds: int = 10,
        no_new_discovery_exit: int = 2,
        model: str = "glm-5"  # 阿里百炼GLM-5 + 思考模式
    ):
        """
        初始化分析引擎
        
        Args:
            data_collector_output_dir: base_report_generator 输出目录
            max_rounds: 最大循环轮数
            no_new_discovery_exit: 连续无新发现退出轮数
            model: 使用的模型
        """
        self.output_dir = data_collector_output_dir
        self.max_rounds = max_rounds
        self.no_new_discovery_exit = no_new_discovery_exit
        self.model = model
        
        # 数据缓存
        self._data_cache: Optional[Dict[str, Any]] = None
        self._dimension_contexts: Dict[str, str] = {}

    def load_base_report_data(self) -> Dict[str, Any]:
        """加载 base_report_generator 生成的数据"""
        if self._data_cache:
            return self._data_cache
        
        data_json_path = os.path.join(self.output_dir, "data.json")
        if os.path.exists(data_json_path):
            with open(data_json_path, 'r', encoding='utf-8') as f:
                self._data_cache = json.load(f)
                return self._data_cache
        
        return {}

    def get_financial_tables(self) -> str:
        """获取财务表格数据"""
        data = self.load_base_report_data()
        tables = data.get('data_tables', [])
        
        result = []
        for table in tables:
            if isinstance(table, dict):
                name = table.get('name', 'Unknown')
                headers = table.get('headers', [])
                rows = table.get('data', [])
                result.append(f"## {name}")
                result.append(f"Headers: {headers}")
                for row in rows:
                    result.append(str(row))
        
        return "\n".join(result) if result else "无财务表格数据"

    def get_section_text(self, section_name: str) -> str:
        """获取指定section的文本"""
        data = self.load_base_report_data()
        sections = data.get('sections', {})
        return sections.get(section_name, '')

    def get_dimension_context(self, dimension: str) -> str:
        """获取指定维度的分析上下文"""
        if dimension in self._dimension_contexts:
            return self._dimension_contexts[dimension]
        
        # 构建上下文
        context_parts = []
        
        # 1. 公司概览
        overview = self.get_section_text("company_overview")
        if overview:
            context_parts.append(f"## 公司概览\n{overview[:1000]}")
        
        # 2. 财务表现
        financial = self.get_section_text("financial_performance")
        if financial:
            context_parts.append(f"## 财务表现\n{financial[:1500]}")
        
        # 3. 投资亮点
        highlights = self.get_section_text("investment_highlights")
        if highlights:
            context_parts.append(f"## 投资亮点\n{highlights[:800]}")
        
        # 4. 风险因素
        risk = self.get_section_text("risk_factors")
        if risk:
            context_parts.append(f"## 风险因素\n{risk[:800]}")
        
        # 5. 估值分析
        valuation = self.get_section_text("valuation_analysis")
        if valuation:
            context_parts.append(f"## 估值分析\n{valuation[:800]}")
        
        # 6. 结论
        conclusions = self.get_section_text("conclusions")
        if conclusions:
            context_parts.append(f"## 结论\n{conclusions[:500]}")
        
        context = "\n\n".join(context_parts)
        self._dimension_contexts[dimension] = context
        return context

    def get_dimension_prompt(self, dimension: str) -> str:
        """获取维度特定的Prompt"""
        prompts = {
            self.DIMENSION_FINANCIAL_ANOMALY: """
# 特定任务
分析企业财务异常，挖掘数据背后的真实经营状况。

## 关注点
- ROE/ROIC异常高的原因和可持续性
- 现金流与利润的匹配度
- 资产质量是否存在隐患
- 会计处理是否激进

## 关键问题
- 这些财务指标"真实"吗？
- 是否有调整空间？
- 竞争对手能做到吗？
- 如果假设不成立，会怎样？
""",
            self.DIMENSION_BUSINESS_INSIGHT: """
# 特定任务
理解企业商业模式和核心竞争力。

## 关注点
- 赚钱的本质是什么？
- 竞争优势来源？
- 是否可复制？

## 关键问题
- 剥离所有包装，核心价值是什么？
- 10年后这个优势还在吗？
- 如果你是竞争对手，会怎么做？
- 这个生意最大的弱点是什么？
""",
            self.DIMENSION_MOAT_IDENTIFICATION: """
# 特定任务
识别企业竞争优势和护城河。

## 关注点
- 无形资产、网络效应、转换成本等
- 护城河是否在加深还是变窄？

## 关键问题
- 对手能否复制这个优势？
- 技术变革会颠覆吗？
- 护城河能持续10年吗？
- 最大的威胁来自哪里？
""",
            self.DIMENSION_SUSTAINABILITY: """
# 特定任务
评估企业长期可持续性。

## 关注点
- 行业趋势、竞争格局
- 管理团队能力
- 潜在风险点

## 关键问题
- 5-10年后行业会怎样？
- 最大风险是什么？
- 能穿越周期吗？
- 什么会打破现在的平衡？
"""
        }
        return prompts.get(dimension, "")

    def build_system_prompt(self, dimension: str) -> str:
        """构建系统Prompt"""
        dimension_prompt = self.get_dimension_prompt(dimension)
        
        return f"""# 角色
你是一位拥有30年经验的资深价值投资大师，擅长深度思考和质疑一切假设。

# 任务
对企业的财务和经营数据进行深度分析，挖掘深层逻辑和潜在问题。

{dimension_prompt}

# 思考框架
每轮思考必须包含以下步骤：

1. 【反思】上轮结论有什么问题/盲点？
   - 列出2-3个"待验证假设"
   
2. 【行动】需要补充什么数据？
   - 明确需要什么数据来验证假设
   - 如需补充，调用data-collector工具（仅使用提供的工具）
   
3. 【推理】基于新数据/视角重新思考
   - 从多角度分析（投资者、竞争对手、监管者）
   - 区分"相关"和"因果"
   - 质疑自己的假设
   
4. 【结论】本轮新发现
   - 总结新的洞察和质疑

# 评分标准
每轮结束后自评：
- 新问题发现 (25分): 发现了什么新盲点？
- 逻辑严谨性 (25分): 推理是否完整？
- 数据支撑 (20分): 有无数据支撑？
- 假设检验 (20分): 是否验证了假设？
- 工具使用 (10分): 是否有效使用工具？

# 输出格式
请按以下格式输出：

## 第 N 轮思考

### 反思
[上轮结论的问题/盲点]

### 行动
[需要补充的数据] / [无需补充]

### 推理
[完整思维链]

### 结论
[本轮新发现]

### 自评
- 新问题发现: X/25
- 逻辑严谨性: X/25
- 数据支撑: X/20
- 假设检验: X/20
- 工具使用: X/10
- 本轮总分: X/100
"""

    def build_user_prompt(self, dimension: str, context: str, previous_rounds: List[ThinkingRound] = None) -> str:
        """构建用户Prompt"""
        prompt_parts = [f"# 待分析企业信息\n{context}"]
        
        # 添加之前轮次的信息
        if previous_rounds:
            prompt_parts.append("\n# 之前的思考轮次\n")
            for t in previous_rounds[-3:]:  # 只显示最近3轮
                prompt_parts.append(f"""
## 第 {t.round} 轮
**反思**: {t.reflection}
**行动**: {t.action}
**推理**: {t.reasoning[:500]}...
**结论**: {t.conclusion}
**新发现**: {', '.join(t.new_insights) if t.new_insights else '无'}
""")
        
        prompt_parts.append("""
# 分析任务
请基于以上信息，进行深度思考分析。

请按照指定格式输出完整的思考过程。
""")
        
        return "\n".join(prompt_parts)

    def call_llm(self, system_prompt: str, user_prompt: str) -> str:
        """调用LLM (阿里百炼: GLM-5/Qwen + 思考模式)"""
        try:
            import openai
            
            # 统一使用阿里百炼 (DashScope)
            openai.api_key = os.getenv("OPENAI_API_KEY", os.getenv("DASHSCOPE_API_KEY", ""))
            base_url = os.getenv("OPENAI_BASE_URL", "")
            if base_url and "dashscope" in base_url and not base_url.endswith("/"):
                base_url = base_url.rstrip("/") + "/"
                os.environ["OPENAI_BASE_URL"] = base_url
            openai.base_url = base_url if base_url else "https://dashscope.aliyuncs.com/compatible-mode/v1/"
            
            # GLM模型支持思考模式
            extra_body = {}
            if self.model.startswith("glm"):
                extra_body["enable_thinking"] = True
            
            response = openai.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=4000,
                extra_body=extra_body if extra_body else None
            )
            
            if response.choices:
                return response.choices[0].message.content
            else:
                return "Error: No response from LLM"
        except Exception as e:
            return f"LLM调用失败: {str(e)}"

    def parse_thinking_round(self, text: str, round_num: int) -> ThinkingRound:
        """解析思考轮次"""
        # 简单解析，实际可以用更复杂的正则
        lines = text.split('\n')
        
        reflection = ""
        action = ""
        reasoning = ""
        conclusion = ""
        new_insights = []
        
        current_section = None
        for line in lines:
            line = line.strip()
            if line.startswith("### 反思"):
                current_section = "reflection"
            elif line.startswith("### 行动"):
                current_section = "action"
            elif line.startswith("### 推理"):
                current_section = "reasoning"
            elif line.startswith("### 结论"):
                current_section = "conclusion"
            elif line.startswith("### 自评"):
                current_section = "score"
            elif line.startswith("- 新问题发现:"):
                pass  # 评分
            elif current_section and line:
                if current_section == "reflection":
                    reflection += line + "\n"
                elif current_section == "action":
                    action += line + "\n"
                elif current_section == "reasoning":
                    reasoning += line + "\n"
                elif current_section == "conclusion":
                    conclusion += line + "\n"
        
        # 尝试提取新发现
        if "新发现" in conclusion.lower() or "洞察" in conclusion.lower():
            new_insights = [conclusion.strip()[:200]]
        
        return ThinkingRound(
            round=round_num,
            reflection=reflection.strip()[:500],
            action=action.strip()[:300],
            reasoning=reasoning.strip()[:2000],
            conclusion=conclusion.strip()[:500],
            new_insights=new_insights,
            data_used=[],
            self_score={}
        )

    def calculate_score(self, thinking: ThinkingRound) -> Dict[str, int]:
        """计算评分"""
        # 简单评分，实际可以从LLM输出中解析
        score = {
            "new_discovery": 15,
            "logic_rigor": 18,
            "data_support": 15,
            "hypothesis_test": 15,
            "tool_usage": 5
        }
        
        # 根据内容调整
        if len(thinking.reflection) > 100:
            score["new_discovery"] += 5
        if len(thinking.reasoning) > 500:
            score["logic_rigor"] += 2
        if thinking.action and "无需" not in thinking.action:
            score["tool_usage"] += 5
        
        score["total"] = sum(score.values())
        return score

    def _extract_data_request(self, action_text: str) -> Optional[Dict[str, str]]:
        """从行动文本中提取数据请求"""
        if not action_text:
            return None
        
        # 检查是否明确说不需要
        lower_action = action_text.lower()
        if "无需" in action_text or "不需要" in action_text or "不需要补充" in action_text:
            return None
        
        # 改进的关键词匹配 - 更宽松的模式
        requests = []
        
        # 财务相关 (ROIC, ROE, 财务, 利润, 资产负债表)
        if any(kw in action_text for kw in ["财务", "ROIC", "ROE", "利润", "资产", "负债", "NOPAT", "投入资本"]):
            requests.append({"type": "financial", "params": {"years": 5}})
        
        # 现金流相关
        if "现金流" in action_text or "经营现金流" in action_text or "自由现金流" in action_text:
            if not requests:  # 避免重复
                requests.append({"type": "cashflow", "params": {"years": 5}})
        
        # 合同负债/预收
        if "合同负债" in action_text or "预收" in action_text or "预付款" in action_text:
            if not requests:
                requests.append({"type": "financial", "params": {}})
        
        # 公告
        if "公告" in action_text:
            requests.append({"type": "announcements", "params": {}})
        
        # 雪球文章
        if "雪球" in action_text or "文章" in action_text or "研报" in action_text:
            requests.append({"type": "articles", "params": {}})
        
        return requests[0] if requests else None

    def _fetch_supplementary_data(self, request: Dict[str, str], stock_code: str) -> tuple:
        """获取补充数据 (返回: 补充数据文本, 使用的数据列表)"""
        req_type = request.get("type", "")
        data_used = []
        
        try:
            # 财务数据 - 使用 calculate_roic_a_share
            if req_type == "financial" and calculate_roic_a_share:
                params = request.get("params", {})
                years = params.get("years", 5)
                data = calculate_roic_a_share(stock_code, years=years)
                data_used.append(f"ROIC数据({years}年)")
                return f"## 补充财务数据 (ROIC)\n{str(data)[:2000]}", data_used
            
            # 现金流数据 - 暂不支持A股，使用ROIC作为替代
            elif req_type == "cashflow" and calculate_roic_a_share:
                params = request.get("params", {})
                years = params.get("years", 5)
                data = calculate_roic_a_share(stock_code, years=years)
                data_used.append(f"财务数据({years}年)")
                return f"## 补充财务数据\n{str(data)[:2000]}", data_used
            
            elif req_type == "announcements":
                data_used.append("公告数据")
                return "## 补充公告数据\n[需要调用雪球API获取]", data_used
            
            elif req_type == "articles":
                data_used.append("雪球文章")
                return "## 补充雪球文章\n[需要调用雪球API获取]", data_used
        except Exception as e:
            return f"## 数据获取失败\n{str(e)}", data_used
        
        return "", data_used

    def analyze_dimension(self, dimension: str, company: str, stock_code: str) -> DimensionAnalysis:
        """分析单个维度"""
        print(f"\n🔍 开始分析维度: {dimension}")
        
        # 获取上下文
        context = self.get_dimension_context(dimension)
        system_prompt = self.build_system_prompt(dimension)
        
        # 初始化
        analysis = DimensionAnalysis(dimension=dimension, status="in_progress")
        previous_rounds = []
        no_discovery_count = 0
        
        # 深度思考循环
        for round_num in range(1, self.max_rounds + 1):
            print(f"  第 {round_num} 轮...")
            
            # 构建Prompt（包含之前的补充数据）
            user_prompt = self.build_user_prompt(dimension, context, previous_rounds)
            
            # 调用LLM
            response = self.call_llm(system_prompt, user_prompt)
            
            # 解析结果
            thinking = self.parse_thinking_round(response, round_num)
            
            # 检查是否需要补充数据
            data_request = self._extract_data_request(thinking.action)
            if data_request:
                print(f"    📡 需要补充数据: {data_request.get('type')}")
                # 调用工具获取补充数据
                supplementary, used = self._fetch_supplementary_data(data_request, stock_code)
                if supplementary:
                    thinking.data_used = used
                    # 将补充数据添加到下一轮上下文
                    thinking.conclusion += f"\n\n{supplementary}"
            
            # 计算评分
            score = self.calculate_score(thinking)
            thinking.self_score = score
            
            # 检查是否有新发现
            if not thinking.new_insights or (len(thinking.new_insights) == 1 and "无" in thinking.new_insights[0]):
                no_discovery_count += 1
            else:
                no_discovery_count = 0
            
            # 保存
            analysis.thinking_chain.append(thinking)
            previous_rounds.append(thinking)
            analysis.rounds = round_num
            
            print(f"    评分: {score.get('total', 0)}/100, 新发现: {len(thinking.new_insights)}个")
            
            # 检查退出条件
            if no_discovery_count >= self.no_new_discovery_exit:
                print(f"  ⚠️ 连续{no_discovery_count}轮无新发现，退出")
                break
            
            if round_num >= 3 and score.get('total', 0) >= 90:
                print(f"  ✅ 评分达标，退出")
                break
        
        # 计算最终评分
        if analysis.thinking_chain:
            scores = [t.self_score.get('total', 0) for t in analysis.thinking_chain]
            analysis.final_score = int(sum(scores) / len(scores))
        
        # 提取最终洞察
        for t in analysis.thinking_chain:
            if t.new_insights:
                analysis.final_insights.extend(t.new_insights)
        
        analysis.final_insights = list(set(analysis.final_insights))[:10]  # 去重
        analysis.status = "completed"
        
        print(f"  ✅ 维度分析完成: {dimension}, 评分: {analysis.final_score}/100, 轮次: {analysis.rounds}")
        
        return analysis

    def analyze(
        self,
        company: str,
        stock_code: str,
        dimensions: List[str] = None
    ) -> AnalysisEngineResult:
        """
        执行完整分析
        
        Args:
            company: 公司名称
            stock_code: 股票代码
            dimensions: 要分析的维度列表
            
        Returns:
            AnalysisEngineResult: 分析结果
        """
        if dimensions is None:
            dimensions = self.ALL_DIMENSIONS
        
        print(f"\n{'='*60}")
        print(f"🔬 Analysis Engine V2.0 - 深度思考分析")
        print(f"   公司: {company} ({stock_code})")
        print(f"   维度: {', '.join(dimensions)}")
        print(f"   最大轮次: {self.max_rounds}")
        print(f"{'='*60}")
        
        result = AnalysisEngineResult(
            company=company,
            stock_code=stock_code,
            analysis_date=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # 分析每个维度
        for dimension in dimensions:
            analysis = self.analyze_dimension(dimension, company, stock_code)
            result.dimensions.append(analysis)
            result.total_rounds += analysis.rounds
        
        # 计算总体评分
        if result.dimensions:
            scores = [d.final_score for d in result.dimensions]
            result.overall_score = int(sum(scores) / len(scores))
        
        # 汇总洞察
        for d in result.dimensions:
            result.summary_insights.extend(d.final_insights)
        result.summary_insights = list(set(result.summary_insights))[:20]
        
        print(f"\n{'='*60}")
        print(f"✅ 分析完成!")
        print(f"   总体评分: {result.overall_score}/100")
        print(f"   总轮次: {result.total_rounds}")
        print(f"{'='*60}")
        
        return result


def analyze_company(
    stock_code: str,
    company: str = None,
    data_dir: str = None,
    dimensions: List[str] = None,
    max_rounds: int = 10
) -> AnalysisEngineResult:
    """
    便捷分析函数
    
    Args:
        stock_code: 股票代码
        company: 公司名称（可选）
        data_dir: 数据目录（base_report_generator输出）
        dimensions: 分析维度
        max_rounds: 最大轮次
        
    Returns:
        AnalysisEngineResult
    """
    # 如果没有提供data_dir，尝试查找
    if data_dir is None:
        import glob
        pattern = f"/tmp/company_analysis/{stock_code}_*"
        dirs = glob.glob(pattern)
        if dirs:
            data_dir = sorted(dirs)[-1]  # 最新
    
    if data_dir is None or not os.path.exists(data_dir):
        raise ValueError(f"数据目录不存在: {data_dir}")
    
    # 如果没有提供公司名，从目录名提取
    if company is None:
        company = os.path.basename(data_dir).split('_')[1]
    
    # 执行分析
    engine = AnalysisEngine(
        data_collector_output_dir=data_dir,
        max_rounds=max_rounds
    )
    
    return engine.analyze(company, stock_code, dimensions)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="深度思考分析引擎")
    parser.add_argument("--stock", required=True, help="股票代码")
    parser.add_argument("--company", help="公司名称")
    parser.add_argument("--data-dir", help="数据目录")
    parser.add_argument("--dimensions", nargs="+", help="分析维度")
    parser.add_argument("--max-rounds", type=int, default=10, help="最大轮次")
    
    args = parser.parse_args()
    
    result = analyze_company(
        stock_code=args.stock,
        company=args.company,
        data_dir=args.data_dir,
        dimensions=args.dimensions,
        max_rounds=args.max_rounds
    )
    
    print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))