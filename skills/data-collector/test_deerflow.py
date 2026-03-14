"""
Test data-collector in DeerFlow.

Usage:
1. Start DeerFlow backend
2. Send a message to the bot that triggers this skill
3. Check the output
"""

# This skill can be tested by sending to the bot:
# "收集 PDD 的财务数据"
# or "使用 data-collector 收集数据"

# The skill will:
# 1. Parse the query
# 2. Collect data from available sources
# 3. Assess quality
# 4. Return standardized JSON

# To see the data-collector in action, check:
# - /tmp/data_collector_output/data.json (if saved)
# - Or the raw response from the LLM

TEST_QUERIES = [
    "收集 PDD Holdings 2024 年财务数据",
    "分析 阿里巴巴 的财务数据",
    "收集 腾讯 的年报信息",
]

print("Data Collector Skill Test")
print("=" * 50)
print("\nTest queries (send one to your DeerFlow bot):")
for q in TEST_QUERIES:
    print(f"  - {q}")
print("\nThe skill will collect data and return quality assessment.")