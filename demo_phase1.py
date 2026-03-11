"""
SEMDS Phase 1 Demo - 单次进化循环演示

本脚本演示SEMDS的核心循环：
1. 创建计算器任务
2. 调用Claude API生成代码实现
3. 运行测试，获取pass_rate
4. 把结果存入SQLite
5. 打印结果

这是Phase 1的最小可运行系统，不包含进化循环。
"""

import os
import sys
import tempfile
from pathlib import Path

# 添加项目根目录到路径
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "storage"))
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))

# 导入SEMDS模块
from kernel import safe_write, append_audit_log
from code_generator import CodeGenerator
from test_runner import TestRunner
from database import init_database, get_session, close_database
from models import Task, Generation


# 计算器任务规格
CALCULATOR_TASK_SPEC = {
    "description": "进化出一个可靠的四则运算计算器函数",
    "function_signature": "def calculate(a: float, b: float, op: str) -> float:",
    "requirements": [
        "支持操作符: +, -, *, /",
        "除零时抛出ValueError",
        "操作符无效时抛出ValueError",
        "支持负数和浮点数"
    ]
}

# 测试文件路径
TEST_FILE_PATH = PROJECT_ROOT / "experiments" / "calculator" / "tests" / "test_calculator.py"


def check_environment() -> tuple[bool, str]:
    """
    检查运行环境是否满足要求。
    
    Returns:
        (is_ready, message): 是否就绪及提示信息
    """
    # 检查API密钥
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return False, (
            "错误：未设置ANTHROPIC_API_KEY环境变量\n"
            "请设置环境变量后再运行：\n"
            "  export ANTHROPIC_API_KEY='your-api-key'"
        )
    
    # 检查测试文件
    if not TEST_FILE_PATH.exists():
        return False, f"错误：测试文件不存在: {TEST_FILE_PATH}"
    
    # 检查pytest
    try:
        import pytest
    except ImportError:
        return False, (
            "错误：未安装pytest\n"
            "请安装：pip install pytest"
        )
    
    return True, "环境检查通过"


def create_task(session) -> Task:
    """
    在数据库中创建计算器任务。
    
    Args:
        session: 数据库会话
        
    Returns:
        创建的任务对象
    """
    task = Task(
        name="calculator_evolution",
        description=CALCULATOR_TASK_SPEC["description"],
        target_function_signature=CALCULATOR_TASK_SPEC["function_signature"],
        test_file_path=str(TEST_FILE_PATH),
        status="running",
        current_generation=0
    )
    
    session.add(task)
    session.commit()
    
    print(f"[1/5] 创建任务: {task.name} (ID: {task.id})")
    
    return task


def generate_code(task: Task) -> dict:
    """
    调用Claude API生成代码。
    
    Args:
        task: 任务对象
        
    Returns:
        生成结果字典
    """
    print("[2/5] 调用Claude API生成代码...")
    
    generator = CodeGenerator()
    
    # 准备策略（Phase 1使用默认策略）
    strategy = {
        "mutation_type": "conservative",
        "improvement_focus": "实现基本四则运算功能，正确处理除零和无效操作符"
    }
    
    result = generator.generate(
        task_spec=CALCULATOR_TASK_SPEC,
        previous_code=None,
        previous_score=None,
        failed_tests=None,
        strategy=strategy,
        temperature=0.5
    )
    
    if result["success"]:
        print("  ✓ 代码生成成功")
        print(f"  代码长度: {len(result['code'])} 字符")
    else:
        print(f"  ✗ 代码生成失败: {result['error']}")
    
    return result


def run_tests(code: str) -> dict:
    """
    运行测试并获取结果。
    
    Args:
        code: 生成的代码
        
    Returns:
        测试结果字典
    """
    print("[3/5] 运行测试...")
    
    runner = TestRunner(timeout_seconds=30, verbose=False)
    
    # 创建临时工作目录
    with tempfile.TemporaryDirectory(prefix="semds_phase1_") as work_dir:
        # 写入解决方案文件
        solution_path = Path(work_dir) / "solution.py"
        safe_write(str(solution_path), code)
        
        # 复制测试文件
        import shutil
        test_dest = Path(work_dir) / "test_calculator.py"
        shutil.copy(TEST_FILE_PATH, test_dest)
        
        # 运行测试
        result = runner.run_tests(
            test_file_path=str(test_dest),
            solution_file_path=str(solution_path),
            working_dir=work_dir
        )
    
    if result["success"]:
        passed = len(result["passed"])
        failed = len(result["failed"])
        total = result["total_tests"]
        pass_rate = result["pass_rate"]
        
        print(f"  ✓ 测试完成")
        print(f"  通过: {passed}/{total}")
        print(f"  失败: {failed}/{total}")
        print(f"  通过率: {pass_rate:.2%}")
        print(f"  执行时间: {result['execution_time_ms']:.2f} ms")
        
        if result["failed"]:
            print(f"  失败的测试: {', '.join(result['failed'])}")
    else:
        print(f"  ✗ 测试执行失败: {result['error']}")
    
    return result


