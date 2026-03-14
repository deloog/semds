#!/usr/bin/env python3
"""
SEMDS 计算器进化实验 - 完整版
多代进化直到通过率达到 95% 或达到最大代数

根据 SEMDS v1.1 规格：
- Gen 0: LLM冷启动，预期得分0.5-0.7
- Gen 1-3: 修复明显错误，预期得分0.75-0.85
- Gen 4-8: 边界用例改进，预期得分0.88-0.95
- Gen 9+: 微调优化
"""

import os
import sys
import json
import tempfile
import time
from pathlib import Path
from datetime import datetime

# 添加项目路径
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "storage"))
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))

from env_loader import load_env
load_env()

from kernel import safe_write
from code_generator import CodeGenerator
from test_runner import TestRunner
from database import init_database, get_session, close_database
from models import Task, Generation


# 计算器任务规格
CALCULATOR_TASK = {
    "name": "calculator_evolution",
    "description": "进化出一个可靠的四则运算计算器函数",
    "function_signature": "def calculate(a: float, b: float, op: str) -> float:",
    "requirements": [
        "支持操作符: +, -, *, /",
        "除零时抛出ValueError",
        "操作符无效时抛出ValueError",
        "支持负数和浮点数"
    ]
}

TEST_FILE_PATH = PROJECT_ROOT / "experiments" / "calculator" / "tests" / "test_calculator.py"

# 进化终止条件
TERMINATION_CONFIG = {
    "success_threshold": 0.95,      # 通过率达到95%视为成功
    "max_generations": 15,          # 最大15代
    "max_wall_time_minutes": 30,    # 最长30分钟
    "stagnation_generations": 5     # 连续5代无改进则停止
}


def check_environment():
    """检查环境是否就绪"""
    from env_loader import check_api_key
    ready, message = check_api_key()
    if not ready:
        print(f"[ERROR] {message}")
        return False
    
    if not TEST_FILE_PATH.exists():
        print(f"[ERROR] 测试文件不存在: {TEST_FILE_PATH}")
        return False
    
    print(f"[DONE] {message}")
    return True


def run_tests(code: str) -> dict:
    """运行测试并返回结果"""
    # 创建临时文件
    with tempfile.TemporaryDirectory(prefix="semds_evolution_") as work_dir:
        solution_path = Path(work_dir) / "solution.py"
        safe_write(str(solution_path), code)
        
        import shutil
        test_dest = Path(work_dir) / "test_calculator.py"
        shutil.copy(TEST_FILE_PATH, test_dest)
        
        # 运行测试
        runner = TestRunner(timeout_seconds=30, verbose=False)
        result = runner.run_tests(
            test_file_path=str(test_dest),
            solution_file_path=str(solution_path),
            working_dir=work_dir
        )
    
    return result


def create_strategy(generation: int, previous_score: float, failed_tests: list) -> dict:
    """
    根据当前代数和前代表现创建进化策略
    
    Args:
        generation: 当前代数
        previous_score: 前代得分
        failed_tests: 前代失败的测试列表
    
    Returns:
        策略字典
    """
    if generation == 0:
        return {
            "mutation_type": "conservative",
            "improvement_focus": "实现基本四则运算功能，正确处理除零和无效操作符",
            "temperature": 0.5
        }
    
    if previous_score < 0.5:
        # 得分很低，激进重写
        return {
            "mutation_type": "aggressive",
            "improvement_focus": "完全重写核心逻辑，参考失败测试: " + ", ".join(failed_tests[:3]),
            "temperature": 0.7
        }
    
    if previous_score < 0.8:
        # 中等得分，针对性修复
        return {
            "mutation_type": "hybrid",
            "improvement_focus": "修复失败的测试用例: " + ", ".join(failed_tests),
            "temperature": 0.5
        }
    
    if previous_score < 0.95:
        # 接近成功，微调优化
        return {
            "mutation_type": "conservative",
            "improvement_focus": "优化边界情况处理，提高健壮性，关注: " + ", ".join(failed_tests[:2]),
            "temperature": 0.3
        }
    
    # 已达目标，极微调
    return {
        "mutation_type": "conservative",
        "improvement_focus": "代码清理和优化，保持现有功能",
        "temperature": 0.2
    }


