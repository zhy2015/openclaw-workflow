# Pixabay Media Skill

Pixabay 媒体下载技能 - 图片和视频检索下载

## 功能
- 搜索 Pixabay 图片/视频
- 自动下载高清素材
- 支持按类型、方向、颜色筛选

## API
Pixabay API: https://pixabay.com/api/docs/

## 使用

```python
from pixabay_media import search_images, search_videos, download_media

# 搜索图片
results = await search_images("cyberpunk city", api_key="your_key", limit=5)

# 搜索视频
results = await search_videos("sci fi animation", api_key="your_key", limit=3)

# 下载
path = await download_media(results[0], output_dir="./media")
```

## 依赖
- aiohttp
- ffmpeg (视频处理)
