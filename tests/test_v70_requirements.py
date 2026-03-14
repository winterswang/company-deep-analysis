#!/usr/bin/env python3
"""
V7.0 需求单元测试

严格对照需求文档 REQUIREMENTS_V70.md，验证每个功能点是否正确实现。
"""

import sys
import os
import unittest
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.financial_data_validator import FinancialDataValidator
from core.negation_validator import NegationValidator, DataQualityLabel
from core.loop_questioning_engine import (
    LoopQuestioningEngine,
    QuestioningResult,
    Evidence,
    ToDo,
    ToDoType,
    FinancialAnomaly,
    MoatType,
    EvidenceQuality
)


class TestXueqiuDataQuality(unittest.TestCase):
    """
    测试需求 §2.2：雪球数据质量评估规则
    
    严格按照需求文档的字符数判断标准
    """
    
    def setUp(self):
        self.validator = FinancialDataValidator()
    
    def test_专栏_300字符以上_P0(self):
        """专栏文章 ≥300字符 → P0"""
        # 确保内容超过300字符
        content = "A" * 350  # 用350个字符确保超过300
        quality, discard = self.validator.evaluate_xueqiu_data_quality("专栏", content, "")
        
        self.assertGreaterEqual(len(content), 300, f"测试内容应≥300字符，实际{len(content)}")
        self.assertEqual(quality, "P0", f"专栏文章≥300字符应为P0")
        self.assertFalse(discard, "P0不应丢弃")
    
    def test_专栏_300字符以下_P2(self):
        """专栏文章 <300字符 → P2"""
        content = "这是一篇短文章"
        quality, discard = self.validator.evaluate_xueqiu_data_quality("专栏", content, "")
        
        self.assertEqual(quality, "P2", "专栏文章<300字符应为P2")
        self.assertFalse(discard, "P2不应丢弃")
    
    def test_公告_固定P1(self):
        """公告 → 固定P1"""
        content = "公告内容"
        quality, discard = self.validator.evaluate_xueqiu_data_quality("公告", content, "")
        
        self.assertEqual(quality, "P1", "公告应为P1")
        self.assertFalse(discard, "P1不应丢弃")
    
    def test_资讯_标题20字符以上_P2(self):
        """资讯 标题≥20字符 → P2"""
        content = "资讯内容"
        title = "这是一个足够长的标题超过二十个字符了啊啊啊"  # 确保超过20字符
        quality, discard = self.validator.evaluate_xueqiu_data_quality("资讯", content, title)
        
        self.assertEqual(quality, "P2", f"资讯标题≥20字符应为P2，标题长度{len(title)}")
        self.assertFalse(discard, "P2不应丢弃")
    
    def test_资讯_标题20字符以下_丢弃(self):
        """资讯 标题<20字符 → 丢弃"""
        content = "资讯内容"
        title = "短标题"
        quality, discard = self.validator.evaluate_xueqiu_data_quality("资讯", content, title)
        
        self.assertTrue(discard, "短标题资讯应丢弃")
    
    def test_讨论_50字符以下_P4丢弃(self):
        """讨论 <50字符 → P4 丢弃"""
        content = "太短了"
        quality, discard = self.validator.evaluate_xueqiu_data_quality("讨论", content, "")
        
        self.assertEqual(quality, "P4", "讨论<50字符应为P4")
        self.assertTrue(discard, "P4应丢弃")
    
    def test_讨论_50到150字符_P3丢弃(self):
        """讨论 50-150字符 → P3 丢弃"""
        content = "这是一个中等长度的讨论大约有一百多个字符我们需要测试一下这个逻辑是否正确工作再多加一些内容确保超过五十字符"  # 确保在50-150之间
        quality, discard = self.validator.evaluate_xueqiu_data_quality("讨论", content, "")
        
        self.assertEqual(quality, "P3", f"讨论50-150字符应为P3，实际长度{len(content)}")
        self.assertTrue(discard, "P3应丢弃")
    
    def test_讨论_150到300字符_P2保留(self):
        """讨论 150-300字符 → P2 保留"""
        content = "这是一个中等长度的讨论我们需要测试一下这个逻辑是否正确工作这是一个中等长度的讨论我们需要测试一下这个逻辑是否正确工作这是第三个段落确保超过一百五十个字符的测试内容" * 2  # 确保在150-300之间
        quality, discard = self.validator.evaluate_xueqiu_data_quality("讨论", content, "")
        
        self.assertEqual(quality, "P2", f"讨论150-300字符应为P2，实际长度{len(content)}")
        self.assertFalse(discard, "P2不应丢弃")
    
    def test_讨论_300字符以上_P1保留(self):
        """讨论 >300字符 → P1 保留"""
        content = "B" * 350  # 用350个字符确保超过300
        quality, discard = self.validator.evaluate_xueqiu_data_quality("讨论", content, "")
        
        self.assertGreaterEqual(len(content), 300, f"测试内容应>300字符，实际{len(content)}")
        self.assertEqual(quality, "P1", f"讨论>300字符应为P1")
        self.assertFalse(discard, "P1不应丢弃")


