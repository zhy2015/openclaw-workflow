#!/bin/bash
# Setup cron jobs for OpenClaw automatic maintenance

echo "Setting up cron jobs for OpenClaw..."

# Create crontab entry
cat > /tmp/openclaw_cron << 'EOF'
# OpenClaw Automatic Maintenance
# Run bootstrap on reboot
@reboot /root/.openclaw/workspace/scripts/openclaw_bootstrap.sh >> /root/.openclaw/workspace/logs/cron.log 2>&1

# Run memory master daily at 3 AM
0 3 * * * /root/.openclaw/workspace/memory/core/memory_master_daemon.py >> /root/.openclaw/workspace/logs/memory_master.log 2>&1

# Run closed loop orchestrator every 6 hours
0 */6 * * * /root/.openclaw/workspace/scripts/closed_loop_orchestrator.py >> /root/.openclaw/workspace/logs/orchestrator.log 2>&1

# Refresh FTS5 index daily at 4 AM
0 4 * * * python3 /root/.openclaw/workspace/memory/core/memory_query_engine.py --index-only >> /root/.openclaw/workspace/logs/fts5_index.log 2>&1
EOF

# Install crontab
crontab /tmp/openclaw_cron
rm /tmp/openclaw_cron

echo "✅ Cron jobs installed:"
crontab -l | grep -v "^#" | grep -v "^$"
