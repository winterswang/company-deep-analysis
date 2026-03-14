"""
V8.0 阶段1：数据收集与质量验证（严格版）

核心理念：准确性优先于速度

检验标准：
1. 至少4个核心财务指标
2. 每个指标有数值范围验证
3. P0级数据源验证
4. 交叉验证（如可能）
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quality_standards import (
    REQUIRED_METRICS, 
    VALIDATION_RULES,
    STAGE1_PASS_CRITERIA,
    P0_SOURCES, P1_SOURCES, P2_SOURCES
)


@dataclass
class DataPoint:
    """数据点"""
    name: str
    value: float
    source: str
    quality: str  # P0/P1/P2/P3
    timestamp: str
    validation: Dict = field(default_factory=dict)  # 验证结果
    
    def is_valid(self) -> bool:
        return self.validation.get("passed", False)


@dataclass
class Stage1Result:
    """阶段1结果"""
    stage: str = "data_collection"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    ticker: str = ""
    market: str = ""
    
    # 核心财务数据（已验证）
    verified_data: List[Dict] = field(default_factory=list)
    
    # 质量统计
    total_collected: int = 0
    total_verified: int = 0
    avg_quality_score: float = 0.0
    
    # 质量门禁结果
    quality_gate: Dict = field(default_factory=dict)
    
    # 问题清单
    issues: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    # 下一步
    next_action: str = ""
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class StrictDataCollector:
    """严格数据收集器"""
    
    def __init__(self):
        self.collected_data: List[DataPoint] = []
    
    def execute(
        self, 
        company: str, 
        ticker: str = None, 
        market: str = "us"
    ) -> Stage1Result:
        """执行阶段1"""
        
        print("=" * 60)
        print("[阶段1] 数据收集与质量验证（严格模式）")
        print("=" * 60)
        print(f"公司: {company}")
        print(f"代码: {ticker}")
        print(f"市场: {market}")
        print()
        
        result = Stage1Result(
            stage="data_collection",
            timestamp=datetime.now().isoformat(),
            company=company,
            ticker=ticker,
            market=market
        )
        
        # Step 1: 收集数据
        print("[Step 1] 收集财务数据...")
        self._collect_all_sources(company, ticker, market)
        result.total_collected = len(self.collected_data)
        print(f"  收集到 {result.total_collected} 条原始数据\n")
        
        # Step 2: 数值范围验证
        print("[Step 2] 数值范围验证...")
        self._validate_ranges()
        
        # Step 3: 来源质量验证
        print("[Step 3] 来源质量验证...")
        self._validate_sources()
        
        # Step 4: 交叉验证（如可能）
        print("[Step 4] 交叉验证...")
        self._cross_validate()
        
        # Step 5: 提取已验证数据
        print("\n[Step 5] 提取已验证数据...")
        verified = [dp for dp in self.collected_data if dp.is_valid()]
        result.total_verified = len(verified)
        result.verified_data = [
            {
                "name": dp.name,
                "value": dp.value,
                "source": dp.source,
                "quality": dp.quality,
                "validation": dp.validation
            }
            for dp in verified
        ]
        
        # 输出验证结果
        print(f"\n  已验证数据 ({len(verified)}/{len(self.collected_data)}):")
        for dp in verified:
            status = "✅" if dp.validation.get("passed") else "⚠️"
            print(f"    {status} {dp.name}: {dp.value} ({dp.source})")
        
        # Step 6: 质量门禁检验
        print("\n[Step 6] 质量门禁检验...")
        passed, issues = self._quality_gate_check(result)
        result.quality_gate = {
            "passed": passed,
            "criteria": STAGE1_PASS_CRITERIA,
            "issues": issues
        }
        
        if passed:
            result.status = "success"
            result.next_action = "stage2"
            print("  ✅ 质量门禁通过")
        else:
            result.status = "failed"
            result.issues = issues
            result.next_action = "retry_with_more_sources"
            print(f"  ❌ 质量门禁未通过:")
            for issue in issues:
                print(f"    - {issue}")
        
        print("\n" + "=" * 60)
        print(f"状态: {result.status}")
        print(f"已验证: {result.total_verified}/{result.total_collected}")
        print(f"下一步: {result.next_action}")
        print("=" * 60)
        
        return result
    
    def _collect_all_sources(self, company: str, ticker: str, market: str):
        """从所有数据源收集"""
        
        # 1. AkShare（P0级）
        if ticker and market == "us":
            self._collect_from_akshare(ticker)
        
        # 2. 雪球（P1/P2级）
        self._collect_from_xueqiu(company, ticker)
    
    def _collect_from_akshare(self, ticker: str):
        """从 AkShare 收集"""
        
        print("  [AkShare] 获取核心财务数据...")
        
        try:
            import akshare as ak
            
            # 获取美股年报财务指标
            df = ak.stock_financial_us_analysis_indicator_em(symbol=ticker, indicator='年报')
            
            if df is None or df.empty:
                print("    ⚠️ 未获取到数据")
                return
            
            latest = df.iloc[0]
            
            # 提取核心指标
            metrics_mapping = {
                'ROE': ('ROE_AVG', '%'),
                '毛利率': ('GROSS_PROFIT_RATIO', '%'),
                '净利润': ('PARENT_HOLDER_NETPROFIT', '元'),
                'EPS': ('BASIC_EPS', '元'),
                '资产负债率': ('DEBT_ASSET_RATIO', '%'),
                '流动比率': ('CURRENT_RATIO', ''),
                'ROA': ('ROA', '%'),
                '净利率': ('NET_PROFIT_RATIO', '%'),
            }
            
            for name, (field, unit) in metrics_mapping.items():
                value = latest.get(field)
                if value is not None and not self._is_nan(value):
                    # 单位转换
                    if unit == '元' and abs(value) > 1e8:
                        value = value / 1e8  # 转为亿
                        unit = '亿元'
                    
                    dp = DataPoint(
                        name=name,
                        value=round(float(value), 4),
                        source="AkShare-东方财富",
                        quality="P0",
                        timestamp=datetime.now().isoformat(),
                        validation={"source_verified": True}
                    )
                    self.collected_data.append(dp)
                    print(f"    ✅ {name}: {value}{unit}")
            
        except Exception as e:
            print(f"    ❌ AkShare 错误: {e}")
    
    def _collect_from_xueqiu(self, company: str, ticker: str):
        """从雪球收集（简化版，只获取关键数据）"""
        
        print("  [雪球] 获取市场数据...")
        
        try:
            from scripts.xueqiu_crawler import XueqiuCrawler
            
            crawler = XueqiuCrawler()
            
            # 获取股票页面数据
            if ticker:
                data = crawler.crawl_stock_page(ticker)
                
                # 提取财务相关讨论
                for item in data.get("articles", [])[:3]:  # 只取前3篇
                    content = item.get("content", "")
                    if len(content) > 100:
                        # 尝试提取财务数据
                        self._extract_financial_from_text(content, "雪球专栏")
                
                print(f"    获取 {len(data.get('articles', []))} 篇专栏文章")
                
        except Exception as e:
            print(f"    ⚠️ 雪球数据获取跳过: {e}")
    
    def _extract_financial_from_text(self, text: str, source: str):
        """从文本提取财务数据"""
        
        import re
        
        patterns = {
            'ROE': r'ROE[：:\s]*([\d.]+)\s*[%％]?',
            '毛利率': r'毛利率[：:\s]*([\d.]+)\s*[%％]?',
            '净利润': r'净利润[：:\s]*([\d.]+)\s*[亿万元]?',
        }
        
        for name, pattern in patterns.items():
            match = re.search(pattern, text)
            if match:
                value = float(match.group(1))
                # 检查是否已存在P0级数据
                existing = [dp for dp in self.collected_data if dp.name == name]
                if not existing:
                    dp = DataPoint(
                        name=name,
                        value=value,
                        source=source,
                        quality="P2",
                        timestamp=datetime.now().isoformat(),
                        validation={"source_verified": False}
                    )
                    self.collected_data.append(dp)
    
    def _validate_ranges(self):
        """数值范围验证"""
        
        for dp in self.collected_data:
            if dp.name in REQUIRED_METRICS:
                rules = REQUIRED_METRICS[dp.name]
                
                issues = []
                
                # 最小值检查
                if rules.get("min") is not None and dp.value < rules["min"]:
                    issues.append(f"低于最小值 {rules['min']}")
                
                # 最大值检查
                if rules.get("max") is not None and dp.value > rules["max"]:
                    issues.append(f"高于最大值 {rules['max']}")
                
                dp.validation["range_check"] = len(issues) == 0
                dp.validation["range_issues"] = issues
    
    def _validate_sources(self):
        """来源质量验证"""
        
        for dp in self.collected_data:
            source = dp.source
            
            if any(s in source for s in P0_SOURCES):
                dp.quality = "P0"
                dp.validation["source_quality"] = "P0"
            elif any(s in source for s in P1_SOURCES):
                dp.quality = "P1"
                dp.validation["source_quality"] = "P1"
            elif any(s in source for s in P2_SOURCES):
                dp.quality = "P2"
                dp.validation["source_quality"] = "P2"
            else:
                dp.quality = "P3"
                dp.validation["source_quality"] = "P3"
    
    def _cross_validate(self):
        """交叉验证"""
        
        # 查找ROE相关数据进行交叉验证
        roe_data = [dp for dp in self.collected_data if dp.name == "ROE"]
        
        if len(roe_data) > 1:
            # 多来源对比
            values = [dp.value for dp in roe_data]
            avg = sum(values) / len(values)
            tolerance = 0.2  # 20%容差
            
            for dp in roe_data:
                if abs(dp.value - avg) / avg < tolerance:
                    dp.validation["cross_check"] = True
                    dp.validation["cross_check_note"] = f"与多源均值 {avg:.2f}% 一致"
                else:
                    dp.validation["cross_check"] = False
                    dp.validation["cross_check_note"] = f"与多源均值 {avg:.2f}% 偏差较大"
        
        # 最终验证状态
        for dp in self.collected_data:
            # 综合判断
            passed = True
            
            # 范围检查
            if dp.validation.get("range_issues"):
                passed = False
            
            # 来源质量
            if dp.quality not in ["P0", "P1"]:
                passed = False  # 非P0/P1数据需要额外验证
            
            dp.validation["passed"] = passed
    
    def _quality_gate_check(self, result: Stage1Result) -> Tuple[bool, List[str]]:
        """质量门禁检验"""
        
        issues = []
        verified_count = result.total_verified
        
        # 检查1：核心指标数量
        min_metrics = STAGE1_PASS_CRITERIA["min_core_metrics"]
        if verified_count < min_metrics:
            issues.append(f"核心指标不足: {verified_count}/{min_metrics}")
        
        # 检查2：必须有P0级数据
        p0_count = sum(1 for dp in self.collected_data if dp.quality == "P0" and dp.is_valid())
        if p0_count == 0:
            issues.append("缺少P0级（官方/权威）数据源")
        
        # 检查3：必需指标
        verified_names = [dp.name for dp in self.collected_data if dp.is_valid()]
        missing_required = [k for k in REQUIRED_METRICS if k not in verified_names]
        if len(missing_required) > 2:  # 允许缺2个
            issues.append(f"缺少关键指标: {', '.join(missing_required)}")
        
        return len(issues) == 0, issues
    
    def _is_nan(self, value) -> bool:
        """检查是否为 NaN"""
        if isinstance(value, float):
            return value != value
        return False
    
    def save_result(self, result: Stage1Result, output_dir: str) -> str:
        """保存结果"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = result.company.replace(" ", "_")
        filename = f"stage1_{company_safe}_{timestamp}.json"
        
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result.to_json())
        
        print(f"\n📁 结果已保存: {filepath}")
        return str(filepath)


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="V8.0 阶段1：数据收集（严格模式）")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--ticker", help="股票代码")
    parser.add_argument("--market", default="us", help="市场")
    parser.add_argument("--output", default="./state", help="输出目录")
    
    args = parser.parse_args()
    
    collector = StrictDataCollector()
    result = collector.execute(
        company=args.company,
        ticker=args.ticker,
        market=args.market
    )
    
    # 保存
    company_safe = args.company.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{args.output}/{company_safe}_{timestamp}"
    collector.save_result(result, output_dir)