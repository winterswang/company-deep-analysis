"""
V8.0 阶段1：数据收集与质量验证

职责：
1. 从多数据源收集财务数据
2. 验证数据质量
3. 输出结构化结果

检验标准：
- 至少获取 5 个核心财务指标
- 平均质量评分 >= 6.0
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.data_collector_v63_fixed import IntegratedDataCollectorV63
from core.financial_data_validator import FinancialDataValidator, DataQualityAssessment


@dataclass
class Stage1Result:
    """阶段1结果"""
    stage: str = "data_collection"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    ticker: str = ""
    market: str = ""
    
    # 财务数据
    financial_data: Dict[str, float] = None
    raw_data_count: int = 0
    
    # 质量报告
    quality_report: Dict = None
    trusted_count: int = 0
    avg_quality_score: float = 0.0
    
    # 错误信息
    errors: List[str] = None
    warnings: List[str] = None
    
    # 下一步
    next_action: str = ""
    
    def __post_init__(self):
        if self.financial_data is None:
            self.financial_data = {}
        if self.quality_report is None:
            self.quality_report = {}
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2)


class Stage1Collector:
    """阶段1：数据收集器"""
    
    # 核心财务指标关键词
    CORE_METRICS = [
        "roe", "roic", "毛利率", "净利率", "营收", "净利润",
        "eps", "资产负债率", "流动比率", "现金流", "pe", "pb",
        "gross_profit_ratio", "operate_income", "parent_holder_netprofit"
    ]
    
    def __init__(self):
        self.collector = IntegratedDataCollectorV63()
        self.validator = FinancialDataValidator()
    
    def execute(
        self, 
        company: str, 
        ticker: str = None, 
        market: str = "us"
    ) -> Stage1Result:
        """
        执行阶段1
        
        Args:
            company: 公司名称
            ticker: 股票代码
            market: 市场（us/cn）
        
        Returns:
            Stage1Result: 阶段1结果
        """
        
        print("=" * 60)
        print("[阶段1] 数据收集与质量验证")
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
        raw_data, sources, timestamps = self._collect_data(company, ticker, market)
        result.raw_data_count = len(raw_data)
        
        if not raw_data:
            result.status = "failed"
            result.errors.append("未收集到任何财务数据")
            result.next_action = "retry_with_different_sources"
            return result
        
        print(f"  收集到 {len(raw_data)} 条原始数据")
        
        # Step 2: 提取核心财务指标
        print("\n[Step 2] 提取核心财务指标...")
        financial_data = self._extract_core_metrics(raw_data)
        result.financial_data = financial_data
        
        print(f"  提取到 {len(financial_data)} 个核心指标:")
        for name, value in financial_data.items():
            print(f"    - {name}: {value}")
        
        if len(financial_data) < 5:
            result.warnings.append(f"核心财务指标不足（{len(financial_data)}/5）")
        
        # Step 3: 质量验证
        print("\n[Step 3] 数据质量验证...")
        
        # 只验证核心财务指标
        core_sources = {k: sources.get(k, "未知") for k in financial_data.keys()}
        core_timestamps = {k: timestamps.get(k, "") for k in financial_data.keys()}
        
        assessments = self.validator.validate_financial_data_batch(
            financial_data, core_sources, core_timestamps
        )
        
        # 计算质量统计
        if assessments:
            trusted = sum(1 for a in assessments.values() if a.quality_label == "可信")
            avg_score = sum(a.quality_score for a in assessments.values()) / len(assessments)
            
            result.trusted_count = trusted
            result.avg_quality_score = round(avg_score, 1)
            
            result.quality_report = {
                "total": len(assessments),
                "trusted": trusted,
                "pending": sum(1 for a in assessments.values() if a.quality_label == "待验证"),
                "unusable": sum(1 for a in assessments.values() if a.quality_label == "不可用"),
                "avg_score": round(avg_score, 1)
            }
            
            print(f"  可信数据: {trusted}/{len(assessments)}")
            print(f"  平均质量评分: {avg_score:.1f}/10")
        
        # Step 4: 检验
        print("\n[Step 4] 检验结果...")
        passed, issues = self._validate_result(result)
        
        if passed:
            result.status = "success"
            result.next_action = "stage2"
            print("  ✅ 检验通过")
        else:
            result.status = "partial"
            result.warnings.extend(issues)
            result.next_action = "stage2_with_warnings"
            print(f"  ⚠️ 检验部分通过: {', '.join(issues)}")
        
        print("\n" + "=" * 60)
        print(f"状态: {result.status}")
        print(f"下一步: {result.next_action}")
        print("=" * 60)
        
        return result
    
    def _collect_data(
        self, 
        company: str, 
        ticker: str, 
        market: str
    ) -> tuple:
        """收集数据"""
        
        data = {}
        sources = {}
        timestamps = {}
        
        try:
            # 1. 先用 AkShare 获取核心财务数据（快速版）
            print("  [AkShare] 获取核心财务指标...")
            akshare_data = self._get_akshare_fast(ticker, market)
            data.update(akshare_data)
            for k in akshare_data.keys():
                sources[k] = "AkShare-东方财富"
                timestamps[k] = datetime.now().isoformat()
            
            # 2. 获取雪球数据
            print("  [雪球] 获取市场数据...")
            raw_data_points = self.collector.collect_all(company, ticker, market)
            
            for item in raw_data_points:
                name = item.name if hasattr(item, 'name') else item.get("name", "")
                value = item.value if hasattr(item, 'value') else item.get("value")
                source = item.source if hasattr(item, 'source') else item.get("source", "未知")
                timestamp = item.timestamp if hasattr(item, 'timestamp') else item.get("timestamp", "")
                
                if name and value is not None and name not in data:
                    parsed = self._parse_value(value)
                    if parsed is not None:
                        data[name] = parsed
                        sources[name] = source
                        timestamps[name] = timestamp
                        
        except Exception as e:
            print(f"  数据收集错误: {e}")
        
        return data, sources, timestamps
    
    def _get_akshare_fast(self, ticker: str, market: str) -> Dict[str, float]:
        """快速获取 AkShare 核心数据"""
        
        result = {}
        
        if market != "us" or not ticker:
            return result
        
        try:
            import akshare as ak
            
            # 直接获取美股财务分析指标（年报）
            df = ak.stock_financial_us_analysis_indicator_em(symbol=ticker, indicator='年报')
            
            if df is not None and not df.empty:
                latest = df.iloc[0]
                
                # 直接提取核心指标
                metrics = {
                    'ROE': latest.get('ROE_AVG'),
                    '毛利率': latest.get('GROSS_PROFIT_RATIO'),
                    '净利润': latest.get('PARENT_HOLDER_NETPROFIT'),
                    'EPS': latest.get('BASIC_EPS'),
                    '资产负债率': latest.get('DEBT_ASSET_RATIO'),
                    '流动比率': latest.get('CURRENT_RATIO'),
                }
                
                for name, value in metrics.items():
                    if value is not None and not (isinstance(value, float) and value != value):
                        result[name] = float(value)
                        print(f"    ✅ {name}: {value}")
                
                print(f"  获取 {len(result)} 个核心指标")
                
        except Exception as e:
            print(f"  AkShare 获取失败: {e}")
        
        return result
    
    def _parse_value(self, value: Any) -> Optional[float]:
        """解析数值"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            value = value.strip()
            value = value.replace("%", "").replace("亿", "").replace("万", "")
            value = value.replace(",", "").replace("元", "").replace("$", "")
            
            try:
                return float(value)
            except ValueError:
                return None
        
        return None
    
    def _extract_core_metrics(self, raw_data: Dict) -> Dict[str, float]:
        """提取核心财务指标"""
        
        financial_data = {}
        
        # 核心指标映射
        metric_mapping = {
            # ROE
            "ROE": ["ROE", "ROE_AVG", "roe", "净资产收益率"],
            # 毛利率
            "毛利率": ["毛利率", "GROSS_PROFIT_RATIO", "gross_profit_ratio", "GrossMargin"],
            # 营收
            "营收": ["营收", "OPERATE_INCOME", "operate_income", "营业收入", "revenue"],
            # 净利润
            "净利润": ["净利润", "PARENT_HOLDER_NETPROFIT", "parent_holder_netprofit", "NetIncome"],
            # EPS
            "EPS": ["EPS", "BASIC_EPS", "basic_eps", "每股收益"],
            # 资产负债率
            "资产负债率": ["资产负债率", "DEBT_ASSET_RATIO", "debt_asset_ratio"],
            # 流动比率
            "流动比率": ["流动比率", "CURRENT_RATIO", "current_ratio"],
        }
        
        for target_name, source_names in metric_mapping.items():
            for source_name in source_names:
                if source_name in raw_data:
                    value = raw_data[source_name]
                    # 格式化数值
                    if isinstance(value, (int, float)):
                        # 大数值转换为亿
                        if abs(value) > 1e8 and target_name in ["营收", "净利润"]:
                            financial_data[target_name] = round(value / 1e8, 2)
                        else:
                            financial_data[target_name] = round(value, 2)
                    break
        
        return financial_data
    
    def _validate_result(self, result: Stage1Result) -> tuple:
        """检验结果"""
        
        issues = []
        
        # 检验1：核心指标数量
        if len(result.financial_data) < 5:
            issues.append(f"核心指标不足（{len(result.financial_data)}/5）")
        
        # 检验2：质量评分
        if result.avg_quality_score < 6.0:
            issues.append(f"质量评分偏低（{result.avg_quality_score}/6.0）")
        
        # 检验3：必需指标
        required = ["ROE", "毛利率", "营收", "净利润"]
        missing = [r for r in required if r not in result.financial_data]
        if missing:
            issues.append(f"缺少必需指标: {', '.join(missing)}")
        
        passed = len(issues) == 0
        return passed, issues
    
    def save_result(self, result: Stage1Result, output_dir: str) -> str:
        """保存结果"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 生成文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = result.company.replace(" ", "_")
        filename = f"stage1_{company_safe}_{timestamp}.json"
        
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result.to_json())
        
        print(f"\n结果已保存: {filepath}")
        return str(filepath)


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="V8.0 阶段1：数据收集")
    parser.add_argument("--company", required=True, help="公司名称")
    parser.add_argument("--ticker", help="股票代码")
    parser.add_argument("--market", default="us", help="市场（us/cn）")
    parser.add_argument("--output", default="./state", help="输出目录")
    
    args = parser.parse_args()
    
    collector = Stage1Collector()
    result = collector.execute(
        company=args.company,
        ticker=args.ticker,
        market=args.market
    )
    
    # 保存结果
    company_safe = args.company.replace(" ", "_")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{args.output}/{company_safe}_{timestamp}"
    collector.save_result(result, output_dir)
    
    # 输出下一步命令
    print(f"\n下一步命令:")
    print(f"python core/stage2_anomaly.py --state {output_dir}")