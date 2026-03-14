"""
V8.0 阶段4：护城河识别

职责：识别护城河类型，验证竞争优势

检验标准：
1. 明确的护城河类型
2. 置信度 >= 0.7
3. 至少2条验证证据
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.quality_standards import MOAT_TYPES, STAGE4_PASS_CRITERIA
from core.llm_client import LLMClient


@dataclass
class Stage4Result:
    """阶段4结果"""
    stage: str = "moat_identification"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    
    # 输入
    core_capability: str = ""
    
    # 护城河
    moat_type: str = ""
    confidence: float = 0.0
    evidence: List[str] = field(default_factory=list)
    
    # 验证问题
    verification_questions: List[str] = field(default_factory=list)
    
    # 质量门禁
    quality_gate: Dict = field(default_factory=dict)
    
    # 下一步
    next_action: str = ""
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class MoatIdentifier:
    """护城河识别器"""
    
    MOAT_QUESTIONS = {
        "网络效应": "用户越多，价值是否越大？",
        "转换成本": "客户换掉我们会损失什么？",
        "成本优势": "低成本来自规模、资源、地理位置还是流程？",
        "无形资产": "品牌/专利能带来定价权吗？",
        "有效规模": "新进入者会破坏均衡吗？"
    }
    
    def __init__(self):
        self.llm = LLMClient()
    
    def execute(self, stage3_result: Dict, stage1_result: Dict) -> Stage4Result:
        """执行阶段4"""
        
        print("=" * 60)
        print("[阶段4] 护城河识别")
        print("=" * 60)
        
        result = Stage4Result(
            stage="moat_identification",
            timestamp=datetime.now().isoformat(),
            company=stage1_result.get("company", "")
        )
        
        financial_data = {item["name"]: item["value"] for item in stage1_result.get("verified_data", [])}
        result.core_capability = stage3_result.get("core_capability", "")
        
        # Step 1: 分析护城河类型
        print("\n[Step 1] 分析护城河类型...")
        moat_type, confidence = self._identify_moat_type(financial_data, result.core_capability)
        result.moat_type = moat_type
        result.confidence = confidence
        print(f"  护城河类型: {moat_type}")
        print(f"  置信度: {confidence:.0%}")
        
        # Step 2: 收集验证证据
        print("\n[Step 2] 收集验证证据...")
        evidence = self._collect_evidence(result.company, moat_type, financial_data)
        result.evidence = evidence
        print(f"  获取 {len(evidence)} 条证据")
        
        # Step 3: 生成验证问题
        print("\n[Step 3] 生成验证问题...")
        result.verification_questions = self._generate_verification_questions(moat_type)
        
        # Step 4: 质量门禁
        print("\n[Step 4] 质量门禁检验...")
        passed, issues = self._quality_gate_check(result)
        result.quality_gate = {"passed": passed, "issues": issues}
        
        if passed:
            result.status = "success"
            result.next_action = "stage5"
        else:
            result.status = "partial"
            result.next_action = "stage5_with_warnings"
        
        print("\n" + "=" * 60)
        print(f"状态: {result.status}")
        print(f"护城河类型: {moat_type} (置信度 {confidence:.0%})")
        print(f"证据: {len(evidence)} 条")
        print(f"下一步: {result.next_action}")
        print("=" * 60)
        
        return result
    
    def _identify_moat_type(self, financial_data: Dict, core_capability: str) -> Tuple[str, float]:
        """识别护城河类型"""
        
        # 基于财务数据特征初步判断
        roe = financial_data.get("ROE", 0)
        margin = financial_data.get("毛利率", 0)
        asset_ratio = financial_data.get("资产负债率", 0)
        
        # 初步判断
        preliminary = None
        
        # 高毛利率 + 低负债 = 可能是品牌/定价权优势
        if margin > 50 and asset_ratio < 50:
            preliminary = ("成本优势", 0.6)
        # 高ROE = 可能有护城河
        elif roe > 30:
            preliminary = ("成本优势", 0.5)
        
        # 用 LLM 确认
        moat_options = "\n".join([f"{i+1}. {t}: {q}" for i, (t, q) in enumerate(self.MOAT_QUESTIONS.items())])
        
        prompt = f"""请判断这家公司的护城河类型。

