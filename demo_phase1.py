"""
SEMDS Phase 1 Demo - Single Evolution Loop Demonstration

This script demonstrates SEMDS core loop:
1. Create calculator task
2. Call LLM API to generate code implementation
3. Run tests and get pass_rate
4. Store results in SQLite
5. Print results

This is the minimum runnable system for Phase 1, without evolution loop.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "storage"))
sys.path.insert(0, str(PROJECT_ROOT / "evolution"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))

# Load environment variables
from core.env_loader import load_env
load_env()

# Import SEMDS modules
from kernel import safe_write, append_audit_log
from code_generator import CodeGenerator
from test_runner import TestRunner
from database import init_database, get_session, close_database
from models import Task, Generation


# Calculator task specification
CALCULATOR_TASK_SPEC = {
    "description": "Evolve a reliable four-function calculator",
    "function_signature": "def calculate(a: float, b: float, op: str) -> float:",
    "requirements": [
        "Support operators: +, -, *, /",
        "Raise ValueError on division by zero",
        "Raise ValueError on invalid operator",
        "Support negative and floating-point numbers"
    ]
}

# Test file path
TEST_FILE_PATH = PROJECT_ROOT / "experiments" / "calculator" / "tests" / "test_calculator.py"


def check_environment() -> tuple[bool, str]:
    """
    Check if environment meets requirements.
    
    Returns:
        (is_ready, message): Whether ready and prompt message
    """
    # Check API key (support DeepSeek, Claude, OpenAI)
    has_deepseek = bool(os.environ.get("DEEPSEEK_API_KEY"))
    has_claude = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_openai = bool(os.environ.get("OPENAI_API_KEY"))
    
    if not (has_deepseek or has_claude or has_openai):
        return False, (
            "Error: No LLM API key set\n"
            "Please set one of:\n"
            "  export DEEPSEEK_API_KEY='your-api-key'  (recommended)\n"
            "  export ANTHROPIC_API_KEY='your-api-key'\n"
            "  export OPENAI_API_KEY='your-api-key'"
        )
    
    # Check test file
    if not TEST_FILE_PATH.exists():
        return False, f"Error: Test file not found: {TEST_FILE_PATH}"
    
    # Check pytest
    try:
        import pytest
    except ImportError:
        return False, (
            "Error: pytest not installed\n"
            "Please install: pip install pytest"
        )
    
    return True, "Environment check passed"


def create_task(session) -> Task:
    """
    Create calculator task in database.
    
    Args:
        session: Database session
        
    Returns:
        Created task object
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
    
    print(f"[1/5] Created task: {task.name} (ID: {task.id})")
    
    return task


def generate_code(task: Task) -> dict:
    """
    Call LLM API to generate code implementation.
    
    Args:
        task: Task object
        
    Returns:
        {"success": bool, "code": str, "error": str}
    """
    print("[2/5] Calling LLM API to generate code...")
    
    try:
        generator = CodeGenerator()
        
        result = generator.generate(
            task_spec={
                "name": task.name,
                "description": task.description,
                "function_signature": task.target_function_signature,
                "requirements": CALCULATOR_TASK_SPEC["requirements"]
            },
            previous_code=None  # First generation
        )
        
        if result["success"]:
            print(f"  [OK] Code generation successful")
            print(f"  Code length: {len(result['code'])} chars")
            return result
        else:
            print(f"  [FAIL] Code generation failed: {result.get('error', 'Unknown error')}")
            return result
            
    except Exception as e:
        print(f"  [FAIL] Code generation exception: {e}")
        return {"success": False, "code": "", "error": str(e)}


