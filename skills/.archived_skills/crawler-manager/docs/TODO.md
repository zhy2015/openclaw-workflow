# Crawler Manager TODO

## 可选爬虫技能（按需下载）

以下爬虫技能可在需要时通过 SkillHub 安装，当前未下载：

### 1. mediacrawler-skill
- **用途**: 多平台社交媒体采集（抖音、微博、小红书等）
- **场景**: 需要采集社交媒体公开信息时
- **安装**: `skillhub install mediacrawler-skill`
- **优先级**: 中
- **状态**: 未安装 ⬜

### 2. video-crawler
- **用途**: 视频下载（抖音、Twitter）
- **场景**: 需要下载短视频时
- **安装**: `skillhub install video-crawler`
- **优先级**: 低
- **状态**: 未安装 ⬜
- **备注**: 已有 one-story-video 视频生成工作流，视频下载需求较低

### 3. finviz-crawler
- **用途**: 金融新闻持续监控
- **场景**: 需要监控金融市场、股票信息时
- **安装**: `skillhub install finviz-crawler`
- **优先级**: 低
- **状态**: 未安装 ⬜
- **备注**: 当前无金融数据需求

### 4. kekik-crawler
- **用途**: Scrapling 确定性爬虫
- **场景**: 需要确定性、可重复的爬虫任务时
- **安装**: `skillhub install kekik-crawler`
- **优先级**: 低
- **状态**: 未安装 ⬜
- **备注**: 与现有 playwright/firecrawler 功能重叠

### 5. arxiv-paper-reviews
- **用途**: arXiv 学术论文获取
- **场景**: 需要学术研究、论文检索时
- **安装**: `skillhub install arxiv-paper-reviews`
- **优先级**: 低
- **状态**: 未安装 ⬜
- **备注**: 当前无学术文献需求

## 已安装爬虫

| 爬虫 | 类型 | 状态 |
|------|------|------|
| playwright-scraper | 浏览器自动化 | ✅ 已安装 |
| firecrawler | API 爬虫 | ✅ 已安装 |
| crawler-manager | 统一管理 | ✅ 已安装 |

## 决策记录

- **2026-03-18**: 仅安装 playwright 和 firecrawler，覆盖 90% 爬虫场景
- **原则**: 按需安装，避免技能膨胀
- **触发条件**: 当现有爬虫无法满足特定需求时，再评估安装新爬虫
