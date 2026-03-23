# Active TODOs

**规则**: 
- 完成项移动到 `archive/YYYY-MM/` 
- > 300 行自动归档最旧已完成项
- 7天无更新降级到 `backlog.md`

---

## Fast/Slow Path Constitution 改造（收尾阶段）

参考文档：
- `docs/system/fast-slow-path-constitution.md`
- `docs/system/fast-slow-path-next-stage.md`

### 剩余尾项
- [ ] 继续扩大 agent / script 对 `ConstitutionRuntime.invoke()` 的覆盖率
- [~] 将 minimal slow-path workflow 扩展为多节点 / 多依赖 DAG 场景（已支持多节点链路，后续可继续补更复杂依赖图）
- [~] 增补更多 constitution tests（complex slow-path / fallback / illegal path）（已补多依赖汇聚与失败路径，后续可继续扩）
- [ ] 将 audit log / route telemetry 用到更广泛的实际执行路径中
- [x] 视推进情况，将 `check_constitution_boundaries.py` 正式纳入 CI

---

## Story-to-Video Director 重构（主干已收口，进入增强项）

参考文档：
- `skills/one-story-video/04-orchestration/story-to-video-director/PHASE_STATUS.md`
- `core/tests/STORY_VIDEO_TESTS.md`
- `output/diagrams/one-story-video-expert-pipeline-plan-20260322.md`

### 已完成
- [x] Phase A：story / visual 结构化落地（`story_plan.json` / `visual_plan.json`）
- [x] Phase B：`sound_plan.json`、声音资产 resolve、BGM/SFX mixing、resume/persistence、regression tests
- [x] Phase C（最小版）：`audio_edit_plan.json` / `edit_plan.json`、`subtitle_policy` / `normalize_dialog` / `crossfade_ms`
- [x] 执行痕迹：plan / execute / trace / summary 已写入 project / manifest / audio_edit_plan
- [x] 统一回归入口：`bash /root/.openclaw/workspace/scripts/testing/run_story_video_regression.sh`
- [x] 当前 bundle 稳定通过（16 tests）

### 剩余增强项
- [ ] richer edit rule language：补更多 scene-level / project-level edit rules，而不只限最小 grammar
- [ ] advanced transition grammar：在 minimal `hard_cut|crossfade` 之外扩更多 transition 类型与 per-edge 语义
- [ ] 更完整的 end-to-end media smoke：在可控条件下补一条更真实的媒体生成回测，不只测轻量合成链路
- [ ] 将 regression bundle 接入更正式的默认测试入口/CI（如后续需要）
- [ ] 评估是否把 capability summary / coverage 输出成更适合下游消费的结构（如 card/report/dashboard）

---

当前活动任务：2 项（Fast/Slow Path Constitution 改造；Story-to-Video Director 重构增强项）
