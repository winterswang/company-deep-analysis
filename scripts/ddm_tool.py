"""
DDM 估值工具
判断是否应使用 DDM 估值，并计算 DDM 目标价
"""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime


def should_use_ddm(dividend_info: Dict[str, Any]) -> Tuple[bool, str]:
    """
    判断是否应该使用 DDM 估值模型
    
    条件：
    1. 分红率 > 50%
    2. 分红连续 3 年以上
    3. 公司处于成熟期
    
    Args:
        dividend_info: 分红信息字典
    
    Returns:
        (是否使用DDM, 原因说明)
    """
    # 获取分红率
    dividend_ratio = dividend_info.get("latest_dividend_ratio")
    avg_dividend_ratio = dividend_info.get("avg_3y_dividend_ratio")
    dividend_years = dividend_info.get("consecutive_dividend_years", 0)
    
    # 条件1：分红率 > 50%
    if dividend_ratio is None:
        return False, "无法获取分红率数据，请从年报获取"
    
    if dividend_ratio < 50:
        return False, f"分红率 {dividend_ratio:.1f}% < 50%，不适用 DDM"
    
    # 条件2：分红连续性
    if dividend_years < 3:
        return False, f"分红连续 {dividend_years} 年 < 3 年，分红稳定性不足"
    
    # 条件3：平均分红率
    if avg_dividend_ratio and avg_dividend_ratio < 40:
        return False, f"3年平均分红率 {avg_dividend_ratio:.1f}% < 40%，分红稳定性存疑"
    
    # 满足条件
    reason = f"分红率 {dividend_ratio:.1f}% > 50%，连续分红 {dividend_years} 年，应使用 DDM"
    return True, reason


def calculate_ddm_value(
    current_dividend: float,
    dividend_growth_rate: float = 0.04,
    required_return: float = 0.10
) -> Dict[str, Any]:
    """
    计算 DDM 目标价
    
    公式：内在价值 = D₁ / (r - g)
    
    Args:
        current_dividend: 当年股息（元/股）
        dividend_growth_rate: 永续增长率（默认4%）
        required_return: 要求回报率（默认10%）
    
    Returns:
        DDM 估值结果
    """
    # D₁ = D₀ × (1 + g)
    next_dividend = current_dividend * (1 + dividend_growth_rate)
    
    # 内在价值 = D₁ / (r - g)
    if required_return <= dividend_growth_rate:
        return {
            "error": "要求回报率必须大于永续增长率",
            "target_price": None
        }
    
    intrinsic_value = next_dividend / (required_return - dividend_growth_rate)
    
    return {
        "current_dividend": current_dividend,
        "dividend_growth_rate": dividend_growth_rate,
        "required_return": required_return,
        "next_dividend": round(next_dividend, 4),
        "target_price": round(intrinsic_value, 2),
        "formula": f"DDM = {next_dividend:.4f} / ({required_return*100:.0f}% - {dividend_growth_rate*100:.0f}%) = {intrinsic_value:.2f}元",
        "calculated_at": datetime.now().isoformat()
    }


def get_dividend_info_from_financials(financial_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    从财务数据中提取分红信息
    
    注意：AkShare 标准化接口暂不包含分红数据
    需要从年报或专门的分红接口获取
    
    Args:
        financial_data: 财务数据
    
    Returns:
        分红信息字典
    """
    # TODO: 从年报或专门接口获取分红数据
    # 当前返回占位数据
    return {
        "latest_dividend_ratio": None,  # 最新分红率
        "avg_3y_dividend_ratio": None,  # 3年平均分红率
        "consecutive_dividend_years": None,  # 连续分红年数
        "latest_dividend_per_share": None,  # 最新每股股息
        "source": "需要从年报获取",
        "note": "AkShare 标准化接口暂不包含分红数据，请从年报或 TuShare 获取"
    }


def generate_ddm_section(
    code: str,
    dividend_info: Dict[str, Any],
    financial_data: Dict[str, Any]
) -> str:
    """
    生成 DDM 估值部分的 Markdown 内容
    
    Args:
        code: 股票代码
        dividend_info: 分红信息
        financial_data: 财务数据
    
    Returns:
        Markdown 格式的 DDM 估值内容
    """
    use_ddm, reason = should_use_ddm(dividend_info)
    
    md = f"""
### 4.3 DDM 估值法判断

**判断结果**：{'✅ 必须使用 DDM' if use_ddm else '❌ 不使用 DDM'}

**原因**：{reason}

| 参数 | 数值 | 来源 |
|------|------|------|
| 当年股息(元/股) | {dividend_info.get('latest_dividend_per_share', '待获取')} | 年报 |
| 分红率 | {dividend_info.get('latest_dividend_ratio', '待获取')}% | 年报 |
| 近5年平均分红率 | {dividend_info.get('avg_3y_dividend_ratio', '待获取')}% | 计算得出 |
| 历史分红连续性 | {dividend_info.get('consecutive_dividend_years', '待获取')}年 | 年报 |
| **是否使用DDM** | {'是' if use_ddm else '否'} | 判断结果 |
"""
    
    if use_ddm and dividend_info.get('latest_dividend_per_share'):
        # 计算 DDM 目标价
        ddm_result = calculate_ddm_value(dividend_info['latest_dividend_per_share'])
        
        md += f"""
**DDM 计算结果**：

| 参数 | 数值 |
|------|------|
| 当年股息 | {ddm_result['current_dividend']} 元/股 |
| 永续增长率(g) | {ddm_result['dividend_growth_rate']*100}% |
| 要求回报率(r) | {ddm_result['required_return']*100}% |
| 下年预期股息(D₁) | {ddm_result['next_dividend']} 元/股 |
| **DDM目标价** | **{ddm_result['target_price']} 元** |

计算公式：{ddm_result['formula']}
"""
    
    return md


# 测试
if __name__ == '__main__':
    # 测试贵州茅台
    dividend_info = {
        "latest_dividend_ratio": 75.67,
        "avg_3y_dividend_ratio": 52.0,
        "consecutive_dividend_years": 10,
        "latest_dividend_per_share": 30.876
    }
    
    use_ddm, reason = should_use_ddm(dividend_info)
    print(f"是否使用 DDM: {use_ddm}")
    print(f"原因: {reason}")
    
    if use_ddm:
        result = calculate_ddm_value(30.876)
        print(f"DDM 目标价: {result['target_price']} 元")
        print(f"计算公式: {result['formula']}")