"""
V7.0 护城河追问引擎

核心理念：
- 五层追问模型：财务数据→经营表现→经营能力→护城河来源→不可复制性
- 每层追问产生ToDo，驱动数据收集
- 奖励函数驱动深度分析

护城河五大类型（巴菲特/晨星分类）：
1. 网络效应
2. 转换成本
3. 成本优势
4. 无形资产
5. 有效规模
"""

import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.llm_client import LLMClient
from core.todo_executor import ToDoExecutor, ToDoTask, ToDoType


class MoatType(Enum):
    """护城河类型"""
    NETWORK_EFFECT = "网络效应"
    SWITCHING_COST = "转换成本"
    COST_ADVANTAGE = "成本优势"
    INTANGIBLE_ASSETS = "无形资产"
    EFFICIENT_SCALE = "有效规模"
    UNKNOWN = "未识别"


class QuestioningLayer(Enum):
    """追问层级"""
    FINANCIAL_DATA = 1  # 财务数据
    BUSINESS_PERFORMANCE = 2  # 经营表现
    BUSINESS_CAPABILITY = 3  # 经营能力
    MOAT_SOURCE = 4  # 护城河来源
    UNREPLICABILITY = 5  # 不可复制性


@dataclass
class QuestioningResult:
    """追问结果"""
    layer: int
    question: str
    observation: str
    evidence: List[Dict] = field(default_factory=list)
    todos: List[Dict] = field(default_factory=list)
    insight: str = ""
    moat_type: Optional[MoatType] = None
    sustainability: str = ""  # 强/中/弱


@dataclass
class MoatAssessment:
    """护城河评估"""
    moat_type: MoatType
    description: str
    evidence: List[Dict]
    sustainability: str  # 强/中/弱
    unreplicable_reason: str
    competitors_cannot_copy: List[str]


# 护城河验证问题库
MOAT_VERIFICATION_QUESTIONS = {
    MoatType.NETWORK_EFFECT: {
        "name": "网络效应",
        "key_question": "用户越多，价值是否越大？",
        "financial_indicators": ["获客成本趋势", "用户留存率", "GMV增速"],
        "verification_questions": [
            "新用户加入是否让所有用户受益？",
            "是双边网络效应还是单边网络效应？",
            "临界规模是多少？是否已达到？",
            "网络效应是否会随规模扩大而增强？"
        ],
        "competitor_questions": [
            "竞争对手是否也在构建网络效应？",
            "网络效应是否存在跨平台迁移的可能？"
        ]
    },
    MoatType.SWITCHING_COST: {
        "name": "转换成本",
        "key_question": "客户换掉我们会损失什么？",
        "financial_indicators": ["客户留存率", "续约率", "提价能力"],
        "verification_questions": [
            "转换成本是财务性的还是运营性的？",
            "转换成本随时间增加还是减少？",
            "新客户是否面临同样的转换成本？",
            "转换成本是否构成实质性壁垒？"
        ],
        "competitor_questions": [
            "竞争对手是否提供迁移工具？",
            "是否存在替代方案降低转换成本？"
        ]
    },
    MoatType.COST_ADVANTAGE: {
        "name": "成本优势",
        "key_question": "低成本来自规模、资源、地理位置还是流程？",
        "financial_indicators": ["毛利率", "成本结构", "单位成本趋势"],
        "verification_questions": [
            "成本优势来源是否可持续？",
            "竞争对手能否复制这个成本结构？",
            "成本优势是否会随规模扩大而增强？",
            "成本优势是否依赖独特的资源或地理位置？"
        ],
        "competitor_questions": [
            "竞争对手的成本结构如何？",
            "新进入者能否以更低成本进入？"
        ]
    },
    MoatType.INTANGIBLE_ASSETS: {
        "name": "无形资产",
        "key_question": "这个无形资产有定价权吗？",
        "financial_indicators": ["溢价定价能力", "品牌价值", "专利数量"],
        "verification_questions": [
            "品牌/专利能带来定价权吗？",
            "无形资产的保护期多久？",
            "监管准入是否可持续？",
            "无形资产是否构成核心壁垒？"
        ],
        "competitor_questions": [
            "竞争对手是否有类似的无形资产？",
            "无形资产是否会被技术进步淘汰？"
        ]
    },
    MoatType.EFFICIENT_SCALE: {
        "name": "有效规模",
        "key_question": "新进入者会破坏均衡吗？",
        "financial_indicators": ["ROIC", "竞争者数量", "市场集中度"],
        "verification_questions": [
            "市场规模是否限制了竞争者数量？",
            "新进入者的资本门槛是什么？",
            "现有竞争者之间是否存在默契？",
            "新进入者能否获得足够的市场份额？"
        ],
        "competitor_questions": [
            "市场是否有增长空间吸引新进入者？",
            "监管是否会放松准入限制？"
        ]
    }
}


