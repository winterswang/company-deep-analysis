"""
V6.2 辩证式投资分析器 - 数据质量严格控制

核心改进：
1. 数据质量检查：P2以下数据丢弃
2. 数据不足时退出，给出明确理由
3. 数据来源强制标注
4. 辩证过程完整展示
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


# ==================== 数据质量分级 ====================

class DataQualityLevel:
    """数据质量等级"""
    P0 = "P0"  # 官方一手数据
    P1 = "P1"  # 权威第三方
    P2 = "P2"  # 专业机构
    P3 = "P3"  # 媒体报道（丢弃）
    P4 = "P4"  # 未验证/估算（丢弃）
    
    @classmethod
    def is_valid(cls, level: str) -> bool:
        """检查数据质量是否达标（P2及以上）"""
        return level in [cls.P0, cls.P1, cls.P2]
    
    @classmethod
    def get_description(cls, level: str) -> str:
        descriptions = {
            cls.P0: "官方一手数据，最高可信度",
            cls.P1: "权威第三方数据，可直接使用",
            cls.P2: "专业机构数据，需交叉验证",
            cls.P3: "媒体报道，质量不足，已丢弃",
            cls.P4: "未验证/估算数据，已丢弃"
        }
        return descriptions.get(level, "未知")


# ==================== 数据项定义 ====================

@dataclass
class DataPoint:
    """数据项"""
    name: str
    value: Any
    source: str
    quality: str
    timestamp: str = ""
    validity: str = ""
    notes: str = ""
    
    def is_valid(self) -> bool:
        return DataQualityLevel.is_valid(self.quality)


@dataclass
class DataCollection:
    """数据集合"""
    company: str
    data_points: List[DataPoint] = field(default_factory=list)
    collection_time: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def add_data(self, data_point: DataPoint):
        self.data_points.append(data_point)
    
    def get_valid_data(self) -> List[DataPoint]:
        return [d for d in self.data_points if d.is_valid()]
    
    def get_invalid_data(self) -> List[DataPoint]:
        return [d for d in self.data_points if not d.is_valid()]
    
    def quality_score(self) -> Tuple[int, int]:
        valid = len(self.get_valid_data())
        total = len(self.data_points)
        return valid, total
    
    def is_sufficient(self, min_valid_count: int = 10) -> Tuple[bool, str]:
        valid_count, total_count = self.quality_score()
        
        if total_count == 0:
            return False, "无任何数据"
        
        if valid_count < min_valid_count:
            invalid = self.get_invalid_data()
            invalid_items = [d.name for d in invalid]
            return False, f"有效数据不足：仅{valid_count}条有效数据（需要≥{min_valid_count}条），{len(invalid)}条低质量数据已丢弃"
        
        return True, f"数据充足：{valid_count}条有效数据"


# ==================== 数据检查器 ====================

class DataValidator:
    """数据验证器"""
    
    REQUIRED_DATA = {
        "financial": ["营收", "净利润", "ROIC", "毛利率", "现金流"],
        "valuation": ["市值", "P/E"],
        "business": ["主营业务"]
    }
    
    def validate(self, data_collection: DataCollection) -> Tuple[bool, Dict[str, Any]]:
        valid_data = data_collection.get_valid_data()
        valid_names = [d.name for d in valid_data]
        
        missing = {}
        for category, required in self.REQUIRED_DATA.items():
            missing[category] = [r for r in required if r not in valid_names]
        
        total_required = sum(len(v) for v in self.REQUIRED_DATA.values())
        total_found = total_required - sum(len(v) for v in missing.values())
        completeness = total_found / total_required if total_required > 0 else 0
        
        is_sufficient = completeness >= 0.7
        
        return is_sufficient, {
            "completeness": f"{completeness:.1%}",
            "missing": missing,
            "valid_count": len(valid_data)
        }


# ==================== 分析器V6.2 ====================

class DialecticalAnalyzerV62:
    """V6.2 辩证式分析器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.min_valid_data = self.config.get("min_valid_data", 8)
        
        self.data_validator = DataValidator()
        self.data_collection: Optional[DataCollection] = None
        self.exit_reason: Optional[str] = None
    
    def analyze(self, company: str, data_points: List[DataPoint] = None) -> Tuple[str, bool]:
        """执行分析"""
        print("=" * 70)
        print("V6.2 辩证式投资分析（数据质量严格控制）")
        print("=" * 70)
        print(f"目标公司: {company}")
        print(f"数据质量要求: P2及以上")
        print(f"最少有效数据: {self.min_valid_data}条")
        print("=" * 70)
        
        # 步骤1: 收集数据
        print("\n【步骤1: 数据收集与质量检查】")
        self.data_collection = DataCollection(company=company)
        
        if data_points:
            for dp in data_points:
                self.data_collection.add_data(dp)
                status = "✅ 有效" if dp.is_valid() else "❌ 丢弃"
                print(f"  {status} [{dp.quality}] {dp.name}: {dp.value}")
        
        # 步骤2: 检查数据充足性
        print("\n【步骤2: 数据充足性检查】")
        is_sufficient, reason = self.data_collection.is_sufficient(self.min_valid_data)
        print(f"  结果: {reason}")
        
        if not is_sufficient:
            self.exit_reason = reason
            print("\n❌ 数据不足，分析终止")
            return self._generate_insufficient_data_report(company, reason), False
        
        print("\n✅ 数据充足，继续分析...")
        return "数据检查通过，继续分析...", True
    
    def _generate_insufficient_data_report(self, company: str, reason: str) -> str:
        """生成数据不足报告"""
        valid_data = self.data_collection.get_valid_data() if self.data_collection else []
        invalid_data = self.data_collection.get_invalid_data() if self.data_collection else []
        
        report = f"""# {company} 分析报告

## ⚠️ 分析终止：数据不足

**终止原因**: {reason}

---

## 📊 数据质量检查结果

### 有效数据（P2及以上）：{len(valid_data)}条

| 数据项 | 数值 | 来源 | 质量 | 时效性 |
|--------|------|------|------|--------|
"""
        for d in valid_data:
            report += f"| {d.name} | {d.value} | {d.source} | {d.quality} | {d.validity} |\n"
        
        report += f"""
### 丢弃数据（P3及以下）：{len(invalid_data)}条

| 数据项 | 数值 | 来源 | 质量 | 丢弃原因 |
|--------|------|------|------|----------|
"""
        for d in invalid_data:
            report += f"| {d.name} | {d.value} | {d.source} | {d.quality} | {DataQualityLevel.get_description(d.quality)} |\n"
        
        report += f"""
---

## 📋 建议补充数据

| 数据项 | 建议来源 | 预期质量 |
|--------|----------|----------|
| 官方财报 | 公司IR网站 | P0 |
| 财务数据 | Bloomberg/S&P | P1 |
| 行业数据 | 行业协会 | P2 |

---

**报告时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析版本**: V6.2
"""
        return report


def main():
    """测试V6.2分析器"""
    
    test_data = [
        DataPoint("营收", "$21.2B", "估算", "P4", "2026-03-11", "2024E", "测试数据"),
        DataPoint("净利润", "$2.2B", "估算", "P4", "2026-03-11", "2024E", "测试数据"),
        DataPoint("ROIC", "8.74%", "官方财报", "P0", "2026-03-11", "TTM", "有效数据"),
        DataPoint("ROE", "22.3%", "Bloomberg", "P1", "2026-03-11", "TTM", "有效数据"),
        DataPoint("毛利率", "56.8%", "媒体报道", "P3", "2026-03-11", "2024E", "低质量数据"),
    ]
    
    analyzer = DialecticalAnalyzerV62({"min_valid_data": 5})
    report, success = analyzer.analyze("FISV", test_data)
    
    print("\n" + "=" * 70)
    print(report)


if __name__ == "__main__":
    main()