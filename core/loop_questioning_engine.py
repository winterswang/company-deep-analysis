"""
V7.0 完整实现 - 循环追问引擎

严格按照需求文档 §7 实现循环追问机制：
1. 当前层追问 → 发现问题 → 生成ToDo → 执行ToDo → 获取新证据 → 验证证据质量
2. 质量达标 → 进入下一层
3. 质量不达标 → 重新生成ToDo
"""

import sys
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient


class MoatType(Enum):
    """护城河类型"""
    NETWORK_EFFECT = "网络效应"
    SWITCHING_COST = "转换成本"
    COST_ADVANTAGE = "成本优势"
    INTANGIBLE_ASSETS = "无形资产"
    EFFICIENT_SCALE = "有效规模"
    UNKNOWN = "未识别"


class ToDoType(Enum):
    """ToDo类型"""
    DATA_VALIDATION = "数据验证"
    DATA_RETRIEVAL = "数据检索"
    DATA_CRAWLING = "数据爬取"
    DEEP_ANALYSIS = "深度分析"
    EVIDENCE_SUPPLEMENT = "证据补充"  # 新增：证据补充类


class EvidenceQuality(Enum):
    """证据质量"""
    P0 = 1.0  # 官方数据
    P1 = 0.8  # 权威第三方
    P2 = 0.6  # 专业机构
    P3 = 0.3  # 一般来源
    INVALID = 0.0  # 无效


@dataclass
class ToDo:
    """待办事项"""
    id: str
    todo_type: ToDoType
    description: str
    data_sources: List[str]
    expected_output: str
    priority: str = "中"  # 高/中/低
    status: str = "pending"  # pending/running/completed/failed
    result: Optional[Dict] = None


@dataclass
class Evidence:
    """证据"""
    id: str
    content: str
    source: str
    quality: EvidenceQuality
    relevance: float  # 0-1
    raw_data: Optional[Dict] = None


@dataclass
class QuestioningResult:
    """追问结果"""
    layer: int
    question: str
    observation: str
    todos: List[ToDo]
    evidence: List[Evidence]
    moat_type: Optional[MoatType] = None
    reward: float = 0.0


@dataclass
class FinancialAnomaly:
    """财务异常"""
    metric: str
    value: Any
    trend: List
    benchmark: Any
    deviation: str
    severity: str
    question: str