class MoatQuestioningEngine:
    """护城河追问引擎"""
    
    LAYER_QUESTIONS = {
        1: "财务数据为什么是这样？",
        2: "经营表现为什么是这样？",
        3: "经营能力来源是什么？",
        4: "护城河是哪个类型？为什么？",
        5: "这个优势为什么竞争对手无法复制？"
    }
    
    LAYER_DATA_SOURCES = {
        1: ["AkShare", "雪球", "年报", "Tavily", "Exa"],
        2: ["AkShare", "雪球", "Exa", "Tavily"],
        3: ["雪球专栏", "Tavily", "本地数据", "Exa"],
        4: ["AkShare", "Exa", "雪球", "本地数据", "Tavily"],
        5: ["Exa", "Tavily", "本地数据"]
    }
    
    def __init__(self, llm_client: LLMClient = None):
        self.llm = llm_client or LLMClient()
        self.todo_executor = ToDoExecutor(self.llm)
        self.questioning_history: List[QuestioningResult] = []
    
    def start_questioning(
        self, 
        financial_data: Dict[str, Any],
        max_iterations: int = 10,
        context: Dict = None
    ) -> List[QuestioningResult]:
        """
        开始五层追问
        
        Args:
            financial_data: 财务数据
            max_iterations: 最大迭代次数
            context: 执行上下文
        
        Returns:
            List[QuestioningResult]: 追问历史
        """
        
        self.questioning_history = []
        context = context or {}
        context["financial_data"] = financial_data
        
        current_layer = 1
        iteration = 0
        consecutive_no_evidence = 0
        
        # 第1层：财务数据
        result = self._question_layer_1(financial_data, context)
        self.questioning_history.append(result)
        
        # 后续层：循环追问
        while current_layer < 5 and iteration < max_iterations:
            iteration += 1
            print(f"\n  [迭代 {iteration}] 当前层: {current_layer}")
            
            # 获取上一层的结果
            prev_result = self.questioning_history[-1]
            
            # 如果没有ToDo，说明已收敛
            if not prev_result.todos:
                print(f"    无待执行ToDo，追问收敛")
                break
            
            # 执行ToDo获取新证据
            print(f"    执行 {len(prev_result.todos)} 个ToDo...")
            new_evidence = self._execute_todos(prev_result.todos, context)
            
            # 验证证据质量
            valid_evidence = [e for e in new_evidence if e.get("quality") in ["P0", "P1", "P2"]]
            
            if valid_evidence:
                consecutive_no_evidence = 0
                print(f"    获取 {len(valid_evidence)} 条有效证据")
                
                # 进入下一层
                current_layer += 1
                result = self._question_layer(
                    layer=current_layer,
                    prev_result=prev_result,
                    new_evidence=valid_evidence,
                    context=context
                )
                self.questioning_history.append(result)
            else:
                consecutive_no_evidence += 1
                print(f"    未获取有效证据 ({consecutive_no_evidence}/3)")
                
                # 连续3次无证据，终止
                if consecutive_no_evidence >= 3:
                    print(f"    连续3次无有效证据，终止追问")
                    break
        
        # 第5层：不可复制性（如果到达）
        if current_layer >= 4:
            result = self._question_layer_5(self.questioning_history[-1], context)
            if result:
                self.questioning_history.append(result)
        
        return self.questioning_history
    
    def _question_layer_1(self, financial_data: Dict, context: Dict = None) -> QuestioningResult:
        """第1层追问：财务数据 - 使用LLM增强"""
        
        # 发现财务异常
        anomalies = self._detect_financial_anomalies(financial_data)
        
        if not anomalies:
            return QuestioningResult(
                layer=1,
                question="财务数据无明显异常",
                observation="财务数据整体正常",
                todos=[]
            )
        
        # 使用LLM生成追问
        primary_anomaly = anomalies[0]
        
        # 构建提示词
        prompt = f"""请针对以下财务异常生成深度追问和观察描述。

## 财务异常
- 指标：{primary_anomaly['metric']}
- 数值：{primary_anomaly['value']}
- 描述：{primary_anomaly['description']}

## 要求
1. 生成一个深度追问，不要只问"为什么"，要指向具体的经营层面
2. 生成一个观察描述，说明这个异常可能反映的经营特点

请按以下格式输出：
追问: xxx
观察: xxx"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            
            # 解析LLM返回
            question = primary_anomaly['metric']
            observation = primary_anomaly["description"]
            
            for line in response.split("\n"):
                if line.startswith("追问:"):
                    question = line.replace("追问:", "").strip()
                elif line.startswith("观察:"):
                    observation = line.replace("观察:", "").strip()
                    
        except Exception as e:
            question = f"{primary_anomaly['metric']} {primary_anomaly['value']}，为什么？"
            observation = primary_anomaly["description"]
        
        return QuestioningResult(
            layer=1,
            question=question,
            observation=observation,
            todos=[
                {
                    "type": "数据验证",
                    "task": f"验证{primary_anomaly['metric']}的数据准确性",
                    "data_sources": self.LAYER_DATA_SOURCES[1]
                },
                {
                    "type": "数据检索",
                    "task": f"获取{primary_anomaly['metric']}的历史趋势",
                    "data_sources": self.LAYER_DATA_SOURCES[1]
                }
            ]
        )
    
    def _question_layer(
        self, 
        layer: int, 
        prev_result: QuestioningResult,
        new_evidence: List[Dict],
        context: Dict = None
    ) -> QuestioningResult:
        """通用层追问"""
        
        question = self.LAYER_QUESTIONS.get(layer, "")
        
        # 根据证据生成洞察
        insight = self._generate_insight(layer, new_evidence)
        
        # 生成下一层ToDo
        todos = self._generate_todos_for_layer(layer, insight)
        
        result = QuestioningResult(
            layer=layer,
            question=question,
            observation=insight,
            evidence=new_evidence,
            todos=todos
        )
        
        # 第4层：识别护城河类型
        if layer == 4:
            result.moat_type = self._identify_moat_type(new_evidence)
        
        return result
    
    def _question_layer_5(self, prev_result: QuestioningResult, context: Dict = None) -> Optional[QuestioningResult]:
        """第5层追问：不可复制性"""
        
        if not prev_result.moat_type:
            return None
        
        moat_type = prev_result.moat_type
        moat_info = MOAT_VERIFICATION_QUESTIONS.get(moat_type, {})
        
        # 生成竞争分析ToDo
        todos = [
            {
                "type": "深度分析",
                "task": f"分析竞争对手为何无法复制{moat_info.get('name', '')}",
                "data_sources": self.LAYER_DATA_SOURCES[5]
            },
            {
                "type": "数据检索",
                "task": "获取竞争对手的业务模式和财务数据",
                "data_sources": self.LAYER_DATA_SOURCES[5]
            }
        ]
        
        return QuestioningResult(
            layer=5,
            question=self.LAYER_QUESTIONS[5],
            observation=f"护城河类型：{moat_info.get('name', '')}",
            todos=todos,
            moat_type=moat_type
        )
    
    def _detect_financial_anomalies(self, data: Dict) -> List[Dict]:
        """检测财务异常"""
        
        anomalies = []
        
        # 字段名映射（支持多种命名方式）
        roic_keys = ["ROIC", "roic", "投入资本回报率"]
        roe_keys = ["ROE", "ROE_AVG", "roe", "净资产收益率"]
        margin_keys = ["毛利率", "GROSS_PROFIT_RATIO", "gross_profit_ratio", "GrossMargin"]
        revenue_keys = ["营收", "OPERATE_INCOME", "revenue", "营业收入"]
        profit_keys = ["净利润", "PARENT_HOLDER_NETPROFIT", "net_profit", "NetIncome"]
        cash_cycle_keys = ["现金周转周期", "cash_conversion_cycle"]
        
        # ROIC 异常
        for key in roic_keys:
            if key in data:
                roic = data[key]
                if isinstance(roic, (int, float)) and roic > 30:
                    anomalies.append({
                        "metric": "ROIC",
                        "value": f"{roic:.1f}%",
                        "description": f"ROIC {roic:.1f}% 显著高于行业均值（约15-20%），资本效率极高",
                        "severity": "高"
                    })
                break
        
        # ROE 异常
        for key in roe_keys:
            if key in data:
                roe = data[key]
                if isinstance(roe, (int, float)) and roe > 30:
                    anomalies.append({
                        "metric": "ROE",
                        "value": f"{roe:.1f}%",
                        "description": f"ROE {roe:.1f}% 显著高于行业均值，股东回报优秀",
                        "severity": "高"
                    })
                break
        
        # 毛利率异常
        for key in margin_keys:
            if key in data:
                margin = data[key]
                if isinstance(margin, (int, float)) and margin > 50:
                    anomalies.append({
                        "metric": "毛利率",
                        "value": f"{margin:.1f}%",
                        "description": f"毛利率 {margin:.1f}% 显著高于行业均值，定价权强或成本控制优秀",
                        "severity": "中"
                    })
                break
        
        # 营收规模
        for key in revenue_keys:
            if key in data:
                revenue = data[key]
                if isinstance(revenue, (int, float)):
                    # 转换为亿元
                    if revenue > 1e11:  # 超过1000亿
                        revenue_bn = revenue / 1e8
                        anomalies.append({
                            "metric": "营收规模",
                            "value": f"{revenue_bn:.0f}亿元",
                            "description": f"营收规模 {revenue_bn:.0f} 亿元，行业龙头级别",
                            "severity": "中"
                        })
                break
        
        # 净利润规模
        for key in profit_keys:
            if key in data:
                profit = data[key]
                if isinstance(profit, (int, float)):
                    if profit > 1e10:  # 超过100亿
                        profit_bn = profit / 1e8
                        anomalies.append({
                            "metric": "净利润规模",
                            "value": f"{profit_bn:.0f}亿元",
                            "description": f"净利润 {profit_bn:.0f} 亿元，盈利能力强",
                            "severity": "中"
                        })
                break
        
        # 现金周转周期异常
        for key in cash_cycle_keys:
            if key in data:
                cycle = data[key]
                if isinstance(cycle, (int, float)) and cycle < 0:
                    anomalies.append({
                        "metric": "现金周转周期",
                        "value": f"{cycle}天",
                        "description": f"现金周转周期为负（{cycle}天），对供应链有强议价权",
                        "severity": "高"
                    })
                break
        
        return anomalies
    
    def _generate_insight(self, layer: int, evidence: List[Dict]) -> str:
        """根据证据生成洞察 - 使用LLM增强"""
        
        if not evidence:
            return "需要更多证据"
        
        # 准备证据文本
        evidence_text = "\n".join([
            f"- [{e.get('source', '未知')}] {e.get('content', str(e))[:200]}"
            for e in evidence[:5]
        ])
        
        # 构建提示词
        layer_names = {
            1: "财务数据层",
            2: "经营表现层",
            3: "经营能力层",
            4: "护城河来源层",
            5: "不可复制性层"
        }
        
        prompt = f"""请基于以下证据，在第{layer}层（{layer_names.get(layer, '')}）生成深度洞察。

