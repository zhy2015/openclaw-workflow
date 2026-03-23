"""
天机阁 API - 大模型调用层 (llm_client.py)
通用异步 LLM 调用客户端，支持 OpenAI 兼容格式
"""

import json
import os
import re
from typing import Dict, Any, Optional
from datetime import datetime

import httpx
from fastapi import HTTPException


# ============================================================================
# 配置
# ============================================================================

# 从环境变量读取，默认使用阿里云百炼
LLM_API_KEY = os.getenv("LLM_API_KEY", "sk-b0fc3717ed2b416db15545a416fbc9f0")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "kimi-k2.5")
LLM_TIMEOUT = int(os.getenv("LLM_TIMEOUT", "180"))  # 秒


# ============================================================================
# JSON 修复工具
# ============================================================================

def extract_json_from_text(text: str) -> Optional[str]:
    """
    从可能包含 Markdown 代码块的文本中提取 JSON
    """
    # 尝试匹配 ```json ... ``` 格式
    json_pattern = r'```(?:json)?\s*([\s\S]*?)```'
    matches = re.findall(json_pattern, text)
    if matches:
        return matches[0].strip()
    
    # 尝试匹配纯 JSON（以 { 开头，以 } 结尾）
    text = text.strip()
    if text.startswith('{') and text.endswith('}'):
        return text
    
    # 尝试从文本中提取第一个 JSON 对象
    start = text.find('{')
    end = text.rfind('}')
    if start != -1 and end != -1 and end > start:
        return text[start:end+1]
    
    return None


def repair_json(text: str) -> Optional[Dict[str, Any]]:
    """
    尝试修复和解析可能损坏的 JSON
    """
    # 首先尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    
    # 提取 JSON 部分
    json_str = extract_json_from_text(text)
    if json_str:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # 尝试修复常见的 JSON 错误
    try:
        # 移除尾部逗号
        cleaned = re.sub(r',(\s*[}\]])', r'\1', text)
        # 修复单引号
        cleaned = cleaned.replace("'", '"')
        # 修复无引号的键
        cleaned = re.sub(r'(\w+):', r'"\1":', cleaned)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    
    return None


# ============================================================================
# LLM 客户端
# ============================================================================

class LLMClient:
    """
    大模型调用客户端
    """
    
    def __init__(self):
        self.api_key = LLM_API_KEY
        self.base_url = LLM_BASE_URL.rstrip('/')
        self.model = LLM_MODEL
        self.timeout = LLM_TIMEOUT
        self.client = httpx.AsyncClient(timeout=self.timeout)
    
    async def close(self):
        """关闭 HTTP 客户端"""
        await self.client.aclose()
    
    async def call(
        self,
        system_prompt: str,
        user_input: str,
        temperature: float = 0.8,
        max_tokens: int = 4000,
        require_json: bool = True
    ) -> Dict[str, Any]:
        """
        调用大模型 API
        
        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            temperature: 温度参数
            max_tokens: 最大 token 数
            require_json: 是否要求返回 JSON 格式
            
        Returns:
            解析后的 JSON 结果
            
        Raises:
            HTTPException: 调用失败时抛出
        """
        # 构建消息
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        
        # 构建请求体
        request_body = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        # 如果需要 JSON 输出，添加相应参数
        if require_json:
            # OpenAI 兼容格式：使用 response_format
            request_body["response_format"] = {"type": "json_object"}
            # 对于某些模型，可能需要额外的提示来强制 JSON
            # 已经在 system_prompt 中要求了，这里不再额外处理
        
        # 发送请求
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = await self.client.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=request_body
            )
            response.raise_for_status()
            
        except httpx.TimeoutException:
            raise HTTPException(
                status_code=504,
                detail="模型调用超时，请稍后重试"
            )
        except httpx.HTTPStatusError as e:
            error_detail = ""
            try:
                error_data = e.response.json()
                error_detail = error_data.get("error", {}).get("message", str(e))
            except:
                error_detail = str(e)
            raise HTTPException(
                status_code=502,
                detail=f"模型服务异常: {error_detail}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"调用模型时发生错误: {str(e)}"
            )
        
        # 解析响应
        try:
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # 记录元数据
            meta = {
                "model_used": self.model,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "created_at": datetime.now().isoformat()
            }
            
        except (KeyError, IndexError) as e:
            raise HTTPException(
                status_code=500,
                detail=f"解析模型响应失败: {str(e)}"
            )
        
        # 解析 JSON 内容
        if require_json:
            parsed_content = repair_json(content)
            if parsed_content is None:
                # 如果解析失败，尝试让模型重新生成（这里先返回原始内容供调试）
                raise HTTPException(
                    status_code=500,
                    detail=f"无法解析模型返回的 JSON，原始内容: {content[:500]}"
                )
            
            return {
                "success": True,
                "data": parsed_content,
                "meta": meta
            }
        else:
            return {
                "success": True,
                "data": {"content": content},
                "meta": meta
            }
    
    async def call_with_retry(
        self,
        system_prompt: str,
        user_input: str,
        max_retries: int = 2,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带重试机制的 LLM 调用
        
        Args:
            system_prompt: 系统提示词
            user_input: 用户输入
            max_retries: 最大重试次数
            **kwargs: 传递给 call() 的其他参数
            
        Returns:
            解析后的结果
        """
        last_error = None
        
        for attempt in range(max_retries + 1):
            try:
                return await self.call(system_prompt, user_input, **kwargs)
            except HTTPException as e:
                last_error = e
                # 如果是客户端错误（4xx），不重试
                if e.status_code < 500:
                    raise
                # 最后一次尝试失败，抛出异常
                if attempt == max_retries:
                    raise
                # 等待后重试
                import asyncio
                await asyncio.sleep(2 ** attempt)  # 指数退避
        
        raise last_error


# ============================================================================
# 全局客户端实例
# ============================================================================

_llm_client: Optional[LLMClient] = None


def get_llm_client() -> LLMClient:
    """
    获取全局 LLM 客户端实例（单例模式）
    """
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client


async def close_llm_client():
    """
    关闭全局 LLM 客户端
    """
    global _llm_client
    if _llm_client:
        await _llm_client.close()
        _llm_client = None


# ============================================================================
# 便捷调用函数
# ============================================================================

async def call_llm(
    system_prompt: str,
    user_input: str,
    require_json: bool = True,
    **kwargs
) -> Dict[str, Any]:
    """
    便捷的 LLM 调用函数
    
    使用示例:
        result = await call_llm(
            system_prompt=TAROT_SYSTEM_PROMPT,
            user_input='{"question": "我该不该辞职？", "cards": ["愚者正位"]}',
            require_json=True
        )
        data = result["data"]
        meta = result["meta"]
    """
    client = get_llm_client()
    return await client.call_with_retry(
        system_prompt=system_prompt,
        user_input=user_input,
        require_json=require_json,
        **kwargs
    )
