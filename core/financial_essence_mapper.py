"""
V7.0 核心理念映射 - 财务数据 → 企业本质

严格按照需求文档 §1.4 实现：
- 营收增速 → 市场需求 + 产品竞争力
- 毛利率 → 定价权 + 成本控制能力
- ROIC/ROE → 资本配置能力 + 商业模式质量
- 现金流 → 盈利质量 + 经营健康度
- 应收账款周转 → 对下游议价权
- 存货周转 → 对市场判断力 + 供应链效率
- 应付账款周转 → 对上游议价权
- 研发投入占比 → 创新能力 + 长期竞争力
- 销售费用率 → 品牌力 + 渠道效率
- 管理费用率 → 组织效率
"""

from typing import Dict, Any, List, Tuple
from dataclasses import dataclass
from enum import Enum


class BusinessEssence(Enum):
    """企业本质类型"""
    MARKET_DEMAND = "市场需求"
    PRODUCT_COMPETITIVENESS = "产品竞争力"
    PRICING_POWER = "定价权"
    COST_CONTROL = "成本控制能力"
    CAPITAL_ALLOCATION = "资本配置能力"
    BUSINESS_MODEL_QUALITY = "商业模式质量"
    PROFIT_QUALITY = "盈利质量"
    OPERATING_HEALTH = "经营健康度"
    DOWNSTREAM_BARGAINING_POWER = "对下游议价权"
    UPSTREAM_BARGAINING_POWER = "对上游议价权"
    MARKET_JUDGMENT = "对市场判断力"
    SUPPLY_CHAIN_EFFICIENCY = "供应链效率"
    INNOVATION_CAPABILITY = "创新能力"
    LONG_TERM_COMPETITIVENESS = "长期竞争力"
    BRAND_POWER = "品牌力"
    CHANNEL_EFFICIENCY = "渠道效率"
    ORGANIZATIONAL_EFFICIENCY = "组织效率"


@dataclass
class MetricMapping:
    """指标映射"""
    financial_metric: str
    essence_types: List[BusinessEssence]
    analysis_questions: List[str]
    key_indicators: List[str]


