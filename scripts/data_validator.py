#!/usr/bin/env python3
"""
数据质量验证工具
- 数据质量评分
- 自动升级检索
- 雪球数据交叉验证
"""

import json
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# 数据源配置
DATA_SOURCES = {
    "financial_data": {
        "P0": ["公司年报", "公司IR"],
        "P1": ["TuShare", "AkShare"],
        "P2": ["雪球专业文章"],
    },
    "industry_data": {
        "P1": ["SNE Research", "IDC", "Gartner"],
        "P2": ["券商研报", "雪球专业文章"],
    },
    "market_share": {
        "P1": ["专业数据商"],
        "P2": ["券商研报", "雪球专业文章"],
        "P3": ["雪球大V"],
    }
}

# 质量评分权重
QUALITY_WEIGHTS = {
    "accuracy": 0.30,
    "timeliness": 0.20,
    "completeness": 0.20,
    "traceability": 0.15,
    "bias": 0.15
}

# 升级检索配置
UPGRADE_CONFIG = {
    "max_attempts": {
        "financial_data": 3,
        "industry_data": 5,
        "market_share": 5,
    },
    "timeout_seconds": {
        "financial_data": 60,
        "industry_data": 120,
        "market_share": 120,
    }
}


class DataQualityValidator:
    """数据质量验证器"""
    
    def __init__(self):
        self.upgrade_attempts = {}
    
    def calculate_quality_score(self, data: Dict) -> float:
        """
        计算数据质量评分
        
        Args:
            data: {
                "source": "AkShare",
                "level": "P1",
                "timestamp": "2026-03-10",
                "completeness": 1.0,
                "bias": 0.0
            }
        
        Returns:
            质量评分 (0-100)
        """
        # 准确性评分（基于数据源级别）
        level = data.get("level", "P4")
        accuracy_scores = {"P0": 100, "P1": 95, "P2": 80, "P3": 70, "P4": 50}
        accuracy = accuracy_scores.get(level, 50)
        
        # 及时性评分
        timestamp_str = data.get("timestamp")
        if timestamp_str:
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d")
                days_ago = (datetime.now() - timestamp).days
                if days_ago < 30:
                    timeliness = 100
                elif days_ago < 90:
                    timeliness = 80
                else:
                    timeliness = 50
            except:
                timeliness = 60
        else:
            timeliness = 60
        
        # 完整性评分
        completeness = data.get("completeness", 0.8) * 100
        
        # 可追溯性评分
        traceability_scores = {"P0": 100, "P1": 90, "P2": 80, "P3": 70, "P4": 50}
        traceability = traceability_scores.get(level, 50)
        
        # 偏见性评分
        bias = data.get("bias", 0.0)
        bias_score = (1 - bias) * 100
        
        # 加权计算
        total_score = (
            accuracy * QUALITY_WEIGHTS["accuracy"] +
            timeliness * QUALITY_WEIGHTS["timeliness"] +
            completeness * QUALITY_WEIGHTS["completeness"] +
            traceability * QUALITY_WEIGHTS["traceability"] +
            bias_score * QUALITY_WEIGHTS["bias"]
        )
        
        return round(total_score, 2)
    
    def get_quality_grade(self, score: float) -> str:
        """获取质量等级"""
        if score >= 90:
            return "A"
        elif score >= 70:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"
    
    def needs_upgrade(self, data: Dict, data_type: str) -> bool:
        """
        判断是否需要升级检索
        
        Args:
            data: 数据字典
            data_type: 数据类型 (financial_data, industry_data, market_share)
        
        Returns:
            是否需要升级
        """
        score = self.calculate_quality_score(data)
        grade = self.get_quality_grade(score)
        
        # B级以下需要升级
        if grade in ["C", "D"]:
            return True
        
        # 检查数据来源级别
        level = data.get("level", "P4")
        
        # 财务数据必须 P0/P1
        if data_type == "financial_data" and level not in ["P0", "P1"]:
            return True
        
        return False
    
    def upgrade_search(self, code: str, data_type: str, current_data: Dict) -> Dict:
        """
        执行升级检索
        
        Args:
            code: 股票代码
            data_type: 数据类型
            current_data: 当前数据
        
        Returns:
            升级后的数据
        """
        config = UPGRADE_CONFIG.get(data_type, {})
        max_attempts = config.get("max_attempts", 3)
        timeout = config.get("timeout_seconds", 60)
        
        # 记录尝试次数
        key = f"{code}_{data_type}"
        attempts = self.upgrade_attempts.get(key, 0)
        
        if attempts >= max_attempts:
            return {
                "success": False,
                "data": current_data,
                "message": f"已达到最大检索次数 ({max_attempts})"
            }
        
        start_time = time.time()
        upgraded_data = current_data.copy()
        sources_used = []
        
        # 按优先级检索
        source_priority = DATA_SOURCES.get(data_type, {})
        
        for level in ["P0", "P1", "P2"]:
            if level not in source_priority:
                continue
            
            for source in source_priority[level]:
                if time.time() - start_time > timeout:
                    break
                
                # 尝试获取数据
                new_data = self._fetch_from_source(code, source, data_type)
                
                if new_data:
                    sources_used.append(source)
                    
                    # 合并/更新数据
                    upgraded_data = self._merge_data(upgraded_data, new_data, source, level)
                    
                    # 检查质量是否达标
                    new_score = self.calculate_quality_score(upgraded_data)
                    if self.get_quality_grade(new_score) in ["A", "B"]:
                        break
        
        # 更新尝试次数
        self.upgrade_attempts[key] = attempts + 1
        
        # 计算最终质量
        final_score = self.calculate_quality_score(upgraded_data)
        
        return {
            "success": self.get_quality_grade(final_score) in ["A", "B"],
            "data": upgraded_data,
            "quality_score": final_score,
            "quality_grade": self.get_quality_grade(final_score),
            "sources_used": sources_used,
            "attempts": self.upgrade_attempts[key]
        }
    
    def _fetch_from_source(self, code: str, source: str, data_type: str) -> Optional[Dict]:
        """从指定数据源获取数据"""
        try:
            if source == "AkShare":
                return self._fetch_from_akshare(code, data_type)
            elif source == "雪球专业文章":
                return self._fetch_from_xueqiu(code, data_type)
            elif source == "TuShare":
                return self._fetch_from_tushare(code, data_type)
            else:
                return None
        except Exception as e:
            print(f"从 {source} 获取数据失败: {e}")
            return None
    
    def _fetch_from_akshare(self, code: str, data_type: str) -> Optional[Dict]:
        """从 AkShare 获取数据"""
        try:
            from akshare_service.skills.financial_summary import get_financial_summary
            
            if data_type == "financial_data":
                data = get_financial_summary(code, years=1, use_cache=True)
                if data and data.get("annual_data"):
                    latest = data["annual_data"][0]
                    return {
                        "revenue": latest.get("revenue", {}),
                        "net_profit": latest.get("net_profit", {}),
                        "roe": latest.get("roe", {}),
                        "gross_margin": latest.get("gross_margin", {}),
                        "source": "AkShare",
                        "level": "P1",
                        "timestamp": datetime.now().strftime("%Y-%m-%d"),
                        "completeness": 1.0,
                        "bias": 0.0
                    }
        except Exception as e:
            print(f"AkShare 获取失败: {e}")
        return None
    
    def _fetch_from_xueqiu(self, code: str, data_type: str) -> Optional[Dict]:
        """从雪球获取数据"""
        # 这里可以调用雪球爬虫
        # 实际实现时调用 smart_crawler_v2.py
        return None
    
    def _fetch_from_tushare(self, code: str, data_type: str) -> Optional[Dict]:
        """从 TuShare 获取数据"""
        # TuShare 实现
        return None
    
    def _merge_data(self, old_data: Dict, new_data: Dict, source: str, level: str) -> Dict:
        """合并数据"""
        merged = old_data.copy()
        
        # 更新缺失字段
        for key, value in new_data.items():
            if key not in merged or not merged.get(key):
                merged[key] = value
        
        # 更新元信息
        if "sources" not in merged:
            merged["sources"] = []
        merged["sources"].append(source)
        merged["level"] = level  # 使用更高级别
        
        return merged
    
    def cross_validate_with_xueqiu(self, code: str, financial_data: Dict) -> Dict:
        """
        用雪球数据交叉验证财务数据
        
        Args:
            code: 股票代码
            financial_data: 财务数据
        
        Returns:
            验证结果
        """
        # 从雪球获取分析文章
        xueqiu_articles = self._fetch_xueqiu_articles(code)
        
        if not xueqiu_articles:
            return {
                "verified": False,
                "consistency_score": None,
                "message": "未找到雪球分析文章"
            }
        
        # 提取财务数据
        extracted_data = self._extract_financial_from_articles(xueqiu_articles)
        
        # 对比数据
        consistency = self._compare_data(financial_data, extracted_data)
        
        return {
            "verified": consistency > 0.9,
            "consistency_score": consistency,
            "xueqiu_sources": len(xueqiu_articles),
            "extracted_data": extracted_data
        }
    
    def _fetch_xueqiu_articles(self, code: str) -> List[Dict]:
        """获取雪球文章"""
        # 实际实现时调用雪球爬虫
        return []
    
    def _extract_financial_from_articles(self, articles: List[Dict]) -> Dict:
        """从文章中提取财务数据"""
        # 提取逻辑
        return {}
    
    def _compare_data(self, data1: Dict, data2: Dict) -> float:
        """对比两组数据的一致性"""
        # 对比逻辑
        return 0.0
    
    def generate_quality_report(self, code: str, data: Dict) -> str:
        """生成数据质量报告"""
        report = []
        report.append(f"# 数据质量报告 - {code}")
        report.append("")
        report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 数据质量评分
        score = self.calculate_quality_score(data)
        grade = self.get_quality_grade(score)
        
        report.append("## 质量评分")
        report.append("")
        report.append(f"- **评分**: {score}")
        report.append(f"- **等级**: {grade}")
        report.append(f"- **来源**: {data.get('source', 'Unknown')}")
        report.append(f"- **级别**: {data.get('level', 'Unknown')}")
        report.append("")
        
        # 数据来源
        sources = data.get("sources", [data.get("source", "Unknown")])
        report.append("## 数据来源")
        report.append("")
        for source in sources:
            report.append(f"- {source}")
        report.append("")
        
        # 建议
        report.append("## 建议")
        report.append("")
        if grade in ["A", "B"]:
            report.append("✅ 数据质量达标，可直接使用")
        elif grade == "C":
            report.append("⚠️ 数据质量一般，建议交叉验证")
            report.append("- 建议使用雪球数据验证")
        else:
            report.append("❌ 数据质量不达标，建议重新获取")
            report.append("- 触发升级检索")
        
        return "\n".join(report)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据质量验证工具")
    parser.add_argument("--code", required=True, help="股票代码")
    parser.add_argument("--type", default="financial_data", help="数据类型")
    parser.add_argument("--upgrade", action="store_true", help="触发升级检索")
    parser.add_argument("--validate-xueqiu", action="store_true", help="雪球交叉验证")
    
    args = parser.parse_args()
    
    validator = DataQualityValidator()
    
    # 示例数据
    sample_data = {
        "source": "AkShare",
        "level": "P1",
        "timestamp": datetime.now().strftime("%Y-%m-%d"),
        "completeness": 0.95,
        "bias": 0.0
    }
    
    # 计算质量评分
    score = validator.calculate_quality_score(sample_data)
    grade = validator.get_quality_grade(score)
    
    print(f"数据质量评分: {score}")
    print(f"数据质量等级: {grade}")
    print()
    
    # 检查是否需要升级
    if validator.needs_upgrade(sample_data, args.type):
        print("⚠️ 数据需要升级检索")
        
        if args.upgrade:
            print("执行升级检索...")
            result = validator.upgrade_search(args.code, args.type, sample_data)
            print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("✅ 数据质量达标")
    
    # 雪球验证
    if args.validate_xueqiu:
        print()
        print("执行雪球交叉验证...")
        result = validator.cross_validate_with_xueqiu(args.code, sample_data)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 生成报告
    print()
    print(validator.generate_quality_report(args.code, sample_data))


if __name__ == "__main__":
    main()