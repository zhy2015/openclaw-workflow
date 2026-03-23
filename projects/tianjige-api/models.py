"""
天机阁 API - 数据模型层 (models.py)
包含 SQLite 数据库初始化和 Pydantic 请求/响应模型
"""

import sqlite3
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from enum import Enum


# ============================================================================
# 数据库初始化
# ============================================================================

def init_database(db_path: str = "./tianjige.db") -> sqlite3.Connection:
    """
    初始化 SQLite 数据库，创建必要的表结构
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    
    cursor = conn.cursor()
    
    # 通用玄学记录表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS mystical_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            module_type TEXT NOT NULL,
            input_params TEXT NOT NULL,
            result_json TEXT NOT NULL,
            user_ip TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 熔断计数表（用于IP限流）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS rate_limit (
            ip TEXT PRIMARY KEY,
            count INTEGER DEFAULT 0,
            window_start DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 创建索引
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_module_type ON mystical_readings(module_type)
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_created_at ON mystical_readings(created_at)
    """)
    
    conn.commit()
    return conn


def save_reading(conn: sqlite3.Connection, module_type: str, 
                 input_params: dict, result_json: dict, user_ip: str = None):
    """
    保存占卜记录到数据库
    """
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO mystical_readings (module_type, input_params, result_json, user_ip)
        VALUES (?, ?, ?, ?)
        """,
        (module_type, json.dumps(input_params, ensure_ascii=False),
         json.dumps(result_json, ensure_ascii=False), user_ip)
    )
    conn.commit()
    return cursor.lastrowid


# ============================================================================
# 枚举类型
# ============================================================================

class ModuleType(str, Enum):
    """模块类型枚举"""
    TAROT = "tarot"
    DREAM = "dream"
    PLUM_BLOSSOM = "plum_blossom"
    MARRIAGE = "marriage"


class CardPosition(str, Enum):
    """塔罗牌阵位置"""
    PAST_PRESENT_FUTURE = "past_present_future"
    SITUATION_ACTION_OUTCOME = "situation_action_outcome"
    MIND_BODY_SPIRIT = "mind_body_spirit"
    CELTIC_CROSS = "celtic_cross"


class AttachmentStyle(str, Enum):
    """依恋类型"""
    SECURE = "安全型"
    ANXIOUS = "焦虑型"
    AVOIDANT = "回避型"
    DISORGANIZED = "混乱型"


# ============================================================================
# 塔罗牌占卜模型
# ============================================================================

class TarotCardInsight(BaseModel):
    """单张塔罗牌洞察"""
    card: str = Field(..., description="牌名，如'愚者正位'")
    projection: str = Field(..., description="这张牌反映的心理投射")
    shadow: str = Field(..., description="阴影面/恐惧")
    archetype: Optional[str] = Field(None, description="激活的荣格原型")


class TarotRequest(BaseModel):
    """塔罗牌占卜请求"""
    question: str = Field(..., min_length=1, max_length=500, 
                          description="用户想问的问题")
    cards: List[str] = Field(..., min_items=1, max_items=10,
                             description="抽到的牌列表，如['愚者正位', '宝剑三逆位']")
    spread_type: CardPosition = Field(default=CardPosition.PAST_PRESENT_FUTURE,
                                      description="牌阵类型")
    
    @validator('cards')
    def validate_cards(cls, v):
        if not v:
            raise ValueError('至少需要一张牌')
        return v


class TarotResult(BaseModel):
    """塔罗牌占卜结果"""
    title: str = Field(..., description="结果标题")
    narrative: str = Field(..., description="叙事风格的主分析")
    card_insights: List[TarotCardInsight] = Field(..., description="每张牌的洞察")
    core_conflict: str = Field(..., description="核心冲突描述")
    actionable_advice: List[str] = Field(..., min_items=1, description="具体建议")
    psychological_note: str = Field(..., description="心理学角度补充")


class TarotResponse(BaseModel):
    """塔罗牌占卜完整响应"""
    success: bool = True
    module: str = "tarot"
    result: TarotResult
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 周公解梦模型
# ============================================================================

class DreamSymbol(BaseModel):
    """梦境关键意象"""
    symbol: str = Field(..., description="意象名称，如'水/下沉'")
    traditional: str = Field(..., description="传统解梦符号意义")
    psychological: str = Field(..., description="现代心理学解读")
    message: str = Field(..., description="这个意象想传达的信息")


class DreamRequest(BaseModel):
    """周公解梦请求"""
    dream_desc: str = Field(..., min_length=10, max_length=2000,
                            description="梦境描述")
    background: Optional[str] = Field(None, max_length=2000,
                                      description="近期现实经历/背景上下文")
    
    @validator('dream_desc')
    def validate_dream(cls, v):
        if len(v.strip()) < 10:
            raise ValueError('梦境描述至少需要10个字符')
        return v.strip()


class DreamResult(BaseModel):
    """周公解梦结果"""
    title: str = Field(..., description="结果标题")
    narrative: str = Field(..., description="叙事主分析")
    key_symbols: List[DreamSymbol] = Field(..., description="关键意象解析")
    ignored_reality: str = Field(..., description="被忽略的现实问题")
    subconscious_message: str = Field(..., description="潜意识的核心信息")
    actionable_advice: List[str] = Field(..., min_items=1, description="行动建议")
    stress_indicator: str = Field(..., description="压力状态说明")


class DreamResponse(BaseModel):
    """周公解梦完整响应"""
    success: bool = True
    module: str = "dream"
    result: DreamResult
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 梅花易数模型
# ============================================================================

class HexagramInfo(BaseModel):
    """卦象信息"""
    main: str = Field(..., description="本卦名称")
    mutual: str = Field(..., description="互卦名称")
    changed: str = Field(..., description="变卦名称")


class PowerDynamics(BaseModel):
    """力量对比分析"""
    your_position: str = Field(..., description="体方（你）的现状")
    opportunity_position: str = Field(..., description="用方（机会/环境）的现状")
    relationship: str = Field(..., description="生克关系解读")


class TimingAssessment(BaseModel):
    """时机评估"""
    favorable: bool = Field(..., description="当前是否 favorable")
    reason: str = Field(..., description="判断理由")
    wait_or_act: str = Field(..., pattern="^(wait|act)$", description="等待或行动")
    optimal_window: Optional[str] = Field(None, description="最佳时机")


class PlumBlossomRequest(BaseModel):
    """梅花易数请求"""
    question: str = Field(..., min_length=1, max_length=500,
                          description="求测事项")
    hexagrams: HexagramInfo = Field(..., description="卦象信息")
    changing_lines: List[int] = Field(default_factory=list,
                                      description="动爻位置列表")
    body_element: str = Field(..., description="体卦五行")
    use_element: str = Field(..., description="用卦五行")


class PlumBlossomResult(BaseModel):
    """梅花易数结果"""
    title: str = Field(..., description="结果标题")
    narrative: str = Field(..., description="局势分析叙事")
    situation_translation: str = Field(..., description="卦象翻译成现代情境")
    power_dynamics: PowerDynamics = Field(..., description="力量对比")
    timing_assessment: TimingAssessment = Field(..., description="时机评估")
    risk_analysis: List[str] = Field(..., min_items=1, description="风险点")
    actionable_advice: List[str] = Field(..., min_items=1, description="战略建议")


class PlumBlossomResponse(BaseModel):
    """梅花易数完整响应"""
    success: bool = True
    module: str = "plum_blossom"
    result: PlumBlossomResult
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 姻缘占卜/合婚匹配模型
# ============================================================================

class CompatibilityScore(BaseModel):
    """兼容度评分"""
    score: int = Field(..., ge=1, le=10, description="1-10分")
    note: str = Field(..., description="评分说明")


class CompatibilityMatrix(BaseModel):
    """兼容度矩阵"""
    emotional: CompatibilityScore = Field(..., description="情感维度")
    communication: CompatibilityScore = Field(..., description="沟通维度")
    values: CompatibilityScore = Field(..., description="价值观维度")


class CoreConflict(BaseModel):
    """核心冲突剖析"""
    description: str = Field(..., description="冲突描述")
    a_perspective: str = Field(..., description="A的视角")
    b_perspective: str = Field(..., description="B的视角")
    translation: str = Field(..., description="真实需求的翻译")


class OperatingManual(BaseModel):
    """相处说明书"""
    for_a: List[str] = Field(..., min_items=1, description="给A的建议")
    for_b: List[str] = Field(..., min_items=1, description="给B的建议")


class Verdict(BaseModel):
    """最终评估"""
    assessment: str = Field(..., description="综合评估")
    confidence: int = Field(..., ge=1, le=100, description="置信度1-100")
    key_work: str = Field(..., description="关键功课")


class PersonInfo(BaseModel):
    """个人信息"""
    name: str = Field(..., min_length=1, max_length=50, description="姓名")
    birth_info: Optional[str] = Field(None, description="出生信息")
    mbti: Optional[str] = Field(None, description="MBTI类型")
    attachment_style: Optional[AttachmentStyle] = Field(None, description="依恋类型")
    core_traits: str = Field(..., min_length=1, description="核心性格特征")


class MarriageRequest(BaseModel):
    """姻缘占卜/合婚匹配请求"""
    person_a_info: PersonInfo = Field(..., description="A的信息")
    person_b_info: PersonInfo = Field(..., description="B的信息")
    current_status: str = Field(..., min_length=1, description="当前关系状态")
    conflict_focus: Optional[str] = Field(None, description="主要冲突焦点")


class MarriageResult(BaseModel):
    """姻缘占卜/合婚匹配结果"""
    title: str = Field(..., description="结果标题")
    narrative: str = Field(..., description="叙事分析")
    compatibility_matrix: CompatibilityMatrix = Field(..., description="兼容度矩阵")
    core_conflict: CoreConflict = Field(..., description="核心冲突")
    attachment_dynamics: str = Field(..., description="依恋模式分析")
    operating_manual: OperatingManual = Field(..., description="相处说明书")
    emotional_value_guide: str = Field(..., description="情绪价值提供方法")
    verdict: Verdict = Field(..., description="最终评估")


class MarriageResponse(BaseModel):
    """姻缘占卜/合婚匹配完整响应"""
    success: bool = True
    module: str = "marriage"
    result: MarriageResult
    meta: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# 通用错误响应模型
# ============================================================================

class ErrorResponse(BaseModel):
    """错误响应"""
    success: bool = False
    error: str = Field(..., description="错误类型")
    message: str = Field(..., description="错误详情")
    retry_after: Optional[int] = Field(None, description="重试等待秒数")
