"""
天机阁 API - 主入口 (main.py)
FastAPI 应用，包含路由和熔断保护中间件
"""

import os
import sqlite3
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Request, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from models import (
    init_database, save_reading,
    TarotRequest, TarotResponse, TarotResult,
    DreamRequest, DreamResponse, DreamResult,
    PlumBlossomRequest, PlumBlossomResponse, PlumBlossomResult,
    MarriageRequest, MarriageResponse, MarriageResult,
    ErrorResponse, ModuleType
)
from prompts import get_prompt, build_user_input
from llm_client import call_llm, close_llm_client


# ============================================================================
# 配置
# ============================================================================

DB_PATH = os.getenv("DB_PATH", "./tianjige.db")
RATE_LIMIT_POINTS = int(os.getenv("RATE_LIMIT_POINTS", "10"))  # 10次
RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", "600"))  # 10分钟 = 600秒
PORT = int(os.getenv("PORT", "30001"))


# ============================================================================
# 数据库连接管理
# ============================================================================

db_connection: Optional[sqlite3.Connection] = None


def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    global db_connection
    if db_connection is None:
        db_connection = init_database(DB_PATH)
    return db_connection


# ============================================================================
# 熔断保护中间件
# ============================================================================

class RateLimiter:
    """
    基于 SQLite 的 IP 限流器
    每 RATE_LIMIT_WINDOW 秒最多 RATE_LIMIT_POINTS 次请求
    """
    
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def get_client_ip(self, request: Request) -> str:
        """获取客户端真实 IP"""
        # 优先从 X-Forwarded-For 获取（如果使用了反向代理）
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # 其次从 X-Real-IP 获取
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # 最后使用直接连接的 IP
        return request.client.host
    
    def check_rate_limit(self, ip: str) -> tuple[bool, Optional[int]]:
        """
        检查是否超过限流
        
        Returns:
            (是否允许, 重试等待秒数)
        """
        cursor = self.db.cursor()
        now = datetime.now()
        window_start = now - timedelta(seconds=RATE_LIMIT_WINDOW)
        
        # 清理过期的限流记录
        cursor.execute(
            "DELETE FROM rate_limit WHERE window_start < ?",
            (window_start,)
        )
        self.db.commit()
        
        # 查询当前 IP 的记录
        cursor.execute(
            "SELECT count, window_start FROM rate_limit WHERE ip = ?",
            (ip,)
        )
        row = cursor.fetchone()
        
        if row is None:
            # 新 IP，创建记录
            cursor.execute(
                "INSERT INTO rate_limit (ip, count, window_start) VALUES (?, 1, ?)",
                (ip, now)
            )
            self.db.commit()
            return True, None
        
        count, _ = row
        
        if count >= RATE_LIMIT_POINTS:
            # 超过限流，计算重试时间
            # 获取最早的请求时间
            cursor.execute(
                """
                SELECT MIN(window_start) FROM rate_limit WHERE ip = ?
                """,
                (ip,)
            )
            earliest = cursor.fetchone()[0]
            if earliest:
                earliest = datetime.fromisoformat(earliest) if isinstance(earliest, str) else earliest
                retry_after = int((earliest + timedelta(seconds=RATE_LIMIT_WINDOW) - now).total_seconds())
                retry_after = max(1, retry_after)
            else:
                retry_after = RATE_LIMIT_WINDOW
            return False, retry_after
        
        # 更新计数
        cursor.execute(
            "UPDATE rate_limit SET count = count + 1 WHERE ip = ?",
            (ip,)
        )
        self.db.commit()
        return True, None


# ============================================================================
# 应用生命周期
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时初始化数据库
    global db_connection
    db_connection = init_database(DB_PATH)
    print(f"✅ 数据库已初始化: {DB_PATH}")
    
    yield
    
    # 关闭时清理资源
    if db_connection:
        db_connection.close()
    await close_llm_client()
    print("👋 服务已关闭")


# ============================================================================
# FastAPI 应用实例
# ============================================================================

app = FastAPI(
    title="天机阁 API",
    description="玄学模块扩展服务 - 塔罗/解梦/梅花易数/合婚",
    version="2.0.0",
    lifespan=lifespan
)

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# 熔断保护依赖
# ============================================================================

async def rate_limit_dependency(request: Request):
    """
    限流检查依赖
    """
    db = get_db()
    limiter = RateLimiter(db)
    ip = limiter.get_client_ip(request)
    
    allowed, retry_after = limiter.check_rate_limit(ip)
    
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "rate_limit_exceeded",
                "message": f"每{RATE_LIMIT_WINDOW//60}分钟最多{RATE_LIMIT_POINTS}次请求，请稍后再试",
                "retry_after": retry_after
            }
        )
    
    return ip


# ============================================================================
# 错误处理
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """统一错误处理"""
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": "error",
            "message": exc.detail
        }
    )


# ============================================================================
# 健康检查
# ============================================================================

