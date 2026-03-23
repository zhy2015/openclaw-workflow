# SFX Generator Skill

程序化音效生成技能 - 使用 FFmpeg 生成高质量音效

## 功能
- 生成环境底噪、电流声、心跳声等
- 无需外部下载，纯本地生成
- 支持自定义时长、频率、音量

## 使用

```python
from sfx_generator import SFXGenerator, generate_sfx_pack

# 生成单个音效
gen = SFXGenerator("./sfx")
path = gen.generate_ambient_hum(duration=8.0)

# 生成完整音效包
sfx = generate_sfx_pack("./sfx")
```

## 可用音效
- `ambient_hum` - 环境底噪
- `electric_sparks` - 电流/电火花
- `digital_data` - 数字数据流
- `heartbeat` - 心跳声
- `bass_drop` - 低频重音
- `energy_surge` - 能量涌动

## 依赖
- FFmpeg (lavfi 滤镜支持)
