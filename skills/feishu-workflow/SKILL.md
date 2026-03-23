---
name: feishu-workflow
description: Unified Feishu workflow facade for document publishing, messaging, chat/member lookup, permission strategy, and retry guidance. Use when the task is a normal Feishu collaboration workflow rather than a low-level API choice.
---

# Feishu Workflow

A facade skill that consolidates:
- document publishing workflow guidance
- messaging workflow guidance
- chat/member lookup strategy
- permission handling strategy
- retry and fallback guidance

## Role

This skill is **not** a replacement for native OpenClaw Feishu tools.
It is a **workflow layer** above them.

## Preferred execution policy

Use native Feishu tools first for execution:
- docs: `feishu_fetch_doc`, `feishu_create_doc`, `feishu_update_doc`, `feishu_doc_comments`, `feishu_doc_media`
- messaging: `message`, `feishu_im_user_message`, `feishu_chat`, `feishu_chat_members`, `feishu_search_user`

Use this facade when you need:
- deciding which Feishu path to take
- Markdown-to-Doc publishing strategy
- messaging retry / ID lookup strategy
- document permission/collaborator workflow guidance

## Consolidated source skills
- `feishu-doc-manager`
- `feishu-messaging`

## Non-goal

This facade does **not** absorb `feishu-evolver-wrapper`, which remains a separate specialized skill for evolver lifecycle/reporting.