@app.get("/api/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "ok",
        "service": "天机阁 API",
        "version": "2.0.0",
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# 模块 1: 塔罗牌占卜
# ============================================================================

@app.post("/api/tarot", response_model=TarotResponse)
async def tarot_divination(
    request: TarotRequest,
    client_ip: str = Depends(rate_limit_dependency)
):
    """
    塔罗牌占卜 - 心理投射分析
    
    解析塔罗牌阵，结合荣格心理学给出洞察和建议
    """
    # 获取 Prompt
    system_prompt = get_prompt("tarot")
    user_input = build_user_input(
        "tarot",
        question=request.question,
        cards=request.cards,
        spread_type=request.spread_type.value
    )
    
    # 调用 LLM
    result = await call_llm(system_prompt, user_input, require_json=True)
    
    # 构建响应
    response_data = result["data"]
    response = TarotResponse(
        success=True,
        module="tarot",
        result=TarotResult(**response_data),
        meta=result["meta"]
    )
    
    # 保存记录
    db = get_db()
    save_reading(
        db,
        module_type="tarot",
        input_params=request.dict(),
        result_json=response_data,
        user_ip=client_ip
    )
    
    return response


# ============================================================================
# 模块 2: 周公解梦
# ============================================================================

@app.post("/api/dream", response_model=DreamResponse)
async def dream_interpretation(
    request: DreamRequest,
    client_ip: str = Depends(rate_limit_dependency)
):
    """
    周公解梦 - 潜意识破译
    
    解析梦境，结合传统符号与现代心理学给出洞察
    """
    system_prompt = get_prompt("dream")
    user_input = build_user_input(
        "dream",
        dream_desc=request.dream_desc,
        background=request.background
    )
    
    result = await call_llm(system_prompt, user_input, require_json=True)
    
    response_data = result["data"]
    response = DreamResponse(
        success=True,
        module="dream",
        result=DreamResult(**response_data),
        meta=result["meta"]
    )
    
    db = get_db()
    save_reading(
        db,
        module_type="dream",
        input_params=request.dict(),
        result_json=response_data,
        user_ip=client_ip
    )
    
    return response


# ============================================================================
# 模块 3: 梅花易数
# ============================================================================

@app.post("/api/plum-blossom", response_model=PlumBlossomResponse)
async def plum_blossom_divination(
    request: PlumBlossomRequest,
    client_ip: str = Depends(rate_limit_dependency)
):
    """
    梅花易数 - 极简决策推演
    
    基于卦象给出战略分析和时机判断
    """
    system_prompt = get_prompt("plum_blossom")
    user_input = build_user_input(
        "plum_blossom",
        question=request.question,
        hexagrams=request.hexagrams.dict(),
        changing_lines=request.changing_lines,
        body_element=request.body_element,
        use_element=request.use_element
    )
    
    result = await call_llm(system_prompt, user_input, require_json=True)
    
    response_data = result["data"]
    response = PlumBlossomResponse(
        success=True,
        module="plum_blossom",
        result=PlumBlossomResult(**response_data),
        meta=result["meta"]
    )
    
    db = get_db()
    save_reading(
        db,
        module_type="plum_blossom",
        input_params=request.dict(),
        result_json=response_data,
        user_ip=client_ip
    )
    
    return response


# ============================================================================
# 模块 4: 姻缘占卜/合婚匹配
# ============================================================================

@app.post("/api/marriage", response_model=MarriageResponse)
async def marriage_matching(
    request: MarriageRequest,
    client_ip: str = Depends(rate_limit_dependency)
):
    """
    姻缘占卜/合婚匹配 - 高情商情感咨询
    
    分析两人匹配度，给出具体可操作的相处建议
    """
    system_prompt = get_prompt("marriage")
    user_input = build_user_input(
        "marriage",
        person_a_info=request.person_a_info.dict(),
        person_b_info=request.person_b_info.dict(),
        current_status=request.current_status,
        conflict_focus=request.conflict_focus
    )
    
    result = await call_llm(system_prompt, user_input, require_json=True)
    
    response_data = result["data"]
    response = MarriageResponse(
        success=True,
        module="marriage",
        result=MarriageResult(**response_data),
        meta=result["meta"]
    )
    
    db = get_db()
    save_reading(
        db,
        module_type="marriage",
        input_params=request.dict(),
        result_json=response_data,
        user_ip=client_ip
    )
    
    return response


# ============================================================================
# 历史记录查询
# ============================================================================

@app.get("/api/history")
async def get_history(
    module: Optional[str] = None,
    limit: int = 20,
    client_ip: str = Depends(rate_limit_dependency)
):
    """
    获取历史记录
    
    Args:
        module: 可选，过滤特定模块 (tarot/dream/plum_blossom/marriage)
        limit: 返回记录数量，默认20
    """
    db = get_db()
    cursor = db.cursor()
    
    if module:
        cursor.execute(
            """
            SELECT id, module_type, input_params, created_at 
            FROM mystical_readings 
            WHERE module_type = ? 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (module, limit)
        )
    else:
        cursor.execute(
            """
            SELECT id, module_type, input_params, created_at 
            FROM mystical_readings 
            ORDER BY created_at DESC 
            LIMIT ?
            """,
            (limit,)
        )
    
    rows = cursor.fetchall()
    
    history = []
    for row in rows:
        history.append({
            "id": row["id"],
            "module": row["module_type"],
            "input": row["input_params"],
            "created_at": row["created_at"]
        })
    
    return {
        "success": True,
        "count": len(history),
        "data": history
    }


# ============================================================================
# 启动入口
# ============================================================================

if __name__ == "__main__":
    print(f"🎯 天机阁 API 启动中...")
    print(f"📍 端口: {PORT}")
    print(f"⚡ 熔断限制: 每{RATE_LIMIT_WINDOW//60}分钟最多{RATE_LIMIT_POINTS}次")
    print(f"🤖 模型: {os.getenv('LLM_MODEL', 'kimi-k2.5')}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=PORT,
        reload=False,
        log_level="info"
    )