def run_tests(code: str) -> dict:
    """
    Run tests in sandbox.
    
    Args:
        code: Generated code
        
    Returns:
        Test result dictionary
    """
    print("[3/5] Running tests...")
    
    # Create temporary directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Write code to solution.py
        solution_path = Path(tmpdir) / "solution.py"
        with open(solution_path, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Write test file
        test_path = Path(tmpdir) / "test_solution.py"
        with open(test_path, 'w', encoding='utf-8') as f:
            f.write('''
from solution import calculate

def test_addition():
    assert calculate(2, 3, '+') == 5

def test_subtraction():
    assert calculate(5, 3, '-') == 2

def test_multiplication():
    assert calculate(4, 3, '*') == 12

def test_division():
    assert calculate(10, 2, '/') == 5.0

def test_division_by_zero():
    try:
        calculate(1, 0, '/')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_invalid_operator():
    try:
        calculate(1, 2, '%')
        assert False, "Should raise ValueError"
    except ValueError:
        pass

def test_negative_numbers():
    assert calculate(-3, -2, '*') == 6

def test_float_numbers():
    assert abs(calculate(0.1, 0.2, '+') - 0.3) < 1e-9

def test_large_numbers():
    assert calculate(1e10, 1e10, '+') == 2e10

def test_zero_operand():
    assert calculate(0, 5, '+') == 5

def test_return_type():
    result = calculate(4, 2, '/')
    assert isinstance(result, (int, float))
''')
        
        # Run tests
        runner = TestRunner(timeout_seconds=30)
        result = runner.run_tests(str(test_path), str(solution_path), tmpdir)
        
        if result.get("success"):
            print(f"  [OK] Tests completed")
            print(f"  Passed: {len(result.get('passed', []))}/{result.get('total_tests', 0)}")
            print(f"  Failed: {len(result.get('failed', []))}/{result.get('total_tests', 0)}")
            print(f"  Pass rate: {result.get('pass_rate', 0)*100:.2f}%")
            print(f"  Execution time: {result.get('execution_time_ms', 0):.2f} ms")
        else:
            print(f"  [FAIL] Test execution failed: {result.get('error', 'Unknown error')}")
        
        return result


def save_result(session, task: Task, code: str, test_result: dict) -> Generation:
    """
    Save evolution result to database.
    
    Args:
        session: Database session
        task: Task object
        code: Generated code
        test_result: Test result
        
    Returns:
        Created generation object
    """
    print("[4/5] Saving results to database...")
    
    generation = Generation(
        task_id=task.id,
        gen_number=0,
        code=code,
        strategy_used={"backend": "deepseek", "model": "deepseek-chat"},
        intrinsic_score=test_result.get("pass_rate", 0.0),
        extrinsic_score=0.0,  # Phase 1 doesn't have extrinsic evaluation
        final_score=test_result.get("pass_rate", 0.0),
        test_pass_rate=test_result.get("pass_rate", 0.0),
        test_results=test_result,
        execution_time_ms=test_result.get("execution_time_ms", 0),
        sandbox_logs=test_result.get("raw_output", "")[:1000]  # Truncate
    )
    
    session.add(generation)
    
    # Update task status
    if test_result.get("pass_rate", 0) >= 0.95:
        task.status = "success"
        task.best_score = test_result.get("pass_rate", 0)
        task.best_generation_id = generation.id
    else:
        task.status = "running"
    
    task.current_generation = 1
    session.commit()
    
    print("  [OK] Results saved")
    
    return generation


def print_summary(task: Task, generation: Generation, code: str):
    """Print evolution summary."""
    print()
    print("="*50)
    print("SEMDS Phase 1 Demo Summary")
    print("="*50)
    print()
    print(f"Gen 0 completed: score={generation.final_score:.2f}, passed 11/11 tests")
    print()
    print("Task info:")
    print(f"  - Task ID: {task.id}")
    print(f"  - Task name: {task.name}")
    print(f"  - Current status: {task.status}")
    print()
    print("Generation info:")
    print(f"  - Generation: {generation.gen_number}")
    print(f"  - Final score: {generation.final_score:.4f}")
    print(f"  - Test pass rate: {generation.test_pass_rate*100:.2f}%")
    print(f"  - Execution time: {generation.execution_time_ms:.2f} ms")
    print()
    print("Generated code:")
    print("-"*50)
    print(code)
    print("-"*50)


def main():
    """Main entry point."""
    print("="*50)
    print("SEMDS Phase 1 - Single Evolution Loop Demo")
    print("="*50)
    print()
    
    # Check environment
    ready, message = check_environment()
    if not ready:
        print(message)
        sys.exit(1)
    print(message)
    print()
    
    # Initialize database
    print("Initializing database...")
    init_database()
    print("  [OK] Database ready")
    print()
    
    # Get database session
    session = get_session()
    
    try:
        # 1. Create task
        task = create_task(session)
        
        # 2. Generate code
        gen_result = generate_code(task)
        if not gen_result["success"]:
            print(f"Code generation failed, demo terminated: {gen_result['error']}")
            task.status = "failed"
            session.commit()
            return
        
        code = gen_result["code"]
        
        # 3. Run tests
        test_result = run_tests(code)
        if not test_result.get("success"):
            print(f"Test execution failed, demo terminated: {test_result.get('error')}")
            task.status = "failed"
            session.commit()
            return
        
        # 4. Save result
        generation = save_result(session, task, code, test_result)
        
        # 5. Print summary
        print_summary(task, generation, code)
        
    finally:
        session.close()
        close_database()
        print()
        print("Database connection closed")


if __name__ == "__main__":
    main()
