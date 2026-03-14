"""
V8.0 数据质量把控标准

核心原则：准确性优先于速度
"""

from typing import List, Dict, Tuple, Any

# ============================================================
# 阶段1：数据收集 - 质量标准
# ============================================================

## 数据源优先级
P0_SOURCES = ["年报", "10-K", "10-Q", "AkShare-东方财富"]  # 官方/权威
P1_SOURCES = ["雪球公告", "Bloomberg", "官方公告"]
P2_SOURCES = ["雪球专栏", "Tavily", "Exa"]
P3_SOURCES = ["雪球讨论", "新闻"]  # 需交叉验证

## 核心财务指标必需项
REQUIRED_METRICS = {
    "ROE": {
        "min": -50,
        "max": 100,
        "description": "净资产收益率",
        "unit": "%",
        "cross_check": ["净利润", "净资产"]
    },
    "毛利率": {
        "min": 0,
        "max": 100,
        "description": "毛利率",
        "unit": "%"
    },
    "营收": {
        "min": 0,
        "max": None,
        "description": "营业收入",
        "unit": "亿元"
    },
    "净利润": {
        "min": None,  # 允许亏损
        "max": None,
        "description": "净利润",
        "unit": "亿元"
    }
}

## 数据验证规则
VALIDATION_RULES = {
    # 规则1：数值范围检查
    "range_check": {
        "enabled": True,
        "action": "warn"  # warn | reject
    },
    
    # 规则2：交叉验证
    "cross_check": {
        "enabled": True,
        "description": "ROE = 净利润 / 净资产 × 100%"
    },
    
    # 规则3：来源验证
    "source_check": {
        "enabled": True,
        "min_source_quality": "P2"  # P0/P1/P2/P3
    },
    
    # 规则4：时效性检查
    "timeliness_check": {
        "enabled": True,
        "max_age_days": 365  # 数据最大年龄
    }
}

## 阶段1 通过标准
STAGE1_PASS_CRITERIA = {
    "min_core_metrics": 4,        # 至少4个核心指标
    "min_quality_score": 6.0,      # 平均质量评分
    "min_trusted_ratio": 0.5,      # 可信数据比例
    "required_sources": ["P0"]     # 必须有P0级数据源
}


# ============================================================
# 阶段2：财务异常分析 - 质量标准
# ============================================================

## 异常检测阈值
ANOMALY_THRESHOLDS = {
    "ROE": {
        "high": 30,      # 高于30%视为异常
        "low": 0,        # 低于0%视为异常
        "compare_industry": True
    },
    "毛利率": {
        "high": 60,
        "low": 10,
        "compare_industry": True
    },
    "净利润增速": {
        "high": 100,     # 增长超过100%
        "low": -50,      # 下降超过50%
        "compare_industry": False
    }
}

## 阶段2 通过标准
STAGE2_PASS_CRITERIA = {
    "min_anomalies": 1,            # 至少发现1个异常
    "anomaly_has_evidence": True,   # 每个异常有证据支撑
    "question_is_specific": True    # 追问指向具体经营层面
}


# ============================================================
# 阶段3：经营分析 - 质量标准
# ============================================================

## 经营洞察标准
INSIGHT_STANDARDS = {
    "min_length": 50,             # 最少50字
    "max_length": 200,            # 最多200字
    "must_have_evidence": True,   # 必须有证据支撑
    "must_be_actionable": True    # 必须指向可验证的经营因素
}

## 阶段3 通过标准
STAGE3_PASS_CRITERIA = {
    "min_insights": 2,
    "min_evidence_per_insight": 1,
    "identified_capability": True  # 识别出核心经营能力
}


# ============================================================
# 阶段4：护城河识别 - 质量标准
# ============================================================