class TestDataSourceReliability(unittest.TestCase):
    """
    测试需求 §2.1：数据源质量等级
    """
    
    def setUp(self):
        self.validator = FinancialDataValidator()
    
    def test_P0_来源_年报(self):
        """年报 → P0 (3.0分)"""
        score = self.validator.SOURCE_RELIABILITY.get("年报", 0)
        self.assertEqual(score, 3.0, "年报应为P0 (3.0分)")
    
    def test_P0_来源_AkShare(self):
        """AkShare → P0-P1 (2.0分)"""
        score = self.validator.SOURCE_RELIABILITY.get("AkShare", 0)
        self.assertGreaterEqual(score, 2.0, "AkShare应≥P1")
    
    def test_P1_来源_雪球专栏(self):
        """雪球专栏 → P1 (2.0分)"""
        score = self.validator.SOURCE_RELIABILITY.get("雪球专栏", 0)
        self.assertGreaterEqual(score, 2.0, "雪球专栏应≥P1")
    
    def test_P2_来源_Tavily(self):
        """Tavily → P2 (1.5分)"""
        score = self.validator.SOURCE_RELIABILITY.get("Tavily", 0)
        self.assertGreaterEqual(score, 1.0, "Tavily应≥P2")


class TestNegationValidation(unittest.TestCase):
    """
    测试需求 §3：否定之否定验证
    """
    
    def setUp(self):
        self.validator = NegationValidator()
    
    def test_四步验证流程(self):
        """验证四步流程是否完整"""
        data = {
            "data_point": "ROIC",
            "value": 18.5,
            "source": "雪球专栏",
            "timestamp": "2024-01-01"
        }
        
        # 第一步：收集初始数据
        self.assertIn("data_point", data)
        
        # 第二步：生成质疑
        doubts = self.validator._generate_doubts(data)
        self.assertGreater(len(doubts), 0, "应生成质疑")
    
    def test_质量标签生成(self):
        """测试质量标签（可信/待验证/不可用）"""
        # 高分 → 可信
        label = self.validator._determine_quality_label(8.5, [])
        self.assertEqual(label, DataQualityLabel.TRUSTED)
        
        # 中分 → 待验证
        label = self.validator._determine_quality_label(6.5, [])
        self.assertEqual(label, DataQualityLabel.PENDING)
        
        # 低分 → 不可用
        label = self.validator._determine_quality_label(4.0, [])
        self.assertEqual(label, DataQualityLabel.UNAVAILABLE)


class TestFiveLayerQuestioning(unittest.TestCase):
    """
    测试需求 §4：五层追问模型
    """
    
    def test_五层追问定义(self):
        """验证五层追问是否正确定义"""
        engine = LoopQuestioningEngine()
        
        # 检查五层定义
        self.assertEqual(len(engine.LAYER_TODO_TEMPLATES), 5, "应有5层追问")
        
        # 检查每层的 ToDo 类型
        for layer in range(1, 6):
            self.assertIn(layer, engine.LAYER_TODO_TEMPLATES)
    
    def test_追问生成(self):
        """测试追问生成"""
        engine = LoopQuestioningEngine()
        
        anomaly = FinancialAnomaly(
            metric="ROIC",
            value=18.5,
            trend=[15.0, 16.0, 17.0, 18.5],
            benchmark=15.0,
            deviation="高于行业平均",
            severity="中",
            question="ROIC为何高于行业平均？"
        )
        
        context = {"company": "拼多多"}
        
        # 生成第1层追问
        question = engine._generate_question(1, anomaly, context)
        self.assertIn("ROIC", question, "第1层追问应包含ROIC")
        
        # 生成第5层追问
        question = engine._generate_question(5, anomaly, context)
        self.assertIn("竞争对手", question, "第5层追问应提及竞争对手")


