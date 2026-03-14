#!/usr/bin/env python3
"""
V8.0 多阶段分析 - 主入口

用法:
    # 完整执行所有阶段
    python run_v80.py --company "PDD Holdings" --ticker PDD --market us

    # 只执行到某个阶段
    python run_v80.py --company "PDD Holdings" --ticker PDD --market us --stop-at 3

    # 从某个阶段继续
    python run_v80.py --state ./state/PDD_20260314 --from-stage 3
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from core.stage1_collector_v8 import StrictDataCollector
from core.stage2_anomaly import FinancialAnomalyAnalyzer
from core.stage3_business import BusinessAnalyzer
from core.stage4_moat import MoatIdentifier
from core.stage5_sustainability import SustainabilityAnalyzer
from core.stage6_report import ReportGenerator


def run_stage1(company: str, ticker: str, market: str, output_dir: str) -> dict:
    """执行阶段1"""
    print("\n" + "="*60)
    print("▶ 阶段1: 数据收集与质量验证")
    print("="*60)
    
    collector = StrictDataCollector()
    result = collector.execute(company, ticker, market)
    collector.save_result(result, output_dir)
    return result.to_json()


def run_stage2(state_dir: str) -> dict:
    """执行阶段2"""
    print("\n" + "="*60)
    print("▶ 阶段2: 财务异常分析")
    print("="*60)
    
    import glob
    import json
    
    stage1_file = glob.glob(f"{state_dir}/stage1_*.json")[0]
    with open(stage1_file) as f:
        stage1_result = json.load(f)
    
    analyzer = FinancialAnomalyAnalyzer()
    result = analyzer.execute(stage1_result)
    analyzer.save_result(result, state_dir)
    return result.to_json()


def run_stage3(state_dir: str) -> dict:
    """执行阶段3"""
    print("\n" + "="*60)
    print("▶ 阶段3: 经营分析")
    print("="*60)
    
    import glob
    import json
    
    stage1_file = glob.glob(f"{state_dir}/stage1_*.json")[0]
    stage2_file = glob.glob(f"{state_dir}/stage2_*.json")[0]
    
    with open(stage1_file) as f:
        stage1_result = json.load(f)
    with open(stage2_file) as f:
        stage2_result = json.load(f)
    
    analyzer = BusinessAnalyzer()
    result = analyzer.execute(stage1_result, stage2_result)
    analyzer.save_result(result, state_dir)
    return result.to_json()


def run_stage4(state_dir: str) -> dict:
    """执行阶段4"""
    print("\n" + "="*60)
    print("▶ 阶段4: 护城河识别")
    print("="*60)
    
    import glob
    import json
    
    stage1_file = glob.glob(f"{state_dir}/stage1_*.json")[0]
    stage3_file = glob.glob(f"{state_dir}/stage3_*.json")[0]
    
    with open(stage1_file) as f:
        stage1_result = json.load(f)
    with open(stage3_file) as f:
        stage3_result = json.load(f)
    
    identifier = MoatIdentifier()
    result = identifier.execute(stage3_result, stage1_result)
    identifier.save_result(result, state_dir)
    return result.to_json()


def run_stage5(state_dir: str) -> dict:
    """执行阶段5"""
    print("\n" + "="*60)
    print("▶ 阶段5: 不可复制性分析")
    print("="*60)
    
    import glob
    import json
    
    stage4_file = glob.glob(f"{state_dir}/stage4_*.json")[0]
    with open(stage4_file) as f:
        stage4_result = json.load(f)
    
    analyzer = SustainabilityAnalyzer()
    result = analyzer.execute(stage4_result)
    analyzer.save_result(result, state_dir)
    return result.to_json()


def run_stage6(state_dir: str) -> dict:
    """执行阶段6"""
    print("\n" + "="*60)
    print("▶ 阶段6: 报告生成")
    print("="*60)
    
    generator = ReportGenerator()
    result = generator.execute(state_dir)
    return result.to_json()


def main():
    parser = argparse.ArgumentParser(description="V8.0 多阶段深度分析")
    
    # 完整执行参数
    parser.add_argument("--company", help="公司名称")
    parser.add_argument("--ticker", help="股票代码")
    parser.add_argument("--market", default="us", help="市场")
    parser.add_argument("--output", default="./state", help="输出目录")
    
    # 阶段控制
    parser.add_argument("--stop-at", type=int, help="停止在指定阶段")
    parser.add_argument("--from-stage", type=int, help="从指定阶段继续")
    parser.add_argument("--state", help="状态目录（用于继续执行）")
    
    args = parser.parse_args()
    
    # 确定执行模式
    if args.state and args.from_stage:
        # 继续模式
        state_dir = args.state
        start_stage = args.from_stage
        print(f"📂 从阶段 {start_stage} 继续")
        print(f"📁 状态目录: {state_dir}")
    elif args.company:
        # 完整执行模式
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        company_safe = args.company.replace(" ", "_")
        state_dir = f"{args.output}/{company_safe}_{timestamp}"
        start_stage = 1
        print(f"🏢 公司: {args.company}")
        print(f"📊 代码: {args.ticker}")
        print(f"📁 状态目录: {state_dir}")
    else:
        parser.print_help()
        return
    
    stop_at = args.stop_at or 6
    
    # 执行阶段
    results = {}
    
    try:
        if start_stage <= 1 and stop_at >= 1:
            results[1] = run_stage1(args.company, args.ticker, args.market, state_dir)
        
        if start_stage <= 2 and stop_at >= 2:
            results[2] = run_stage2(state_dir)
        
        if start_stage <= 3 and stop_at >= 3:
            results[3] = run_stage3(state_dir)
        
        if start_stage <= 4 and stop_at >= 4:
            results[4] = run_stage4(state_dir)
        
        if start_stage <= 5 and stop_at >= 5:
            results[5] = run_stage5(state_dir)
        
        if start_stage <= 6 and stop_at >= 6:
            results[6] = run_stage6(state_dir)
        
        print("\n" + "="*60)
        print("✅ 分析完成！")
        print("="*60)
        print(f"📁 状态目录: {state_dir}")
        
        if results.get(6):
            import json
            r6 = json.loads(results[6])
            if r6.get("gist_url"):
                print(f"🔗 Gist: {r6['gist_url']}")
        
    except Exception as e:
        print(f"\n❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()
        
        print(f"\n💡 可以使用以下命令继续:")
        print(f"python run_v80.py --state {state_dir} --from-stage {max(results.keys()) + 1 if results else 1}")


if __name__ == "__main__":
    main()