## 护城河类型定义
MOAT_TYPES = {
    "网络效应": {
        "key_question": "用户越多，价值是否越大？",
        "required_evidence": ["用户增长", "GMV增速", "获客成本下降"]
    },
    "转换成本": {
        "key_question": "客户换掉我们会损失什么？",
        "required_evidence": ["客户留存率", "续约率"]
    },
    "成本优势": {
        "key_question": "低成本来自哪里？",
        "required_evidence": ["毛利率对比", "单位成本对比"]
    },
    "无形资产": {
        "key_question": "品牌/专利能带来定价权吗？",
        "required_evidence": ["品牌溢价", "专利数量"]
    },
    "有效规模": {
        "key_question": "新进入者会破坏均衡吗？",
        "required_evidence": ["ROIC对比", "竞争者数量"]
    }
}

## 阶段4 通过标准
STAGE4_PASS_CRITERIA = {
    "moat_type_identified": True,
    "min_confidence": 0.7,
    "min_evidence": 2,
    "answered_key_question": True
}


# ============================================================
# 阶段5：不可复制性分析 - 质量标准
# ============================================================

## 可持续性评级标准
SUSTAINABILITY_RATINGS = {
    "强": {
        "timeframe": "5年以上",
        "criteria": "竞争对手无法在短期内复制"
    },
    "中": {
        "timeframe": "3-5年",
        "criteria": "竞争对手需要大量投入才能复制"
    },
    "弱": {
        "timeframe": "1-3年",
        "criteria": "竞争对手可能快速追赶"
    }
}

## 阶段5 通过标准
STAGE5_PASS_CRITERIA = {
    "sustainability_rated": True,
    "min_reasons": 2,
    "identified_risks": True,  # 必须识别风险
    "conclusion_complete": True
}


# ============================================================
# 阶段6：报告生成 - 质量标准
# ============================================================

## 报告质量检查
REPORT_QUALITY_CHECKS = [
    "核心结论完整（一句话）",
    "核心结论无截断",
    "财务数据表格清晰",
    "每层追问有核心发现",
    "护城河类型明确",
    "投资建议有依据"
]

## 报告结构验证
REPORT_STRUCTURE = {
    "must_have": [
        "核心结论",
        "财务数据表格",
        "五层追问分析",
        "护城河评估",
        "投资建议"
    ],
    "must_not_have": [
        "截断的句子",
        "空白的表格",
        "未识别的护城河类型"
    ]
}


# ============================================================
# 质量把控流程
# ============================================================

class QualityGate:
    """质量门禁"""
    
    def __init__(self, stage: str, criteria: dict):
        self.stage = stage
        self.criteria = criteria
        self.results = []
    
    def check(self, result: dict) -> tuple:
        """
        检验结果
        
        Returns:
            (passed: bool, issues: List[str])
        """
        issues = []
        
        for key, requirement in self.criteria.items():
            if isinstance(requirement, bool):
                if result.get(key) != requirement:
                    issues.append(f"{key} 未满足")
            elif isinstance(requirement, (int, float)):
                if result.get(key, 0) < requirement:
                    issues.append(f"{key} 不达标 ({result.get(key, 0)} < {requirement})")
        
        passed = len(issues) == 0
        return passed, issues
    
    def report(self, passed: bool, issues: List[str]):
        """输出检验报告"""
        print(f"\n{'='*50}")
        print(f"[质量检验] {self.stage}")
        print(f"{'='*50}")
        
        if passed:
            print("✅ 检验通过")
        else:
            print("❌ 检验未通过")
            for issue in issues:
                print(f"  - {issue}")
        
        print(f"{'='*50}\n")


# ============================================================
# 使用示例
# ============================================================

if __name__ == "__main__":
    # 阶段1质量检验
    stage1_gate = QualityGate("数据收集", STAGE1_PASS_CRITERIA)
    
    # 模拟结果
    result = {
        "min_core_metrics": 7,
        "min_quality_score": 7.0,
        "min_trusted_ratio": 0.6,
        "required_sources": ["P0"]
    }
    
    passed, issues = stage1_gate.check(result)
    stage1_gate.report(passed, issues)