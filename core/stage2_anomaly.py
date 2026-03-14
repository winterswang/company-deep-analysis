"""
V8.0 阶段2：财务异常分析

职责：检测财务异常，生成深度追问

检验标准：
1. 至少发现1个财务异常
2. 每个异常有明确的问题
3. 问题指向具体的经营层面
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quality_standards import (
    ANOMALY_THRESHOLDS,
    STAGE2_PASS_CRITERIA
)
from core.llm_client import LLMClient


@dataclass
class Anomaly:
    """财务异常"""
    metric: str
    value: float
    threshold: Dict
    severity: str  # high/medium/low
    description: str
    question: str
    evidence: List[str] = field(default_factory=list)


@dataclass
class Stage2Result:
    """阶段2结果"""
    stage: str = "financial_anomaly"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    
    # 财务数据来源
    financial_data: Dict = field(default_factory=dict)
    
    # 异常列表
    anomalies: List[Dict] = field(default_factory=list)
    
    # 主要追问
    primary_question: str = ""
    
    # 质量门禁
    quality_gate: Dict = field(default_factory=dict)
    
    # 下一步
    next_action: str = ""
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class FinancialAnomalyAnalyzer:
    """财务异常分析器"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.anomalies: List[Anomaly] = []
    
    def execute(self, stage1_result: Dict) -> Stage2Result:
        """执行阶段2"""
        
        print("=" * 60)
        print("[阶段2] 财务异常分析")
        print("=" * 60)
        
        result = Stage2Result(
            stage="financial_anomaly",
            timestamp=datetime.now().isoformat(),
            company=stage1_result.get("company", "")
        )
        
        # 获取已验证的财务数据
        verified_data = stage1_result.get("verified_data", [])
        financial_data = {item["name"]: item["value"] for item in verified_data}
        result.financial_data = financial_data
        
        print(f"财务数据: {financial_data}\n")
        
        # Step 1: 检测异常
        print("[Step 1] 检测财务异常...")
        self._detect_anomalies(financial_data)
        
        if not self.anomalies:
            print("  ⚠️ 未检测到明显异常")
            result.status = "success"
            result.primary_question = "财务数据整体正常，继续分析经营能力"
            result.next_action = "stage3"
            return result
        
        # Step 2: 生成追问
        print(f"\n[Step 2] 生成深度追问...")
        for anomaly in self.anomalies:
            self._generate_question(anomaly, financial_data)
        
        # Step 3: 质量门禁
        print("\n[Step 3] 质量门禁检验...")
        passed, issues = self._quality_gate_check()
        result.quality_gate = {
            "passed": passed,
            "issues": issues
        }
        
        # 输出结果
        result.anomalies = [
            {
                "metric": a.metric,
                "value": a.value,
                "severity": a.severity,
                "description": a.description,
                "question": a.question
            }
            for a in self.anomalies
        ]
        
        if self.anomalies:
            result.primary_question = self.anomalies[0].question
        
        if passed:
            result.status = "success"
            result.next_action = "stage3"
        else:
            result.status = "partial"
            result.next_action = "stage3_with_warnings"
        
        # 输出摘要
        print("\n" + "=" * 60)
        print(f"状态: {result.status}")
        print(f"发现异常: {len(self.anomalies)} 个")
        for a in self.anomalies:
            print(f"  - {a.metric}: {a.value} ({a.severity})")
            print(f"    追问: {a.question[:60]}...")
        print(f"下一步: {result.next_action}")
        print("=" * 60)
        
        return result
    
    def _detect_anomalies(self, data: Dict):
        """检测异常"""
        
        for metric, thresholds in ANOMALY_THRESHOLDS.items():
            if metric not in data:
                continue
            
            value = data[metric]
            
            # 高值异常
            if thresholds.get("high") and value > thresholds["high"]:
                anomaly = Anomaly(
                    metric=metric,
                    value=value,
                    threshold=thresholds,
                    severity="high",
                    description=f"{metric} {value}% 显著高于行业均值（约{thresholds['high']}%）",
                    question=""
                )
                self.anomalies.append(anomaly)
                print(f"  ✅ 发现异常: {metric}={value}% > {thresholds['high']}%")
            
            # 低值异常
            elif thresholds.get("low") is not None and value < thresholds["low"]:
                anomaly = Anomaly(
                    metric=metric,
                    value=value,
                    threshold=thresholds,
                    severity="medium",
                    description=f"{metric} {value}% 低于正常水平",
                    question=""
                )
                self.anomalies.append(anomaly)
                print(f"  ✅ 发现异常: {metric}={value}% < {thresholds['low']}%")
    
    def _generate_question(self, anomaly: Anomaly, data: Dict):
        """生成深度追问"""
        
        prompt = f"""作为投资分析师，请针对以下财务异常生成一个深度追问。

## 公司财务数据
{json.dumps(data, ensure_ascii=False, indent=2)}

## 财务异常
- 指标: {anomaly.metric}
- 数值: {anomaly.value}%
- 描述: {anomaly.description}

## 要求
1. 追问要指向具体的经营层面（不是问"为什么"，而是问具体因素）
2. 追问要帮助理解异常的根本原因
3. 简洁明了，不超过50字

请直接输出追问内容，不要加任何前缀。"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            anomaly.question = response.strip()[:100]
        except Exception as e:
            # 默认追问
            anomaly.question = f"{anomaly.metric} {anomaly.value}% 的核心驱动因素是什么？是运营效率还是财务杠杆？"
    
    def _quality_gate_check(self) -> Tuple[bool, List[str]]:
        """质量门禁"""
        
        issues = []
        
        # 检查1：是否发现异常
        if STAGE2_PASS_CRITERIA.get("min_anomalies", 1) and len(self.anomalies) == 0:
            issues.append("未发现财务异常（可能是好事，也可能是检测不够深入）")
        
        # 检查2：追问是否具体
        for a in self.anomalies:
            if not a.question or len(a.question) < 10:
                issues.append(f"{a.metric} 的追问不够具体")
        
        return len(issues) == 0, issues
    
    def save_result(self, result: Stage2Result, output_dir: str) -> str:
        """保存结果"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage2_{timestamp}.json"
        
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result.to_json())
        
        print(f"\n📁 结果已保存: {filepath}")
        return str(filepath)


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="V8.0 阶段2：财务异常分析")
    parser.add_argument("--state", required=True, help="阶段1状态目录")
    
    args = parser.parse_args()
    
    # 读取阶段1结果
    state_dir = Path(args.state)
    stage1_files = list(state_dir.glob("stage1_*.json"))
    
    if not stage1_files:
        print(f"错误: 未找到阶段1结果")
        sys.exit(1)
    
    with open(stage1_files[0], 'r') as f:
        stage1_result = json.load(f)
    
    # 执行阶段2
    analyzer = FinancialAnomalyAnalyzer()
    result = analyzer.execute(stage1_result)
    
    # 保存
    analyzer.save_result(result, args.state)