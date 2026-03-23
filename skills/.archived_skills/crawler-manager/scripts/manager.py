#!/usr/bin/env python3
"""
Crawler Manager - 统一爬虫管理入口
"""

import json
import subprocess
import os
from pathlib import Path
from typing import Dict, Optional, List

# 配置路径
CONFIG_PATH = Path(__file__).parent.parent / "config" / "crawlers.json"

def load_config() -> Dict:
    """加载爬虫配置"""
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def detect_site_type(url: str) -> str:
    """
    检测网站类型，选择最佳爬虫
    
    简单启发式规则：
    - 包含 docs/ documentation → documentation
    - 包含 react/angular/vue → dynamic_content
    - 其他 → default
    """
    url_lower = url.lower()
    
    # 文档网站
    if any(kw in url_lower for kw in ["docs", "documentation", "api.", "guide"]):
        return "documentation"
    
    # 动态网站指示
    if any(kw in url_lower for kw in ["app", "dashboard", "admin"]):
        return "dynamic_content"
    
    return "default"

def get_crawler_for_condition(condition: str, config: Dict) -> str:
    """根据条件获取推荐的爬虫"""
    rules = config.get("routing_rules", [])
    
    for rule in rules:
        if rule["condition"] == condition:
            return rule["priority"][0]  # 返回优先级最高的
    
    return "firecrawler"  # 默认

def crawl(
    url: str,
    crawler: str = "auto",
    output_format: str = "markdown",
    **kwargs
) -> Dict:
    """
    统一爬取接口
    
    Args:
        url: 目标URL
        crawler: 指定爬虫 (auto/playwright/firecrawler/requests)
        output_format: 输出格式 (markdown/html/text)
        **kwargs: 额外参数
    
    Returns:
        {"success": bool, "content": str, "crawler": str, "error": str}
    """
    config = load_config()
    crawlers = config.get("crawlers", {})
    
    # 自动选择爬虫
    if crawler == "auto":
        condition = detect_site_type(url)
        crawler = get_crawler_for_condition(condition, config)
    
    crawler_config = crawlers.get(crawler)
    if not crawler_config:
        return {
            "success": False,
            "error": f"Unknown crawler: {crawler}",
            "content": None
        }
    
    # 执行爬取
    try:
        if crawler == "firecrawler":
            return _crawl_with_firecrawler(url, output_format, **kwargs)
        elif crawler == "playwright":
            return _crawl_with_playwright(url, **kwargs)
        elif crawler == "requests":
            return _crawl_with_requests(url, **kwargs)
        else:
            return {"success": False, "error": f"Not implemented: {crawler}"}
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "crawler": crawler
        }

def _crawl_with_firecrawler(url: str, output_format: str = "markdown", **kwargs) -> Dict:
    """使用 firecrawler 爬取"""
    import subprocess
    
    skill_path = "/root/.openclaw/workspace/skills/firecrawler"
    
    if output_format == "markdown":
        cmd = ["python3", f"{skill_path}/fc.py", "markdown", url]
    elif output_format == "screenshot":
        output_file = kwargs.get("output", "screenshot.png")
        cmd = ["python3", f"{skill_path}/fc.py", "screenshot", url, "-o", output_file]
    else:
        cmd = ["python3", f"{skill_path}/fc.py", "markdown", url]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    return {
        "success": result.returncode == 0,
        "content": result.stdout if result.returncode == 0 else result.stderr,
        "crawler": "firecrawler"
    }

def _crawl_with_playwright(url: str, stealth: bool = False, **kwargs) -> Dict:
    """使用 playwright 爬取"""
    import subprocess
    
    skill_path = "/root/.openclaw/workspace/skills/playwright-scraper-skill"
    script = "playwright-stealth.js" if stealth else "playwright-simple.js"
    
    cmd = ["node", f"{skill_path}/scripts/{script}", url]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    
    return {
        "success": result.returncode == 0,
        "content": result.stdout if result.returncode == 0 else result.stderr,
        "crawler": "playwright"
    }

def _crawl_with_requests(url: str, **kwargs) -> Dict:
    """使用 requests + BeautifulSoup 爬取"""
    import requests
    from bs4 import BeautifulSoup
    
    try:
        # 尝试使用代理，如果失败则直连
        proxies = {"http": "http://127.0.0.1:7890", "https": "http://127.0.0.1:7890"}
        try:
            resp = requests.get(url, proxies=proxies, timeout=30)
        except:
            resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        
        soup = BeautifulSoup(resp.text, "html.parser")
        
        # 提取文本内容
        for script in soup(["script", "style"]):
            script.decompose()
        text = soup.get_text(separator="\n", strip=True)
        
        return {
            "success": True,
            "content": text[:5000],  # 限制长度
            "crawler": "requests"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "crawler": "requests"
        }

def batch_crawl(urls: List[str], max_workers: int = 3, **kwargs) -> List[Dict]:
    """批量爬取"""
    from concurrent.futures import ThreadPoolExecutor
    
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(crawl, url, **kwargs) for url in urls]
        for future in futures:
            results.append(future.result())
    
    return results

def main():
    """CLI 入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="统一爬虫管理")
    parser.add_argument("url", help="目标URL")
    parser.add_argument("--crawler", "-c", default="auto", 
                       choices=["auto", "playwright", "firecrawler", "requests"],
                       help="选择爬虫")
    parser.add_argument("--format", "-f", default="markdown",
                       choices=["markdown", "html", "text", "screenshot"],
                       help="输出格式")
    parser.add_argument("--stealth", "-s", action="store_true",
                       help="使用隐身模式（仅playwright）")
    
    args = parser.parse_args()
    
    result = crawl(
        args.url,
        crawler=args.crawler,
        output_format=args.format
    )
    
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