## 财务数据
{json.dumps(financial_data, ensure_ascii=False)}

## 核心经营能力
{core_capability}

## 护城河类型选项
{moat_options}

## 要求
1. 分析财务数据反映的竞争优势本质
2. 选择最符合的护城河类型
3. 给出置信度（0.0-1.0）

请按以下格式输出：
类型: xxx
置信度: 0.xx
理由: 一句话说明"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            
            moat_type = "未识别"
            confidence = 0.5
            
            for line in response.split("\n"):
                if line.startswith("类型:"):
                    moat_type = line.replace("类型:", "").strip()
                elif line.startswith("置信度:"):
                    conf_str = line.replace("置信度:", "").strip()
                    try:
                        confidence = float(conf_str)
                    except:
                        confidence = 0.5
            
            # 验证类型是否有效
            valid_types = list(self.MOAT_QUESTIONS.keys())
            if moat_type not in valid_types:
                moat_type = preliminary[0] if preliminary else "成本优势"
                confidence = preliminary[1] if preliminary else 0.5
            
            return moat_type, confidence
            
        except Exception as e:
            print(f"  LLM分析失败: {e}")
            return preliminary if preliminary else ("成本优势", 0.5)
    
    def _collect_evidence(self, company: str, moat_type: str, financial_data: Dict) -> List[str]:
        """收集验证证据"""
        
        evidence = []
        
        # 基于护城河类型收集证据
        if moat_type == "成本优势":
            if financial_data.get("毛利率", 0) > 50:
                evidence.append(f"毛利率 {financial_data['毛利率']:.1f}%，显著高于行业均值")
            if financial_data.get("ROE", 0) > 30:
                evidence.append(f"ROE {financial_data['ROE']:.1f}%，资本效率高")
        
        elif moat_type == "网络效应":
            evidence.append("用户增长驱动价值提升")
        
        elif moat_type == "转换成本":
            evidence.append("客户留存率高")
        
        # 搜索额外证据
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
                query = f"{company} {moat_type} competitive advantage 护城河"
                response = requests.post(
                    "https://api.tavily.com/search",
                    json={"api_key": tavily_key, "query": query, "max_results": 3},
                    timeout=30
                )
                if response.status_code == 200:
                    for r in response.json().get("results", [])[:2]:
                        content = r.get("content", "")[:100]
                        if content:
                            evidence.append(content)
            except:
                pass
        
        return evidence[:5]
    
    def _generate_verification_questions(self, moat_type: str) -> List[str]:
        """生成验证问题"""
        
        questions = []
        
        if moat_type in MOAT_TYPES:
            moat_info = MOAT_TYPES[moat_type]
            questions.append(moat_info.get("key_question", ""))
            
            # 添加额外验证问题
            if moat_type == "成本优势":
                questions.append("成本优势来源是否可持续？")
                questions.append("竞争对手能否复制这个成本结构？")
            elif moat_type == "网络效应":
                questions.append("临界规模是多少？是否已达到？")
        
        return questions
    
    def _quality_gate_check(self, result: Stage4Result) -> Tuple[bool, List[str]]:
        """质量门禁"""
        
        issues = []
        
        if not result.moat_type or result.moat_type == "未识别":
            issues.append("护城河类型未识别")
        
        if result.confidence < STAGE4_PASS_CRITERIA.get("min_confidence", 0.7):
            issues.append(f"置信度不足: {result.confidence:.0%} < 70%")
        
        if len(result.evidence) < STAGE4_PASS_CRITERIA.get("min_evidence", 2):
            issues.append(f"证据不足: {len(result.evidence)}/2")
        
        return len(issues) == 0, issues
    
    def save_result(self, result: Stage4Result, output_dir: str) -> str:
        """保存结果"""
        
        output_path = Path(output_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"stage4_{timestamp}.json"
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
    
    stage1_files = list(state_dir.glob("stage1_*.json"))
    stage3_files = list(state_dir.glob("stage3_*.json"))
    
    with open(stage1_files[0], 'r') as f:
        stage1_result = json.load(f)
    with open(stage3_files[0], 'r') as f:
        stage3_result = json.load(f)
    
    identifier = MoatIdentifier()
    result = identifier.execute(stage3_result, stage1_result)
    identifier.save_result(result, args.state)