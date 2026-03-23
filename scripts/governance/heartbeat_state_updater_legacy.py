#!/usr/bin/env python3
import json
import time

filepath = '/root/.openclaw/workspace/memory/heartbeat-state.json'
try:
    with open(filepath, 'r') as f:
        state = json.load(f)
except Exception:
    state = {"lastChecks": {}}

if "lastChecks" not in state:
    state["lastChecks"] = {}
    
state["lastChecks"]["moltbook"] = int(time.time() * 1000)

with open(filepath, 'w') as f:
    json.dump(state, f, indent=2)
