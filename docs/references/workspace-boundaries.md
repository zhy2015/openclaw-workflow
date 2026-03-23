# Workspace Boundaries

## logs/
系统与工作流日志。尽量只放：
- heartbeat / cron / orchestrator / WAL / index logs
- 不放长期项目文档

## output/
工作流和媒体生成输出区。允许大量中间产物，但不应承担“项目定义”职责。
- 通用输出留这里
- 明确归属到项目的产物，可逐步下放到 `projects/_outputs/` 或项目专属输出目录
- 为避免打断现有脚本，先采用“复制归位”，再逐步修改默认输出路径

## archive/
历史归档区。只放冷资料、旧 workflow、历史成片、备份。

## resources/
通用素材与资源库。异常垃圾文件、错误输出、临时噪音不应留在这里。

## projects/
项目代码与项目私有配置、项目记忆。
- 项目级 `.env` 留在项目目录
- 项目长期经验优先写项目自己的 `MEMORY.md` / manual
