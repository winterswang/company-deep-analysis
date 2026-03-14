"""
V8.0 阶段6：报告生成

职责：整合所有阶段结果，生成最终报告

检验标准：
1. 核心结论完整
2. 财务数据表格清晰
3. 护城河类型明确
"""

import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from dataclasses import dataclass, asdict, field

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class Stage6Result:
    """阶段6结果"""
    stage: str = "report_generation"
    status: str = "pending"
    timestamp: str = ""
    company: str = ""
    
    # 最终报告
    report: str = ""
    report_path: str = ""
    
    # Gist 链接
    gist_url: str = ""
    
    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)


class ReportGenerator:
    """报告生成器"""
    
    def execute(self, state_dir: str) -> Stage6Result:
        """执行阶段6"""
        
        print("=" * 60)
        print("[阶段6] 报告生成")
        print("=" * 60)
        
        result = Stage6Result(
            stage="report_generation",
            timestamp=datetime.now().isoformat()
        )
        
        # 读取所有阶段结果
        state_path = Path(state_dir)
        
        stage1 = self._load_json(state_path / "stage1_*.json")
        stage2 = self._load_json(state_path / "stage2_*.json")
        stage3 = self._load_json(state_path / "stage3_*.json")
        stage4 = self._load_json(state_path / "stage4_*.json")
        stage5 = self._load_json(state_path / "stage5_*.json")
        
        result.company = stage1.get("company", "")
        
        # 生成报告
        print("\n[生成报告]")
        report = self._generate_report(stage1, stage2, stage3, stage4, stage5)
        result.report = report
        
        # 保存报告
        print("\n[保存报告]")
        report_path = self._save_report(report, state_path, result.company)
        result.report_path = report_path
        
        # 上传到 Gist
        print("\n[上传到 Gist]")
        gist_url = self._upload_to_gist(report, result.company)
        result.gist_url = gist_url
        
        result.status = "success"
        
        print("\n" + "=" * 60)
        print("✅ 分析完成！")
        print(f"报告: {report_path}")
        if gist_url:
            print(f"Gist: {gist_url}")
        print("=" * 60)
        
        return result
    
    def _load_json(self, pattern: Path) -> Dict:
        """加载 JSON"""
        import glob
        files = list(glob.glob(str(pattern)))
        if files:
            with open(files[0], 'r') as f:
                return json.load(f)
        return {}
    
    def _generate_report(
        self, 
        stage1: Dict, 
        stage2: Dict, 
        stage3: Dict, 
        stage4: Dict, 
        stage5: Dict
    ) -> str:
        """生成报告"""
        
        company = stage1.get("company", "")
        financial_data = stage1.get("verified_data", [])
        anomalies = stage2.get("anomalies", [])
        core_capability = stage3.get("core_capability", "")
        insights = stage3.get("insights", [])
        moat_type = stage4.get("moat_type", "")
        moat_evidence = stage4.get("evidence", [])
        sustainability = stage5.get("sustainability", "")
        reasons = stage5.get("reasons", [])
        risks = stage5.get("risks", [])
        conclusion = stage5.get("conclusion", "")
        
        # 生成核心结论
        core_conclusion = self._generate_core_conclusion(
            company, core_capability, moat_type
        )
        
        # 构建报告
        report = f"""# {company} 投资分析报告

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**分析框架**: V8.0 多阶段深度分析

---

## 一句话结论

{company}的本质是"{core_capability}"，护城河来自"{moat_type}"。

---

## 一、核心财务数据

| 指标 | 数值 | 行业对比 |
|------|------|----------|
"""
        
        # 添加财务数据
        for item in financial_data[:7]:
            name = item.get("name", "")
            value = item.get("value", 0)
            
            # 格式化
            if abs(value) > 100:
                value_str = f"{value:.1f}"
            else:
                value_str = f"{value:.2f}%"
            
            report += f"| {name} | {value_str} | - |\n"
        
        # 财务异常
        report += f"""
---

## 二、财务异常分析

"""
        
        if anomalies:
            for a in anomalies:
                report += f"""### {a.get('metric', '')}

**数值**: {a.get('value', '')}%
**描述**: {a.get('description', '')}
**追问**: {a.get('question', '')}

"""
        else:
            report += "未检测到明显财务异常。\n\n"
        
        # 经营分析
        report += f"""---

## 三、经营分析

**核心经营能力**: {core_capability}

### 关键洞察

"""
        
        for i, insight in enumerate(insights[:3], 1):
            content = insight.get("content", "")
            report += f"{i}. {content}\n\n"
        
        # 护城河
        report += f"""---

## 四、护城河分析

**护城河类型**: {moat_type}

### 验证证据

"""
        
        for e in moat_evidence[:3]:
            report += f"- {e}\n"
        
        # 可持续性
        report += f"""
---

## 五、可持续性分析

**可持续性评级**: {sustainability}

### 支撑理由

"""
        
        for r in reasons[:3]:
            report += f"- {r}\n"
        
        report += f"""
### 风险因素

"""
        
        for r in risks[:2]:
            report += f"- {r}\n"
        
        # 结论
        report += f"""
---

## 六、投资结论

{conclusion}

---

**分析完成**

*本报告由 Company Deep Analysis V8.0 生成*
"""
        
        return report
    
    def _generate_core_conclusion(
        self, 
        company: str, 
        core_capability: str, 
        moat_type: str
    ) -> str:
        """生成核心结论"""
        
        return f"{company}的核心优势是{core_capability}，护城河类型为{moat_type}"
    
    def _save_report(self, report: str, state_path: Path, company: str) -> str:
        """保存报告"""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = company.replace(" ", "_")
        filename = f"{company_safe}_v8_report_{timestamp}.md"
        
        filepath = state_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        print(f"  保存到: {filepath}")
        return str(filepath)
    
    def _upload_to_gist(self, report: str, company: str) -> str:
        """上传到 Gist"""
        
        import subprocess
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = company.replace(" ", "_")
        filename = f"{company_safe}_v8_report_{timestamp}.md"
        
        try:
            result = subprocess.run(
                ["gh", "gist", "create", "--filename", filename, "--public"],
                input=report.encode(),
                capture_output=True,
                timeout=30
            )
            
            if result.returncode == 0:
                gist_url = result.stdout.decode().strip()
                print(f"  Gist URL: {gist_url}")
                return gist_url
            else:
                print(f"  Gist 上传失败: {result.stderr.decode()}")
                return ""
                
        except Exception as e:
            print(f"  Gist 上传失败: {e}")
            return ""


# CLI
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("--state", required=True)
    args = parser.parse_args()
    
    generator = ReportGenerator()
    result = generator.execute(args.state)