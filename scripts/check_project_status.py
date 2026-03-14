#!/usr/bin/env python3
"""
项目状态检查脚本

快速检查 SEMDS 项目关键组件的状态。
供 AI Agent 快速了解项目当前状态。
"""

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent


def check_file_exists(filepath, description):
    """检查文件是否存在"""
    full_path = PROJECT_ROOT / filepath
    exists = full_path.exists()
    status = "[OK]" if exists else "[FAIL]"
    print(f"  {status} {description}: {filepath}")
    return exists


def check_env_var(var_name):
    """检查环境变量"""
    value = os.environ.get(var_name)
    status = "[OK]" if value else "[FAIL]"
    masked = value[:10] + "..." if value and len(value) > 10 else value
    print(f"  {status} {var_name}: {masked if value else 'not set'}")
    return bool(value)


def main():
    print("="*60)
    print("SEMDS Project Status Check")
    print("="*60)
    print()
    
    # Phase 1: Core Files
    print("[Phase 1: Core Skeleton]")
    p1_files = [
        ("core/kernel.py", "Safe write & audit log"),
        ("storage/models.py", "Database models"),
        ("evolution/code_generator.py", "Code generator"),
        ("evolution/test_runner.py", "Test runner"),
    ]
    p1_ok = sum(check_file_exists(f, d) for f, d in p1_files)
    print(f"  -> {p1_ok}/{len(p1_files)} P1 files")
    print()
    
    # Phase 3: Evolution Loop
    print("[Phase 3: Evolution Loop]")
    p3_files = [
        ("evolution/orchestrator.py", "Orchestrator"),
        ("evolution/strategy_optimizer.py", "Strategy optimizer"),
        ("evolution/dual_evaluator.py", "Dual evaluator"),
        ("evolution/termination_checker.py", "Termination checker"),
    ]
    p3_ok = sum(check_file_exists(f, d) for f, d in p3_files)
    print(f"  -> {p3_ok}/{len(p3_files)} P3 files")
    print()
    
    # Phase 4: API + Monitoring
    print("[Phase 4: API + Monitoring]")
    p4_files = [
        ("api/main.py", "FastAPI app"),
        ("api/routers/tasks.py", "Task router"),
        ("api/routers/evolution.py", "Evolution router"),
        ("api/routers/monitor.py", "Monitor router"),
        ("monitor/index.html", "Monitor UI"),
    ]
    p4_ok = sum(check_file_exists(f, d) for f, d in p4_files)
    print(f"  -> {p4_ok}/{len(p4_files)} P4 files")
    print()
    
    # Phase 5: Multi-Task
    print("[Phase 5: Multi-Task Concurrency]")
    p5_files = [
        ("factory/task_manager.py", "Task manager"),
        ("factory/isolation_manager.py", "Isolation manager"),
        ("factory/human_gate.py", "Human gate"),
    ]
    p5_ok = sum(check_file_exists(f, d) for f, d in p5_files)
    print(f"  -> {p5_ok}/{len(p5_files)} P5 files")
    print()
    
    # 文档
    print("[Documentation]")
    docs = [
        ("SEMDS_v1.1_SPEC.md", "Main specification"),
        ("docs/standards/DESIGN_DECISIONS.md", "Design decisions (CRITICAL)"),
        ("AGENTS.md", "AI Agent guide"),
        ("PROJECT_COMPLETION_REPORT.md", "Project completion report"),
    ]
    docs_ok = sum(check_file_exists(f, d) for f, d in docs)
    print(f"  -> {docs_ok}/{len(docs)} docs")
    print()
    
    # 环境变量
    print("[Environment Variables]")
    has_deepseek = check_env_var("DEEPSEEK_API_KEY")
    has_claude = check_env_var("ANTHROPIC_API_KEY")
    has_openai = check_env_var("OPENAI_API_KEY")
    
    if has_deepseek:
        print("  -> Using: DeepSeek API (recommended)")
    elif has_claude:
        print("  -> Using: Claude API")
    elif has_openai:
        print("  -> Using: OpenAI API")
    else:
        print("  -> [WARN] No LLM API key configured!")
    print()
    
    # 关键设计决策提醒
    print("[Design Decisions Summary]")
    print("  [OK] DD-001: Using subprocess + tempfile (NOT Docker)")
    print("  [OK] DD-002: DeepSeek API as default LLM")
    print("  [OK] DD-003: SQLite as default database")
    print()
    
    # 测试
    print("[Quick Import Test]")
    try:
        sys.path.insert(0, str(PROJECT_ROOT))
        from core.kernel import safe_write
        print("  [OK] kernel.py imports")
        
        from evolution.test_runner import TestRunner
        print("  [OK] test_runner.py imports")
        
        from storage.models import Task, Generation
        print("  [OK] models.py imports")
        
        from api.main import app
        print("  [OK] api.main imports")
        
        imports_ok = True
    except Exception as e:
        print(f"  [FAIL] Import error: {e}")
        imports_ok = False
    print()
    
    # 总结
    print("="*60)
    print("Summary")
    print("="*60)
    
    all_phases_ok = p1_ok == len(p1_files) and p3_ok == len(p3_files) and p4_ok == len(p4_files) and p5_ok == len(p5_files)
    
    if all_phases_ok and imports_ok:
        print("Status: [OK] ALL PHASES COMPLETE (1-5)")
        print()
        print("Quick Start:")
        print("  1. python demo_phase1.py         # Test Phase 1")
        print("  2. python demo_phase3_evolution.py # Test Phase 3")
        print("  3. python -m uvicorn api.main:app  # Start API server")
        print("  4. Open http://127.0.0.1:8000/monitor")
    else:
        print("Status: [INCOMPLETE] Some components missing")
        print(f"  Phase 1: {p1_ok}/{len(p1_files)}")
        print(f"  Phase 3: {p3_ok}/{len(p3_files)}")
        print(f"  Phase 4: {p4_ok}/{len(p4_files)}")
        print(f"  Phase 5: {p5_ok}/{len(p5_files)}")
    
    print()
    print("Documentation:")
    print("  - Read: docs/standards/DESIGN_DECISIONS.md")
    print("  - Read: PROJECT_COMPLETION_REPORT.md")
    print("  - Spec: SEMDS_v1.1_SPEC.md")
    
    return 0 if (all_phases_ok and imports_ok) else 1


if __name__ == "__main__":
    sys.exit(main())
