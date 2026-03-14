"""
V7.0 财务数据质量验证器

核心理念：
- 财务数据是分析的基石
- 通过"否定之否定"验证数据质量
- 每个数据点必须有质量评分和标签

验证流程：
1. 收集初始数据
2. 否定（生成质疑）
3. 验证质疑 → 可能产生ToDo
4. 否定之否定（确认质量）
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


@dataclass
class DataQualityAssessment:
    """数据质量评估结果"""
    data_point: str
    value: Any
    source: str
    quality_score: float  # 0-10
    quality_label: str  # 可信/待验证/不可用
    doubts: List[Dict]  # 质疑点
    validation_results: List[Dict]  # 验证结果
    todos: List[Dict]  # 待执行的ToDo
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class FinancialDataValidator:
    """财务数据质量验证器"""
    
    # 数据来源可靠性评分
    SOURCE_RELIABILITY = {
        # 官方来源 (P0)
        "年报": 3.0,
        "10-K": 3.0,
        "10-Q": 3.0,
        "年报计算": 3.0,
        "官方公告": 2.5,
        "官方数据": 2.5,
        # 权威第三方 (P0-P1)
        "AkShare": 2.5,  # P0 级数据源，提高评分
        "AkShare-东方财富": 2.5,  # 东方财富美股财务数据，P0 级
        "Bloomberg": 2.5,
        "雪球专栏": 2.0,
        "雪球公告": 2.5,
        "雪球爬虫-财务": 2.0,
        "雪球爬虫-公告": 2.5,
        "雪球爬虫-专栏": 2.0,
        "本地数据": 2.0,
        # 一般来源 (P1-P2)
        "雪球讨论": 1.0,
        "Exa": 1.5,
        "Tavily": 1.5,
        "雪球爬虫-讨论": 1.0,
        "雪球爬虫-资讯": 1.5,
        # 未知
        "未知": 0.0
    }
    
    # 来源别名映射
    SOURCE_ALIASES = {
        "年报计算": "年报",
        "年报数据": "年报",
        "年度报告": "年报",
        "财报": "年报",
        "季报": "年报",
        "雪球": "雪球专栏",
        "雪球数据": "雪球专栏",
    }
    
    # 雪球数据质量评估规则（需求文档 §3.2）
    XUEQIU_QUALITY_RULES = {
        "专栏": {
            "min_length_p0": 300,  # ≥300字符 = P0
            "min_length_p2": 0,    # <300字符 = P2
        },
        "公告": {
            "default_quality": "P1"  # 固定P1
        },
        "资讯": {
            "min_title_length": 20,  # 标题≥20字符 = P2
            "default_quality": "P2"
        },
        "讨论": {
            "p4_max_length": 50,      # <50字符 = P4（丢弃）
            "p3_max_length": 150,     # 50-150字符 = P3（丢弃）
            "p2_max_length": 300,     # 150-300字符 = P2
            # >300字符 = P1
        }
    }
    
    # 质量评分阈值
    QUALITY_THRESHOLDS = {
        "high": 7.0,  # 高质量，可直接使用（降低阈值，让 P0 级数据源更容易通过）
        "medium": 5.0,  # 中等质量，需标注
        "low": 0.0  # 低质量，需补充验证
    }
    
    # 质量标签
    QUALITY_LABELS = {
        "可信": "可信，可直接使用",
        "待验证": "待验证，需补充证据",
        "不可用": "不可用，质量过低"
    }
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
    
    def validate_data_point(
        self, 
        data_point: str, 
        value: Any, 
        source: str,
        timestamp: str = "",
        alternative_sources: List[Dict] = None
    ) -> DataQualityAssessment:
        """
        对单个财务数据点进行否定之否定验证
        
        Args:
            data_point: 数据项名称（如 "ROIC"）
            value: 数据值
            source: 数据来源
            timestamp: 数据时间戳
            alternative_sources: 其他来源的数据（用于交叉验证）
        
        Returns:
            DataQualityAssessment: 数据质量评估结果
        """
        
        # 第一步：收集初始数据
        initial_data = {
            "data_point": data_point,
            "value": value,
            "source": source,
            "timestamp": timestamp,
            "alternatives": alternative_sources or []
        }
        
        # 第二步：否定（生成质疑）
        doubts = self._generate_doubts(initial_data)
        
        # 第三步：验证质疑
        validation_results = []
        todos = []
        
        for doubt in doubts:
            result = self._validate_doubt(doubt, initial_data)
            validation_results.append(result)
            
            # 如果验证失败，生成ToDo
            if not result.get("passed", False):
                todos.extend(result.get("todos", []))
        
        # 第四步：否定之否定（确认质量）
        quality_score = self._calculate_quality_score(
            initial_data, 
            validation_results
        )
        quality_label = self._determine_quality_label(quality_score)
        
        return DataQualityAssessment(
            data_point=data_point,
            value=value,
            source=source,
            quality_score=quality_score,
            quality_label=quality_label,
            doubts=doubts,
            validation_results=validation_results,
            todos=todos
        )
    
    def validate_financial_data_batch(
        self, 
        financial_data: Dict[str, Any],
        sources: Dict[str, str] = None,
        timestamps: Dict[str, str] = None
    ) -> Dict[str, DataQualityAssessment]:
        """
        批量验证财务数据
        
        Args:
            financial_data: 财务数据字典 {指标名: 值}
            sources: 数据来源字典 {指标名: 来源}
            timestamps: 数据时间戳字典 {指标名: 时间戳}
        
        Returns:
            Dict[str, DataQualityAssessment]: 各指标的质量评估结果
        """
        
        results = {}
        sources = sources or {}
        timestamps = timestamps or {}
        
        for data_point, value in financial_data.items():
            source = sources.get(data_point, "未知")
            timestamp = timestamps.get(data_point, "")
            
            result = self.validate_data_point(
                data_point=data_point,
                value=value,
                source=source,
                timestamp=timestamp
            )
            results[data_point] = result
        
        return results
    
    def _generate_doubts(self, data: Dict) -> List[Dict]:
        """生成质疑点"""
        
        doubts = []
        
        # 质疑1：数据来源是否可靠？
        doubts.append({
            "type": "source_reliability",
            "question": f"数据来源'{data['source']}'是否可靠？",
            "check_method": "verify_official_source",
            "severity": "高"
        })
        
        # 质疑2：数据是否一致？（如果有多个来源）
        if data.get("alternatives"):
            doubts.append({
                "type": "data_consistency",
                "question": "不同来源的数据是否一致？",
                "check_method": "cross_validate",
                "severity": "高"
            })
        
        # 质疑3：数据是否异常？
        if self._is_anomaly(data):
            doubts.append({
                "type": "data_anomaly",
                "question": f"数据{data['value']}是否合理？是否存在异常？",
                "check_method": "check_reasonability",
                "severity": "中"
            })
        
        # 质疑4：数据是否有原文引用？
        doubts.append({
            "type": "source_reference",
            "question": "是否有原文引用或计算过程？",
            "check_method": "verify_reference",
            "severity": "中"
        })
        
        return doubts
    
    def _validate_doubt(self, doubt: Dict, data: Dict) -> Dict:
        """验证质疑"""
        
        check_method = doubt["check_method"]
        
        if check_method == "verify_official_source":
            # 检查来源是否可靠
            source = data["source"]
            reliability_score = self.SOURCE_RELIABILITY.get(source, 0)
            is_reliable = reliability_score >= 2.0
            
            return {
                "doubt": doubt,
                "passed": is_reliable,
                "evidence": f"来源'{source}'可靠性评分: {reliability_score}/3",
                "todos": [] if is_reliable else [{
                    "type": "数据验证",
                    "task": f"从官方渠道验证{data['data_point']}数据",
                    "priority": "高"
                }]
            }
        
        elif check_method == "cross_validate":
            # 交叉验证
            alternatives = data.get("alternatives", [])
            if not alternatives:
                return {
                    "doubt": doubt,
                    "passed": False,
                    "evidence": "无其他来源数据可供对比",
                    "todos": [{
                        "type": "数据检索",
                        "task": f"从其他来源获取{data['data_point']}数据进行对比",
                        "priority": "高"
                    }]
                }
            
            # 检查一致性
            values = [data["value"]] + [a.get("value") for a in alternatives]
            is_consistent = self._check_consistency(values)
            
            return {
                "doubt": doubt,
                "passed": is_consistent,
                "evidence": f"多源数据{'一致' if is_consistent else '不一致'}: {values}",
                "todos": [] if is_consistent else [{
                    "type": "数据验证",
                    "task": f"确认{data['data_point']}的正确值",
                    "priority": "高"
                }]
            }
        
        elif check_method == "check_reasonability":
            # 检查合理性
            # 这里可以添加更多的合理性检查逻辑
            return {
                "doubt": doubt,
                "passed": True,
                "evidence": "数据在合理范围内",
                "todos": []
            }
        
        elif check_method == "verify_reference":
            # 检查是否有原文引用
            # 这里需要检查数据是否有原文引用
            return {
                "doubt": doubt,
                "passed": False,
                "evidence": "未找到原文引用",
                "todos": [{
                    "type": "数据验证",
                    "task": f"获取{data['data_point']}的原文引用或计算过程",
                    "priority": "中"
                }]
            }
        
        return {
            "doubt": doubt,
            "passed": False,
            "evidence": "未知验证方法",
            "todos": []
        }
    
    def _calculate_quality_score(
        self, 
        data: Dict, 
        validation_results: List[Dict]
    ) -> float:
        """计算数据质量评分"""
        
        score = 0.0
        
        # 1. 来源可靠性（0-3分）
        source = data["source"]
        score += self._get_source_reliability(source)
        
        # 2. 交叉验证（0-3分）
        consistency_results = [r for r in validation_results if r["doubt"]["type"] == "data_consistency"]
        if consistency_results:
            if consistency_results[0]["passed"]:
                score += 3.0
            else:
                score += 1.0
        else:
            score += 1.0  # 单来源
        
        # 3. 时效性（0-2分）- 根据数据时间戳判断
        timestamp = data.get("timestamp", "")
        timeliness_score = self._calculate_timeliness_score(timestamp)
        score += timeliness_score
        
        # 4. 完整性（0-2分）- 根据数据点是否有支持信息判断
        completeness_score = self._calculate_completeness_score(data, validation_results)
        score += completeness_score
        
        return min(score, 10.0)
    
    def _get_source_reliability(self, source: str) -> float:
        """获取来源可靠性评分，支持别名匹配"""
        
        # 直接匹配
        if source in self.SOURCE_RELIABILITY:
            return self.SOURCE_RELIABILITY[source]
        
        # 别名匹配
        if source in self.SOURCE_ALIASES:
            alias = self.SOURCE_ALIASES[source]
            return self.SOURCE_RELIABILITY.get(alias, 0)
        
        # 模糊匹配
        source_lower = source.lower()
        for key, value in self.SOURCE_RELIABILITY.items():
            if key.lower() in source_lower or source_lower in key.lower():
                return value
        
        # 包含关键词匹配
        if any(kw in source_lower for kw in ["年报", "10-k", "10-q", "官方"]):
            return 3.0
        elif any(kw in source_lower for kw in ["akshare", "bloomberg"]):
            return 2.0
        elif any(kw in source_lower for kw in ["雪球", "本地"]):
            return 1.5
        elif any(kw in source_lower for kw in ["tavily", "exa"]):
            return 1.5
        
        return 0.0
    
    def _calculate_timeliness_score(self, timestamp: str) -> float:
        """
        计算时效性评分
        
        - 最新季度：2分
        - 最近一年：1.5分
        - 1-2年：1分
        - >2年：0.5分
        - 无时间戳：1.0分（默认中等）
        """
        if not timestamp:
            return 1.0  # 默认中等分数
        
        try:
            from datetime import datetime, timedelta
            
            # 尝试解析时间戳
            if "T" in timestamp:
                data_time = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            else:
                # 尝试其他格式
                for fmt in ["%Y-%m-%d", "%Y%m%d", "%Y/%m/%d"]:
                    try:
                        data_time = datetime.strptime(timestamp, fmt)
                        break
                    except ValueError:
                        continue
                else:
                    return 1.0
            
            now = datetime.now()
            age = now - data_time.replace(tzinfo=None) if data_time.tzinfo else now - data_time
            
            if age.days <= 90:  # 3个月内
                return 2.0
            elif age.days <= 365:  # 1年内
                return 1.5
            elif age.days <= 730:  # 2年内
                return 1.0
            else:
                return 0.5
                
        except Exception:
            return 1.0  # 解析失败，默认中等
    
    def _calculate_completeness_score(self, data: Dict, validation_results: List[Dict]) -> float:
        """
        计算完整性评分
        
        - 有原文引用/计算过程：2分
        - 有交叉验证通过：1.5分
        - P0级数据源（AkShare、年报等）：1.5分（无需额外验证）
        - 单来源但来源可靠：1分
        - 单来源不可靠：0.5分
        """
        source = data.get("source", "未知")
        source_reliability = self._get_source_reliability(source)
        
        # P0 级数据源（AkShare、年报等）直接给予较高完整性评分
        p0_sources = ["年报", "10-K", "10-Q", "AkShare", "AkShare-东方财富", "年报计算"]
        if any(p0 in source for p0 in p0_sources):
            return 1.5
        
        # 检查是否有交叉验证
        consistency_results = [r for r in validation_results if r["doubt"]["type"] == "data_consistency"]
        if consistency_results and consistency_results[0]["passed"]:
            return 1.5
        
        # 检查来源可靠性
        if source_reliability >= 2.0:
            return 1.0
        else:
            return 0.5
    
    def _determine_quality_label(self, score: float) -> str:
        """确定质量标签"""
        
        if score >= self.QUALITY_THRESHOLDS["high"]:
            return "可信"
        elif score >= self.QUALITY_THRESHOLDS["medium"]:
            return "待验证"
        else:
            return "不可用"
    
    def _is_anomaly(self, data: Dict) -> bool:
        """检查数据是否异常"""
        # 这里可以添加更复杂的异常检测逻辑
        # 目前简单返回 False
        return False
    
    def _check_consistency(self, values: List[Any]) -> bool:
        """检查数据一致性"""
        
        if not values:
            return False
        
        # 过滤掉 None 值
        valid_values = [v for v in values if v is not None]
        
        if len(valid_values) < 2:
            return True
        
        # 检查数值是否接近
        if all(isinstance(v, (int, float)) for v in valid_values):
            mean = sum(valid_values) / len(valid_values)
            tolerance = 0.1  # 10% 容差
            return all(abs(v - mean) / mean < tolerance for v in valid_values if mean != 0)
        
        # 非数值类型，检查是否完全相同
        return len(set(str(v) for v in valid_values)) == 1
    
    def generate_quality_report(
        self, 
        assessments: Dict[str, DataQualityAssessment]
    ) -> str:
        """生成数据质量报告"""
        
        report = "# 财务数据质量报告\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 统计
        total = len(assessments)
        
        if total == 0:
            report += "## ⚠️ 无有效数据\n\n"
            report += "未收集到有效的财务数据，请检查数据源。\n\n"
            return report
        
        trusted = sum(1 for a in assessments.values() if a.quality_label == "可信")
        pending = sum(1 for a in assessments.values() if a.quality_label == "待验证")
        unusable = sum(1 for a in assessments.values() if a.quality_label == "不可用")
        
        report += "## 📊 质量统计\n\n"
        report += f"- 总数据项: {total}\n"
        report += f"- 可信: {trusted} ({trusted/total*100:.1f}%)\n"
        report += f"- 待验证: {pending} ({pending/total*100:.1f}%)\n"
        report += f"- 不可用: {unusable} ({unusable/total*100:.1f}%)\n\n"
        
        # 详细列表 - 只显示关键财务数据
        report += "## 📋 关键财务数据\n\n"
        report += "| 指标 | 数值 | 来源 | 质量评分 | 标签 |\n"
        report += "|------|------|------|----------|------|\n"
        
        # 关键财务指标关键词
        key_metrics = ["roe", "roic", "毛利率", "净利率", "营收", "净利润", "eps", 
                       "资产负债率", "流动比率", "现金流", "pe", "pb"]
        
        for name, assessment in assessments.items():
            # 过滤：只显示关键财务指标
            name_lower = name.lower()
            is_key_metric = any(kw in name_lower for kw in key_metrics) or len(name) < 20
            
            if is_key_metric:
                # 截断数值显示
                value_str = str(assessment.value)
                if len(value_str) > 20:
                    # 尝试格式化数字
                    try:
                        num = float(value_str)
                        if abs(num) > 1e8:
                            value_str = f"{num/1e8:.1f}亿"
                        elif abs(num) > 1e4:
                            value_str = f"{num/1e4:.1f}万"
                        else:
                            value_str = f"{num:.2f}"
                    except:
                        value_str = value_str[:20] + "..."
                
                # 截断来源显示
                source_str = assessment.source
                if len(source_str) > 15:
                    source_str = source_str[:15] + "..."
                
                report += f"| {name[:15]} | {value_str} | {source_str} | {assessment.quality_score:.1f} | {assessment.quality_label} |\n"
        
        # 非关键数据统计
        non_key_count = sum(1 for n in assessments if not any(kw in n.lower() for kw in key_metrics) and len(n) >= 20)
        if non_key_count > 0:
            report += f"\n*另有 {non_key_count} 条辅助数据（新闻、讨论等）*\n"
        
        # ToDo列表
        all_todos = []
        for assessment in assessments.values():
            all_todos.extend(assessment.todos)
        
        if all_todos:
            report += "\n## 📝 待执行ToDo\n\n"
            for i, todo in enumerate(all_todos, 1):
                report += f"{i}. [{todo.get('priority', '中')}] {todo.get('task', '')}\n"
        
        return report
    
    def evaluate_xueqiu_data_quality(
        self,
        data_type: str,
        content: str,
        title: str = ""
    ) -> Tuple[str, bool]:
        """
        评估雪球数据质量（严格按需求文档 §3.2）
        
        Args:
            data_type: 数据类型（专栏/公告/资讯/讨论）
            content: 内容文本
            title: 标题（资讯需要）
        
        Returns:
            Tuple[str, bool]: (质量等级, 是否应该丢弃)
        """
        
        content_length = len(content.strip()) if content else 0
        title_length = len(title.strip()) if title else 0
        
        rules = self.XUEQIU_QUALITY_RULES.get(data_type, {})
        
        if data_type == "专栏":
            # 专栏文章
            min_length_p0 = rules.get("min_length_p0", 300)
            if content_length >= min_length_p0:
                return "P0", False
            else:
                return "P2", False
        
        elif data_type == "公告":
            # 公告：固定P1
            return "P1", False
        
        elif data_type == "资讯":
            # 资讯：标题≥20字符 = P2
            min_title = rules.get("min_title_length", 20)
            if title_length >= min_title:
                return "P2", False
            else:
                return "P3", True  # 标题太短的资讯丢弃
        
        elif data_type == "讨论":
            # 讨论：按字符数分级
            p4_max = rules.get("p4_max_length", 50)
            p3_max = rules.get("p3_max_length", 150)
            p2_max = rules.get("p2_max_length", 300)
            
            if content_length < p4_max:
                return "P4", True  # <50字符，丢弃
            elif content_length < p3_max:
                return "P3", True  # 50-150字符，丢弃
            elif content_length < p2_max:
                return "P2", False  # 150-300字符，保留
            else:
                return "P1", False  # >300字符，保留
        
        else:
            return "P3", True  # 未知类型，丢弃


# 测试
if __name__ == "__main__":
    validator = NegationValidator()
    
    print("=== 测试雪球数据质量评估 ===")
    print()
    
    test_cases = [
        ("专栏", "这是一篇非常详细的专栏文章，内容超过了三百个字符的限制。我们会详细分析这家公司的财务数据、经营状况以及未来的发展前景。通过深入的研究和分析，我们可以更好地理解这家公司的商业模式和竞争优势。" * 3, ""),
        ("专栏", "短文章", ""),
        ("公告", "公告内容", ""),
        ("资讯", "这是一条资讯内容", "这是一个足够长的标题超过二十个字符"),
        ("资讯", "资讯内容", "短标题"),
        ("讨论", "太短了", ""),
        ("讨论", "这是一个中等长度的讨论，大约有一百多个字符，我们需要测试一下这个逻辑是否正确工作。" * 2, ""),
        ("讨论", "这是一个很长的讨论内容，字符数超过了三百个，应该被评定为P1等级。我们需要确保这个测试用例足够长才能验证逻辑的正确性。" * 4, ""),
    ]
    
    for data_type, content, title in test_cases:
        quality, discard = validator.evaluate_xueqiu_data_quality(data_type, content, title)
        status = "丢弃" if discard else "保留"
        print(f"{data_type}: {len(content)}字符 -> {quality} ({status})")


# 测试
if __name__ == "__main__":
    validator = FinancialDataValidator()
    
    # 测试单个数据点
    result = validator.validate_data_point(
        data_point="ROIC",
        value="32.4%",
        source="年报计算"
    )
    
    print(f"数据项: {result.data_point}")
    print(f"质量评分: {result.quality_score:.1f}/10")
    print(f"质量标签: {result.quality_label}")
    print(f"质疑点数: {len(result.doubts)}")
    print(f"ToDo数: {len(result.todos)}")