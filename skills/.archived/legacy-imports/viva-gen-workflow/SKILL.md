---
name: viva-gen-workflow
description: 高清多模态内容（图片/视频）生成与标准交付工作流。当用户要求“画图”、“生成视频”或通过描述特定画面来请求可视化内容时调用。该技能集成了 Viva-Gen 的生成能力与 QQMail 的兜底发送能力。
metadata: {"openclaw": {"requires": {"bins": ["python3", "wget"]}, "os": ["win32", "linux", "darwin"]}}
---

# Viva-Gen Multimodal Workflow

这是一个标准化的多模态内容生成与交付工作流。它将复杂的参数配置对用户隐藏，只暴露自然语言接口。

## 依赖
- **核心能力**: 必须确保 `skills/hidream-api-gen` 和 `skills/qqmail` 已安装且环境变已配置（`OPENCLAW_AUTHORIZATION` 等）。
- **默认交付邮箱**: `zhy20152015@qq.com` (根据 USER.md 规则)。

## 工作流步骤 (Agent 执行指南)

### Step 1: 提示词优化 (Prompt Refinement)
1. 接收用户的自然语言描述（可能是中文或英文）。
2. 将其转化为高质量的英文 Prompt，包含：主体特征、动作/姿态、环境背景、光影氛围、镜头语言、画质词（如 `8K, hyper-realistic, cinematic color grading`）。
3. **字数限制**：确保最终传递给脚本的 `--prompt` 长度在 **1000 字符** 以内。

### Step 2: 触发生成 (Execution)

**对于图片生成 (Image Generation)**:
默认使用 Seedream M2 模型。优先使用高分辨率。
```bash
python3 /root/.openclaw/workspace/skills/hidream-api-gen/scripts/seedream.py --version M2 --resolution "2048*2048" --prompt "优化后的英文提示词"
```

**对于视频生成 (Video Generation)**:
默认使用 Kling 模型。如果用户提供了一张基础图片（Image-to-Video），则传入图片 URL。
```bash
python3 /root/.openclaw/workspace/skills/hidream-api-gen/scripts/kling.py --version Q2.5T-pro --duration 5 --prompt "优化后的英文动作描述" --images "可选的图片URL"
```

*注意：上述脚本均为异步长轮询操作，如果脚本内部未自动处理轮询，请通过 `process` 工具挂起等待或解析 task_id 进行手动轮询。*

### Step 3: 结果下载 (Download)
解析脚本或轮询返回的 JSON，获取 `image` 或 `video` 的 URL。
```bash
wget -q -O "downloads/viva_gen_output.[jpg|mp4]" "返回的URL"
```

### Step 4: 结果交付 (Delivery)
根据生成内容的格式进行分类处理：
- **如果是图片 (.jpg / .png)**:
  直接在聊天窗口通过专属标签渲染发送。
  ```xml
  <qqimg>/root/.openclaw/workspace/downloads/viva_gen_output.jpg</qqimg>
  ```
- **如果是视频 (.mp4) 或其他富媒体**:
  因当前渠道限制，必须静默通过邮件发送，并向用户报告已发送。
  ```bash
  export QQMAIL_USER="harry_zhu@qq.com" && export QQMAIL_AUTH_CODE="lzupkjrihisrcabj" && python3 /root/.openclaw/workspace/skills/qqmail/scripts/qqmail.py send --to "zhy20152015@qq.com" --subject "Generated Media Content" --body "您的多模态内容已生成，请查看附件。" --attachment "downloads/viva_gen_output.mp4"
  ```
