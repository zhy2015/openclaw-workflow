# Progress Plane Runtime Integration

## Status

Core progress plane is now implemented up to a **session-aware adapter** layer:

- progress tracker
- progress policy
- progress watcher
- progress notifier
- progress bridge -> notification manager
- session progress adapter

What is still missing is the **runtime edge binding**:

> a concrete sender for the current conversation/session must be injected by the OpenClaw runtime boundary.

## Why this matters

Without runtime edge binding, long-task progress architecture exists internally but cannot guarantee user-visible delivery.
This is the exact class of failure observed in long-running story-video tasks.

## Required integration point

The runtime edge (the part of OpenClaw that owns the active inbound session/channel context) must provide:

- current channel (e.g. feishu)
- current conversation target (e.g. user/chat target)
- callable sender(text) or equivalent async sender(payload)

Then it should instantiate and attach:

```python
adapter = SessionProgressAdapter(sender=sender, context=SessionDeliveryContext(channel="feishu", target="user:..."))
adapter.attach()
```

## Architectural decision

### Core owns
- when progress should be emitted
- how progress events are normalized
- how failures / interrupts are escalated

### Runtime edge owns
- where messages go
- which active session/channel should receive progress updates
- transport-specific delivery semantics

## Minimal implementation path

1. At session bootstrap / inbound message handling, create a session sender wrapper.
2. Register `SessionProgressAdapter.attach()` for the active session.
3. Ensure handler lifecycle matches session lifecycle.
4. Add e2e verification:
   - milestone delivery to current DM
   - alert delivery on SIGTERM/failure
   - periodic 10-minute update delivery

## Regression target

The story-video 1-minute task should be used as the first live verification case.
