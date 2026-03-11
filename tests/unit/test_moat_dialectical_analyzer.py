"""
单元测试：护城河辩证分析器
"""

import pytest
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from scripts.moat_dialectical_analyzer import (
    MoatDialecticalAnalyzer,
    MoatType,
    RealityGrade,
    ContinuityGrade,
    WarningLevel
)


class TestMoatDialecticalAnalyzer:
    """护城河辩证分析器测试"""

    @pytest.fixture
    def analyzer(self):
        return MoatDialecticalAnalyzer()

    @pytest.fixture
    def sample_financial_data(self):
        """示例财务数据"""
        return {
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

    def test_identify_moat_type_brand(self, analyzer):
        """测试护城河类型识别：品牌"""
        data = {
            "roe": 25,
            "gross_margin": 50,  # 高毛利率
            "asset_turnover": 0.5,
            "rd_ratio": 2
        }
        moat_type = analyzer._identify_moat_type(data)
        assert moat_type == MoatType.BRAND

    def test_identify_moat_type_cost(self, analyzer):
        """测试护城河类型识别：成本优势"""
        data = {
            "roe": 20,
            "gross_margin": 20,  # 低毛利率
            "asset_turnover": 1.5,  # 高周转
            "rd_ratio": 1
        }
        moat_type = analyzer._identify_moat_type(data)
        assert moat_type == MoatType.COST

    def test_identify_moat_type_technology(self, analyzer):
        """测试护城河类型识别：技术壁垒"""
        data = {
            "roe": 20,
            "gross_margin": 40,
            "asset_turnover": 0.5,
            "rd_ratio": 8  # 高研发投入
        }
        moat_type = analyzer._identify_moat_type(data)
        assert moat_type == MoatType.TECHNOLOGY

    def test_assess_reality_high(self, analyzer, sample_financial_data):
        """测试真实性评估：高真实性"""
        score = analyzer._assess_reality(sample_financial_data, MoatType.TECHNOLOGY)
        assert score >= 70  # 应该是 B 级以上

    def test_assess_reality_low(self, analyzer):
        """测试真实性评估：低真实性"""
        data = {
            "roe": 15,
            "gross_margin": 30,
            "industry_roe": 14,  # 接近行业平均
            "years_stable": 1,  # 不稳定
            "competitor_gap": 1,
            "one_time_income": 0.2  # 一次性收入高
        }
        score = analyzer._assess_reality(data, MoatType.BRAND)
        assert score < 60  # 应该是 C 级以下

    def test_grade_reality(self, analyzer):
        """测试真实性评级"""
        assert analyzer._grade_reality(90) == RealityGrade.A
        assert analyzer._grade_reality(75) == RealityGrade.B
        assert analyzer._grade_reality(55) == RealityGrade.C
        assert analyzer._grade_reality(40) == RealityGrade.D

    def test_assess_erosion(self, analyzer, sample_financial_data):
        """测试侵蚀程度评估"""
        erosion = analyzer._assess_erosion(sample_financial_data, MoatType.TECHNOLOGY)
        assert 0 <= erosion <= 100

    def test_assess_strengthening(self, analyzer, sample_financial_data):
        """测试强化程度评估"""
        strengthening = analyzer._assess_strengthening(sample_financial_data, MoatType.TECHNOLOGY)
        assert 0 <= strengthening <= 100

    def test_calculate_continuity(self, analyzer):
        """测试延续性计算"""
        continuity = analyzer._calculate_continuity(80, 30, 50)
        assert 0 <= continuity <= 100
        # 真实性高、侵蚀低、强化中等 → 延续性应该较高
        assert continuity >= 60

    def test_grade_continuity(self, analyzer):
        """测试延续性评级"""
        assert analyzer._grade_continuity(90) == ContinuityGrade.A
        assert analyzer._grade_continuity(75) == ContinuityGrade.B
        assert analyzer._grade_continuity(55) == ContinuityGrade.C
        assert analyzer._grade_continuity(40) == ContinuityGrade.D

    def test_determine_warning_level_red(self, analyzer):
        """测试预警等级：红色"""
        level = analyzer._determine_warning_level(40, 80)
        assert level == WarningLevel.RED

    def test_determine_warning_level_green(self, analyzer):
        """测试预警等级：绿色"""
        level = analyzer._determine_warning_level(85, 20)
        assert level == WarningLevel.GREEN

    def test_analyze_layer2_reality(self, analyzer, sample_financial_data):
        """测试第二层分析"""
        result = analyzer.analyze_layer2_reality(sample_financial_data)
        
        assert "moat_type" in result
        assert "reality_grade" in result
        assert "reality_score" in result
        assert "boundary_conditions" in result

    def test_analyze_layer3_continuity(self, analyzer, sample_financial_data):
        """测试第三层分析"""
        result = analyzer.analyze_layer3_continuity(
            sample_financial_data,
            MoatType.TECHNOLOGY,
            80
        )
        
        assert "continuity_grade" in result
        assert "continuity_score" in result
        assert "warning_level" in result
        assert "erosion_score" in result
        assert "strengthening_score" in result

    def test_generate_assessment_report(self, analyzer, sample_financial_data):
        """测试报告生成"""
        report = analyzer.generate_assessment_report(sample_financial_data, "测试公司")
        
        assert "测试公司" in report
        assert "护城河类型" in report
        assert "真实性" in report
        assert "延续性" in report


if __name__ == "__main__":
    pytest.main([__file__, "-v"])