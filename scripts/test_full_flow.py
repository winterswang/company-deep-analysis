#!/usr/bin/env python3
"""
Company Deep Analysis V1.1 全流程测试
验证所有工具和接口是否正常工作
"""

# 1. 首先设置路径
import sys
from pathlib import Path

# 添加 AkShare 标准化接口路径
AKSHARE_PATH = "/root/.openclaw/workspace/akshare_docs"
if AKSHARE_PATH not in sys.path:
    sys.path.insert(0, AKSHARE_PATH)

print("=" * 60)
print("Company Deep Analysis V1.1 全流程测试")
print("=" * 60)

# 2. 测试结果收集
test_results = []

def run_test(name: str, test_func):
    """运行测试并记录结果"""
    print(f"\n{'='*20} {name} {'='*20}")
    try:
        result = test_func()
        test_results.append({"name": name, "status": "PASS", "result": result})
        print(f"✅ {name} - 通过")
        return result
    except Exception as e:
        test_results.append({"name": name, "status": "FAIL", "error": str(e)})
        print(f"❌ {name} - 失败: {e}")
        return None

# 3. 测试1：AkShare 标准化接口
def test_akshare_api():
    print("测试 AkShare 标准化接口...")
    from akshare_service.skills.financial_summary import get_financial_summary
    from akshare_service.skills.cashflow import get_cashflow_data
    
    # 测试财务指标
    result = get_financial_summary("300760", years=2, use_cache=False)
    assert result.get("annual_data"), f"财务数据为空: {result.get('errors')}"
    print(f"  - 财务指标: {len(result['annual_data'])}年, 来源: {result.get('source')}")
    
    # 测试现金流
    result2 = get_cashflow_data("300760", years=2, use_cache=False)
    assert result2.get("annual_data"), f"现金流数据为空: {result2.get('errors')}"
    print(f"  - 现金流: {len(result2['annual_data'])}年, 来源: {result2.get('source')}")
    
    return {"financials": result, "cashflow": result2}

# 4. 测试2：DDM 估值工具
def test_ddm_tool():
    print("测试 DDM 估值工具...")
    sys.path.insert(0, "/root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/scripts")
    from ddm_tool import should_use_ddm, calculate_ddm_value
    
    # 测试判断逻辑（茅台）
    dividend_info = {
        "latest_dividend_ratio": 75.67,
        "avg_3y_dividend_ratio": 52.0,
        "consecutive_dividend_years": 10,
        "latest_dividend_per_share": 30.876
    }
    
    use_ddm, reason = should_use_ddm(dividend_info)
    assert use_ddm, f"茅台应使用DDM: {reason}"
    print(f"  - DDM判断: {reason}")
    
    # 测试计算
    result = calculate_ddm_value(30.876)
    assert result.get("target_price"), "DDM目标价计算失败"
    print(f"  - DDM目标价: {result['target_price']}元")
    
    return {"use_ddm": use_ddm, "target_price": result['target_price']}

# 5. 测试3：国际对比估值
def test_international_comparison():
    print("测试国际对比估值...")
    from international_comparison import calculate_valuation_comparison, generate_comparison_table
    
    # 测试数据（迈瑞医疗）
    company_data = {
        "name": "迈瑞医疗",
        "pe_ttm": 24,
        "pb": 5.5,
        "roe": 28
    }
    
    peers_data = [
        {"name": "美敦力", "code": "MDT", "market": "US", "pe_ttm": 25, "pb": 3.2, "roe": 12},
        {"name": "雅培", "code": "ABT", "market": "US", "pe_ttm": 28, "pb": 4.5, "roe": 15},
    ]
    
    result = calculate_valuation_comparison(company_data, peers_data)
    assert result.get("verdict"), "对比结果为空"
    print(f"  - 估值判断: {result['verdict']['status']}")
    print(f"  - 原因: {result['verdict']['reason']}")
    
    return result

# 6. 测试4：业务结构数据
def test_business_segments():
    print("测试业务结构数据...")
    from business_segments import get_business_segments, generate_segment_table
    
    # 测试迈瑞医疗
    data = get_business_segments("300760", year=2024)
    assert data.get("segments"), "业务结构数据为空"
    print(f"  - 业务线数量: {len(data['segments'])}")
    
    # 生成表格
    table = generate_segment_table(data)
    assert "体外诊断" in table, "业务结构表格生成失败"
    
    return {"segments": len(data['segments']), "source": data.get('source')}

# 7. 测试5：数据来源标注格式
def test_data_source_format():
    print("测试数据来源标注格式...")
    
    # 验证 SKILL.md 中是否有数据来源标注规范
    skill_path = Path("/root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/SKILL.md")
    content = skill_path.read_text(encoding='utf-8')
    
    assert "数据来源标注" in content, "SKILL.md 缺少数据来源标注章节"
    assert "| 数据项 | 数值 | 单位 | 来源" in content, "缺少数据来源表格格式"
    print("  - 数据来源标注规范: 存在")
    
    # 验证 DDM 章节
    assert "DDM 估值法" in content, "缺少 DDM 估值章节"
    assert "分红率 > 50%" in content, "缺少 DDM 判断条件"
    print("  - DDM 强制使用规范: 存在")
    
    # 验证国际对比章节
    assert "国际对比估值" in content, "缺少国际对比估值章节"
    print("  - 国际对比估值规范: 存在")
    
    return {"data_source": True, "ddm": True, "international": True}

# 8. 运行所有测试
if __name__ == "__main__":
    # 添加脚本路径
    sys.path.insert(0, "/root/.openclaw/workspace/deer-flow-analysis/skills/custom/company-deep-analysis/scripts")
    
    # 运行测试
    run_test("1. AkShare 标准化接口", test_akshare_api)
    run_test("2. DDM 估值工具", test_ddm_tool)
    run_test("3. 国际对比估值", test_international_comparison)
    run_test("4. 业务结构数据", test_business_segments)
    run_test("5. 数据来源标注格式", test_data_source_format)
    
    # 汇总结果
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    passed = sum(1 for r in test_results if r["status"] == "PASS")
    failed = sum(1 for r in test_results if r["status"] == "FAIL")
    
    for r in test_results:
        status = "✅" if r["status"] == "PASS" else "❌"
        print(f"{status} {r['name']}: {r['status']}")
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    # 输出 JSON 结果
    import json
    print("\n--- JSON OUTPUT ---")
    print(json.dumps({
        "total": len(test_results),
        "passed": passed,
        "failed": failed,
        "tests": test_results
    }, ensure_ascii=False, indent=2, default=str))