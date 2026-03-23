## [LRN-20260322-001] correction

**Logged**: 2026-03-22T02:43:00Z
**Priority**: high
**Status**: promoted
**Area**: docs

### Summary
OpenClaw 的 `edit` 是精确匹配替换；README 这类频繁变化文件不能假设目标片段一定精确存在。

### Details
用户指出这是一个反复出现的错误模式：我在修改 `~/.openclaw/workspace/skills/one-story-video/README.md` 时，多次直接使用 `edit` 按预估片段替换，导致出现 “Edit ... failed / Could not find the exact text” 的失败。根因不是工具坏，而是我在修改动态文档时没有先读取最新上下文并只对已确认存在的精确片段进行替换。

### Suggested Action
对 README、文档、长文件做修改时：
1. 先 `read` 当前相关片段；
2. 再用 `edit` 替换确认存在的精确文本；
3. 如果改动较大或片段不稳定，直接 `write` 重写完整文件，而不是连续猜测式 `edit`。

### Metadata
- Source: user_feedback
- Related Files: /root/.openclaw/workspace/TOOLS.md, /root/.openclaw/workspace/.learnings/LEARNINGS.md
- Tags: openclaw, edit, exact-match, docs, recurring-error
- Pattern-Key: tool.edit.exact_match_on_dynamic_docs
- Recurrence-Count: 1
- First-Seen: 2026-03-22
- Last-Seen: 2026-03-22

### Resolution
- **Resolved**: 2026-03-22T02:43:00Z
- **Notes**: 已将该规则提升到 TOOLS.md，作为后续修改文件时的固定注意事项。

---
