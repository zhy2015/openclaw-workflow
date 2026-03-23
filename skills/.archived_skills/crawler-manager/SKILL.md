# Crawler Manager Skill

统一爬虫管理 Skill。整合多个爬虫工具，提供统一的 API 接口，自动选择最佳爬虫方案。

## 已集成的爬虫

| 爬虫 | 类型 | 适用场景 | 优先级 |
|------|------|----------|--------|
| **playwright-scraper** | 浏览器自动化 | 动态网站、反爬保护 | 高 |
| **firecrawler** | API 爬虫 | 通用网页、Markdown、截图 | 中 |
| **requests + BeautifulSoup** | 轻量爬虫 | 静态页面、快速抓取 | 低 |

## 目录结构

```
crawler-manager/
├── SKILL.md              # 本文件
├── scripts/
│   ├── manager.py        # 统一入口
│   ├── router.py         # 爬虫选择器
│   └── utils.py          # 工具函数
├── config/
│   └── crawlers.json     # 爬虫配置
└── docs/
    └── comparison.md     # 爬虫对比文档
```

## 使用方式

### 1. 智能路由（自动选择）
```python
from scripts.manager import crawl

# 自动选择最佳爬虫
result = crawl("https://example.com")
# Returns: {"content": "...", "crawler": "firecrawler", "time": 1.23}
```

### 2. 指定爬虫
```python
# 使用特定爬虫
result = crawl("https://example.com", crawler="playwright")
result = crawl("https://example.com", crawler="firecrawler")
result = crawl("https://example.com", crawler="requests")
```

### 3. 批量爬取
```python
urls = ["https://site1.com", "https://site2.com"]
results = batch_crawl(urls, max_workers=3)
```

## 爬虫选择策略

```
输入 URL
    ↓
检查反爬保护？
    ↓ 是 → playwright-scraper（隐身模式）
检查动态渲染？
    ↓ 是 → playwright-scraper / firecrawler
静态页面？
    ↓ 是 → firecrawler / requests
```

## 功能对比

| 功能 | playwright | firecrawler | requests |
|------|------------|-------------|----------|
| JavaScript 渲染 | ✅ | ✅ | ❌ |
| 反爬保护 | ✅✅ | ✅ | ❌ |
| Markdown 输出 | ❌ | ✅ | ❌ |
| 截图 | ✅ | ✅ | ❌ |
| 结构化数据 | ❌ | ✅ | ❌ |
| 速度 | 慢 | 中 | 快 |
| 资源占用 | 高 | 中 | 低 |

## 配置

```json
{
  "default_crawler": "auto",
  "fallback_order": ["firecrawler", "playwright", "requests"],
  "timeout": 30,
  "retry": 3,
  "proxy": "http://127.0.0.1:7890"
}
```

## 集成到其他 Skill

```python
from skills.crawler-manager.scripts.manager import crawl

def process_url(url):
    result = crawl(url)
    return result["content"]
```

## 注意事项

- playwright-scraper 需要 Node.js 环境
- firecrawler 需要 Firecrawl API Key
- requests 爬虫仅适用于静态页面
