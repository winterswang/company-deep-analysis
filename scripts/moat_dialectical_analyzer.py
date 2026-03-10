#!/usr/bin/env python3
"""
护城河辩证分析工具 V4.4
Moat Dialectical Analyzer

三层辩证分析：
1. 第一层：财务数据辩证
2. 第二层：护城河本质辩证
3. 第三层：护城河延续性辩证
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional


class MoatType(Enum):
    """护城河类型"""
    BRAND = "品牌"
    TECHNOLOGY = "技术"
    COST = "成本"
    NETWORK_EFFECT = "网络效应"
    SWITCHING_COST = "转换成本"
    FRANCHISE = "特许经营"
    NONE = "无"


class RealityGrade(Enum):
    """真实性等级"""
    A = "A级-真护城河"
    B = "B级-较强护城河"
    C = "C级-弱护城河"
    D = "D级-伪护城河"


class ContinuityGrade(Enum):
    """延续性等级"""
    A = "A级-可持续10年以上"
    B = "B级-可持续5-10年"
    C = "C级-可能3-5年内被侵蚀"
    D = "D级-优势正在消失"


class WarningLevel(Enum):
    """预警等级"""
    RED = "红色-护城河即将失效"
    ORANGE = "橙色-护城河加速侵蚀"
    YELLOW = "黄色-护城河出现侵蚀迹象"
    GREEN = "绿色-护城河稳定或加强"


@dataclass
class MoatAssessment:
    """护城河评估结果"""
    moat_type: MoatType
    reality_grade: RealityGrade
    reality_score: float  # 0-100
    continuity_grade: ContinuityGrade
    continuity_score: float  # 0-100
    warning_level: WarningLevel
    erosion_factors: List[str]
    strengthening_factors: List[str]
    boundary_conditions: List[str]
    early_warning_signals: List[str]


class MoatDialecticalAnalyzer:
    """护城河辩证分析器"""

    def __init__(self):
        self.erosion_factors = {
            "技术变革": "新技术颠覆传统模式",
            "竞争加剧": "竞争对手追赶、新进入者",
            "消费习惯": "消费者偏好改变",
            "监管政策": "政策变化影响商业模式",
            "成本结构": "成本优势丧失",
            "人才流失": "关键人才离职"
        }

        self.strengthening_factors = {
            "规模效应": "规模扩大，成本下降",
            "品牌积累": "品牌认知度提升",
            "网络效应": "用户增长带来价值提升",
            "技术积累": "技术壁垒提高",
            "客户粘性": "转换成本提高"
        }

    def analyze_layer2_reality(self, financial_data: Dict) -> MoatAssessment:
        """
        第二层：护城河本质辩证分析
        
        正题：从财务数据推断护城河
        反题：质疑护城河真实性
        合题：护城河本质验证
        再否定：护城河边界条件
        """
        # Step 1: 识别护城河类型（正题）
        moat_type = self._identify_moat_type(financial_data)

        # Step 2: 质疑护城河真实性（反题）
        reality_score = self._assess_reality(financial_data, moat_type)

        # Step 3: 真实性评级（合题）
        reality_grade = self._grade_reality(reality_score)

        # Step 4: 边界条件（再否定）
        boundary_conditions = self._identify_boundaries(moat_type)

        return {
            "moat_type": moat_type,
            "reality_grade": reality_grade,
            "reality_score": reality_score,
            "boundary_conditions": boundary_conditions
        }

    def analyze_layer3_continuity(self, 
                                   financial_data: Dict,
                                   moat_type: MoatType,
                                   reality_score: float) -> Dict:
        """
        第三层：护城河延续性辩证分析
        
        正题：护城河当前状态
        反题：护城河正在被侵蚀吗？
        合题：护城河演变趋势
        再否定：护城河失效临界点
        """
        # Step 1: 评估侵蚀因素（反题）
        erosion_score = self._assess_erosion(financial_data, moat_type)

        # Step 2: 评估强化因素（合题）
        strengthening_score = self._assess_strengthening(financial_data, moat_type)

        # Step 3: 延续性评分
        continuity_score = self._calculate_continuity(
            reality_score, erosion_score, strengthening_score
        )

        # Step 4: 延续性评级
        continuity_grade = self._grade_continuity(continuity_score)

        # Step 5: 预警等级
        warning_level = self._determine_warning_level(
            continuity_score, erosion_score
        )

        # Step 6: 失效临界点
        failure_points = self._identify_failure_points(moat_type)

        return {
            "continuity_grade": continuity_grade,
            "continuity_score": continuity_score,
            "warning_level": warning_level,
            "erosion_score": erosion_score,
            "strengthening_score": strengthening_score,
            "failure_points": failure_points
        }

    def _identify_moat_type(self, financial_data: Dict) -> MoatType:
        """从财务数据推断护城河类型"""
        roe = financial_data.get("roe", 0)
        gross_margin = financial_data.get("gross_margin", 0)
        asset_turnover = financial_data.get("asset_turnover", 0)
        rd_ratio = financial_data.get("rd_ratio", 0)

        # 推断逻辑
        if roe > 15 and gross_margin > 40:
            return MoatType.BRAND  # 高ROE + 高毛利率 → 品牌溢价
        elif roe > 15 and gross_margin < 30 and asset_turnover > 1:
            return MoatType.COST  # 高ROE + 低毛利率 + 高周转 → 成本优势
        elif rd_ratio > 5 and roe > 15:
            return MoatType.TECHNOLOGY  # 高研发 + 高ROE → 技术壁垒
        elif financial_data.get("user_growth", 0) > 10:
            return MoatType.NETWORK_EFFECT  # 用户高增长 → 网络效应
        else:
            return MoatType.NONE

    def _assess_reality(self, financial_data: Dict, moat_type: MoatType) -> float:
        """评估护城河真实性"""
        score = 50  # 基础分

        # 质疑一：是护城河还是行业红利？
        industry_roe = financial_data.get("industry_roe", 10)
        if financial_data.get("roe", 0) > industry_roe + 5:
            score += 15  # 超越行业

        # 质疑二：是能力还是运气？
        years_stable = financial_data.get("years_stable", 0)
        if years_stable >= 5:
            score += 15  # 跨周期验证

        # 质疑三：是可持续优势还是一次性机会？
        competitor_gap = financial_data.get("competitor_gap", 0)
        if competitor_gap > 10:  # 与竞争对手差距
            score += 10

        # 负面因素
        if financial_data.get("one_time_income", 0) > 0.1:
            score -= 15  # 一次性收入占比高

        return min(100, max(0, score))

    def _grade_reality(self, score: float) -> RealityGrade:
        """真实性评级"""
        if score >= 85:
            return RealityGrade.A
        elif score >= 70:
            return RealityGrade.B
        elif score >= 50:
            return RealityGrade.C
        else:
            return RealityGrade.D

    def _identify_boundaries(self, moat_type: MoatType) -> List[str]:
        """识别护城河边界条件"""
        boundaries = {
            MoatType.BRAND: [
                "品牌信任危机",
                "替代品崛起",
                "负面舆论持续发酵"
            ],
            MoatType.TECHNOLOGY: [
                "技术路线被颠覆",
                "核心专利过期",
                "研发人才大规模流失"
            ],
            MoatType.COST: [
                "规模优势丧失",
                "原材料价格大幅上涨",
                "竞争对手实现更低成本"
            ],
            MoatType.NETWORK_EFFECT: [
                "用户大规模流失",
                "平台迁移成本降低",
                "竞品网络效应超越"
            ],
            MoatType.SWITCHING_COST: [
                "客户找到替代方案",
                "转换成本大幅降低",
                "客户续约率持续下降"
            ],
            MoatType.FRANCHISE: [
                "政策变化取消特许",
                "新进入者获得同样许可",
                "行业监管收紧"
            ],
            MoatType.NONE: [
                "本身无护城河"
            ]
        }
        return boundaries.get(moat_type, ["未识别"])

    def _assess_erosion(self, financial_data: Dict, moat_type: MoatType) -> float:
        """评估侵蚀程度"""
        erosion_score = 0  # 0-100，越高越严重

        # 技术变革
        if financial_data.get("tech_disruption_risk", 0) > 0.5:
            erosion_score += 20

        # 竞争加剧
        if financial_data.get("competition_intensity", 0) > 0.7:
            erosion_score += 15

        # 消费习惯变化
        if financial_data.get("consumer_change", 0) > 0.5:
            erosion_score += 15

        # 毛利率下滑
        if financial_data.get("gross_margin_trend", 0) < -0.05:
            erosion_score += 15

        # 市占率下滑
        if financial_data.get("market_share_trend", 0) < -0.02:
            erosion_score += 20

        return min(100, erosion_score)

    def _assess_strengthening(self, financial_data: Dict, moat_type: MoatType) -> float:
        """评估强化程度"""
        strengthening_score = 0  # 0-100

        # 规模效应
        if financial_data.get("revenue_growth", 0) > 0.15:
            strengthening_score += 20

        # 研发投入增加
        if financial_data.get("rd_trend", 0) > 0.05:
            strengthening_score += 15

        # 用户增长
        if financial_data.get("user_growth", 0) > 0.10:
            strengthening_score += 15

        # 市占率提升
        if financial_data.get("market_share_trend", 0) > 0.02:
            strengthening_score += 20

        # 品牌投入
        if financial_data.get("marketing_ratio", 0) > 0.10:
            strengthening_score += 10

        return min(100, strengthening_score)

    def _calculate_continuity(self, 
                              reality_score: float,
                              erosion_score: float,
                              strengthening_score: float) -> float:
        """计算延续性评分"""
        # 基于真实性、侵蚀、强化三因素
        # 真实性权重40%，侵蚀权重-30%，强化权重+30%
        continuity = (
            reality_score * 0.4 +
            (100 - erosion_score) * 0.3 +
            strengthening_score * 0.3
        )
        return min(100, max(0, continuity))

    def _grade_continuity(self, score: float) -> ContinuityGrade:
        """延续性评级"""
        if score >= 85:
            return ContinuityGrade.A
        elif score >= 70:
            return ContinuityGrade.B
        elif score >= 50:
            return ContinuityGrade.C
        else:
            return ContinuityGrade.D

    def _determine_warning_level(self, 
                                  continuity_score: float,
                                  erosion_score: float) -> WarningLevel:
        """确定预警等级"""
        if continuity_score < 50 or erosion_score > 70:
            return WarningLevel.RED
        elif continuity_score < 65 or erosion_score > 50:
            return WarningLevel.ORANGE
        elif continuity_score < 75 or erosion_score > 30:
            return WarningLevel.YELLOW
        else:
            return WarningLevel.GREEN

    def _identify_failure_points(self, moat_type: MoatType) -> List[str]:
        """识别失效临界点"""
        return self._identify_boundaries(moat_type)

    def generate_assessment_report(self, 
                                    financial_data: Dict,
                                    company_name: str = "公司") -> str:
        """生成护城河评估报告"""
        # 第一层分析
        layer2_result = self.analyze_layer2_reality(financial_data)

        # 第二层分析
        layer3_result = self.analyze_layer3_continuity(
            financial_data,
            layer2_result["moat_type"],
            layer2_result["reality_score"]
        )

        # 生成报告
        report = []
        report.append(f"# 护城河辩证分析报告")
        report.append(f"\n## 公司：{company_name}\n")

        report.append("## 第一层：财务数据辩证")
        report.append("（已有框架分析）\n")

        report.append("## 第二层：护城河本质辩证 ⭐")
        report.append(f"- **识别的护城河类型**：{layer2_result['moat_type'].value}")
        report.append(f"- **真实性评分**：{layer2_result['reality_score']:.1f}")
        report.append(f"- **真实性等级**：{layer2_result['reality_grade'].value}")
        report.append(f"- **边界条件**：{', '.join(layer2_result['boundary_conditions'])}\n")

        report.append("## 第三层：护城河延续性辩证 ⭐")
        report.append(f"- **延续性评分**：{layer3_result['continuity_score']:.1f}")
        report.append(f"- **延续性等级**：{layer3_result['continuity_grade'].value}")
        report.append(f"- **预警等级**：{layer3_result['warning_level'].value}")
        report.append(f"- **侵蚀评分**：{layer3_result['erosion_score']:.1f}")
        report.append(f"- **强化评分**：{layer3_result['strengthening_score']:.1f}")
        report.append(f"- **失效临界点**：{', '.join(layer3_result['failure_points'])}\n")

        report.append("## 综合判断")
        # 判断投资价值
        if (layer2_result["reality_grade"] in [RealityGrade.A, RealityGrade.B] and
            layer3_result["continuity_grade"] in [ContinuityGrade.A, ContinuityGrade.B]):
            report.append("✅ **核心资产**：真护城河 + 强延续性")
        elif layer3_result["warning_level"] == WarningLevel.RED:
            report.append("❌ **避免投资**：护城河即将失效")
        elif layer3_result["warning_level"] == WarningLevel.ORANGE:
            report.append("⚠️ **暂缓投资**：护城河加速侵蚀")
        else:
            report.append("📋 **待观察**：需要进一步验证")

        return "\n".join(report)


# 使用示例
if __name__ == "__main__":
    analyzer = MoatDialecticalAnalyzer()

    # 示例财务数据
    sample_data = {
        "roe": 28.6,
        "gross_margin": 63.1,
        "asset_turnover": 0.8,
        "rd_ratio": 10.2,
        "industry_roe": 15,
        "years_stable": 8,
        "competitor_gap": 15,
        "one_time_income": 0.02,
        "tech_disruption_risk": 0.2,
        "competition_intensity": 0.5,
        "consumer_change": 0.3,
        "gross_margin_trend": -0.02,
        "market_share_trend": 0.01,
        "revenue_growth": 0.05,
        "rd_trend": 0.08,
        "user_growth": 0,
        "marketing_ratio": 0.12
    }

    report = analyzer.generate_assessment_report(sample_data, "迈瑞医疗")
    print(report)