def run_evolution():
    """运行完整进化实验"""
    print("="*70)
    print("🧬 SEMDS 计算器进化实验")
    print("="*70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标: 通过率达到 {TERMINATION_CONFIG['success_threshold']*100}%")
    print(f"最大代数: {TERMINATION_CONFIG['max_generations']}")
    print("="*70)
    
    # 检查环境
    if not check_environment():
        sys.exit(1)
    
    # 初始化数据库
    print("\n📊 初始化数据库...")
    init_database()
    session = get_session()
    
    try:
        # 创建任务
        task = Task(
            name=CALCULATOR_TASK["name"],
            description=CALCULATOR_TASK["description"],
            target_function_signature=CALCULATOR_TASK["function_signature"],
            test_file_path=str(TEST_FILE_PATH),
            status="running",
            current_generation=0
        )
        session.add(task)
        session.commit()
        print(f"[DONE] 任务创建: {task.name} (ID: {task.id})")
        
        # 初始化代码生成器
        generator = CodeGenerator(backend="deepseek")
        
        # 进化循环
        best_score = 0.0
        best_generation = None
        stagnation_count = 0
        start_time = time.time()
        
        print("\n" + "="*70)
        print("🚀 开始进化循环")
        print("="*70)
        
        for gen in range(TERMINATION_CONFIG["max_generations"]):
            print(f"\n{'='*70}")
            print(f"🧬 Generation {gen}")
            print(f"{'='*70}")
            
            # 检查超时
            elapsed = (time.time() - start_time) / 60
            if elapsed > TERMINATION_CONFIG["max_wall_time_minutes"]:
                print(f"\n⏰ 达到最大运行时间 ({TERMINATION_CONFIG['max_wall_time_minutes']}分钟)，终止进化")
                break
            
            # 获取前代信息
            previous_code = None
            previous_score = None
            failed_tests = None
            
            if gen > 0:
                prev_gen = session.query(Generation).filter_by(
                    task_id=task.id, 
                    gen_number=gen-1
                ).first()
                if prev_gen:
                    previous_code = prev_gen.code
                    previous_score = prev_gen.test_pass_rate
                    failed_tests = json.loads(prev_gen.test_results).get("failed", [])
                    print(f"📊 前代得分: {previous_score:.2%}")
                    print(f"[ERROR] 失败测试: {failed_tests}")
            
            # 创建策略
            strategy = create_strategy(gen, previous_score or 0, failed_tests or [])
            print(f"📋 进化策略: {strategy['mutation_type']}")
            print(f"[GOAL] 改进重点: {strategy['improvement_focus']}")
            
            # 生成代码
            print(f"\n💻 生成代码 (temperature={strategy['temperature']})...")
            gen_result = generator.generate(
                task_spec=CALCULATOR_TASK,
                previous_code=previous_code,
                previous_score={"intrinsic_score": previous_score} if previous_score else None,
                failed_tests=failed_tests,
                strategy=strategy,
                temperature=strategy['temperature']
            )
            
            if not gen_result["success"]:
                print(f"[ERROR] 代码生成失败: {gen_result.get('error')}")
                continue
            
            code = gen_result["code"]
            print(f"[DONE] 代码生成成功，长度: {len(code)} 字符")
            
            # 运行测试
            print(f"\n🧪 运行测试...")
            test_result = run_tests(code)
            
            if not test_result["success"]:
                print(f"[ERROR] 测试执行失败: {test_result.get('error')}")
                pass_rate = 0.0
                passed = 0
                failed = 10
            else:
                pass_rate = test_result["pass_rate"]
                passed = len(test_result["passed"])
                failed = len(test_result["failed"])
                print(f"📊 测试结果: {passed}/{passed+failed} 通过 ({pass_rate:.2%})")
                if test_result["failed"]:
                    print(f"[ERROR] 失败: {', '.join(test_result['failed'][:5])}")
            
            # 保存结果到数据库
            generation = Generation(
                task_id=task.id,
                gen_number=gen,
                code=code,
                strategy_used=strategy,
                intrinsic_score=pass_rate,
                extrinsic_score=None,  # Phase 1 暂不计算
                final_score=pass_rate,
                test_pass_rate=pass_rate,
                test_results={
                    "passed": test_result.get("passed", []),
                    "failed": test_result.get("failed", []),
                    "total": test_result.get("total_tests", 10)
                },
                execution_time_ms=test_result.get("execution_time_ms", 0),
                goodhart_flag=False,
                human_reviewed=False
            )
            session.add(generation)
            
            # 更新最佳记录
            if pass_rate > best_score:
                best_score = pass_rate
                best_generation = gen
                stagnation_count = 0
                task.best_score = best_score
                task.best_generation_id = generation.id
                print(f"🌟 新的最佳记录！Gen {gen}: {best_score:.2%}")
            else:
                stagnation_count += 1
                print(f"📉 未改进，连续 {stagnation_count} 代无提升")
            
            task.current_generation = gen
            session.commit()
            
            # 检查终止条件
            if pass_rate >= TERMINATION_CONFIG["success_threshold"]:
                print(f"\n[SUCCESS] 达到目标！通过率达到 {pass_rate:.2%} >= {TERMINATION_CONFIG['success_threshold']*100}%")
                task.status = "success"
                break
            
            if stagnation_count >= TERMINATION_CONFIG["stagnation_generations"]:
                print(f"\n⛔ 连续 {stagnation_count} 代无改进，终止进化")
                task.status = "paused"
                break
            
            # 延迟避免API限流
            if gen < TERMINATION_CONFIG["max_generations"] - 1:
                print("\n⏳ 等待3秒...")
                time.sleep(3)
        
        else:
            print(f"\n⛔ 达到最大代数 {TERMINATION_CONFIG['max_generations']}，终止进化")
            task.status = "paused"
        
        session.commit()
        
        # 打印最终报告
        print_summary(session, task)
        
    except Exception as e:
        print(f"\n[ERROR] 进化过程中出错: {e}")
        import traceback
        traceback.print_exc()
        task.status = "failed"
        session.commit()
    
    finally:
        session.close()
        close_database()


def print_summary(session, task):
    """打印实验摘要"""
    print("\n" + "="*70)
    print("📊 实验摘要")
    print("="*70)
    
    generations = session.query(Generation).filter_by(task_id=task.id).order_by(Generation.gen_number).all()
    
    print(f"\n任务: {task.name}")
    print(f"状态: {task.status}")
    print(f"总代数: {len(generations)}")
    print(f"最佳得分: {task.best_score:.2%}" if task.best_score else "最佳得分: N/A")
    print(f"最佳代数: Gen {generations[-1].gen_number if generations else 'N/A'}")
    
    print(f"\n📈 进化轨迹:")
    print("-"*70)
    print(f"{'Gen':<5} {'Pass Rate':<12} {'Strategy':<15} {'Improvement'}")
    print("-"*70)
    
    prev_score = 0
    for gen in generations:
        strategy = gen.strategy_used.get("mutation_type", "unknown") if gen.strategy_used else "unknown"
        improvement = gen.test_pass_rate - prev_score
        improvement_str = f"+{improvement:.2%}" if improvement > 0 else f"{improvement:.2%}" if improvement < 0 else "-"
        print(f"{gen.gen_number:<5} {gen.test_pass_rate:<12.2%} {strategy:<15} {improvement_str}")
        prev_score = gen.test_pass_rate
    
    print("-"*70)
    
    if task.best_score and task.best_score >= TERMINATION_CONFIG["success_threshold"]:
        print(f"\n[DONE] 实验成功！达到目标通过率 {TERMINATION_CONFIG['success_threshold']*100}%")
    else:
        print(f"\n[WARN]  实验未达标。最高通过率: {task.best_score:.2% if task.best_score else 0}")
    
    # 显示最佳代码
    best_gen = session.query(Generation).filter_by(id=task.best_generation_id).first()
    if best_gen:
        print(f"\n🏆 最佳实现 (Gen {best_gen.gen_number}):")
        print("-"*70)
        print(best_gen.code)
        print("-"*70)


if __name__ == "__main__":
    run_evolution()
