# Komori SFX Skill

小森平音效下载技能 - 高质量免费音效库

## 来源
- 网站: https://taira-komori.net/freesoundcn.html
- 作者: 小森平 (日本)
- 授权: 免费商用，需注明出处

## 功能
- 按分类浏览音效
- 关键词搜索
- 自动下载 MP3
- 智能标签分类

## 使用

```python
from komori_sfx import KomoriSFX, SFX_CATEGORIES

sfx = KomoriSFX()

# 浏览分类
print(SFX_CATEGORIES)

# 下载分类下的音效
await sfx.download_category("electric01", output_dir="./sfx")

# 搜索特定音效
results = await sfx.search("clock", output_dir="./sfx")

# 获取所有分类音效
all_sounds = await sfx.get_all_categories()

# 智能标签分类
categorized = sfx.categorize_by_tag(all_sounds["electric01"])
```

## 音效分类
| 分类代码 | 内容 |
|----------|------|
| electric01 | 家用设备 |
| nature01 | 自然·季节 |
| human01 | 人·脚步声 |
| car01 | 汽车声音 |
| environment01 | 街环境声音 |
| transfer01 | 交通工具 |

## 智能标签
- electric - 电子/电器
- mechanical - 机械
- nature - 自然
- human - 人声/动作
- transport - 交通
- environment - 环境

## 依赖
- aiohttp
- re (HTML解析)
