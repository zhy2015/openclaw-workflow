#!/usr/bin/env python3
"""
Komori SFX Downloader
小森平免费音效下载器
https://taira-komori.net/freesoundcn.html
"""

import asyncio
import aiohttp
import re
from pathlib import Path
from typing import List, Dict, Optional


# 音效分类映射
SFX_CATEGORIES = {
    "daily01": "生活上的动作1",
    "daily02": "生活上的动作2",
    "putting01": "放置·举起",
    "electric01": "家用设备",
    "cooking01": "烹饪·厨房",
    "eating01": "饭菜·吃饭",
    "openclose01": "开关音",
    "nature01": "自然地·季节·昆虫",
    "animals01": "动物",
    "human01": "人·脚步声",
    "sports01": "体育·大会·学校",
    "event01": "活动·祭祀·宴会",
    "environment01": "街环境声音1(日常系)",
    "environment02": "街环境声音2(噪音系)",
    "car01": "汽车声音",
    "transfer01": "交通工具",
    "tokyo01": "东京",
    "us01": "国外1 美国纽约曼哈顿",
    "french01": "国外2 法国",
}


class KomoriSFX:
    """小森平音效下载器"""

    BASE_URL = "https://taira-komori.net"

    def __init__(self, output_dir: str = "./sfx"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    async def list_sounds(self, category: str) -> List[Dict]:
        """
        列出分类下的所有音效

        Args:
            category: 分类代码 (electric01, nature01 等)

        Returns:
            音效列表 [{name, url, description}, ...]
        """
        url = f"{self.BASE_URL}/{category}cn.html"

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    if resp.status == 200:
                        html = await resp.text()
                        return self._parse_sounds(html, category)
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        return []

    def _parse_sounds(self, html: str, category: str) -> List[Dict]:
        """解析 HTML 提取音效信息"""
        sounds = []

        # 匹配 <A href="sound_os2/xxx/xxx.mp3" ...> 格式
        # 同时获取前面的音效名
        pattern = r'<TD>([^<]+)<A[^>]*href="(sound_os2/[^"]+\.mp3)"[^>]*>'
        matches = re.findall(pattern, html)

        for desc, path in matches:
            name = path.split("/")[-1].replace(".mp3", "")
            sounds.append({
                "name": name.strip(),
                "url": f"{self.BASE_URL}/{path}",
                "description": desc.strip()[:50],
                "category": category,
                "file_size": None
            })

        return sounds

    async def get_all_categories(self) -> Dict[str, List[Dict]]:
        """获取所有分类的音效"""
        all_sounds = {}

        for category in SFX_CATEGORIES.keys():
            print(f"Fetching {category}...")
            sounds = await self.list_sounds(category)
            if sounds:
                all_sounds[category] = sounds

        return all_sounds

    def categorize_by_tag(self, sounds: List[Dict]) -> Dict[str, List[Dict]]:
        """按标签自动分类音效"""
        categories = {
            "electric": [],      # 电子/电器
            "mechanical": [],    # 机械
            "nature": [],        # 自然
            "human": [],         # 人声/动作
            "transport": [],     # 交通
            "environment": [],   # 环境
            "other": []
        }

        keywords = {
            "electric": ["电", "fan", "switch", "power", "broadcast", "radio", "clock", "light"],
            "mechanical": ["门", "窗", "开关", "机器", "工具"],
            "nature": ["雨", "风", "雷", "海", "鸟", "动物"],
            "human": ["走", "跑", "声", "人", "脚步"],
            "transport": ["车", "电铁", "地铁", "飞机", "自行车"],
            "environment": ["街", "城市", "环境", "店"]
        }

        for sound in sounds:
            text = f"{sound['name']} {sound['description']}"
            matched = False

            for cat, words in keywords.items():
                if any(w in text.lower() for w in words):
                    categories[cat].append(sound)
                    matched = True
                    break

            if not matched:
                categories["other"].append(sound)

        return categories

    async def download(self, sound_url: str, output_name: str = None) -> Optional[Path]:
        """
        下载单个音效

        Args:
            sound_url: 音效 URL
            output_name: 输出文件名 (不含扩展名)

        Returns:
            下载的文件路径
        """
        filename = output_name or sound_url.split("/")[-1]
        if not filename.endswith(".mp3"):
            filename += ".mp3"

        filepath = self.output_dir / filename

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(sound_url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    if resp.status == 200:
                        content = await resp.read()
                        if len(content) > 1000:  # 确保是有效音频
                            with open(filepath, "wb") as f:
                                f.write(content)
                            print(f"✓ Downloaded: {filename} ({len(content)} bytes)")
                            return filepath
            except Exception as e:
                print(f"✗ Error: {e}")

        return None

    async def download_category(self, category: str, limit: int = None) -> List[Path]:
        """
        下载整个分类的音效

        Args:
            category: 分类代码
            limit: 限制下载数量

        Returns:
            下载的文件路径列表
        """
        sounds = await self.list_sounds(category)
        if limit:
            sounds = sounds[:limit]

        downloaded = []
        for sound in sounds:
            path = await self.download(sound["url"], sound["name"])
            if path:
                downloaded.append(path)

        return downloaded

    async def search(self, keyword: str, max_results: int = 10) -> List[Path]:
        """
        跨分类搜索音效 (简单实现)

        Args:
            keyword: 关键词
            max_results: 最大结果数

        Returns:
            下载的文件路径列表
        """
        downloaded = []

        # 遍历所有分类搜索
        for category in list(SFX_CATEGORIES.keys())[:5]:  # 限制前5个分类
            sounds = await self.list_sounds(category)
            matching = [s for s in sounds if keyword.lower() in s["name"].lower() or keyword.lower() in s["description"].lower()]

            for sound in matching[:max_results]:
                path = await self.download(sound["url"], sound["name"])
                if path:
                    downloaded.append(path)
                    if len(downloaded) >= max_results:
                        return downloaded

        return downloaded


# 快捷函数
async def download_komori_sfx(category: str, output_dir: str = "./sfx", limit: int = None) -> List[Path]:
    """下载分类音效"""
    downloader = KomoriSFX(output_dir)
    return await downloader.download_category(category, limit)


if __name__ == "__main__":
    async def test():
        print("Komori SFX Downloader")
        print(f"Categories: {len(SFX_CATEGORIES)}")

        # 测试下载一个音效
        downloader = KomoriSFX("/tmp/komori_test")
        result = await downloader.download(
            "https://taira-komori.net/sound_os2/electric01/clock1.mp3",
            "test_clock"
        )
        print(f"Result: {result}")

    asyncio.run(test())
