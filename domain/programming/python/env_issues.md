# Python Environment Issues

## Common Problems & Solutions

### ModuleNotFoundError
**Error**: `No module named 'xxx'`

**Solution**:
```bash
# Set PYTHONPATH before running
export PYTHONPATH=/path/to/project:$PYTHONPATH

# Or use absolute import
python3 -m module_name
```

### Pip Install Permission Error
**Error**: `Permission denied`

**Solution**:
```bash
# Use user install
pip install --user package_name

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install package_name
```

### SSL Certificate Error
**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
```bash
# For macOS
/Applications/Python\ 3.x/Install\ Certificates.command

# Or use trusted host
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org package_name
```

### One Story Video Specific
**Error**: `No module named 'agents'`

**Solution**:
```bash
cd /root/.openclaw/workspace/skills/video-production/04-orchestration/story-to-video-director
PYTHONPATH=/root/.openclaw/workspace/skills/video-production/04-orchestration/story-to-video-director:$PYTHONPATH \
python3 scripts/workflow_v2.py "剧本"
```

---
*领域: Programming/Python | 更新: 2026-03-16*
