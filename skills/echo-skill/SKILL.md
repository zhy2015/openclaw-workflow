---
name: echo-skill
description: Minimal smoke test skill for openclaw-core engine validation. Two nodes: A prints "Hello", B prints "World".
---

# Echo Skill

用于测试新引擎的极简技能。

## 工作流

```
Node A (Hello) → Node B (World)
```

## 用途

- 验证 DAG 解析
- 验证 WAL 双写
- 验证节点依赖
