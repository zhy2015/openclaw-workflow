"""
Legacy Manifest Registry - 兼容型 manifest 执行器

说明：
- 该模块保留旧的 manifest 扫描 + URI 执行路径，用于兼容历史 skill 调用
- 新的控制面（注册、schema 聚合、统一分发）应使用 `core.infra.skill_manager`
- 新的统一契约（ISkill / ExecutionResult / GlobalContext）应使用 `core.infra.skill_contracts`

支持的旧执行类型:
- cli: 通过 subprocess 调用外部命令
- python_import: 通过 importlib 导入 Python 模块
"""

import json
import os
import sys
import subprocess
import importlib
import importlib.util
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Callable

WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
SKILLS_DIR = WORKSPACE_ROOT / "skills"


class SkillNotFoundError(Exception):
    """技能未找到"""
    pass


class SkillLoadError(Exception):
    """技能加载失败"""
    pass


class RegistryManager:
    """Legacy manifest registry/executor.

    兼容职责：
    1. 扫描并缓存 skills/ 下的 manifest.json
    2. 根据 execution_type 执行旧动作 (cli / python_import)
    3. 继续支持 `skill://{name}/{action}` 旧式 URI

    非职责：
    - 不再作为新的全局控制面抽象
    - 不负责通用 ISkill 契约治理
    - 不作为新的 schema 聚合总线
    """
    
    def __init__(self):
        self._manifests: Dict[str, dict] = {}
        self._loaded_modules: Dict[str, Any] = {}
        self._routing_table: Dict[str, dict] = {}
        self._categories: Dict[str, list] = {}
    
    def scan(self) -> None:
        """扫描 skills/ 目录，读取所有 manifest.json"""
        self._manifests.clear()
        self._routing_table.clear()
        self._categories.clear()

        if not SKILLS_DIR.exists():
            print(f"[Registry] skills 目录不存在: {SKILLS_DIR}")
            return

        for skill_dir in SKILLS_DIR.iterdir():
            if not skill_dir.is_dir() or skill_dir.name.startswith("."):
                continue

            manifest_path = skill_dir / "manifest.json"
            if manifest_path.exists():
                try:
                    with open(manifest_path, encoding="utf-8") as f:
                        manifest = json.load(f)

                    # 隔离已归档/隐藏/占位技能，避免寻址地雷
                    if manifest.get("status") == "archived" or manifest.get("visibility") == "hidden":
                        continue

                    manifest['_skill_dir'] = str(skill_dir)
                    self._manifests[manifest["name"]] = manifest

                    for action_name, action_config in manifest.get("actions", {}).items():
                        if not isinstance(action_config, dict):
                            continue
                        uri = f"skill://{manifest['name']}/{action_name}"
                        self._routing_table[uri] = {
                            "skill": manifest["name"],
                            "action": action_name,
                            "config": action_config
                        }

                    category = manifest.get("category", "uncategorized")
                    if category not in self._categories:
                        self._categories[category] = []
                    self._categories[category].append(manifest["name"])
                except Exception as e:
                    print(f"[Registry] 警告: 无法加载 {manifest_path}: {e}")

        print(f"[Registry] 已扫描 {len(self._manifests)} 个技能")
        if self._categories:
            print(f"[Registry] 分类分布: {dict((k, len(v)) for k, v in self._categories.items())}")
    
    def resolve(self, uri: str) -> Optional[dict]:
        """解析 URI，返回路由配置"""
        return self._routing_table.get(uri)
    
    def execute(self, uri: str, **kwargs) -> Any:
        """
        执行技能动作
        
        根据 manifest 中的 execution_type 自动分发:
        - cli: 通过 subprocess 执行命令
        - python_import: 通过 importlib 导入并调用函数
        """
        route = self.resolve(uri)
        if not route:
            raise SkillNotFoundError(f"未找到 URI: {uri}")
        
        skill_name = route["skill"]
        action_name = route["action"]
        action_config = route["config"]
        manifest = self._manifests[skill_name]
        
        exec_type = manifest.get("execution_type", "python_import")
        
        if exec_type == "cli":
            return self._execute_cli(manifest, action_config, kwargs)
        elif exec_type == "python_import":
            return self._execute_python(manifest, action_config, kwargs)
        else:
            raise SkillLoadError(f"未知的 execution_type: {exec_type}")
    
    def _execute_cli(self, manifest: dict, action: dict, kwargs: dict) -> dict:
        """执行 CLI 命令"""
        skill_dir = manifest['_skill_dir']
        command_template = action.get("command", "")
        
        # 合并默认值和用户参数
        args_def = action.get("args", {})
        merged_kwargs = {}
        for key, config in args_def.items():
            if key in kwargs:
                merged_kwargs[key] = kwargs[key]
            elif "default" in config:
                merged_kwargs[key] = config["default"]
        
        # 添加 entry_point
        merged_kwargs["entry_point"] = manifest.get("entry_point", "")
        
        # 渲染命令模板
        try:
            cmd = command_template.format(**merged_kwargs)
        except KeyError as e:
            raise SkillLoadError(f"缺少必要参数: {e}")
        
        # 执行命令
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                cwd=skill_dir,
                timeout=action.get("timeout", 60)
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "执行超时"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _execute_python(self, manifest: dict, action: dict, kwargs: dict) -> Any:
        """执行 Python 导入调用"""
        skill_dir = Path(manifest['_skill_dir']).resolve()
        module_path = action.get("module")
        func_name = action.get("function")

        if not module_path or not func_name:
            raise SkillLoadError(f"Python 动作缺少 module 或 function: {action}")

        default_args = action.get("default_args", {})
        final_kwargs = {**default_args, **kwargs}

        try:
            if str(skill_dir) not in sys.path:
                sys.path.insert(0, str(skill_dir))
            if str(WORKSPACE_ROOT) not in sys.path:
                sys.path.insert(0, str(WORKSPACE_ROOT))

            module = None
            import_error = None

            try:
                module = importlib.import_module(module_path)
            except ImportError as e:
                import_error = e
                file_name = module_path + '.py' if '-' in module_path else module_path.replace('.', '/') + '.py'
                candidate_paths = [
                    skill_dir / file_name,
                    WORKSPACE_ROOT / file_name,
                    WORKSPACE_ROOT / 'scripts' / Path(file_name).name,
                ]
                for candidate in candidate_paths:
                    if candidate.exists():
                        spec = importlib.util.spec_from_file_location(f"dynamic_{manifest['name']}_{func_name}", candidate)
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                            break

            if module is None:
                raise SkillLoadError(f"无法导入模块 {module_path}: {import_error}")

            func = getattr(module, func_name)
            if not callable(func):
                raise SkillLoadError(f"{module_path}.{func_name} 不可调用")

            return func(**final_kwargs)

        except ImportError as e:
            raise SkillLoadError(f"无法导入模块 {module_path}: {e}")
        except AttributeError as e:
            raise SkillLoadError(f"模块 {module_path} 没有函数 {func_name}: {e}")
    
    def get_routing_table(self) -> Dict[str, dict]:
        """获取路由表"""
        return self._routing_table.copy()
    
    def list_skills(self) -> list:
        """列出所有已注册技能"""
        return list(self._manifests.keys())
    
    def get_manifest(self, skill_name: str) -> Optional[dict]:
        """获取技能 manifest"""
        return self._manifests.get(skill_name)
    
    def list_by_category(self, category: Optional[str] = None) -> Dict[str, list]:
        """按类别列出技能
        
        Args:
            category: 指定类别名，None 返回全部分类
        
        Returns:
            {category: [skill_names]} 或指定类别的 [skill_names]
        """
        if category:
            return {category: self._categories.get(category, [])}
        return self._categories.copy()
    
    def get_categories(self) -> list:
        """获取所有类别列表"""
        return list(self._categories.keys())


# 兼容旧名
SkillRegistry = RegistryManager
LegacyManifestRegistry = RegistryManager

# 全局单例
_registry_instance = None

def get_registry() -> RegistryManager:
    """获取全局 Registry 实例

    Deprecated: legacy manifest entrypoint kept for migration only.
    Prefer SkillManager / ConstitutionRuntime for all new code.
    """
    warnings.warn(
        "core.infra.registry.get_registry() is deprecated; use SkillManager/ConstitutionRuntime instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = RegistryManager()
        _registry_instance.scan()
    return _registry_instance


if __name__ == "__main__":
    # 测试
    reg = get_registry()
    print("\n路由表:")
    for uri, route in reg.get_routing_table().items():
        print(f"  {uri}")