## 证据
{evidence_text}

## 要求
1. 用2-3句话概括核心发现
2. 指出关键的经营特点或竞争优势
3. 避免空泛描述，要有具体洞察
4. 如果发现异常，说明可能的原因

请直接输出洞察，不要加标题或其他格式。"""

        try:
            insight = self.llm.chat([{"role": "user", "content": prompt}])
            return insight.strip()
        except Exception as e:
            # LLM失败时，返回证据摘要
            insights = []
            for e_item in evidence[:3]:
                if isinstance(e_item, dict):
                    insights.append(e_item.get("content", str(e_item))[:100])
            return "; ".join(insights)
    
    def _generate_todos_for_layer(self, layer: int, insight: str) -> List[Dict]:
        """为指定层生成ToDo"""
        
        data_sources = self.LAYER_DATA_SOURCES.get(layer, [])
        
        if layer == 2:
            return [
                {
                    "type": "数据检索",
                    "task": "获取行业对比数据",
                    "data_sources": data_sources
                },
                {
                    "type": "分析深化",
                    "task": "分析经营指标变化的驱动因素",
                    "data_sources": data_sources
                }
            ]
        elif layer == 3:
            return [
                {
                    "type": "数据检索",
                    "task": "获取业务模式相关信息",
                    "data_sources": data_sources
                },
                {
                    "type": "深度分析",
                    "task": "识别核心经营能力",
                    "data_sources": data_sources
                }
            ]
        elif layer == 4:
            return [
                {
                    "type": "数据检索",
                    "task": "获取竞争对手数据进行对比",
                    "data_sources": data_sources
                },
                {
                    "type": "深度分析",
                    "task": "验证护城河类型",
                    "data_sources": data_sources
                }
            ]
        
        return []
    
    def _identify_moat_type(self, evidence: List[Dict]) -> MoatType:
        """根据证据识别护城河类型 - 使用LLM增强"""
        
        if not evidence:
            return MoatType.UNKNOWN
        
        # 准备证据文本
        evidence_text = "\n".join([
            f"- {e.get('content', str(e))[:200]}"
            for e in evidence[:5]
        ])
        
        # 构建提示词
        moat_options = "\n".join([
            f"{i+1}. {mt.value}: {MOAT_VERIFICATION_QUESTIONS.get(mt, {}).get('key_question', '')}"
            for i, mt in enumerate([
                MoatType.NETWORK_EFFECT,
                MoatType.SWITCHING_COST,
                MoatType.COST_ADVANTAGE,
                MoatType.INTANGIBLE_ASSETS,
                MoatType.EFFICIENT_SCALE
            ])
        ])
        
        prompt = f"""请根据以下证据，判断该公司的护城河类型。

