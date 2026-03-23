# OSV: One Story Video

一键故事视频生成工作流。

## 节点链路

```
Story Generator → HiDream Gen → Video Production
     (分镜生成)      (素材生成)      (视频组装)
```

## 使用

### 参数

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| story_prompt | string | 必填 | 故事主题或剧本 |
| style | string | cyberpunk | 视觉风格 |
| duration_per_scene | int | 5 | 每场景时长(秒) |
| max_concurrent | int | 3 | 并发数(1-5) |
| output_name | string | story_video | 输出文件名 |

### 执行

```python
from registry import Registry, WorkflowEngine

registry = Registry()
engine = WorkflowEngine(registry)

execution_id = engine.execute_workflow(
    workflow_def,
    {
        "story_prompt": "...",
        "style": "唯美治愈风",
        "max_concurrent": 3,
        "output_name": "my_video"
    }
)
```

## 首杀记录

- **项目**: 《云端图书馆》
- **时长**: 21秒 (1280×720)
- **生成时间**: 20分56秒
- **并发**: 3
- **输出**: cloud_library_osv.mp4

## 经验

1. 超时设置 30 分钟 (`runTimeoutSeconds: 1800`)
2. 并发数 3 是平衡点
3. 输出文件使用英文命名