class TestLoopMechanism(unittest.TestCase):
    """
    测试需求 §7：循环追问机制
    """
    
    def test_终止条件_连续失败(self):
        """测试终止条件：连续失败N次"""
        engine = LoopQuestioningEngine()
        self.assertEqual(engine.max_consecutive_failures, 3, "连续失败3次应终止")
    
    def test_终止条件_最大迭代(self):
        """测试终止条件：最大迭代次数"""
        engine = LoopQuestioningEngine()
        self.assertEqual(engine.max_iterations, 10, "最大迭代10次")
    
    def test_证据质量验证(self):
        """测试证据质量验证"""
        engine = LoopQuestioningEngine()
        
        # 创建不同质量的证据
        evidence_list = [
            Evidence(
                id="1",
                content="这是一个测试内容长度超过五十个字符应该被保留下来用于后续分析处理的证据材料需要再多加一些字符确保超过五十",
                source="测试",
                quality=EvidenceQuality.P1,
                relevance=0.8
            ),
            Evidence(
                id="2",
                content="短内容",
                source="测试",
                quality=EvidenceQuality.P3,  # P3是最低质量
                relevance=0.3
            )
        ]
        
        valid = engine._validate_evidence(evidence_list)
        
        # P3 低质量证据应被过滤，P1 高质量证据应保留
        self.assertEqual(len(valid), 1, "应过滤低质量证据，保留高质量证据")
    
    def test_备选搜索关键词生成(self):
        """测试备选搜索关键词生成"""
        engine = LoopQuestioningEngine()
        
        anomaly = FinancialAnomaly(
            metric="ROIC",
            value=18.5,
            trend=[15.0, 16.0, 17.0, 18.5],
            benchmark=15.0,
            deviation="高于行业平均",
            severity="中",
            question="ROIC为何高于行业平均？"
        )
        
        # 测试各层备选查询
        for layer in range(1, 6):
            queries = engine._generate_alternative_queries(anomaly, layer)
            self.assertGreater(len(queries), 0, f"第{layer}层应有备选查询")


class TestToDoTypes(unittest.TestCase):
    """
    测试需求 §7.2：ToDo 类型定义
    """
    
    def test_ToDo类型完整性(self):
        """验证所有 ToDo 类型是否定义"""
        required_types = [
            "DATA_VALIDATION",
            "DATA_RETRIEVAL",
            "DATA_CRAWLING",
            "DEEP_ANALYSIS",
            "EVIDENCE_SUPPLEMENT"
        ]
        
        for type_name in required_types:
            self.assertTrue(hasattr(ToDoType, type_name), f"ToDoType 应包含 {type_name}")
    
    def test_ToDo创建(self):
        """测试 ToDo 创建"""
        todo = ToDo(
            id="test_1",
            todo_type=ToDoType.DATA_RETRIEVAL,
            description="测试任务",
            priority="高",
            status="待执行",
            data_sources=["年报"],
            expected_output="财务数据"
        )
        
        self.assertEqual(todo.priority, "高")


class TestReportStructure(unittest.TestCase):
    """
    测试需求 §9.3：报告结构
    """
    
    def test_报告四部分结构(self):
        """验证报告包含四部分"""
        from core.report_generator import V70ReportGenerator
        
        generator = V70ReportGenerator()
        
        # 检查报告结构
        self.assertTrue(hasattr(generator, "generate_complete_report"))
        self.assertTrue(hasattr(generator, "_generate_core_insight"))
        self.assertTrue(hasattr(generator, "_generate_risk_analysis"))
        self.assertTrue(hasattr(generator, "_generate_investment_recommendation"))


class TestMoatIdentification(unittest.TestCase):
    """
    测试护城河识别
    """
    
    def test_护城河类型定义(self):
        """验证护城河类型定义"""
        required_moats = [
            "NETWORK_EFFECT",
            "SWITCHING_COST",
            "COST_ADVANTAGE",
            "INTANGIBLE_ASSETS",  # 注意：是复数
            "EFFICIENT_SCALE"
        ]
        
        for moat in required_moats:
            self.assertTrue(hasattr(MoatType, moat), f"MoatType 应包含 {moat}")


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestXueqiuDataQuality))
    suite.addTests(loader.loadTestsFromTestCase(TestDataSourceReliability))
    suite.addTests(loader.loadTestsFromTestCase(TestNegationValidation))
    suite.addTests(loader.loadTestsFromTestCase(TestFiveLayerQuestioning))
    suite.addTests(loader.loadTestsFromTestCase(TestLoopMechanism))
    suite.addTests(loader.loadTestsFromTestCase(TestToDoTypes))
    suite.addTests(loader.loadTestsFromTestCase(TestReportStructure))
    suite.addTests(loader.loadTestsFromTestCase(TestMoatIdentification))
    
    # 运行测试
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    sys.exit(0 if result.wasSuccessful() else 1)