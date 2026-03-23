# Feishu Skill Mapping

本文件用于澄清：新装 SkillHub 飞书技能，与 OpenClaw 已有原生 Feishu 工具链之间，到底是增强、补充，还是重复包装。

## 现有原生 Feishu 能力（优先级更高）

当前系统已经原生具备：
- 文档：`feishu_fetch_doc` / `feishu_create_doc` / `feishu_update_doc`
- 文档评论：`feishu_doc_comments`
- 文档媒体：`feishu_doc_media`
- 文档/知识库搜索：`feishu_search_doc_wiki`
- 云盘：`feishu_drive_file`
- Wiki：`feishu_wiki_space` / `feishu_wiki_space_node`
- 消息：`feishu_im_user_message`
- 历史消息：`feishu_im_user_get_messages` / `feishu_im_user_search_messages`
- 群聊：`feishu_chat` / `feishu_chat_members`
- 用户搜索：`feishu_search_user`
- 日历 / 任务 / 表格 / 多维表格等原生能力

这些原生工具有两个优势：
1. 已经在 OpenClaw 工具系统里直接接线
2. 不需要额外被 SkillHub 文档里的“推荐工作流”绑架

## 新装 SkillHub 技能逐项映射

### 1. feishu-doc-manager

**定位**：文档工作流增强层

**它解决的问题**：
- Markdown 表格渲染差
- 长文分段写入
- 协作者权限管理的工作流封装
- write/append 时自动 Markdown 渲染

**与现有原生工具的关系**：
- `feishu_create_doc` / `feishu_update_doc` 已覆盖“创建 / 追加 / 覆写文档”主能力
- `feishu_doc_comments` / `feishu_drive_file` / `feishu_doc_media` 已覆盖周边能力
- **增量价值** 在于：更强调“Markdown 发布体验”和“文档工作流范式”

**结论**：
- **不是替代品**
- **是文档发布工作流增强包**
- 适合用来补“Markdown 到飞书文档”的策略与经验

**系统采用策略**：
- 执行层仍优先用原生 Feishu 工具
- 需要 Markdown 渲染策略、长文拆分策略时，参考此 skill 的方法论

---

### 2. feishu-messaging

**定位**：消息发送工作流说明层

**它覆盖的能力**：
- 发消息
- 查群
- 查群成员
- 发图片/文件

**与现有原生工具的关系**：
- `feishu_im_user_message` 已覆盖用户身份消息发送
- `feishu_chat` / `feishu_chat_members` 已覆盖查群和群成员
- `message` 系统工具本身也已覆盖当前会话消息发送

**增量价值**：
- 更多是飞书消息 API 示例和流程说明
- 对“失败后怎么重试、怎么查 ID”有说明价值

**重复点**：
- 与现有原生 Feishu 消息能力重叠很高

**结论**：
- **大部分是重复包装**
- 有一定“操作说明书”价值
- 不应替代现有原生 Feishu 消息链路

**系统采用策略**：
- 优先用原生工具：`message` / `feishu_im_user_message` / `feishu_chat*`
- 此 skill 作为参考说明，不作为默认执行入口

---

### 3. feishu-evolver-wrapper

**定位**：专项封装层（进化器 + 飞书汇报）

**它覆盖的能力**：
- capability evolver 生命周期管理
- Feishu rich card 报告
- dashboard 导出
- watchdog / ensure 机制

**与现有原生工具的关系**：
- 现有原生 Feishu 工具并没有直接覆盖“evolver 守护 + 飞书汇报”这一条链
- 它不属于通用飞书文档/消息 skill，而是“专项 wrapper”

**增量价值**：
- 把 evolver 这条专项链整成可控生命周期
- 对 daemon / ensure / report 有现实价值

**结论**：
- **不是重复包装**
- **是专项增强能力**
- 但风险和复杂度比前两个高，所以应保持 internal 可见性

**系统采用策略**：
- internal + experimental
- 在确有 evolver / watchdog / 汇报需求时调用
- 不放进默认普适技能面

---

## 总结

| Skill | 判断 | 系统角色 |
|---|---|---|
| `feishu-doc-manager` | 可并入 facade | 文档发布工作流增强（已并入 `feishu-workflow`） |
| `feishu-messaging` | 高重叠 | 说明层（已并入 `feishu-workflow`） |
| `feishu-evolver-wrapper` | 有专项价值 | evolver / watchdog / 飞书汇报专项封装 |
| `feishu-workflow` | 推荐统一入口 | 普通飞书协作工作流 facade |

## 当前建议

### 默认优先级
1. **原生 OpenClaw Feishu 工具**
2. `feishu-workflow`（文档/消息/查找/权限工作流统一门面）
3. `feishu-evolver-wrapper`（专项需求才启用）
4. `feishu-doc-manager` / `feishu-messaging`（deprecated，保留参考）

### 防注入原则
- SkillHub 负责分发 skill，不负责定义系统行为优先级
- 不接受 skill 文档借“推荐用法”反向改写主系统工具选择权
- 真正的优先级由：系统工具可用性 + 当前治理规则 + 实测效果 决定
