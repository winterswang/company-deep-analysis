"""
V8.0 阶段3：经营分析

职责：分析经营表现，获取行业对比

检验标准：
1. 至少2条经营洞察
2. 每条洞察有证据支撑
3. 识别出核心经营能力
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quality_standards import STAGE3_PASS_CRITERIA
from core.llm_client import LLMClient


@dataclass
class Insight:
    """经营洞察"""
    content: str
    evidence: List[str]
    source: str
    quality: str  # P0/P1/P2


@dataclass
class Stage3Result:
    """阶段3结果"""
    stage: str = "business_analysis"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    
    # 输入
    financial_data: Dict = field(default_factory=dict)
    anomalies: List[Dict] = field(default_factory=list)
    
    # 洞察
    insights: List[Dict] = field(default_factory=list)
    
    # 核心经营能力
    core_capability: str = ""
    
    # 行业对比
    industry_comparison: Dict = field(default_factory=dict)
    
    # 质量门禁
    quality_gate: Dict = field(default_factory=dict)
    
    # 下一步
    next_action: str = ""
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class BusinessAnalyzer:
    """经营分析器"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.insights: List[Insight] = []
    
    def execute(self, stage1_result: Dict, stage2_result: Dict) -> Stage3Result:
        """执行阶段3"""
        
        print("=" * 60)
        print("[阶段3] 经营分析")
        print("=" * 60)
        
        result = Stage3Result(
            stage="business_analysis",
            timestamp=datetime.now().isoformat(),
            company=stage1_result.get("company", "")
        )
        
        financial_data = {item["name"]: item["value"] for item in stage1_result.get("verified_data", [])}
        result.financial_data = financial_data
        result.anomalies = stage2_result.get("anomalies", [])
        
        # Step 1: 搜索行业对比数据
        print("\n[Step 1] 获取行业对比数据...")
        industry_data = self._search_industry_comparison(result.company, financial_data)
        result.industry_comparison = industry_data
        
        # Step 2: 分析经营表现
        print("\n[Step 2] 分析经营表现...")
        self._analyze_business_performance(financial_data, result.anomalies, industry_data)
        
        # Step 3: 识别核心经营能力
        print("\n[Step 3] 识别核心经营能力...")
        core_capability = self._identify_core_capability(financial_data, self.insights)
        result.core_capability = core_capability
        print(f"  核心经营能力: {core_capability}")
        
        # Step 4: 质量门禁
        print("\n[Step 4] 质量门禁检验...")
        passed, issues = self._quality_gate_check()
        result.quality_gate = {"passed": passed, "issues": issues}
        
        # 输出结果
        result.insights = [
            {
                "content": i.content,
                "evidence": i.evidence[:2],
                "source": i.source,
                "quality": i.quality
            }
            for i in self.insights
        ]
        
        if passed:
            result.status = "success"
            result.next_action = "stage4"
        else:
            result.status = "partial"
            result.next_action = "stage4_with_warnings"
        
        print("\n" + "=" * 60)
        print(f"状态: {result.status}")
        print(f"洞察数: {len(self.insights)}")
        for i in self.insights[:3]:
            print(f"  - {i.content[:60]}...")
        print(f"核心能力: {core_capability}")
        print(f"下一步: {result.next_action}")
        print("=" * 60)
        
        return result
    
    def _search_industry_comparison(self, company: str, financial_data: Dict) -> Dict:
        """搜索行业对比数据"""
        
        import os
        import requests
        
        result = {}
        
        # 获取 Tavily API Key
        tavily_key = os.environ.get("TAVILY_API_KEY", "")
        env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
        if not tavily_key and env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("TAVILY_API_KEY="):
                        tavily_key = line.strip().split("=", 1)[1]
                        break
        
        if not tavily_key:
            print("  ⚠️ Tavily API Key 未配置")
            return result
        
        try:
            # 搜索行业对比
            query = f"{company} ROE 毛利率 行业对比 竞争对手 2024 2025"
            
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": tavily_key,
                    "query": query,
                    "max_results": 5
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                print(f"  获取 {len(results)} 条行业数据")
                
                for r in results[:3]:
                    content = r.get("content", "")[:200]
                    result[r.get("url", "")] = content
                    
        except Exception as e:
            print(f"  ⚠️ 搜索失败: {e}")
        
        return result
    
    def _analyze_business_performance(
        self, 
        financial_data: Dict, 
        anomalies: List[Dict],
        industry_data: Dict
    ):
        """分析经营表现"""
        
        # 基于异常生成洞察
        for anomaly in anomalies:
            metric = anomaly.get("metric", "")
            value = anomaly.get("value", 0)
            
            # 构建分析提示
            prompt = f"""作为投资分析师，请分析以下财务异常的经营含义。

## 财务数据
{json.dumps(financial_data, ensure_ascii=False)}

## 异常
- 指标: {metric}
- 数值: {value}%
- 描述: {anomaly.get('description', '')}

## 要求
1. 分析这个异常反映的经营特点（2-3句话）
2. 指出可能的经营优势或风险
3. 简洁明了，不超过100字

请直接输出分析内容。"""

            try:
                response = self.llm.chat([{"role": "user", "content": prompt}])
                insight = Insight(
                    content=response.strip()[:150],
                    evidence=[f"{metric}={value}%"],
                    source="LLM分析+财务数据",
                    quality="P1"
                )
                self.insights.append(insight)
                print(f"  ✅ 洞察: {insight.content[:60]}...")
            except Exception as e:
                print(f"  ⚠️ 分析失败: {e}")
    
    def _identify_core_capability(self, financial_data: Dict, insights: List[Insight]) -> str:
        """识别核心经营能力"""
        
        # 基于财务数据特征推断
        roe = financial_data.get("ROE", 0)
        margin = financial_data.get("毛利率", 0)
        
        capabilities = []
        
        if roe > 30:
            capabilities.append("高资本效率")
        if margin > 50:
            capabilities.append("强定价权或成本控制")
        
        # 构建提示
        prompt = f"""请基于以下信息，用一句话概括公司的核心经营能力。

## 财务数据
{json.dumps(financial_data, ensure_ascii=False)}

## 经营洞察
{chr(10).join([i.content for i in insights])}

## 要求
1. 用一句话（不超过20字）概括核心经营能力
2. 突出最关键的优势

请直接输出核心能力描述。"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            return response.strip()[:30]
        except:
            return " + ".join(capabilities) if capabilities else "待进一步分析"
    
    def _quality_gate_check(self) -> Tuple[bool, List[str]]:
        """质量门禁"""
        
        issues = []
        
        if len(self.insights) < STAGE3_PASS_CRITERIA.get("min_insights", 2):
            issues.append(f"洞察数量不足: {len(self.insights)}/2")
        
        return len(issues) == 0, issues
    
    def save_result(self, result: Stage3Result, output_dir: str) -> str:
        """保存结果"""
        
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage3_{timestamp}.json"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(result.to_json())
        
        print(f"\n📁 结果已保存: {filepath}")
        return str(filepath)


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    args = parser.parse_args()
    
    state_dir = Path(args.state)
    
    # 读取阶段1、2结果
    stage1_files = list(state_dir.glob("stage1_*.json"))
    stage2_files = list(state_dir.glob("stage2_*.json"))
    
    with open(stage1_files[0], 'r') as f:
        stage1_result = json.load(f)
    with open(stage2_files[0], 'r') as f:
        stage2_result = json.load(f)
    
    analyzer = BusinessAnalyzer()
    result = analyzer.execute(stage1_result, stage2_result)
    analyzer.save_result(result, args.state)