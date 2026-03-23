#!/usr/bin/env python3
"""
AGENTS Reflection Module
认知闭环实现：记忆 → 反思 → 预防

在日记蒸馏完成后执行，读取最新规律，生成防御型 DAG 模板
"""

import json
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, "/root/.openclaw/workspace/memory/core")
from memory_query_engine import MemoryQueryEngine
from memory_bootstrap import CORE_MEMORY_PATH


class AgentsReflection:
    """
    AGENTS 反思模块
    
    职责:
    1. 读取 memory/core/MEMORY.md 最新提炼的规律
    2. 识别高频失败模式
    3. 生成防御型 DAG 模板
    4. 存储至 memory/core/defensive_dags/
    """
    
    def __init__(self):
        self.core_memory = Path(CORE_MEMORY_PATH)
        self.defensive_dags_dir = Path("/root/.openclaw/workspace/memory/core/defensive_dags")
        self.defensive_dags_dir.mkdir(parents=True, exist_ok=True)
        
        self.memory_engine = MemoryQueryEngine()
    
    def reflect(self):
        """执行反思流程"""
        print("=" * 60)
        print("🧠 AGENTS REFLECTION - Cognitive Loop")
        print("=" * 60)
        print(f"Started: {datetime.now().isoformat()}\n")
        
        # 1. 查询高频失败模式
        print("[1/4] Querying high-frequency failure patterns...")
        failures = self.memory_engine.search("FAILED error 失败", limit=10)
        print(f"  Found {len(failures)} failure records")
        
        # 2. 识别需要防御的工作流
        print("\n[2/4] Identifying workflows needing defense...")
        workflows_to_defend = self._identify_vulnerable_workflows(failures)
        print(f"  Identified {len(workflows_to_defend)} vulnerable workflow(s)")
        
        # 3. 生成防御型 DAG 模板
        print("\n[3/4] Generating defensive DAG templates...")
        templates_generated = 0
        for workflow in workflows_to_defend:
            template = self._generate_defensive_template(workflow)
            self._save_template(template)
            templates_generated += 1
            print(f"  ✅ Generated template for: {workflow['name']}")
        
        # 4. 更新索引
        print("\n[4/4] Updating defensive DAGs index...")
        self._update_index()
        
        print("\n" + "=" * 60)
        print(f"✅ Reflection completed: {templates_generated} defensive template(s) generated")
        print("=" * 60)
        
        return templates_generated
    
    def _identify_vulnerable_workflows(self, failures):
        """识别脆弱的工作流"""
        # 基于失败记录识别需要防御的工作流
        vulnerable = []
        
        # 检查 video-production 相关失败
        video_failures = [f for f in failures if "video" in f.content.lower()]
        if video_failures:
            vulnerable.append({
                "name": "video-production",
                "failure_count": len(video_failures),
                "common_errors": ["GPU OOM", "API Timeout", "Rate Limit"]
            })
        
        return vulnerable
    
    def _generate_defensive_template(self, workflow):
        """生成防御型 DAG 模板"""
        return {
            "name": f"{workflow['name']}-defensive",
            "version": "1.0.0",
            "description": f"Defensive template for {workflow['name']} with retry, degrade, and circuit breaker",
            "defense_mechanisms": [
                "retry_policy: max_attempts=3, exponential backoff",
                "degraded_mode: fallback to CPU/simple mode on GPU failure",
                "circuit_breaker: open after 3 failures, recovery in 300s",
                "pre_validation: validate inputs before execution"
            ],
            "nodes": [
                {
                    "id": "pre_validate",
                    "name": "Pre-validate Inputs (NEW)",
                    "action": "validate_inputs",
                    "failure_policy": "fail_fast"
                },
                {
                    "id": "main_task",
                    "name": f"{workflow['name']} (With Retry)",
                    "retry_policy": {
                        "max_attempts": 3,
                        "backoff": "exponential",
                        "initial_delay": 5
                    },
                    "degraded_mode": True
                },
                {
                    "id": "fallback",
                    "name": "Fallback Handler (NEW)",
                    "trigger": "on_main_task_failure",
                    "action": "use_degraded_mode"
                }
            ],
            "circuit_breaker": {
                "failure_threshold": 3,
                "recovery_timeout": 300
            },
            "generated_at": datetime.now().isoformat(),
            "based_on_failures": workflow['failure_count']
        }
    
    def _save_template(self, template):
        """保存模板到文件"""
        filename = f"{template['name']}.json"
        filepath = self.defensive_dags_dir / filename
        
        with open(filepath, "w") as f:
            json.dump(template, f, indent=2)
    
    def _update_index(self):
        """更新防御型 DAG 索引"""
        index = {
            "last_updated": datetime.now().isoformat(),
            "templates": []
        }
        
        for f in self.defensive_dags_dir.glob("*.json"):
            with open(f) as fp:
                template = json.load(fp)
                index["templates"].append({
                    "name": template["name"],
                    "description": template["description"],
                    "file": str(f)
                })
        
        index_path = self.defensive_dags_dir / "index.json"
        with open(index_path, "w") as f:
            json.dump(index, f, indent=2)


def main():
    """CLI entry"""
    reflection = AgentsReflection()
    count = reflection.reflect()
    return 0 if count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
