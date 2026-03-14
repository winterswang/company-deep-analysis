"""
V7.0 ROIC 自己计算验证模块

严格按照需求文档 §3.4 实现：
- 从年报/AkShare获取 NOPAT、Invested Capital
- 自己计算 ROIC
- 对比不同来源的数据
"""

import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

sys.path.insert(0, str(Path(__file__).parent.parent))


@dataclass
class ROICComponents:
    """ROIC 组成部分"""
    net_income: float  # 净利润
    tax_rate: float  # 税率
    interest_expense: float  # 利息支出
    total_equity: float  # 股东权益
    total_debt: float  # 总债务
    cash_and_equivalents: float  # 现金及等价物
    nopat: float  # 税后净营业利润
    invested_capital: float  # 投入资本
    roic: float  # 计算出的 ROIC


class ROICCalculator:
    """
    ROIC 自己计算验证器
    
    严格按需求文档 §3.4 示例实现
    """
    
    def __init__(self):
        self.calculations = {}
    
    def calculate_roic_from_financials(
        self,
        net_income: float,
        tax_rate: float = 0.25,
        interest_expense: float = 0,
        total_equity: float = 0,
        total_debt: float = 0,
        cash_and_equivalents: float = 0,
        minority_interest: float = 0
    ) -> ROICComponents:
        """
        从财务数据计算 ROIC
        
        公式：
        NOPAT = Net Income + Interest Expense × (1 - Tax Rate)
        Invested Capital = Total Equity + Total Debt - Cash
        ROIC = NOPAT / Invested Capital
        """
        
        # 计算 NOPAT (Net Operating Profit After Tax)
        nopat = net_income + interest_expense * (1 - tax_rate)
        
        # 计算 Invested Capital
        invested_capital = total_equity + total_debt - cash_and_equivalents + minority_interest
        
        # 计算 ROIC
        if invested_capital > 0:
            roic = (nopat / invested_capital) * 100
        else:
            roic = 0.0
        
        components = ROICComponents(
            net_income=net_income,
            tax_rate=tax_rate,
            interest_expense=interest_expense,
            total_equity=total_equity,
            total_debt=total_debt,
            cash_and_equivalents=cash_and_equivalents,
            nopat=nopat,
            invested_capital=invested_capital,
            roic=roic
        )
        
        return components
    
    def calculate_roic_from_akshare(
        self,
        ticker: str,
        market: str = "us"
    ) -> Optional[ROICComponents]:
        """
        从 AkShare 获取财务数据并计算 ROIC
        
        按需求文档要求："从年报中提取 NOPAT 和 Invested Capital 明细"
        """
        
        try:
            import akshare as ak
            import pandas as pd
            
            if market == "us":
                # 获取利润表
                print(f"  从 AkShare 获取 {ticker} 利润表...")
                df_income = ak.stock_financial_us_report_em(
                    stock=ticker, 
                    symbol='综合损益表', 
                    indicator='年报'
                )
                
                # 获取资产负债表
                print(f"  从 AkShare 获取 {ticker} 资产负债表...")
                df_balance = ak.stock_financial_us_report_em(
                    stock=ticker,
                    symbol='资产负债表',
                    indicator='年报'
                )
                
                if df_income is None or df_balance is None:
                    return None
                
                # 透视转换
                income_pivot = df_income.pivot(
                    index='REPORT_DATE', 
                    columns='ITEM_NAME', 
                    values='AMOUNT'
                ).reset_index()
                income_pivot['REPORT_DATE'] = pd.to_datetime(income_pivot['REPORT_DATE'])
                
                balance_pivot = df_balance.pivot(
                    index='REPORT_DATE',
                    columns='ITEM_NAME',
                    values='AMOUNT'
                ).reset_index()
                balance_pivot['REPORT_DATE'] = pd.to_datetime(balance_pivot['REPORT_DATE'])
                
                # 取最新一期数据
                latest_income = income_pivot.iloc[-1]
                latest_balance = balance_pivot.iloc[-1]
                
                # 提取关键数据
                net_income = latest_income.get('Net income', latest_income.get('净利润', 0))
                if net_income is None or pd.isna(net_income):
                    net_income = 0
                
                interest_expense = latest_income.get('Interest expense', latest_income.get('利息支出', 0))
                if interest_expense is None or pd.isna(interest_expense):
                    interest_expense = 0
                
                total_equity = latest_balance.get("Stockholders' equity", latest_balance.get('股东权益合计', 0))
                if total_equity is None or pd.isna(total_equity):
                    total_equity = 0
                
                total_debt = latest_balance.get('Total debt', latest_balance.get('总债务', 0))
                if total_debt is None or pd.isna(total_debt):
                    # 尝试从其他字段计算
                    long_term_debt = latest_balance.get('Long-term debt', latest_balance.get('长期债务', 0)) or 0
                    short_term_debt = latest_balance.get('Short-term debt', latest_balance.get('短期债务', 0)) or 0
                    total_debt = (long_term_debt or 0) + (short_term_debt or 0)
                
                cash = latest_balance.get('Cash and cash equivalents', latest_balance.get('现金及现金等价物', 0))
                if cash is None or pd.isna(cash):
                    cash = 0
                
                # 计算 ROIC
                return self.calculate_roic_from_financials(
                    net_income=float(net_income),
                    interest_expense=float(interest_expense),
                    total_equity=float(total_equity),
                    total_debt=float(total_debt),
                    cash_and_equivalents=float(cash)
                )
                
        except Exception as e:
            print(f"  AkShare 获取失败: {e}")
        
        return None
    
    def compare_sources(
        self,
        self_calculated: ROICComponents,
        external_value: float,
        external_source: str
    ) -> Dict[str, Any]:
        """
        对比自己计算的结果与外部来源
        
        按需求文档 §3.4 示例
        """
        
        diff_pct = abs(self_calculated.roic - external_value) / external_value * 100 if external_value else 0
        
        if diff_pct < 5:
            conclusion = "一致"
            detail = f"自己计算 {self_calculated.roic:.1f}% 与 {external_source} {external_value:.1f}% 接近"
        elif diff_pct < 20:
            conclusion = "略有差异"
            detail = f"自己计算 {self_calculated.roic:.1f}% 与 {external_source} {external_value:.1f}% 有 {diff_pct:.1f}% 差异"
        else:
            conclusion = "差异较大"
            detail = f"自己计算 {self_calculated.roic:.1f}% 与 {external_source} {external_value:.1f}% 差异 {diff_pct:.1f}%，需检查计算方法"
        
        return {
            "self_calculated_roic": self_calculated.roic,
            "external_roic": external_value,
            "external_source": external_source,
            "difference_pct": diff_pct,
            "conclusion": conclusion,
            "detail": detail,
            "calculation_details": {
                "NOPAT": self_calculated.nopat,
                "Invested_Capital": self_calculated.invested_capital,
                "Net_Income": self_calculated.net_income,
                "Total_Equity": self_calculated.total_equity,
                "Total_Debt": self_calculated.total_debt,
                "Cash": self_calculated.cash_and_equivalents
            }
        }
    
    def generate_calculation_report(self, components: ROICComponents) -> str:
        """生成计算过程报告"""
        
        report = f"""
## ROIC 自己计算验证报告

### 计算过程

**第一步：计算 NOPAT（税后净营业利润）**

```
NOPAT = Net Income + Interest Expense × (1 - Tax Rate)
      = {components.net_income:,.0f} + {components.interest_expense:,.0f} × (1 - {components.tax_rate:.0%})
      = {components.nopat:,.0f}
```

**第二步：计算 Invested Capital（投入资本）**

```
Invested Capital = Total Equity + Total Debt - Cash
                 = {components.total_equity:,.0f} + {components.total_debt:,.0f} - {components.cash_and_equivalents:,.0f}
                 = {components.invested_capital:,.0f}
```

**第三步：计算 ROIC**

```
ROIC = NOPAT / Invested Capital × 100%
     = {components.nopat:,.0f} / {components.invested_capital:,.0f} × 100%
     = {components.roic:.2f}%
```

### 结论

自己计算的 ROIC 为 **{components.roic:.2f}%**
"""
        
        return report


# 测试
if __name__ == "__main__":
    calculator = ROICCalculator()
    
    print("=== 测试 ROIC 自己计算 ===")
    print()
    
    # 测试 PDD 数据（需求文档示例）
    components = calculator.calculate_roic_from_financials(
        net_income=28.87,  # 十亿
        interest_expense=0,
        total_equity=89.05,  # 十亿（调整后）
        total_debt=0,
        cash_and_equivalents=0
    )
    
    print(f"NOPAT: {components.nopat:.2f}")
    print(f"Invested Capital: {components.invested_capital:.2f}")
    print(f"ROIC: {components.roic:.2f}%")
    
    print()
    print(calculator.generate_calculation_report(components))