def save_results(
    session,
    task: Task,
    code: str,
    test_result: dict
) -> Generation:
    """
    保存结果到数据库。
    
    Args:
        session: 数据库会话
        task: 任务对象
        code: 生成的代码
        test_result: 测试结果
        
    Returns:
        创建的代对象
    """
    print("[4/5] 保存结果到数据库...")
    
    generation = Generation(
        task_id=task.id,
        gen_number=0,
        code=code,
        strategy_used={
            "mutation_type": "conservative",
            "temperature": 0.5
        },
        intrinsic_score=test_result["pass_rate"],
        extrinsic_score=None,  # Phase 1不计算外生分
        final_score=test_result["pass_rate"],  # Phase 1简化为仅使用内生分
        test_pass_rate=test_result["pass_rate"],
        test_results={
            "passed": test_result["passed"],
            "failed": test_result["failed"],
            "total": test_result["total_tests"]
        },
        execution_time_ms=test_result["execution_time_ms"],
        sandbox_logs=test_result["raw_output"][:2000] if test_result["raw_output"] else None,
        goodhart_flag=False,
        human_reviewed=False,
        git_commit_hash=None  # Phase 1不使用Git
    )
    
    session.add(generation)
    
    # 更新任务状态
    task.best_score = test_result["pass_rate"]
    task.best_generation_id = generation.id
    task.status = "success" if test_result["pass_rate"] >= 0.95 else "paused"
    
    session.commit()
    
    print("  ✓ 结果已保存")
    
    return generation


def print_summary(task: Task, generation: Generation, test_result: dict):
    """
    打印结果摘要。
    
    Args:
        task: 任务对象
        generation: 代对象
        test_result: 测试结果
    """
    print("\n" + "=" * 50)
    print("SEMDS Phase 1 演示完成")
    print("=" * 50)
    
    passed = len(test_result["passed"])
    total = test_result["total_tests"]
    pass_rate = test_result["pass_rate"]
    
    print(f"\nGen 0 完成，得分：{pass_rate:.2f}，通过 {passed}/{total} 个测试")
    
    print(f"\n任务信息:")
    print(f"  - 任务ID: {task.id}")
    print(f"  - 任务名称: {task.name}")
    print(f"  - 当前状态: {task.status}")
    
    print(f"\n生成信息:")
    print(f"  - 代数: {generation.gen_number}")
    print(f"  - 综合得分: {generation.final_score:.4f}")
    print(f"  - 测试通过率: {generation.test_pass_rate:.2%}")
    print(f"  - 执行时间: {generation.execution_time_ms:.2f} ms")
    
    print(f"\n生成的代码:")
    print("-" * 50)
    print(generation.code)
    print("-" * 50)
    
    if test_result["failed"]:
        print(f"\n失败的测试:")
        for test_name in test_result["failed"]:
            print(f"  - {test_name}")


def main():
    """主函数。"""
    print("=" * 50)
    print("SEMDS Phase 1 - 单次进化循环演示")
    print("=" * 50)
    print()
    
    # 环境检查
    ready, message = check_environment()
    if not ready:
        print(message)
        sys.exit(1)
    print(message)
    print()
    
    # 初始化数据库
    print("初始化数据库...")
    init_database()
    print("  ✓ 数据库就绪")
    print()
    
    # 获取数据库会话
    session = get_session()
    
    try:
        # 1. 创建任务
        task = create_task(session)
        
        # 2. 生成代码
        gen_result = generate_code(task)
        if not gen_result["success"]:
            print(f"代码生成失败，演示终止: {gen_result['error']}")
            task.status = "failed"
            session.commit()
            return
        
        code = gen_result["code"]
        
        # 3. 运行测试
        test_result = run_tests(code)
        if not test_result["success"]:
            print(f"测试执行失败，演示终止: {test_result['error']}")
            task.status = "failed"
            session.commit()
            return
        
        # 4. 保存结果
        generation = save_results(session, task, code, test_result)
        
        # 5. 打印摘要
        print_summary(task, generation, test_result)
        
    except Exception as e:
        print(f"\n演示过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        session.close()
        close_database()
        print("\n数据库连接已关闭")


if __name__ == "__main__":
    main()