## 证据
{evidence_text}

## 护城河类型选项
{moat_options}

## 要求
1. 分析证据中反映的竞争优势本质
2. 选择最符合的护城河类型
3. 如果无法确定，选择"未识别"

请只输出类型名称（网络效应/转换成本/成本优势/无形资产/有效规模/未识别），不要输出其他内容。"""

        try:
            response = self.llm.chat([{"role": "user", "content": prompt}])
            response = response.strip()
            
            # 解析LLM返回的类型
            type_mapping = {
                "网络效应": MoatType.NETWORK_EFFECT,
                "转换成本": MoatType.SWITCHING_COST,
                "成本优势": MoatType.COST_ADVANTAGE,
                "无形资产": MoatType.INTANGIBLE_ASSETS,
                "有效规模": MoatType.EFFICIENT_SCALE,
                "未识别": MoatType.UNKNOWN
            }
            
            for name, moat_type in type_mapping.items():
                if name in response:
                    return moat_type
            
            return MoatType.UNKNOWN
            
        except Exception as e:
            # LLM失败时，使用关键词匹配
            evidence_text_lower = " ".join(str(e) for e in evidence).lower()
            
            if "网络效应" in evidence_text_lower or "用户越多" in evidence_text_lower:
                return MoatType.NETWORK_EFFECT
            elif "转换成本" in evidence_text_lower or "锁定" in evidence_text_lower:
                return MoatType.SWITCHING_COST
            elif "成本优势" in evidence_text_lower or "低成本" in evidence_text_lower:
                return MoatType.COST_ADVANTAGE
            elif "品牌" in evidence_text_lower or "专利" in evidence_text_lower:
                return MoatType.INTANGIBLE_ASSETS
            elif "有效规模" in evidence_text_lower or "自然垄断" in evidence_text_lower:
                return MoatType.EFFICIENT_SCALE
            
            return MoatType.UNKNOWN
    
    def _execute_todos(self, todos: List[Dict], context: Dict = None) -> List[Dict]:
        """执行ToDo"""
        
        if not todos:
            return []
        
        context = context or {}
        results = []
        
        for todo_dict in todos:
            # 转换为ToDoTask
            todo = ToDoTask(
                task_id=f"todo_{datetime.now().strftime('%Y%m%d%H%M%S')}",
                task_type=ToDoType.DATA_RETRIEVAL,  # 默认类型
                description=todo_dict.get("task", ""),
                priority=todo_dict.get("priority", "中"),
                data_sources=todo_dict.get("data_sources", ["Tavily", "Exa"]),
                expected_output="相关数据"
            )
            
            # 构建包含公司名称的上下文
            todo_context = {
                **context,
                "company": context.get("company", "PDD Holdings"),
                "ticker": context.get("ticker", "PDD")
            }
            
            # 执行ToDo
            evidence = self.todo_executor.execute_todo(todo, todo_context)
            
            results.append({
                "content": evidence.content,
                "source": evidence.source,
                "quality": evidence.quality,
                "relevance": evidence.relevance
            })
        
        return results
    
    def calculate_reward(self) -> float:
        """
        计算奖励函数值
        
        R = Σ(层级深度 × 证据强度 × 不可复制性)
        """
        
        total_reward = 0.0
        
        for result in self.questioning_history:
            # 层级深度
            layer_score = result.layer
            
            # 证据强度（基于证据数量和质量）
            evidence_score = min(len(result.evidence) * 0.2, 1.0)
            
            # 不可复制性（第5层才有）
            sustainability_score = 0.0
            if result.layer == 5:
                sustainability_map = {"强": 1.0, "中": 0.7, "弱": 0.4}
                sustainability_score = sustainability_map.get(result.sustainability, 0.1)
            else:
                sustainability_score = 0.5  # 默认值
            
            reward = layer_score * evidence_score * sustainability_score
            total_reward += reward
        
        return total_reward
    
    def generate_questioning_report(self) -> str:
        """生成追问报告"""
        
        report = "# 护城河追问报告\n\n"
        report += f"**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        # 追问历史 - 简洁版
        report += "## 📋 五层追问历史\n\n"
        
        for result in self.questioning_history:
            layer_name = {
                1: "财务数据",
                2: "经营表现",
                3: "经营能力",
                4: "护城河来源",
                5: "不可复制性"
            }.get(result.layer, f"第{result.layer}层")
            
            report += f"### 第{result.layer}层：{layer_name}\n\n"
            
            # 问题 - 截断到50字符
            question = result.question[:80] + "..." if len(result.question) > 80 else result.question
            report += f"**追问**: {question}\n\n"
            
            # 观察 - 取第一句完整的话
            observation = result.observation.strip()
            # 按句号分割，取前两句
            sentences = observation.replace('。', '。\n').split('\n')
            key_observation = '。'.join([s.strip() for s in sentences[:2] if s.strip()])
            if len(key_observation) > 200:
                key_observation = key_observation[:200] + "..."
            report += f"**核心发现**: {key_observation}\n\n"
            
            if result.moat_type:
                report += f"**护城河类型**: {result.moat_type.value}\n\n"
        
        # 奖励函数值
        reward = self.calculate_reward()
        report += f"## 📊 奖励函数值\n\n"
        report += f"**总奖励**: {reward:.2f}\n\n"
        
        return report


# 测试
if __name__ == "__main__":
    engine = MoatQuestioningEngine()
    
    # 测试财务数据
    financial_data = {
        "ROIC": 42.0,
        "毛利率": 60.0,
        "现金周转周期": -127
    }
    
    results = engine.start_questioning(financial_data)
    
    print(f"追问层数: {len(results)}")
    print(f"奖励函数值: {engine.calculate_reward():.2f}")
    
    report = engine.generate_questioning_report()
    print(report)