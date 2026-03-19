"""
SEMDS Live - 真正运行、自我进化、为你服务

不再演示，真实执行：
1. 接收你的任务
2. 调用DeepSeek生成代码
3. 执行测试
4. 记录真实结果
5. 根据结果自我改进
6. 部署运行中的服务

启动: python semds_live.py
"""

import os
import sys
import json
import time
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from mother.core.meta_evolution import MetaEvolutionEngine
from mother.lifecycle import LifecycleManager, DeploymentConfig
from evolution.code_generator import CodeGenerator
from evolution.test_runner import TestRunner


class SEMDSLive:
    """
    真正运行的SEMDS系统

    不只是演示，真实调用API，真实执行任务，真实自我进化。
    """

    def __init__(self):
        print("[SEMDS] Initializing live system...")

        # 检查API Key
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        if not self.api_key:
            # 尝试从.env读取
            env_file = Path(".env")
            if env_file.exists():
                with open(env_file, "r", encoding="utf-8") as f:
                    for line in f:
                        if line.startswith("DEEPSEEK_API_KEY="):
                            self.api_key = line.strip().split("=", 1)[1].strip("\"'")
                            os.environ["DEEPSEEK_API_KEY"] = self.api_key
                            break

        if not self.api_key:
            print("[ERROR] DeepSeek API Key not found!")
            print("  Set DEEPSEEK_API_KEY environment variable or add to .env")
            sys.exit(1)

        print(f"[SEMDS] API Key: {self.api_key[:8]}...{self.api_key[-4:]}")

        # 初始化组件
        self.code_gen = CodeGenerator(backend="deepseek")
        self.test_runner = TestRunner()
        self.meta_evolution = MetaEvolutionEngine()
        self.lifecycle = LifecycleManager()

        # 统计
        self.session_tasks = 0
        self.session_success = 0

        print("[SEMDS] System ready")
        print("[SEMDS] I will learn from every task you give me")

    def execute_task(self, description: str, test_cases: list = None) -> dict:
        """
        执行真实任务

        Args:
            description: 任务描述
            test_cases: 测试用例（可选）

        Returns:
            执行结果
        """
        print(f"\n{'='*60}")
        print(f"[TASK] {description}")
        print("=" * 60)

        start_time = time.time()
        self.session_tasks += 1

        try:
            # Step 1: 生成代码（真实调用DeepSeek）
            print("\n[1/4] Generating code via DeepSeek API...")
            print("      (this takes 2-5 seconds)...")

            # 构建提示词
            prompt = f"""
Write a Python function based on this description:
{description}

Requirements:
- Include type hints
- Include docstring
- Handle edge cases
- Return correct results

Just provide the code, no explanation.
"""

            generation_result = self.code_gen.generate(prompt)
            # 处理返回值（可能是字符串或字典）
            if isinstance(generation_result, dict):
                code = generation_result.get("code", "")
            else:
                code = str(generation_result)
            print(f"      Generated {len(code)} characters")

            # Step 2: 执行测试
            print("\n[2/4] Executing tests...")

            if test_cases:
                # 使用提供的测试用例
                test_code = "\n".join(test_cases)
            else:
                # 生成基本测试
                test_code = self._generate_basic_test(code)

            result = self.test_runner.run(code, test_code)

            if result.success:
                print(f"      ✓ Tests passed: {result.pass_rate:.0%}")
                self.session_success += 1
                success = True
                score = result.pass_rate
            else:
                print(f"      ✗ Tests failed: {result.pass_rate:.0%}")
                print(f"      Error: {result.error_message[:100]}")
                success = False
                score = result.pass_rate

            # Step 3: 记录结果（用于自我进化）
            print("\n[3/4] Recording for self-improvement...")

            generation_time = time.time() - start_time
            error_type = (
                self._classify_error(result.error_message) if not success else None
            )

            self.meta_evolution.record_generation_result(
                task_type=self._classify_task(description),
                success=success,
                score=score,
                generation_time=generation_time,
                error_type=error_type,
            )
            print("      Recorded")

            # Step 4: 如果成功，部署服务
            service_url = None
            if success and "api" in description.lower():
                print("\n[4/4] Deploying service...")
                service_url = self._deploy_service(code, description)
            else:
                print("\n[4/4] Deployment skipped (not an API service)")

            return {
                "success": success,
                "code": code,
                "score": score,
                "execution_time": generation_time,
                "service_url": service_url,
                "error": result.error_message if not success else None,
            }

        except Exception as e:
            print(f"\n[ERROR] {e}")

            # 记录失败
            self.meta_evolution.record_generation_result(
                task_type=self._classify_task(description),
                success=False,
                score=0.0,
                generation_time=time.time() - start_time,
                error_type="system_error",
            )

            return {"success": False, "error": str(e)}

    def evolve_self(self):
        """触发真实的自我进化"""
        print(f"\n{'='*60}")
        print("[SEMDS] Initiating self-evolution")
        print("=" * 60)

        result = self.meta_evolution.run_evolution_cycle()

        print(f"\n[RESULT]")
        print(f"  Hypotheses generated: {result.get('hypotheses_generated', 0)}")
        print(f"  Experiments run: {result.get('experiments_run', 0)}")
        print(f"  Improvements applied: {result.get('improvements_applied', 0)}")

        if result.get("improvements_applied", 0) > 0:
            print(f"\n  ✓✓✓ SEMDS HAS EVOLVED ✓✓✓")
            print(f"  Next tasks will use improved strategy")

        return result

    def show_stats(self):
        """显示当前统计"""
        print(f"\n{'='*60}")
        print("[SEMDS] Session Statistics")
        print("=" * 60)
        print(f"  Tasks executed: {self.session_tasks}")
        print(f"  Successful: {self.session_success}")
        print(
            f"  Success rate: {self.session_success/self.session_tasks*100:.1f}%"
            if self.session_tasks > 0
            else "  N/A"
        )

        print(f"\n[SEMDS] Self-Analysis")
        analysis = self.meta_evolution.telemetry.analyze_recent_performance(hours=24)

        if "error" not in analysis:
            print(f"  24h success rate: {analysis.get('success_rate', 0)*100:.1f}%")
            print(f"  Total generations: {analysis.get('total_generations', 0)}")
            if analysis.get("error_patterns"):
                print(f"  Error patterns: {analysis.get('error_patterns')}")

    def _deploy_service(self, code: str, description: str) -> str:
        """部署服务"""
        import random

        port = random.randint(8000, 9000)

        # 包装成FastAPI应用
        app_code = f"""
from fastapi import FastAPI
import uvicorn

app = FastAPI(title="SEMDS Generated Service")

{code}

@app.get("/")
def root():
    return {{"service": "generated by SEMDS", "status": "running"}}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port={port})
"""

        result = self.lifecycle.deploy_service(
            name=f"semds-service-{int(time.time())}",
            app_code=app_code,
            config=DeploymentConfig(name="semds-service", port=port),
            wait_for_healthy=False,
        )

        if result.status.value == "running":
            print(f"      Service running at: {result.service_url}")
            return result.service_url
        else:
            print(f"      Deployment failed: {result.error}")
            return None

    def _generate_basic_test(self, code: str) -> str:
        """生成基本测试"""
        # 提取函数名
        import re

        match = re.search(r"def\s+(\w+)\s*\(", code)
        if match:
            func_name = match.group(1)
            return f'''
import sys
sys.path.insert(0, '.')

# Import the generated code
exec("""
{code}
""")

# Basic test
assert {func_name} is not None
print("Basic import test passed")
'''
        return "print('No tests specified')"

    def _classify_task(self, description: str) -> str:
        """分类任务"""
        d = description.lower()
        if "api" in d:
            return "api_development"
        elif "scrape" in d:
            return "web_scraping"
        elif "sort" in d or "algorithm" in d:
            return "algorithm"
        else:
            return "general"

    def _classify_error(self, error_message: str) -> str:
        """分类错误"""
        if not error_message:
            return "unknown"
        e = error_message.lower()
        if "syntax" in e:
            return "syntax_error"
        elif "import" in e or "module" in e:
            return "import_error"
        elif "assert" in e:
            return "test_failure"
        else:
            return "runtime_error"


