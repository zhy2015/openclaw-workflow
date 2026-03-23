#!/usr/bin/env python3
"""
Legacy Skill CLI
Skill 生命周期管理命令行工具（迁移期保留）

命令:
  skill install <source>     安装 Skill
  skill uninstall <name>     卸载 Skill
  skill update <name>        更新 Skill
  skill list                 列出所有 Skill
  skill info <name>          查看 Skill 详情
  skill doctor [name]        健康检查
  skill rollback <name> <v>  回滚版本
"""

import argparse
import sys
import subprocess
import json
from pathlib import Path
from typing import Optional

# 导入 Registry
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from manager import SkillRegistry, SkillMetadata
from discovery import SkillDiscovery
from health import SkillHealthChecker

SKILLS_ROOT = Path(__file__).parent.parent.parent.parent / "skills"


def install_skill(source: str, name: Optional[str] = None) -> bool:
    """
    安装 Skill
    
    支持:
    - GitHub: skill install github.com/user/repo
    - Git: skill install git@github.com:user/repo.git
    - Local: skill install /path/to/skill
    """
    print(f"Installing skill from: {source}")
    
    target_dir = SKILLS_ROOT / (name or Path(source).stem)
    
    # 检查是否已存在
    if target_dir.exists():
        print(f"Error: Skill '{target_dir.name}' already exists")
        print(f"Use 'skill update {target_dir.name}' to update")
        return False
    
    # 克隆/复制
    if source.startswith("github.com"):
        # github.com/user/repo -> https://github.com/user/repo.git
        source = f"https://{source}.git"
    
    if source.startswith("http") or source.startswith("git@"):
        # Git 克隆
        cmd = ["git", "clone", "--depth", "1", source, str(target_dir)]
    else:
        # 本地复制
        cmd = ["cp", "-r", source, str(target_dir)]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    # 安装依赖
    install_dependencies(target_dir)
    
    # 自动注册
    registry = SkillRegistry()
    discovery = SkillDiscovery()
    count = discovery.auto_register(registry)
    
    if count > 0:
        print(f"✅ Installed and registered: {target_dir.name}")
    else:
        print(f"⚠️ Installed but not registered (no SKILL.md found)")
    
    return True


def install_dependencies(skill_dir: Path):
    """安装 Skill 依赖"""
    print("Installing dependencies...")
    
    # Python 依赖
    req_file = skill_dir / "requirements.txt"
    if req_file.exists():
        print("  Found requirements.txt")
        subprocess.run(
            ["pip", "install", "-r", str(req_file), "-q"],
            capture_output=True
        )
    
    # Node.js 依赖
    pkg_file = skill_dir / "package.json"
    if pkg_file.exists():
        print("  Found package.json")
        subprocess.run(
            ["npm", "install", "--prefix", str(skill_dir)],
            capture_output=True
        )
    
    # 执行 setup.sh
    setup_sh = skill_dir / "setup.sh"
    if setup_sh.exists():
        print("  Found setup.sh")
        subprocess.run(
            ["bash", str(setup_sh)],
            cwd=skill_dir,
            capture_output=True
        )


def uninstall_skill(name: str) -> bool:
    """卸载 Skill"""
    skill_dir = SKILLS_ROOT / name
    
    if not skill_dir.exists():
        print(f"Error: Skill '{name}' not found")
        return False
    
    # 从 Registry 注销
    registry = SkillRegistry()
    if name in registry.list_skills():
        # 从索引中移除
        import shutil
        index_file = Path(__file__).parent / "index.json"
        if index_file.exists():
            with open(index_file) as f:
                data = json.load(f)
            if name in data.get("skills", {}):
                del data["skills"][name]
                with open(index_file, "w") as f:
                    json.dump(data, f, indent=2)
    
    # 删除目录
    import shutil
    shutil.rmtree(skill_dir)
    
    print(f"✅ Uninstalled: {name}")
    return True


