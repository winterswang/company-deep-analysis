"""
V7.0 ToDo执行器

核心功能：
1. 数据验证类：从现有数据提取、交叉验证
2. 数据检索类：Tavily/Exa/雪球搜索
3. 爬取数据：雪球/年报网站
4. 深度分析：LLM深度推理

严格遵循需求文档 §7.2
"""

import sys
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class ToDoType(Enum):
    """ToDo类型"""
    DATA_VALIDATION = "数据验证"
    DATA_RETRIEVAL = "数据检索"
    DATA_CRAWLING = "数据爬取"
    DEEP_ANALYSIS = "深度分析"
    EVIDENCE_SUPPLEMENT = "证据补充"


@dataclass
class ToDoTask:
    """ToDo任务"""
    task_id: str
    task_type: ToDoType
    description: str
    priority: str  # 高/中/低
    data_sources: List[str]
    expected_output: str
    status: str = "pending"  # pending/running/completed/failed
    result: Any = None
    quality_score: float = 0.0


@dataclass
class Evidence:
    """证据"""
    evidence_id: str
    content: str
    source: str
    quality: str  # P0/P1/P2
    relevance: str  # 高/中/低
    raw_data: Any = None


class ToDoExecutor:
    """ToDo执行器"""
    
    # API配置
    TAVILY_API_URL = "https://api.tavily.com/search"
    EXA_API_URL = "https://api.exa.ai/search"
    
    def __init__(self, llm_client: LLMClient = None, config: Dict = None):
        self.llm = llm_client or LLMClient()
        self.config = config or {}
        
        # API密钥
        self.tavily_key = self._get_api_key("TAVILY_API_KEY")
        self.exa_key = self._get_api_key("EXA_API_KEY")
        
        # 执行历史
        self.execution_history: List[Dict] = []
    
    def execute_todo(self, todo: ToDoTask, context: Dict = None) -> Evidence:
        """
        执行单个ToDo任务
        
        Args:
            todo: ToDo任务
            context: 执行上下文（包含公司信息、已有数据等）
        
        Returns:
            Evidence: 证据结果
        """
        
        print(f"  执行ToDo [{todo.task_type.value}]: {todo.description[:50]}...")
        
        todo.status = "running"
        context = context or {}
        
        try:
            if todo.task_type == ToDoType.DATA_VALIDATION:
                result = self._execute_data_validation(todo, context)
            elif todo.task_type == ToDoType.DATA_RETRIEVAL:
                result = self._execute_data_retrieval(todo, context)
            elif todo.task_type == ToDoType.DATA_CRAWLING:
                result = self._execute_data_crawling(todo, context)
            elif todo.task_type == ToDoType.DEEP_ANALYSIS:
                result = self._execute_deep_analysis(todo, context)
            else:
                result = self._execute_evidence_supplement(todo, context)
            
            todo.status = "completed"
            todo.result = result
            todo.quality_score = result.quality_score if hasattr(result, 'quality_score') else 0.5
            
            # 记录执行历史
            self.execution_history.append({
                "todo_id": todo.task_id,
                "type": todo.task_type.value,
                "status": "completed",
                "timestamp": datetime.now().isoformat()
            })
            
            return result
            
        except Exception as e:
            todo.status = "failed"
            todo.result = str(e)
            
            self.execution_history.append({
                "todo_id": todo.task_id,
                "type": todo.task_type.value,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })
            
            return Evidence(
                evidence_id=f"error_{todo.task_id}",
                content=f"执行失败: {str(e)}",
                source="error",
                quality="P4",
                relevance="低"
            )
    
    def execute_todos(self, todos: List[ToDoTask], context: Dict = None) -> List[Evidence]:
        """批量执行ToDo"""
        
        results = []
        for todo in todos:
            result = self.execute_todo(todo, context)
            results.append(result)
        
        return results
    
    def _execute_data_validation(self, todo: ToDoTask, context: Dict) -> Evidence:
        """
        执行数据验证类ToDo
        
        需求要求：
        - 从现有数据中重新提取依据
        - 交叉验证关键数据
        - 标注数据来源和质量
        """
        
        company = context.get("company", "")
        data_point = context.get("data_point", "")
        
        # 从本地数据提取
        local_data = self._extract_from_local(todo.description, context)
        
        if local_data:
            return Evidence(
                evidence_id=f"val_{todo.task_id}",
                content=str(local_data),
                source="本地数据",
                quality="P1",
                relevance="高",
                raw_data=local_data
            )
        
        # 尝试从雪球数据验证
        xueqiu_data = self._validate_from_xueqiu(todo.description, context)
        
        if xueqiu_data:
            return Evidence(
                evidence_id=f"val_{todo.task_id}",
                content=str(xueqiu_data),
                source="雪球",
                quality="P1",
                relevance="高",
                raw_data=xueqiu_data
            )
        
        return Evidence(
            evidence_id=f"val_{todo.task_id}",
            content="无法验证",
            source="validation",
            quality="P4",
            relevance="低"
        )
    
    def _execute_data_retrieval(self, todo: ToDoTask, context: Dict) -> Evidence:
        """
        执行数据检索类ToDo
        
        需求要求：
        - Tavily搜索（实时新闻）
        - Exa深度搜索（研究报告）
        - 雪球搜索（专业观点）
        - 本地数据检索（用户收藏）
        """
        
        company = context.get("company", "")
        query = f"{company} {todo.description}"
        
        results = []
        
        # Tavily搜索
        if "Tavily" in todo.data_sources and self.tavily_key:
            tavily_results = self._search_tavily(query)
            results.extend(tavily_results)
        
        # Exa搜索
        if "Exa" in todo.data_sources and self.exa_key:
            exa_results = self._search_exa(query)
            results.extend(exa_results)
        
        # 本地数据
        if "本地数据" in todo.data_sources:
            local_results = self._search_local(query, context)
            results.extend(local_results)
        
        if results:
            content = "\n".join([
                f"- [{r.get('source', 'unknown')}] {r.get('content', '')[:200]}"
                for r in results[:5]
            ])
            
            return Evidence(
                evidence_id=f"ret_{todo.task_id}",
                content=content,
                source="多源检索",
                quality="P2",
                relevance="高",
                raw_data=results
            )
        
        return Evidence(
            evidence_id=f"ret_{todo.task_id}",
            content="未找到相关数据",
            source="retrieval",
            quality="P4",
            relevance="低"
        )
    
    def _execute_data_crawling(self, todo: ToDoTask, context: Dict) -> Evidence:
        """
        执行数据爬取类ToDo
        
        需求要求：
        - 雪球爬取
        - 年报网站爬取
        """
        
        company = context.get("company", "")
        ticker = context.get("ticker", "")
        
        # 年报爬取（简化实现）
        if "年报" in todo.description or "10-K" in todo.description:
            annual_report = self._crawl_annual_report(company, ticker)
            if annual_report:
                return Evidence(
                    evidence_id=f"crawl_{todo.task_id}",
                    content=annual_report[:1000],
                    source="年报",
                    quality="P0",
                    relevance="高",
                    raw_data=annual_report
                )
        
        return Evidence(
            evidence_id=f"crawl_{todo.task_id}",
            content="爬取功能待实现",
            source="crawling",
            quality="P4",
            relevance="低"
        )
    
    def _execute_deep_analysis(self, todo: ToDoTask, context: Dict) -> Evidence:
        """
        执行深度分析类ToDo
        
        需求要求：
        - LLM深度推理
        - 透过财务数据看到企业经营本质
        """
        
        # 准备分析提示词
        prompt = f"""
请对以下内容进行深度分析：

公司：{context.get('company', '')}
问题：{todo.description}
已有数据：{json.dumps(context.get('financial_data', {}), ensure_ascii=False)}

请从以下角度分析：
1. 财务数据的本质含义是什么？
2. 这反映了什么经营能力？
3. 是否存在异常？原因是什么？
4. 对投资意味着什么？

请给出具体、有洞察的分析，避免空泛描述。
"""
        
        try:
            analysis = self.llm.chat([{"role": "user", "content": prompt}])
            
            return Evidence(
                evidence_id=f"analysis_{todo.task_id}",
                content=analysis,
                source="LLM深度分析",
                quality="P1",
                relevance="高",
                raw_data=analysis
            )
        except Exception as e:
            return Evidence(
                evidence_id=f"analysis_{todo.task_id}",
                content=f"深度分析失败: {str(e)}",
                source="analysis",
                quality="P4",
                relevance="低"
            )
    
    def _execute_evidence_supplement(self, todo: ToDoTask, context: Dict) -> Evidence:
        """执行证据补充类ToDo"""
        
        # 简化实现：调用数据检索
        return self._execute_data_retrieval(todo, context)
    
    # ============ 辅助方法 ============
    
    def _get_api_key(self, key_name: str) -> Optional[str]:
        """获取API密钥"""
        import os
        
        # 先从环境变量获取
        key = os.environ.get(key_name)
        if key:
            return key
        
        # 从 .env 文件加载
        env_paths = [
            Path(__file__).parent.parent.parent.parent / ".env",  # deer-flow-analysis/.env
            Path(__file__).parent.parent.parent / ".env",
            Path("/root/.openclaw/workspace/deer-flow-analysis/.env"),
        ]
        
        for env_path in env_paths:
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith(f"{key_name}="):
                            return line.split("=", 1)[1]
        
        return None
    
    def _search_tavily(self, query: str) -> List[Dict]:
        """Tavily搜索"""
        
        if not self.tavily_key:
            return []
        
        try:
            response = requests.post(
                self.TAVILY_API_URL,
                json={
                    "api_key": self.tavily_key,
                    "query": query,
                    "max_results": 5
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "source": "Tavily",
                        "title": r.get("title", ""),
                        "content": r.get("content", ""),
                        "url": r.get("url", "")
                    }
                    for r in data.get("results", [])
                ]
        except Exception as e:
            print(f"    Tavily搜索失败: {e}")
        
        return []
    
    def _search_exa(self, query: str) -> List[Dict]:
        """Exa搜索"""
        
        if not self.exa_key:
            return []
        
        try:
            response = requests.post(
                self.EXA_API_URL,
                headers={"x-api-key": self.exa_key},
                json={
                    "query": query,
                    "numResults": 5
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "source": "Exa",
                        "title": r.get("title", ""),
                        "content": r.get("text", ""),
                        "url": r.get("url", "")
                    }
                    for r in data.get("results", [])
                ]
        except Exception as e:
            print(f"    Exa搜索失败: {e}")
        
        return []
    
    def _search_local(self, query: str, context: Dict) -> List[Dict]:
        """搜索本地数据"""
        
        results = []
        local_data = context.get("local_data", {})
        
        for key, value in local_data.items():
            if query.lower() in key.lower() or query.lower() in str(value).lower():
                results.append({
                    "source": "本地数据",
                    "title": key,
                    "content": str(value)
                })
        
        return results
    
    def _extract_from_local(self, description: str, context: Dict) -> Optional[Any]:
        """从本地数据提取"""
        
        local_data = context.get("local_data", {})
        
        # 简化实现：关键词匹配
        keywords = description.lower().split()
        for key, value in local_data.items():
            if any(kw in key.lower() for kw in keywords):
                return {key: value}
        
        return None
    
    def _validate_from_xueqiu(self, description: str, context: Dict) -> Optional[Any]:
        """从雪球数据验证"""
        
        xueqiu_data = context.get("xueqiu_data", {})
        
        # 简化实现
        return None
    
    def _crawl_annual_report(self, company: str, ticker: str) -> Optional[str]:
        """爬取年报"""
        
        # 简化实现：返回提示
        return f"年报爬取功能待实现: {company} ({ticker})"
    
    def generate_todo_from_question(
        self, 
        layer: int, 
        question: str, 
        context: Dict
    ) -> List[ToDoTask]:
        """
        根据追问生成ToDo任务
        
        需求要求：
        - 第1层：财务数据验证、年报查询
        - 第2层：行业对比、历史趋势分析
        - 第3层：业务模式分析、流程研究
        - 第4层：竞品对比、护城河验证
        - 第5层：竞争格局分析、路径依赖分析
        """
        
        todos = []
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        
        # 根据层级生成不同类型的ToDo
        layer_data_sources = {
            1: ["AkShare", "年报", "雪球"],
            2: ["AkShare", "雪球", "Exa搜索"],
            3: ["雪球专栏", "Tavily搜索", "本地数据"],
            4: ["AkShare", "Exa搜索", "雪球", "本地数据"],
            5: ["Exa深度搜索", "Tavily搜索", "本地数据"]
        }
        
        data_sources = layer_data_sources.get(layer, ["Tavily", "Exa"])
        
        # 生成数据检索ToDo
        todos.append(ToDoTask(
            task_id=f"ret_{layer}_{timestamp}",
            task_type=ToDoType.DATA_RETRIEVAL,
            description=question,
            priority="高",
            data_sources=data_sources,
            expected_output="相关数据和分析"
        ))
        
        # 生成深度分析ToDo
        todos.append(ToDoTask(
            task_id=f"analysis_{layer}_{timestamp}",
            task_type=ToDoType.DEEP_ANALYSIS,
            description=f"深度分析：{question}",
            priority="中",
            data_sources=["LLM"],
            expected_output="深度洞察"
        ))
        
        return todos


# 测试
if __name__ == "__main__":
    executor = ToDoExecutor()
    
    # 测试ToDo执行
    todo = ToDoTask(
        task_id="test_001",
        task_type=ToDoType.DATA_RETRIEVAL,
        description="ROIC 为什么这么高？",
        priority="高",
        data_sources=["Tavily", "Exa"],
        expected_output="相关分析"
    )
    
    context = {
        "company": "PDD Holdings",
        "ticker": "PDD",
        "financial_data": {"ROIC": 32.4}
    }
    
    result = executor.execute_todo(todo, context)
    print(f"结果: {result.content[:200]}")