class FinancialToEssenceMapper:
    """
    财务数据 → 企业本质 映射器
    
    严格按需求文档 §1.4 实现
    """
    
    # 完整的映射关系
    MAPPINGS: Dict[str, MetricMapping] = {
        "营收增速": MetricMapping(
            financial_metric="营收增速",
            essence_types=[BusinessEssence.MARKET_DEMAND, BusinessEssence.PRODUCT_COMPETITIVENESS],
            analysis_questions=[
                "市场需求是否在增长？增长来源是什么？",
                "产品竞争力如何？市场份额是否提升？",
                "营收增长是量增还是价增？"
            ],
            key_indicators=["行业增速", "市场份额", "客单价变化", "用户增长"]
        ),
        "毛利率": MetricMapping(
            financial_metric="毛利率",
            essence_types=[BusinessEssence.PRICING_POWER, BusinessEssence.COST_CONTROL],
            analysis_questions=[
                "定价权来自哪里？品牌、技术还是垄断？",
                "成本控制能力如何？有哪些成本优势？",
                "毛利率趋势是上升还是下降？原因是什么？"
            ],
            key_indicators=["同业毛利率对比", "成本结构", "提价能力"]
        ),
        "ROIC": MetricMapping(
            financial_metric="ROIC",
            essence_types=[BusinessEssence.CAPITAL_ALLOCATION, BusinessEssence.BUSINESS_MODEL_QUALITY],
            analysis_questions=[
                "资本配置效率如何？投资回报是否高于资本成本？",
                "商业模式质量如何？轻资产还是重资产？",
                "ROIC的驱动因素是什么？利润率还是周转率？"
            ],
            key_indicators=["WACC", "资产周转率", "净利率", "投入资本结构"]
        ),
        "ROE": MetricMapping(
            financial_metric="ROE",
            essence_types=[BusinessEssence.CAPITAL_ALLOCATION, BusinessEssence.BUSINESS_MODEL_QUALITY],
            analysis_questions=[
                "ROE的驱动因素是什么？净利率、周转率还是杠杆？",
                "高ROE是否可持续？",
                "财务杠杆风险如何？"
            ],
            key_indicators=["杜邦分析", "资产负债率", "权益乘数"]
        ),
        "现金流": MetricMapping(
            financial_metric="现金流",
            essence_types=[BusinessEssence.PROFIT_QUALITY, BusinessEssence.OPERATING_HEALTH],
            analysis_questions=[
                "盈利质量如何？利润是否有现金流支撑？",
                "经营健康度如何？现金流是否稳定？",
                "自由现金流是否为正？"
            ],
            key_indicators=["经营现金流/净利润", "自由现金流", "资本支出占比"]
        ),
        "应收账款周转": MetricMapping(
            financial_metric="应收账款周转",
            essence_types=[BusinessEssence.DOWNSTREAM_BARGAINING_POWER],
            analysis_questions=[
                "对下游客户的议价能力如何？",
                "应收账款周转天数是否在缩短？",
                "客户结构如何？是否依赖大客户？"
            ],
            key_indicators=["应收账款周转天数", "客户集中度", "账期变化"]
        ),
        "存货周转": MetricMapping(
            financial_metric="存货周转",
            essence_types=[BusinessEssence.MARKET_JUDGMENT, BusinessEssence.SUPPLY_CHAIN_EFFICIENCY],
            analysis_questions=[
                "对市场的判断力如何？存货是否合理？",
                "供应链效率如何？周转是否加快？",
                "是否存在存货积压风险？"
            ],
            key_indicators=["存货周转天数", "库龄结构", "存货跌价准备"]
        ),
        "应付账款周转": MetricMapping(
            financial_metric="应付账款周转",
            essence_types=[BusinessEssence.UPSTREAM_BARGAINING_POWER],
            analysis_questions=[
                "对上游供应商的议价能力如何？",
                "应付账款周转天数是否在延长？",
                "供应商关系如何？"
            ],
            key_indicators=["应付账款周转天数", "供应商集中度", "账期变化"]
        ),
        "研发投入占比": MetricMapping(
            financial_metric="研发投入占比",
            essence_types=[BusinessEssence.INNOVATION_CAPABILITY, BusinessEssence.LONG_TERM_COMPETITIVENESS],
            analysis_questions=[
                "创新能力如何？研发投入是否足够？",
                "长期竞争力如何？研发产出如何？",
                "研发方向是否符合行业趋势？"
            ],
            key_indicators=["研发费用率", "专利数量", "研发人员占比"]
        ),
        "销售费用率": MetricMapping(
            financial_metric="销售费用率",
            essence_types=[BusinessEssence.BRAND_POWER, BusinessEssence.CHANNEL_EFFICIENCY],
            analysis_questions=[
                "品牌力如何？是否需要大量营销投入？",
                "渠道效率如何？获客成本是否在下降？",
                "销售费用率趋势如何？"
            ],
            key_indicators=["品牌认知度", "获客成本", "复购率"]
        ),
        "管理费用率": MetricMapping(
            financial_metric="管理费用率",
            essence_types=[BusinessEssence.ORGANIZATIONAL_EFFICIENCY],
            analysis_questions=[
                "组织效率如何？管理成本是否合理？",
                "人均产出如何？",
                "组织架构是否精简？"
            ],
            key_indicators=["人均营收", "人均利润", "管理费用率趋势"]
        ),
        "现金周转周期": MetricMapping(
            financial_metric="现金周转周期",
            essence_types=[
                BusinessEssence.UPSTREAM_BARGAINING_POWER,
                BusinessEssence.DOWNSTREAM_BARGAINING_POWER,
                BusinessEssence.SUPPLY_CHAIN_EFFICIENCY
            ],
            analysis_questions=[
                "现金周转周期为什么是这样？",
                "对上下游的议价能力如何？",
                "供应链效率如何？"
            ],
            key_indicators=["应收账款周转天数", "存货周转天数", "应付账款周转天数"]
        )
    }
    
    def map_financial_metric(self, metric: str) -> MetricMapping:
        """映射财务指标到企业本质"""
        return self.MAPPINGS.get(metric)
    
    def get_analysis_questions(self, metric: str) -> List[str]:
        """获取分析问题"""
        mapping = self.MAPPINGS.get(metric)
        return mapping.analysis_questions if mapping else []
    
    def get_essence_types(self, metric: str) -> List[BusinessEssence]:
        """获取企业本质类型"""
        mapping = self.MAPPINGS.get(metric)
        return mapping.essence_types if mapping else []
    
    def get_key_indicators(self, metric: str) -> List[str]:
        """获取关键指标"""
        mapping = self.MAPPINGS.get(metric)
        return mapping.key_indicators if mapping else []
    
    def generate_essence_analysis(
        self,
        metric: str,
        value: Any,
        trend: List = None
    ) -> Dict[str, Any]:
        """
        生成企业本质分析
        
        根据财务指标自动生成对应的企业本质分析框架
        """
        
        mapping = self.MAPPINGS.get(metric)
        if not mapping:
            return {"error": f"未找到指标 {metric} 的映射关系"}
        
        # 构建分析框架
        analysis = {
            "financial_metric": metric,
            "value": value,
            "trend": trend,
            "essence_types": [e.value for e in mapping.essence_types],
            "analysis_questions": mapping.analysis_questions,
            "key_indicators_needed": mapping.key_indicators,
            "questions_for_each_essence": {}
        }
        
        # 为每个本质类型生成追问
        for essence in mapping.essence_types:
            questions = self._generate_essence_questions(essence, metric, value)
            analysis["questions_for_each_essence"][essence.value] = questions
        
        return analysis
    
    def _generate_essence_questions(
        self,
        essence: BusinessEssence,
        metric: str,
        value: Any
    ) -> List[str]:
        """为每个企业本质生成追问"""
        
        questions_map = {
            BusinessEssence.MARKET_DEMAND: [
                f"{metric}反映的市场需求变化趋势是什么？",
                "需求增长的可持续性如何？"
            ],
            BusinessEssence.PRODUCT_COMPETITIVENESS: [
                f"{metric}反映的产品竞争力来自哪里？",
                "竞争对手的{metric}如何？"
            ],
            BusinessEssence.PRICING_POWER: [
                f"{metric}反映的定价权来自哪里？品牌、技术还是垄断？",
                "是否有提价能力？提价对销量的影响？"
            ],
            BusinessEssence.COST_CONTROL: [
                f"{metric}反映的成本控制能力如何？",
                "成本优势来自规模、技术还是管理？"
            ],
            BusinessEssence.CAPITAL_ALLOCATION: [
                f"{metric}反映的资本配置效率如何？",
                "投资回报是否高于资本成本？"
            ],
            BusinessEssence.BUSINESS_MODEL_QUALITY: [
                f"{metric}反映的商业模式质量如何？",
                "轻资产还是重资产模式？"
            ],
            BusinessEssence.UPSTREAM_BARGAINING_POWER: [
                f"{metric}反映的对上游议价能力如何？",
                "账期是否有优势？"
            ],
            BusinessEssence.DOWNSTREAM_BARGAINING_POWER: [
                f"{metric}反映的对下游议价能力如何？",
                "是否能快速回款？"
            ],
            BusinessEssence.SUPPLY_CHAIN_EFFICIENCY: [
                f"{metric}反映的供应链效率如何？",
                "周转效率是否领先同行？"
            ]
        }
        
        return questions_map.get(essence, [f"{metric}反映的{essence.value}如何？"])


# 测试
if __name__ == "__main__":
    mapper = FinancialToEssenceMapper()
    
    # 测试映射
    test_metrics = ["ROIC", "毛利率", "现金周转周期"]
    
    for metric in test_metrics:
        print(f"\n{'='*60}")
        print(f"财务指标: {metric}")
        print("="*60)
        
        analysis = mapper.generate_essence_analysis(metric, 32.4, [18.5, 22.3, 28.7, 32.4])
        
        print(f"\n企业本质类型: {analysis['essence_types']}")
        print(f"\n分析问题:")
        for q in analysis['analysis_questions']:
            print(f"  - {q}")
        
        print(f"\n关键指标: {analysis['key_indicators_needed']}")
        
        print(f"\n各本质类型的追问:")
        for essence, questions in analysis['questions_for_each_essence'].items():
            print(f"\n  【{essence}】")
            for q in questions:
                print(f"    - {q}")