def update_skill(name: str) -> bool:
    """更新 Skill"""
    skill_dir = SKILLS_ROOT / name
    
    if not skill_dir.exists():
        print(f"Error: Skill '{name}' not found")
        return False
    
    # 检查是否是 Git 仓库
    git_dir = skill_dir / ".git"
    if git_dir.exists():
        print(f"Updating {name} from git...")
        result = subprocess.run(
            ["git", "-C", str(skill_dir), "pull"],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
    else:
        print(f"Warning: {name} is not a git repository, cannot update")
        return False
    
    # 重新安装依赖
    install_dependencies(skill_dir)
    
    # 重新注册
    registry = SkillRegistry()
    discovery = SkillDiscovery()
    discovery.auto_register(registry)
    
    # 健康检查
    print("Running health check...")
    reports = registry.health_check(name)
    report = reports.get(name)
    if report:
        from .health import HealthStatus
        if report.status == HealthStatus.HEALTHY:
            print(f"✅ Updated and healthy: {name}")
        else:
            print(f"⚠️ Updated but has issues: {name}")
            for issue in report.issues:
                print(f"   - {issue}")
    
    return True


def list_skills():
    """列出所有 Skill"""
    registry = SkillRegistry()
    skills = registry.list_skills()
    
    if not skills:
        print("No skills registered")
        return
    
    print(f"\n{'Name':<20} {'Version':<10} {'Status':<10} {'Description'}")
    print("-" * 70)
    
    for name in sorted(skills):
        skill = registry.get_skill_info(name)
        if skill:
            status = "✅" if skill.loaded else "⏸️"
            desc = skill.description[:30] + "..." if len(skill.description) > 30 else skill.description
            print(f"{name:<20} {skill.version:<10} {status:<10} {desc}")
    
    print(f"\nTotal: {len(skills)} skills")


def skill_info(name: str):
    """查看 Skill 详情"""
    registry = SkillRegistry()
    skill = registry.get_skill_info(name)
    
    if not skill:
        print(f"Error: Skill '{name}' not found")
        return
    
    print(f"\n{'='*50}")
    print(f"Skill: {skill.name}")
    print(f"{'='*50}")
    print(f"Version: {skill.version}")
    print(f"Description: {skill.description}")
    print(f"Path: {skill.path}")
    print(f"Loaded: {skill.loaded}")
    print(f"\nEntrypoint:")
    print(f"  Script: {skill.entrypoint.get('script')}")
    print(f"  Runtime: {skill.entrypoint.get('runtime')}")
    print(f"\nCapabilities:")
    for cap in skill.capabilities:
        print(f"  - {cap.name}: {cap.description}")
    print(f"\nPermissions:")
    for perm in skill.permissions:
        print(f"  - {perm}")


def doctor(name: Optional[str] = None):
    """健康检查"""
    registry = SkillRegistry()
    
    if name:
        # 检查单个
        reports = registry.health_check(name)
        report = reports.get(name)
        if report:
            from .health import SkillHealthChecker
            checker = SkillHealthChecker()
            checker.print_report(report)
    else:
        # 检查所有
        print("Checking all skills...\n")
        reports = registry.health_check()
        
        healthy = 0
        degraded = 0
        unhealthy = 0
        
        from .health import HealthStatus
        for skill_name, report in reports.items():
            if report.status == HealthStatus.HEALTHY:
                healthy += 1
            elif report.status == HealthStatus.DEGRADED:
                degraded += 1
            else:
                unhealthy += 1
        
        print(f"\n{'='*50}")
        print(f"Health Summary: {healthy} healthy, {degraded} degraded, {unhealthy} unhealthy")
        print(f"{'='*50}")


def rollback_skill(name: str, version: str) -> bool:
    """回滚版本"""
    registry = SkillRegistry()
    vm = registry.get_version_manager()
    
    if vm.rollback(name, version):
        print(f"✅ Rolled back {name} to {version}")
        return True
    else:
        print(f"Error: Cannot rollback {name} to {version}")
        return False


def main():
    """CLI 入口"""
    print("[legacy-skill-cli] This CLI is a migration-path interface. Prefer the new control-plane abstractions in core.infra.skill_manager for new governance work.")
    parser = argparse.ArgumentParser(
        description="Skill Lifecycle Manager",
        prog="skill"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # install
    install_parser = subparsers.add_parser("install", help="Install a skill")
    install_parser.add_argument("source", help="Source (github.com/... or /path/to/skill)")
    install_parser.add_argument("--name", "-n", help="Custom name")
    
    # uninstall
    uninstall_parser = subparsers.add_parser("uninstall", help="Uninstall a skill")
    uninstall_parser.add_argument("name", help="Skill name")
    
    # update
    update_parser = subparsers.add_parser("update", help="Update a skill")
    update_parser.add_argument("name", help="Skill name")
    
    # list
    subparsers.add_parser("list", help="List all skills")
    
    # info
    info_parser = subparsers.add_parser("info", help="Show skill info")
    info_parser.add_argument("name", help="Skill name")
    
    # doctor
    doctor_parser = subparsers.add_parser("doctor", help="Health check")
    doctor_parser.add_argument("name", nargs="?", help="Skill name (optional)")
    
    # rollback
    rollback_parser = subparsers.add_parser("rollback", help="Rollback to version")
    rollback_parser.add_argument("name", help="Skill name")
    rollback_parser.add_argument("version", help="Version to rollback")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # 执行命令
    if args.command == "install":
        install_skill(args.source, args.name)
    elif args.command == "uninstall":
        uninstall_skill(args.name)
    elif args.command == "update":
        update_skill(args.name)
    elif args.command == "list":
        list_skills()
    elif args.command == "info":
        skill_info(args.name)
    elif args.command == "doctor":
        doctor(args.name)
    elif args.command == "rollback":
        rollback_skill(args.name, args.version)


if __name__ == "__main__":
    main()
