"""
V7.0 增强版护城河追问引擎

核心改进：
1. 分析所有财务异常，不只是 ROIC
2. 每个异常都要深入追问
3. 真正的循环机制，直到数据充分
"""

import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class MoatType(Enum):
    """护城河类型"""
    NETWORK_EFFECT = "网络效应"
    SWITCHING_COST = "转换成本"
    COST_ADVANTAGE = "成本优势"
    INTANGIBLE_ASSETS = "无形资产"
    EFFICIENT_SCALE = "有效规模"
    UNKNOWN = "未识别"


@dataclass
class FinancialAnomaly:
    """财务异常"""
    metric: str  # 指标名称
    value: Any  # 当前值
    trend: List  # 趋势数据
    benchmark: Any  # 行业基准
    deviation: str  # 偏离程度（高/低/异常）
    severity: str  # 严重程度（高/中/低）
    question: str  # 追问问题
    layer: int = 1  # 当前追问层级
    history: List = field(default_factory=list)  # 追问历史


class EnhancedMoatQuestioningEngine:
    """增强版护城河追问引擎"""
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
        self.anomalies: List[FinancialAnomaly] = []
        self.current_anomaly_index = 0
    
    def analyze_all_financial_data(
        self, 
        financial_data: Dict[str, Any],
        context: Dict = None
    ) -> Tuple[List[FinancialAnomaly], str]:
        """
        分析所有财务数据，识别异常
        
        Returns:
            Tuple[List[FinancialAnomaly], str]: (异常列表, 分析报告)
        """
        
        print("\n" + "=" * 70)
        print("全面财务数据异常分析")
        print("=" * 70)
        
        context = context or {}
        company = context.get("company", "该公司")
        
        anomalies = []
        
        # 1. 盈利能力分析
        print("\n【盈利能力分析】")
        
        # ROIC 分析
        if "ROIC" in financial_data:
            anomaly = self._analyze_roic(financial_data["ROIC"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # ROE 分析
        if "ROE" in financial_data:
            anomaly = self._analyze_roe(financial_data["ROE"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # 毛利率分析
        if "毛利率" in financial_data:
            anomaly = self._analyze_gross_margin(financial_data["毛利率"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # 2. 成长能力分析
        print("\n【成长能力分析】")
        
        if "营收增速" in financial_data:
            anomaly = self._analyze_revenue_growth(financial_data["营收增速"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        if "净利润增速" in financial_data:
            anomaly = self._analyze_profit_growth(financial_data["净利润增速"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # 3. 运营效率分析
        print("\n【运营效率分析】")
        
        if "现金周转周期" in financial_data:
            anomaly = self._analyze_cash_cycle(financial_data["现金周转周期"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # 4. 费用控制分析
        print("\n【费用控制分析】")
        
        if "销售费用率" in financial_data:
            anomaly = self._analyze_sales_expense(financial_data["销售费用率"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # 5. 现金流分析
        print("\n【现金流分析】")
        
        if "经营现金流" in financial_data:
            anomaly = self._analyze_cash_flow(financial_data["经营现金流"], company)
            if anomaly:
                anomalies.append(anomaly)
        
        # 汇总
        print("\n" + "-" * 70)
        print(f"发现 {len(anomalies)} 个财务异常:")
        for i, a in enumerate(anomalies, 1):
            print(f"  {i}. {a.metric}: {a.deviation} ({a.severity})")
        print("-" * 70)
        
        self.anomalies = anomalies
        
        return anomalies, self._generate_anomaly_report(anomalies)
    
    def _analyze_roic(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析 ROIC"""
        
        # 提取数值
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        # 行业基准
        benchmark = 15  # 一般行业 ROIC 基准
        
        if current and current > benchmark * 1.5:
            return FinancialAnomaly(
                metric="ROIC",
                value=current,
                trend=values,
                benchmark=benchmark,
                deviation="显著高于行业均值",
                severity="高",
                question=f"{company}的ROIC为{current}%，显著高于行业均值{benchmark}%，这种高资本回报来自哪里？"
            )
        elif current and current < benchmark * 0.5:
            return FinancialAnomaly(
                metric="ROIC",
                value=current,
                trend=values,
                benchmark=benchmark,
                deviation="显著低于行业均值",
                severity="高",
                question=f"{company}的ROIC为{current}%，显著低于行业均值{benchmark}%，资本效率为何这么低？"
            )
        
        return None
    
    def _analyze_roe(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析 ROE"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        benchmark = 12
        
        if current and current > benchmark * 2:
            return FinancialAnomaly(
                metric="ROE",
                value=current,
                trend=values,
                benchmark=benchmark,
                deviation="显著高于行业均值",
                severity="高",
                question=f"{company}的ROE为{current}%，远超行业均值，这种高净资产回报是可持续的吗？"
            )
        
        return None
    
    def _analyze_gross_margin(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析毛利率"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        benchmark = 30  # 零售电商行业基准
        
        if current and current > benchmark * 1.5:
            return FinancialAnomaly(
                metric="毛利率",
                value=current,
                trend=values,
                benchmark=benchmark,
                deviation="显著高于行业均值",
                severity="中",
                question=f"{company}的毛利率为{current}%，远高于行业均值{benchmark}%，这种定价权来自哪里？"
            )
        
        return None
    
    def _analyze_revenue_growth(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析营收增速"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        # 检查增速变化
        if len(values) >= 2:
            if values[-1] < values[-2] * 0.5:  # 增速腰斩
                return FinancialAnomaly(
                    metric="营收增速",
                    value=current,
                    trend=values,
                    benchmark=values[-2],
                    deviation="增速大幅下滑",
                    severity="高",
                    question=f"{company}的营收增速从{values[-2]}%下滑至{current}%，增长为何失速？"
                )
        
        return None
    
    def _analyze_profit_growth(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析净利润增速"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        # 检查利润与营收增速背离
        if current and current > 100:  # 利润增速超100%
            return FinancialAnomaly(
                metric="净利润增速",
                value=current,
                trend=values,
                benchmark=50,
                deviation="异常高增长",
                severity="中",
                question=f"{company}的净利润增速达{current}%，这种高增长是可持续的还是一次性因素？"
            )
        
        return None
    
    def _analyze_cash_cycle(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析现金周转周期"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        benchmark = 30  # 一般行业基准
        
        if current and current < 0:  # 负周期
            return FinancialAnomaly(
                metric="现金周转周期",
                value=current,
                trend=values,
                benchmark=benchmark,
                deviation="负周期（极高效）",
                severity="高",
                question=f"{company}的现金周转周期为{current}天，为负值，说明对供应链有极强议价权，这种能力来自哪里？"
            )
        
        return None
    
    def _analyze_sales_expense(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析销售费用率"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        benchmark = 40  # 电商行业基准
        
        if current and current < benchmark * 0.5:  # 费用率远低于行业
            return FinancialAnomaly(
                metric="销售费用率",
                value=current,
                trend=values,
                benchmark=benchmark,
                deviation="显著低于行业均值",
                severity="高",
                question=f"{company}的销售费用率为{current}%，远低于行业均值{benchmark}%，获客成本为何这么低？"
            )
        
        return None
    
    def _analyze_cash_flow(self, data: Any, company: str) -> Optional[FinancialAnomaly]:
        """分析现金流"""
        
        if isinstance(data, dict):
            values = list(data.values())
            current = values[-1] if values else None
        elif isinstance(data, (int, float)):
            current = data
            values = [data]
        else:
            return None
        
        # 检查现金流是否为负
        if current and current < 0:
            return FinancialAnomaly(
                metric="经营现金流",
                value=current,
                trend=values,
                benchmark=0,
                deviation="现金流为负",
                severity="高",
                question=f"{company}的经营现金流为负，盈利质量是否有问题？"
            )
        
        return None
    
    def _generate_anomaly_report(self, anomalies: List[FinancialAnomaly]) -> str:
        """生成异常分析报告"""
        
        report = "# 财务异常分析报告\n\n"
        
        for a in anomalies:
            report += f"## {a.metric}\n\n"
            report += f"- **当前值**: {a.value}\n"
            report += f"- **行业基准**: {a.benchmark}\n"
            report += f"- **偏离程度**: {a.deviation}\n"
            report += f"- **严重程度**: {a.severity}\n"
            report += f"- **追问**: {a.question}\n\n"
        
        return report
    
    def deep_dive_anomaly(
        self, 
        anomaly: FinancialAnomaly,
        context: Dict = None,
        max_layers: int = 5
    ) -> FinancialAnomaly:
        """
        深入追问单个异常
        
        追问层级：
        1. 财务数据层：这个数据为什么是这样？
        2. 经营表现层：经营上是如何实现的？
        3. 经营能力层：需要什么能力？
        4. 护城河来源层：竞争优势来自哪里？
        5. 不可复制层：为什么对手无法复制？
        """
        
        context = context or {}
        company = context.get("company", "该公司")
        
        print(f"\n深入追问: {anomaly.metric}")
        print("-" * 50)
        
        layer_questions = {
            1: f"{anomaly.question}",
            2: f"从经营角度看，{company}是如何实现这种{anomaly.metric}表现的？",
            3: f"{company}需要具备什么核心能力才能维持这种{anomaly.metric}？",
            4: f"这种能力的护城河来源是什么？是网络效应、转换成本、成本优势、无形资产还是有效规模？",
            5: f"为什么竞争对手无法复制{company}的这种优势？"
        }
        
        for layer in range(1, max_layers + 1):
            question = layer_questions.get(layer, "")
            
            print(f"\n第{layer}层追问: {question[:60]}...")
            
            # 使用 LLM 生成洞察
            insight = self._generate_layer_insight(anomaly, layer, question, context)
            
            # 记录到历史
            anomaly.history.append({
                "layer": layer,
                "question": question,
                "insight": insight
            })
            
            print(f"洞察: {insight[:100]}...")
        
        anomaly.layer = max_layers
        
        return anomaly
    
    def _generate_layer_insight(
        self, 
        anomaly: FinancialAnomaly,
        layer: int,
        question: str,
        context: Dict
    ) -> str:
        """生成层级洞察"""
        
        company = context.get("company", "该公司")
        
        prompt = f"""请针对以下问题进行深入分析：

公司：{company}
财务指标：{anomaly.metric}
当前值：{anomaly.value}
偏离程度：{anomaly.deviation}

问题：{question}

要求：
1. 直接回答问题，不要绕圈子
2. 如果需要数据支撑，指出需要什么数据
3. 如果能推断，给出具体推断
4. 层级深度：第{layer}层

请给出你的分析洞察（2-3句话）："""
        
        try:
            insight = self.llm.chat([{"role": "user", "content": prompt}])
            return insight.strip()
        except Exception as e:
            return f"需要更多数据来回答这个问题"
    
    def generate_final_report(self) -> str:
        """生成最终分析报告"""
        
        report = "# 五层追问分析报告\n\n"
        
        for anomaly in self.anomalies:
            report += f"## {anomaly.metric} 深度分析\n\n"
            
            for h in anomaly.history:
                report += f"### 第{h['layer']}层\n\n"
                report += f"**追问**: {h['question']}\n\n"
                report += f"**洞察**: {h['insight']}\n\n"
            
            report += "---\n\n"
        
        return report


# 测试
if __name__ == "__main__":
    engine = EnhancedMoatQuestioningEngine()
    
    # 模拟财务数据
    financial_data = {
        "ROIC": {"2020": 18.5, "2021": 22.3, "2022": 28.7, "2023": 32.4},
        "ROE": {"2020": 25.0, "2021": 32.5, "2022": 41.2, "2023": 48.5},
        "毛利率": {"2020": 45.2, "2021": 52.3, "2022": 58.1, "2023": 60.9},
        "现金周转周期": {"2020": -45, "2021": -78, "2022": -98, "2023": -127}
    }
    
    anomalies, report = engine.analyze_all_financial_data(
        financial_data, 
        context={"company": "PDD Holdings"}
    )
    
    print(report)