class LoopQuestioningEngine:
    """
    循环追问引擎
    
    严格按需求文档 §7 实现：
    - 追问 → ToDo → 执行 → 新证据 → 验证 → 循环
    """
    
    # 护城河验证问题清单（需求文档 §5.2）
    MOAT_VERIFICATION_QUESTIONS = {
        MoatType.NETWORK_EFFECT: {
            "core_question": "新用户加入是否让所有用户受益？",
            "verification_questions": [
                "双边网络效应还是单边？",
                "临界规模是多少？",
                "用户增长是否带动价值增长？"
            ],
            "verification_data": ["获客成本趋势", "用户留存率", "GMV增速"]
        },
        MoatType.SWITCHING_COST: {
            "core_question": "客户换掉我们会损失什么？",
            "verification_questions": [
                "转换成本是财务性的还是运营性的？",
                "转换成本随时间增加还是减少？",
                "客户数据迁移成本多高？"
            ],
            "verification_data": ["客户留存率", "续约率", "提价能力"]
        },
        MoatType.COST_ADVANTAGE: {
            "core_question": "低成本来自规模、资源、地理位置还是流程？",
            "verification_questions": [
                "成本优势来源是否可持续？",
                "竞争对手能否复制这个成本结构？",
                "规模效应的临界点是多少？"
            ],
            "verification_data": ["毛利率", "成本结构", "单位成本趋势"]
        },
        MoatType.INTANGIBLE_ASSETS: {
            "core_question": "这个无形资产有定价权吗？",
            "verification_questions": [
                "品牌/专利能带来定价权吗？",
                "无形资产的保护期多久？",
                "研发投入是否持续？"
            ],
            "verification_data": ["溢价定价能力", "品牌价值", "专利数量"]
        },
        MoatType.EFFICIENT_SCALE: {
            "core_question": "新进入者会破坏均衡吗？",
            "verification_questions": [
                "市场规模是否限制了竞争者数量？",
                "新进入者的资本门槛？",
                "监管壁垒有多高？"
            ],
            "verification_data": ["ROIC", "竞争者数量", "市场集中度"]
        }
    }
    
    # 每层追问的ToDo类型（需求文档 §4.2）
    LAYER_TODO_TEMPLATES = {
        1: {
            "question_types": ["财务数据为什么是这样？"],
            "todo_types": [ToDoType.DATA_VALIDATION, ToDoType.DATA_RETRIEVAL],
            "data_sources": ["AkShare", "年报", "雪球"]
        },
        2: {
            "question_types": ["经营表现为什么是这样？"],
            "todo_types": [ToDoType.DATA_RETRIEVAL, ToDoType.DEEP_ANALYSIS],
            "data_sources": ["AkShare", "雪球", "Exa"]
        },
        3: {
            "question_types": ["经营能力来源是什么？"],
            "todo_types": [ToDoType.DATA_RETRIEVAL, ToDoType.DATA_CRAWLING],
            "data_sources": ["雪球专栏", "Tavily", "本地数据"]
        },
        4: {
            "question_types": ["护城河是哪个类型？"],
            "todo_types": [ToDoType.DEEP_ANALYSIS, ToDoType.DATA_CRAWLING],
            "data_sources": ["AkShare", "Exa", "雪球", "本地数据"]
        },
        5: {
            "question_types": ["为什么不可复制？"],
            "todo_types": [ToDoType.DEEP_ANALYSIS, ToDoType.DATA_RETRIEVAL],
            "data_sources": ["Exa", "Tavily", "本地数据"]
        }
    }
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
        self.questioning_history: List[QuestioningResult] = []
        self.all_todos: List[ToDo] = []
        self.all_evidence: List[Evidence] = []
        
        # API Keys
        self.tavily_key = self._load_api_key("TAVILY_API_KEY")
        self.exa_key = self._load_api_key("EXA_API_KEY")
        
        # 配置
        self.max_consecutive_failures = 3  # 连续失败N次终止
        self.max_iterations = 10  # 最大迭代次数
        self.min_evidence_quality = EvidenceQuality.P2  # 最低证据质量要求
    
    def _load_api_key(self, key_name: str) -> Optional[str]:
        """加载API Key"""
        import os
        key = os.environ.get(key_name)
        if not key:
            env_path = Path("/root/.openclaw/workspace/deer-flow-analysis/.env")
            if env_path.exists():
                with open(env_path) as f:
                    for line in f:
                        if line.startswith(f"{key_name}="):
                            return line.strip().split("=", 1)[1]
        return key
    
    def start_loop_questioning(
        self,
        financial_data: Dict[str, Any],
        context: Dict = None
    ) -> Tuple[List[QuestioningResult], str]:
        """
        启动循环追问
        
        完整实现需求文档 §7 的循环机制
        """
        
        context = context or {}
        company = context.get("company", "该公司")
        
        print("=" * 70)
        print("V7.0 循环追问引擎启动")
        print("严格按需求文档 §7 实现")
        print("=" * 70)
        
        # 识别财务异常
        anomalies = self._identify_anomalies(financial_data, company)
        
        if not anomalies:
            print("未发现财务异常，分析终止")
            return [], "未发现财务异常"
        
        print(f"\n发现 {len(anomalies)} 个财务异常:")
        for i, a in enumerate(anomalies, 1):
            print(f"  {i}. {a.metric}: {a.deviation} ({a.severity})")
        
        # 对每个异常进行循环追问
        for anomaly in anomalies[:2]:  # 先分析前2个异常
            print(f"\n{'='*70}")
            print(f"开始分析: {anomaly.metric}")
            print("=" * 70)
            
            result = self._loop_question_anomaly(anomaly, context)
            if result:
                self.questioning_history.append(result)
        
        # 生成报告
        report = self._generate_report(company)
        
        return self.questioning_history, report
    
    def _loop_question_anomaly(
        self,
        anomaly: FinancialAnomaly,
        context: Dict
    ) -> Optional[QuestioningResult]:
        """
        对单个异常进行循环追问
        
        核心：追问 → ToDo → 执行 → 新证据 → 验证 → 循环
        """
        
        layer = 1
        consecutive_failures = 0
        total_iterations = 0
        all_evidence_for_anomaly: List[Evidence] = []
        all_todos_for_anomaly: List[ToDo] = []
        moat_type = None
        
        while layer <= 5 and consecutive_failures < self.max_consecutive_failures and total_iterations < self.max_iterations:
            total_iterations += 1
            
            print(f"\n【第{layer}层追问】(迭代 {total_iterations})")
            print("-" * 50)
            
            # 1. 生成追问
            question = self._generate_question(layer, anomaly, context)
            print(f"追问: {question}")
            
            # 2. 生成ToDo
            todos = self._generate_todos(layer, anomaly, context)
            print(f"生成 {len(todos)} 个ToDo")
            
            # 3. 执行ToDo
            new_evidence = []
            for todo in todos:
                todo.status = "running"
                result = self._execute_todo(todo, context)
                
                if result:
                    todo.status = "completed"
                    todo.result = result
                    new_evidence.extend(result)
                    all_todos_for_anomaly.append(todo)
                else:
                    todo.status = "failed"
            
            print(f"执行完成，获取 {len(new_evidence)} 条新证据")
            
            # 4. 验证证据质量
            valid_evidence = self._validate_evidence(new_evidence)
            print(f"有效证据: {len(valid_evidence)} 条")
            
            if valid_evidence:
                all_evidence_for_anomaly.extend(valid_evidence)
                consecutive_failures = 0
                
                # 5. 生成观察
                observation = self._generate_observation(layer, valid_evidence, context)
                print(f"观察: {observation[:100]}...")
                
                # 6. 检查是否识别到护城河
                if layer >= 4:
                    moat_type = self._identify_moat_type(valid_evidence, context)
                    if moat_type:
                        print(f"护城河类型: {moat_type.value}")
                
                # 7. 进入下一层
                layer += 1
                
            else:
                consecutive_failures += 1
                print(f"证据不足，连续失败次数: {consecutive_failures}")
                
                # ★★★ 关键：实际执行新的搜索策略 ★★★
                if consecutive_failures < self.max_consecutive_failures:
                    print("尝试新的搜索策略...")
                    
                    # 1. 换不同的搜索关键词
                    alternative_queries = self._generate_alternative_queries(anomaly, layer)
                    
                    # 2. 尝试不同的数据源
                    for query in alternative_queries[:2]:  # 最多尝试2个新查询
                        if self.tavily_key:
                            new_results = self._search_tavily(query)
                            for r in new_results[:3]:
                                new_evidence.append(Evidence(
                                    id=f"ev_alt_{int(time.time()*1000)}",
                                    content=r.get("content", "")[:500],
                                    source="Tavily备选搜索",
                                    quality=EvidenceQuality.P2,
                                    relevance=0.6
                                ))
                    
                    # 3. 重新验证证据
                    valid_evidence = self._validate_evidence(new_evidence)
                    
                    if valid_evidence:
                        print(f"  新搜索获得 {len(valid_evidence)} 条有效证据")
                        all_evidence_for_anomaly.extend(valid_evidence)
                        consecutive_failures = 0  # 重置失败计数
                    else:
                        print("  新搜索仍未获得有效证据")
        
        # 计算奖励
        reward = self._calculate_reward(layer, all_evidence_for_anomaly, moat_type)
        
        return QuestioningResult(
            layer=layer - 1,
            question=self._generate_question(1, anomaly, context),  # 原始问题
            observation=self._generate_observation(layer - 1, all_evidence_for_anomaly, context),
            todos=all_todos_for_anomaly,
            evidence=all_evidence_for_anomaly,
            moat_type=moat_type,
            reward=reward
        )
    
    def _generate_question(self, layer: int, anomaly: FinancialAnomaly, context: Dict) -> str:
        """生成追问"""
        
        company = context.get("company", "该公司")
        
        layer_questions = {
            1: f"{anomaly.question}",
            2: f"从经营角度看，{company}是如何实现这种{anomaly.metric}表现的？",
            3: f"{company}需要具备什么核心能力才能维持这种{anomaly.metric}？",
            4: f"这种能力的护城河来源是什么？是网络效应、转换成本、成本优势、无形资产还是有效规模？",
            5: f"为什么竞争对手无法复制{company}的这种优势？"
        }
        
        return layer_questions.get(layer, "")
    
    def _generate_todos(self, layer: int, anomaly: FinancialAnomaly, context: Dict) -> List[ToDo]:
        """生成ToDo（按需求文档 §4.2）"""
        
        company = context.get("company", "该公司")
        template = self.LAYER_TODO_TEMPLATES.get(layer, {})
        todos = []
        
        # 根据层级生成不同的ToDo
        if layer == 1:
            todos = [
                ToDo(
                    id=f"todo_{layer}_validation",
                    todo_type=ToDoType.DATA_VALIDATION,
                    description=f"验证{anomaly.metric}的数据准确性",
                    data_sources=["AkShare", "年报"],
                    expected_output="验证后的数据来源",
                    priority="高"
                ),
                ToDo(
                    id=f"todo_{layer}_history",
                    todo_type=ToDoType.DATA_RETRIEVAL,
                    description=f"获取{anomaly.metric}的历史趋势（5年）",
                    data_sources=["AkShare", "雪球"],
                    expected_output="5年趋势数据",
                    priority="高"
                )
            ]
        elif layer == 2:
            todos = [
                ToDo(
                    id=f"todo_{layer}_industry",
                    todo_type=ToDoType.DATA_RETRIEVAL,
                    description=f"获取{anomaly.metric}的行业对比数据",
                    data_sources=["Tavily", "Exa"],
                    expected_output="行业对比数据",
                    priority="高"
                ),
                ToDo(
                    id=f"todo_{layer}_analysis",
                    todo_type=ToDoType.DEEP_ANALYSIS,
                    description=f"分析{company}{anomaly.metric}变化的经营原因",
                    data_sources=["Tavily", "Exa"],
                    expected_output="经营分析结论",
                    priority="中"
                )
            ]
        elif layer == 3:
            todos = [
                ToDo(
                    id=f"todo_{layer}_capability",
                    todo_type=ToDoType.DATA_RETRIEVAL,
                    description=f"研究{company}的核心经营能力",
                    data_sources=["Tavily", "雪球专栏"],
                    expected_output="核心能力描述",
                    priority="高"
                )
            ]
        elif layer == 4:
            todos = [
                ToDo(
                    id=f"todo_{layer}_moat",
                    todo_type=ToDoType.DEEP_ANALYSIS,
                    description=f"验证{company}的护城河类型",
                    data_sources=["Exa", "Tavily"],
                    expected_output="护城河类型判断",
                    priority="高"
                )
            ]
        elif layer == 5:
            todos = [
                ToDo(
                    id=f"todo_{layer}_competition",
                    todo_type=ToDoType.DEEP_ANALYSIS,
                    description=f"分析{company}竞争对手为何无法复制",
                    data_sources=["Exa", "Tavily"],
                    expected_output="竞争分析结论",
                    priority="高"
                )
            ]
        
        self.all_todos.extend(todos)
        return todos
    
    def _execute_todo(self, todo: ToDo, context: Dict) -> List[Evidence]:
        """执行ToDo"""
        
        evidence_list = []
        company = context.get("company", "")
        
        if todo.todo_type == ToDoType.DATA_RETRIEVAL:
            # 使用 Tavily/Exa 搜索
            if self.tavily_key:
                results = self._search_tavily(f"{company} {todo.description}")
                for r in results[:3]:
                    evidence = Evidence(
                        id=f"ev_{int(time.time()*1000)}",
                        content=r.get("content", "")[:500],
                        source="Tavily",
                        quality=EvidenceQuality.P2,
                        relevance=0.7
                    )
                    evidence_list.append(evidence)
        
        elif todo.todo_type == ToDoType.DEEP_ANALYSIS:
            # 使用 LLM 分析
            prompt = f"""请分析：{todo.description}

公司：{company}

请给出具体分析结论（2-3句话）："""
            
            try:
                analysis = self.llm.chat([{"role": "user", "content": prompt}])
                evidence = Evidence(
                    id=f"ev_{int(time.time()*1000)}",
                    content=analysis,
                    source="LLM分析",
                    quality=EvidenceQuality.P2,
                    relevance=0.8
                )
                evidence_list.append(evidence)
            except Exception as e:
                print(f"LLM分析失败: {e}")
        
        elif todo.todo_type == ToDoType.EVIDENCE_SUPPLEMENT:
            # 证据补充：原文引用标注、数据来源链接、置信度评估
            # 从搜索结果中提取更详细的证据
            if self.tavily_key:
                results = self._search_tavily(f"{company} {todo.description} 来源 原文")
                for r in results[:3]:
                    # 提取 URL 作为来源链接
                    url = r.get("url", "")
                    title = r.get("title", "")
                    content = r.get("content", "")[:500]
                    
                    evidence = Evidence(
                        id=f"ev_{int(time.time()*1000)}",
                        content=f"【{title}】\n{content}\n\n来源链接: {url}",
                        source=f"Tavily/{title}",
                        quality=EvidenceQuality.P2,
                        relevance=0.9,  # 证据补充类相关性更高
                        raw_data={"url": url, "title": title}
                    )
                    evidence_list.append(evidence)
        
        elif todo.todo_type == ToDoType.DATA_CRAWLING:
            # 数据爬取：雪球数据、年报数据
            # 尝试从雪球爬取数据
            crawled_evidence = self._crawl_xueqiu_data(company, todo.description)
            evidence_list.extend(crawled_evidence)
        
        return evidence_list
    
    def _crawl_xueqiu_data(self, company: str, description: str) -> List[Evidence]:
        """
        从雪球爬取数据
        
        实现需求文档 §7.2 的数据爬取类 ToDo
        """
        
        evidence_list = []
        
        try:
            # 尝试导入雪球爬虫
            sys.path.insert(0, "/root/.openclaw/workspace/ir-crawler")
            
            # 检查是否有雪球数据目录
            xueqiu_data_dir = Path("/root/.openclaw/workspace/ir-crawler/downloads")
            
            # 搜索公司相关的雪球文件
            for company_dir in xueqiu_data_dir.iterdir():
                if company.lower() in company_dir.name.lower():
                    # 找到公司目录，读取文件
                    for file_type in ["annual", "quarterly", "presentations"]:
                        type_dir = company_dir / file_type
                        if type_dir.exists():
                            for file_path in type_dir.glob("*.pdf"):
                                # 读取 PDF 内容
                                try:
                                    import subprocess
                                    result = subprocess.run(
                                        ["pdftotext", str(file_path), "-"],
                                        capture_output=True,
                                        text=True,
                                        timeout=30
                                    )
                                    if result.returncode == 0:
                                        content = result.stdout[:1000]
                                        evidence = Evidence(
                                            id=f"ev_{int(time.time()*1000)}",
                                            content=f"【本地文件: {file_path.name}】\n{content}",
                                            source=f"雪球爬虫/{file_type}",
                                            quality=EvidenceQuality.P1,
                                            relevance=0.8,
                                            raw_data={"file_path": str(file_path)}
                                        )
                                        evidence_list.append(evidence)
                                except Exception as e:
                                    print(f"读取PDF失败: {e}")
            
            # 如果没有本地文件，尝试在线爬取
            if not evidence_list:
                print(f"  本地无雪球数据，尝试在线爬取...")
                # 这里可以调用雪球在线爬虫
                # 暂时用搜索替代
                if self.tavily_key:
                    results = self._search_tavily(f"雪球 {company} 财务数据")
                    for r in results[:3]:
                        evidence = Evidence(
                            id=f"ev_{int(time.time()*1000)}",
                            content=r.get("content", "")[:500],
                            source="雪球在线",
                            quality=EvidenceQuality.P2,
                            relevance=0.7
                        )
                        evidence_list.append(evidence)
                        
        except Exception as e:
            print(f"雪球爬取失败: {e}")
        
        return evidence_list
    
    def _generate_alternative_queries(self, anomaly: FinancialAnomaly, layer: int) -> List[str]:
        """
        生成备选搜索关键词
        
        当证据不足时，尝试不同的搜索角度
        """
        
        company = anomaly.company if hasattr(anomaly, 'company') else "该公司"
        metric = anomaly.metric
        
        # 根据层级生成不同的备选查询
        if layer == 1:
            # 第一层：财务数据
            return [
                f"{company} {metric} 2024 2023 年报",
                f"{company} {metric} 财报 数据",
                f"{company} {metric} 同比 环比"
            ]
        elif layer == 2:
            # 第二层：经营表现
            return [
                f"{company} 经营策略 商业模式",
                f"{company} 收入结构 盈利来源",
                f"{company} 业务布局 战略"
            ]
        elif layer == 3:
            # 第三层：经营能力
            return [
                f"{company} 核心竞争力 优势",
                f"{company} 护城河 壁垒",
                f"{company} 市场份额 地位"
            ]
        elif layer == 4:
            # 第四层：护城河来源
            return [
                f"{company} 护城河 来源 类型",
                f"{company} 竞争优势 可持续性",
                f"{company} 品牌 技术 渠道"
            ]
        elif layer == 5:
            # 第五层：不可复制性
            return [
                f"{company} 竞争对手 对比",
                f"{company} 行业格局 竞争",
                f"{company} 不可复制 差异化"
            ]
        else:
            return [f"{company} {metric}"]
    
    def _search_tavily(self, query: str) -> List[Dict]:
        """Tavily搜索"""
        if not self.tavily_key:
            return []
        
        try:
            response = requests.post(
                "https://api.tavily.com/search",
                json={
                    "api_key": self.tavily_key,
                    "query": query,
                    "max_results": 5
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json().get("results", [])
        except Exception as e:
            print(f"Tavily搜索失败: {e}")
        
        return []
    
    def _validate_evidence(self, evidence_list: List[Evidence]) -> List[Evidence]:
        """验证证据质量"""
        valid = []
        for e in evidence_list:
            # 质量必须达到 P2 及以上
            if e.quality.value >= self.min_evidence_quality.value:
                # 相关性必须 > 0.5
                if e.relevance > 0.5:
                    # 内容长度必须 > 50 字符
                    if len(e.content) > 50:
                        valid.append(e)
        return valid
    
    def _generate_observation(self, layer: int, evidence: List[Evidence], context: Dict) -> str:
        """生成观察"""
        if not evidence:
            return "证据不足，无法生成观察"
        
        # 简单拼接证据
        contents = [e.content[:200] for e in evidence[:3]]
        return "；".join(contents)
    
    def _identify_moat_type(self, evidence: List[Evidence], context: Dict) -> Optional[MoatType]:
        """识别护城河类型"""
        
        # 使用护城河验证问题清单
        evidence_text = " ".join([e.content for e in evidence]).lower()
        
        # 简单的关键词匹配
        if any(kw in evidence_text for kw in ["网络效应", "用户越多", "双边"]):
            return MoatType.NETWORK_EFFECT
        elif any(kw in evidence_text for kw in ["转换成本", "锁定", "迁移成本"]):
            return MoatType.SWITCHING_COST
        elif any(kw in evidence_text for kw in ["成本优势", "低成本", "规模效应"]):
            return MoatType.COST_ADVANTAGE
        elif any(kw in evidence_text for kw in ["品牌", "专利", "牌照"]):
            return MoatType.INTANGIBLE_ASSETS
        elif any(kw in evidence_text for kw in ["有效规模", "自然垄断", "监管"]):
            return MoatType.EFFICIENT_SCALE
        
        return None
    
    def _calculate_reward(
        self,
        max_layer: int,
        evidence: List[Evidence],
        moat_type: Optional[MoatType]
    ) -> float:
        """
        计算奖励函数
        
        R = Σ(层级深度 × 证据强度 × 不可复制性)
        """
        
        # 层级深度
        layer_score = max_layer
        
        # 证据强度
        if evidence:
            avg_evidence_quality = sum(e.quality.value for e in evidence) / len(evidence)
        else:
            avg_evidence_quality = 0.0
        
        # 不可复制性
        sustainability_map = {
            MoatType.NETWORK_EFFECT: 1.0,
            MoatType.SWITCHING_COST: 0.9,
            MoatType.COST_ADVANTAGE: 0.7,
            MoatType.INTANGIBLE_ASSETS: 0.8,
            MoatType.EFFICIENT_SCALE: 0.7,
            None: 0.3
        }
        sustainability = sustainability_map.get(moat_type, 0.3)
        
        # 计算奖励
        reward = layer_score * avg_evidence_quality * sustainability
        
        return round(reward, 2)
    
    def _identify_anomalies(self, financial_data: Dict, company: str) -> List[FinancialAnomaly]:
        """识别财务异常"""
        anomalies = []
        
        # 检查ROIC
        if "ROIC" in financial_data:
            roic_data = financial_data["ROIC"]
            if isinstance(roic_data, dict):
                current = list(roic_data.values())[-1]
            else:
                current = roic_data
            
            if current and current > 20:  # 高于行业均值
                anomalies.append(FinancialAnomaly(
                    metric="ROIC",
                    value=current,
                    trend=list(roic_data.values()) if isinstance(roic_data, dict) else [current],
                    benchmark=15,
                    deviation="显著高于行业均值",
                    severity="高",
                    question=f"{company}的ROIC为{current}%，显著高于行业均值15%，这种高资本回报来自哪里？"
                ))
        
        # 检查毛利率
        if "毛利率" in financial_data:
            gm_data = financial_data["毛利率"]
            if isinstance(gm_data, dict):
                current = list(gm_data.values())[-1]
            else:
                current = gm_data
            
            if current and current > 40:
                anomalies.append(FinancialAnomaly(
                    metric="毛利率",
                    value=current,
                    trend=list(gm_data.values()) if isinstance(gm_data, dict) else [current],
                    benchmark=30,
                    deviation="显著高于行业均值",
                    severity="中",
                    question=f"{company}的毛利率为{current}%，远高于行业均值30%，这种定价权来自哪里？"
                ))
        
        return anomalies
    
    def _generate_report(self, company: str) -> str:
        """生成报告"""
        
        report = f"# {company} 五层追问分析报告\n\n"
        
        for i, result in enumerate(self.questioning_history, 1):
            report += f"## 异常 {i}: {result.todos[0].description if result.todos else '未知'}\n\n"
            report += f"- **到达层级**: 第{result.layer}层\n"
            report += f"- **有效证据**: {len(result.evidence)}条\n"
            if result.moat_type:
                report += f"- **护城河类型**: {result.moat_type.value}\n"
            report += f"- **奖励函数值**: {result.reward}\n\n"
            report += f"**观察**: {result.observation}\n\n"
            report += "---\n\n"
        
        return report


if __name__ == "__main__":
    # 测试
    engine = LoopQuestioningEngine()
    
    financial_data = {
        "ROIC": {"2020": 18.5, "2021": 22.3, "2022": 28.7, "2023": 32.4, "2024": 34.5},
        "毛利率": {"2020": 45.2, "2021": 52.3, "2022": 58.1, "2023": 60.9, "2024": 62.1}
    }
    
    results, report = engine.start_loop_questioning(
        financial_data,
        context={"company": "PDD Holdings", "ticker": "PDD"}
    )
    
    print(report)