#!/usr/bin/env python3
"""
Pixabay Media Downloader
图片和视频检索下载
"""

import asyncio
import aiohttp
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class MediaItem:
    """媒体项目"""
    id: int
    title: str
    url: str
    preview_url: str
    width: int
    height: int
    duration: int = 0  # 视频时长
    media_type: str = "image"  # image or video


class PixabayMediaAPI:
    """Pixabay 媒体 API"""

    API_URL = "https://pixabay.com/api"
    VIDEO_API_URL = "https://pixabay.com/api/videos"

    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search_images(
        self,
        query: str,
        image_type: str = "all",  # all, photo, illustration, vector
        orientation: str = "all",  # all, horizontal, vertical
        min_width: int = 0,
        min_height: int = 0,
        limit: int = 20
    ) -> List[MediaItem]:
        """搜索图片"""
        params = {
            "key": self.api_key,
            "q": query,
            "image_type": image_type,
            "orientation": orientation,
            "min_width": min_width,
            "min_height": min_height,
            "per_page": limit
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.API_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_image_results(data.get("hits", []))
            except Exception as e:
                print(f"Search error: {e}")
        return []

    async def search_videos(
        self,
        query: str,
        video_type: str = "all",  # all, film, animation
        limit: int = 20
    ) -> List[MediaItem]:
        """搜索视频"""
        params = {
            "key": self.api_key,
            "q": query,
            "video_type": video_type,
            "per_page": limit
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.VIDEO_API_URL, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return self._parse_video_results(data.get("hits", []))
            except Exception as e:
                print(f"Search error: {e}")
        return []

    def _parse_image_results(self, hits: List[Dict]) -> List[MediaItem]:
        """解析图片结果"""
        results = []
        for item in hits:
            results.append(MediaItem(
                id=item.get("id", 0),
                title=item.get("tags", "Untitled"),
                url=item.get("largeImageURL", item.get("webformatURL", "")),
                preview_url=item.get("previewURL", ""),
                width=item.get("imageWidth", 0),
                height=item.get("imageHeight", 0),
                media_type="image"
            ))
        return results

    def _parse_video_results(self, hits: List[Dict]) -> List[MediaItem]:
        """解析视频结果"""
        results = []
        for item in hits:
            videos = item.get("videos", {})
            # 优先使用 large 尺寸
            video_url = videos.get("large", {}).get("url", "")
            if not video_url:
                video_url = videos.get("medium", {}).get("url", "")
            if not video_url:
                video_url = videos.get("small", {}).get("url", "")

            results.append(MediaItem(
                id=item.get("id", 0),
                title=item.get("tags", "Untitled"),
                url=video_url,
                preview_url=item.get("picture_id", ""),
                width=item.get("videos", {}).get("large", {}).get("width", 0),
                height=item.get("videos", {}).get("large", {}).get("height", 0),
                duration=item.get("duration", 0),
                media_type="video"
            ))
        return results

    async def download(self, item: MediaItem, output_dir: str) -> Optional[Path]:
        """下载媒体文件"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        ext = "mp4" if item.media_type == "video" else "jpg"
        filename = f"pixabay_{item.id}.{ext}"
        filepath = output_path / filename

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(item.url, timeout=aiohttp.ClientTimeout(total=60)) as resp:
                    if resp.status == 200:
                        with open(filepath, "wb") as f:
                            f.write(await resp.read())
                        return filepath
            except Exception as e:
                print(f"Download error: {e}")
        return None


# 快捷函数
async def search_images(query: str, api_key: str, **kwargs) -> List[MediaItem]:
    """搜索图片"""
    api = PixabayMediaAPI(api_key)
    return await api.search_images(query, **kwargs)


async def search_videos(query: str, api_key: str, **kwargs) -> List[MediaItem]:
    """搜索视频"""
    api = PixabayMediaAPI(api_key)
    return await api.search_videos(query, **kwargs)


async def download_media(item: MediaItem, output_dir: str = "./media") -> Optional[Path]:
    """下载媒体"""
    api = PixabayMediaAPI("")
    return await api.download(item, output_dir)


if __name__ == "__main__":
    async def test():
        # 需要 API key 才能测试
        print("Pixabay Media Downloader")
        print("Usage:")
        print("  results = await search_images('nature', api_key='your_key')")
        print("  path = await download_media(results[0], './downloads')")

    asyncio.run(test())
