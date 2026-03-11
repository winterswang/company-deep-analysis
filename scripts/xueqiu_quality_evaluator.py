"""
V6.3 数据质量评价标准

基于雪球分析项目的data_quality_checker.py

质量评价规则：
1. 文章(专栏) -> P0 (通常较长，深度分析)
2. 公告 -> P1 (官方信息)
3. 资讯 -> P2 (新闻类)
4. 讨论 -> 根据长度动态判断：
   - < 50字符 -> P4 (丢弃)
   - 50-150字符 -> P3 (低质量)
   - 150-300字符 -> P2
   - > 300字符 -> P1
"""

import re
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class DataQualityAssessment:
    """数据质量评估结果"""
    original_quality: str  # 原始质量等级
    adjusted_quality: str  # 调整后质量等级
    content_length: int
    reason: str


class XueqiuDataQualityEvaluator:
    """雪球数据质量评估器"""
    
    # 内容长度阈值
    MIN_DISCUSSION_LENGTH = 50  # 讨论最小长度
    DISCUSSION_P2_THRESHOLD = 150  # 讨论达到P2的长度
    DISCUSSION_P1_THRESHOLD = 300  # 讨论达到P1的长度
    MIN_NEWS_TITLE_LENGTH = 20  # 资讯标题最小长度
    MIN_ARTICLE_LENGTH = 300  # 文章最小长度
    
    # 无关标记模式
    NOISE_PATTERNS = [
        r'收起\s*',
        r'来自\w+\s*',
        r'展开\s*$',
        r'转发\s*$',
        r'赞\s*$',
        r'收藏\s*$',
    ]
    
    def evaluate_discussion(self, content: str) -> DataQualityAssessment:
        """评估讨论质量"""
        # 清洗内容
        cleaned = self._clean_content(content)
        length = len(cleaned)
        
        # 根据长度判断质量
        if length < self.MIN_DISCUSSION_LENGTH:
            return DataQualityAssessment(
                original_quality="P0",
                adjusted_quality="P4",
                content_length=length,
                reason=f"内容过短({length}字符 < {self.MIN_DISCUSSION_LENGTH})"
            )
        elif length < self.DISCUSSION_P2_THRESHOLD:
            return DataQualityAssessment(
                original_quality="P0",
                adjusted_quality="P3",
                content_length=length,
                reason=f"内容较短({length}字符)"
            )
        elif length < self.DISCUSSION_P1_THRESHOLD:
            return DataQualityAssessment(
                original_quality="P0",
                adjusted_quality="P2",
                content_length=length,
                reason=f"内容适中({length}字符)"
            )
        else:
            return DataQualityAssessment(
                original_quality="P0",
                adjusted_quality="P1",
                content_length=length,
                reason=f"内容充实({length}字符)"
            )
    
    def evaluate_news(self, title: str, content: str = "") -> DataQualityAssessment:
        """评估资讯质量"""
        title_len = len(title)
        content_len = len(content) if content else 0
        
        if title_len < self.MIN_NEWS_TITLE_LENGTH:
            return DataQualityAssessment(
                original_quality="P0",
                adjusted_quality="P4",
                content_length=title_len,
                reason=f"标题过短({title_len}字符)"
            )
        
        # 资讯固定为P2
        return DataQualityAssessment(
            original_quality="P0",
            adjusted_quality="P2",
            content_length=title_len + content_len,
            reason="新闻资讯，P2级别"
        )
    
    def evaluate_article(self, title: str, content: str) -> DataQualityAssessment:
        """评估文章质量"""
        content_len = len(content)
        
        if content_len < self.MIN_ARTICLE_LENGTH:
            return DataQualityAssessment(
                original_quality="P0",
                adjusted_quality="P2",
                content_length=content_len,
                reason=f"文章内容较短({content_len}字符)"
            )
        
        # 深度文章为P0
        return DataQualityAssessment(
            original_quality="P0",
            adjusted_quality="P0",
            content_length=content_len,
            reason=f"深度分析文章({content_len}字符)"
        )
    
    def evaluate_notice(self, title: str) -> DataQualityAssessment:
        """评估公告质量"""
        # 公告为官方信息，固定P1
        return DataQualityAssessment(
            original_quality="P0",
            adjusted_quality="P1",
            content_length=len(title),
            reason="官方公告，P1级别"
        )
    
    def _clean_content(self, content: str) -> str:
        """清洗内容"""
        cleaned = content
        
        # 移除时间标记
        cleaned = re.sub(r'\d+小时前·?\s*', '', cleaned)
        cleaned = re.sub(r'\d+天前·?\s*', '', cleaned)
        cleaned = re.sub(r'昨天\s*\d{1,2}:\d{2}·?\s*', '', cleaned)
        cleaned = re.sub(r'今天\s*\d{1,2}:\d{2}·?\s*', '', cleaned)
        cleaned = re.sub(r'来自\w+\s*', '', cleaned)
        
        # 移除无关标记
        for pattern in self.NOISE_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned)
        
        # 清理多余空白
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def batch_evaluate(self, data_points: List) -> Tuple[List, List]:
        """
        批量评估数据点
        
        Returns:
            (有效数据点列表, 被过滤的数据点列表)
        """
        valid = []
        filtered = []
        
        for dp in data_points:
            source = dp.source
            
            # 根据来源类型评估
            if "讨论" in source:
                assessment = self.evaluate_discussion(dp.value)
            elif "资讯" in source:
                assessment = self.evaluate_news(dp.name, dp.value)
            elif "专栏" in source or "文章" in source:
                assessment = self.evaluate_article(dp.name, dp.notes)
            elif "公告" in source:
                assessment = self.evaluate_notice(dp.name)
            else:
                # 其他来源保持原质量
                assessment = DataQualityAssessment(
                    original_quality=dp.quality,
                    adjusted_quality=dp.quality,
                    content_length=len(dp.value),
                    reason="保持原质量等级"
                )
            
            # 更新质量等级
            dp.quality = assessment.adjusted_quality
            dp.notes = f"{dp.notes} | 质量评估: {assessment.reason}"
            
            # P2及以上保留，P3及以下过滤
            if assessment.adjusted_quality in ["P0", "P1", "P2"]:
                valid.append(dp)
            else:
                filtered.append((dp, assessment.reason))
        
        return valid, filtered


# 测试
if __name__ == "__main__":
    evaluator = XueqiuDataQualityEvaluator()
    
    # 测试讨论
    test_cases = [
        ("短讨论", "好！"),
        ("中等讨论", "这是一个中等长度的讨论内容，大约有五十个字符左右。"),
        ("较长讨论", "这是一个比较长的讨论内容，包含了更多的信息和观点。用户在这里分享了自己对公司的看法，分析了公司的优势和劣势，并给出了一些建议。这样的内容更有价值。"),
        ("长讨论", "这是一个非常长的讨论内容，用户详细分析公司的商业模式、财务状况、竞争优势等多个方面。首先，从商业模式来看，这家公司采用了...其次，财务方面...再次，竞争格局...最后，投资建议...这样的深度分析非常有价值。"),
    ]
    
    print("=== 讨论质量评估测试 ===\n")
    for name, content in test_cases:
        result = evaluator.evaluate_discussion(content)
        print(f"{name}: {content[:30]}...")
        print(f"  长度: {result.content_length}字符")
        print(f"  质量: {result.adjusted_quality}")
        print(f"  原因: {result.reason}\n")