def main():
    """主交互循环"""
    print("\n" + "=" * 70)
    print("  SEMDS - Self-Evolving Meta-Development System")
    print("  LIVE MODE - Real API calls, real execution")
    print("=" * 70)

    # 初始化系统
    try:
        semds = SEMDSLive()
    except SystemExit:
        print("\n[SETUP] Please configure DeepSeek API key:")
        print("  1. Create .env file with: DEEPSEEK_API_KEY=your-key")
        print("  2. Or set environment variable: set DEEPSEEK_API_KEY=your-key")
        return

    # 交互循环
    while True:
        print("\n" + "-" * 70)
        print("Commands:")
        print("  [task]  - Execute a task (e.g., 'Create a calculator')")
        print("  evolve  - Trigger self-evolution")
        print("  stats   - Show statistics")
        print("  quit    - Exit")
        print("-" * 70)

        try:
            command = input("\nSEMDS> ").strip()
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break

        if command.lower() == "quit":
            semds.show_stats()
            print("\nGoodbye!")
            break

        elif command.lower() == "evolve":
            semds.evolve_self()

        elif command.lower() == "stats":
            semds.show_stats()

        elif command:
            # 执行任务
            result = semds.execute_task(command)

            print(f"\n[RESULT]")
            print(f"  Success: {result['success']}")
            print(f"  Score: {result.get('score', 0):.2f}")
            print(f"  Time: {result.get('execution_time', 0):.2f}s")

            if result.get("service_url"):
                print(f"  Service: {result['service_url']}")

            if not result["success"] and result.get("error"):
                print(f"  Error: {result['error'][:200]}")

            # 如果连续失败2次，建议进化
            if semds.session_tasks >= 3 and semds.session_success == 0:
                print(
                    f"\n[WARNING] Success rate is low ({semds.session_success}/{semds.session_tasks})"
                )
                print("  Consider running 'evolve' to improve strategy")


if __name__ == "__main__":
    main()
