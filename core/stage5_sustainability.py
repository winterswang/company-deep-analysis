"""
V8.0 阶段5：不可复制性分析

职责：分析护城河的可持续性

检验标准：
1. 明确的可持续性评级
2. 至少2条支撑理由
3. 识别风险因素
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quality_standards import SUSTAINABILITY_RATINGS, STAGE5_PASS_CRITERIA
from core.llm_client import LLMClient


@dataclass
class Stage5Result:
    """阶段5结果"""
    stage: str = "sustainability"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    
    # 输入
    moat_type: str = ""
    confidence: float = 0.0
    
    # 可持续性
    sustainability: str = ""  # 强/中/弱
    reasons: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    
    # 结论
    conclusion: str = ""
    
    # 质量门禁
    quality_gate: Dict = field(default_factory=dict)
    
    # 下一步
    next_action: str = ""
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class SustainabilityAnalyzer:
    """不可复制性分析器"""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def execute(self, stage4_result: Dict) -> Stage5Result:
        """执行阶段5"""
        
        print("=" * 60)
        print("[阶段5] 不可复制性分析")
        print("=" * 60)
        
        result = Stage5Result(
            stage="sustainability",
            timestamp=datetime.now().isoformat(),
            company=stage4_result.get("company", "")
        )
        
        result.moat_type = stage4_result.get("moat_type", "")
        result.confidence = stage4_result.get("confidence", 0)
        
        evidence = stage4_result.get("evidence", [])
        
        # Step 1: 分析可持续性
        print("\n[Step 1] 分析可持续性...")
        sustainability, reasons = self._analyze_sustainability(
            result.company, result.moat_type, evidence
        )
        result.sustainability = sustainability
        result.reasons = reasons
        print(f"  可持续性: {sustainability}")
        print(f"  理由: {len(reasons)} 条")
        
        # Step 2: 识别风险
        print("\n[Step 2] 识别风险因素...")
        risks = self._identify_risks(result.company, result.moat_type)
        result.risks = risks
        print(f"  风险: {len(risks)} 条")
        
        # Step 3: 生成结论
        print("\n[Step 3] 生成结论...")
        conclusion = self._generate_conclusion(result)
        result.conclusion = conclusion
        print(f"  结论: {conclusion[:60]}...")
        
        # Step 4: 质量门禁
        print("\n[Step 4] 质量门禁检验...")
        passed, issues = self._quality_gate_check(result)
        result.quality_gate = {"passed": passed, "issues": issues}
        
        if passed:
            result.status = "success"
            result.next_action = "stage6"
        else:
            result.status = "partial"
            result.next_action = "stage6_with_warnings"
        
        print("\n" + "=" * 60)
        print(f"状态: {result.status}")
        print(f"可持续性: {sustainability}")
        print(f"理由: {len(reasons)} 条")
        print(f"风险: {len(risks)} 条")
        print(f"下一步: {result.next_action}")
        print("=" * 60)
        
        return result
    
    def _analyze_sustainability(
        self, 
        company: str, 
        moat_type: str, 
        evidence: List[str]
    ) -> Tuple[str, List[str]]:
        """分析可持续性"""
        
        prompt = f"""请分析这家公司护城河的可持续性。

## 公司
{company}

## 护城河类型
{moat_type}

## 证据
{chr(10).join([f'- {e}' for e in evidence[:5]])}

## 要求
1. 评估护城河的可复制性（竞争对手能否复制？需要多长时间？）
2. 给出可持续性评级：强/中/弱
3. 列出2-3条支撑理由

请按以下格式输出：
评级: 强/中/弱
理由1: xxx
理由2: xxx
理由3: xxx"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            
            sustainability = "中"
            reasons = []
            
            for line in response.split("\n"):
                if line.startswith("评级:"):
                    sustainability = line.replace("评级:", "").strip()
                elif line.startswith("理由"):
                    reason = line.split(":", 1)[-1].strip() if ":" in line else ""
                    if reason:
                        reasons.append(reason)
            
            # 验证评级
            valid_ratings = ["强", "中", "弱"]
            if sustainability not in valid_ratings:
                sustainability = "中"
            
            return sustainability, reasons
            
        except Exception as e:
            print(f"  分析失败: {e}")
            return "中", ["需要进一步分析"]
    
    def _identify_risks(self, company: str, moat_type: str) -> List[str]:
        """识别风险"""
        
        risks = []
        
        # 基于护城河类型的风险
        if moat_type == "成本优势":
            risks.append("竞争对手可能通过技术创新降低成本")
            risks.append("原材料价格波动可能侵蚀利润")
        elif moat_type == "网络效应":
            risks.append("用户增长可能放缓")
            risks.append("平台可能面临监管风险")
        elif moat_type == "转换成本":
            risks.append("技术变革可能降低转换成本")
        
        # 公司特定风险（基于搜索）
        import os
        import requests
        
        tavily_key = os.environ.get("TAVILY_API_KEY", "")
        env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
        if not tavily_key and env_path.exists():
            with open(env_path) as f:
                for line in f:
                    if line.startswith("TAVILY_API_KEY="):
                        tavily_key = line.strip().split("=", 1)[1]
                        break
        
        if tavily_key:
            try:
                query = f"{company} risks challenges competition 2025"
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_key, "query": query, "max_results": 3},
                    timeout=30
                )
                if response.status_code == 200:
                    for r in response.json().get("results", [])[:2]:
                        content = r.get("content", "")[:80]
                        if content and "risk" in content.lower() or "challenge" in content.lower():
                            risks.append(content)
            except:
                pass
        
        return risks[:4]
    
    def _generate_conclusion(self, result: Stage5Result) -> str:
        """生成结论"""
        
        sustainability = result.sustainability
        moat_type = result.moat_type
        company = result.company
        
        # 生成结论
        conclusions = {
            "强": f"{company}的{moat_type}护城河难以被竞争对手在短期内复制，可持续性较强。",
            "中": f"{company}的{moat_type}护城河具有一定可持续性，但需关注竞争态势变化。",
            "弱": f"{company}的{moat_type}护城河可持续性较弱，需警惕竞争对手追赶。"
        }
        
        return conclusions.get(sustainability, "需要进一步分析")
    
    def _quality_gate_check(self, result: Stage5Result) -> Tuple[bool, List[str]]:
        """质量门禁"""
        
        issues = []
        
        if not result.sustainability:
            issues.append("可持续性评级缺失")
        
        if len(result.reasons) < 2:
            issues.append(f"支撑理由不足: {len(result.reasons)}/2")
        
        if not result.risks:
            issues.append("未识别风险因素")
        
        if not result.conclusion:
            issues.append("结论缺失")
        
        return len(issues) == 0, issues
    
    def save_result(self, result: Stage5Result, output_dir: str) -> str:
        """保存结果"""
        
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage5_{timestamp}.json"
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
    stage4_files = list(state_dir.glob("stage4_*.json"))
    
    with open(stage4_files[0], 'r') as f:
        stage4_result = json.load(f)
    
    analyzer = SustainabilityAnalyzer()
    result = analyzer.execute(stage4_result)
    analyzer.save_result(result, args.state)