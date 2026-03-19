"""
演示：逻辑分解 vs 物理组装

解决文件数量爆炸问题：
- 逻辑上分解成原子任务（便于验证）
- 物理上组装为合适模块（便于维护）
"""

import sys

sys.path.insert(0, "D:\\semds")

from mother.task_decomposer.decomposer import AtomicTask, TaskType
from mother.task_decomposer.code_assembler import CodeAssembler


def demo_without_assembly():
    """演示：不使用组装（文件爆炸）"""
    print("=" * 70)
    print("SCENARIO 1: Without Assembly (File Explosion)")
    print("=" * 70)
    print()

    # 模拟一个复杂系统的原子任务
    tasks = [
        "fetch_data() - 获取数据",
        "validate_input() - 验证输入",
        "parse_json() - 解析JSON",
        "transform_data() - 转换数据",
        "validate_output() - 验证输出",
        "save_to_db() - 保存到数据库",
        "handle_error() - 错误处理",
        "log_operation() - 记录日志",
    ]

    print(f"Complex system decomposed into {len(tasks)} atomic tasks")
    print()
    print("Without assembly:")
    for i, task in enumerate(tasks, 1):
        print(f"  {i}. {task}.py (15 lines)")

    print()
    print("Result:")
    print(f"  - Total files: {len(tasks)}")
    print(f"  - Average size: 15 lines")
    print(f"  - Problems:")
    print(f"    * Too many small files")
    print(f"    * Hard to navigate")
    print(f"    * Context scattered")
    print(f"    * Import chaos")


def demo_with_assembly():
    """演示：使用智能组装（合理文件数）"""
    print("\n\n" + "=" * 70)
    print("SCENARIO 2: With Smart Assembly")
    print("=" * 70)
    print()

    # 创建原子任务
    mock_tasks = [
        AtomicTask(
            id="t1",
            name="fetch_data",
            description="Fetch data from API",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def fetch_data(url: str, timeout: int = 30) -> dict:
    """Fetch data from URL."""
    import requests
    
    if not isinstance(url, str):
        raise ValueError("URL must be string")
    
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return {"data": response.json(), "status": response.status_code}
    except requests.RequestException as e:
        return {"error": str(e)}
''',
        ),
        AtomicTask(
            id="t2",
            name="validate_input",
            description="Validate input data",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def validate_input(data: dict) -> bool:
    """Validate input data structure."""
    required_fields = ['id', 'name', 'value']
    
    if not isinstance(data, dict):
        return False
    
    return all(field in data for field in required_fields)
''',
        ),
        AtomicTask(
            id="t3",
            name="transform_data",
            description="Transform data format",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def transform_data(raw: dict) -> dict:
    """Transform raw data to standard format."""
    return {
        "id": raw.get("id"),
        "name": raw.get("name", "").strip(),
        "value": float(raw.get("value", 0)),
        "timestamp": raw.get("timestamp")
    }
''',
        ),
        AtomicTask(
            id="t4",
            name="save_to_db",
            description="Save data to database",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def save_to_db(data: dict) -> bool:
    """Save data to database."""
    import sqlite3
    
    conn = sqlite3.connect("data.db")
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            "INSERT INTO records (id, name, value) VALUES (?, ?, ?)",
            (data["id"], data["name"], data["value"])
        )
        conn.commit()
        return True
    except Exception as e:
        print(f"Save failed: {e}")
        return False
    finally:
        conn.close()
''',
        ),
        AtomicTask(
            id="t5",
            name="test_fetch",
            description="Test fetch function",
            task_type=TaskType.TEST,
            actual_output="""
import pytest
from data_module import fetch_data

def test_fetch_success():
    result = fetch_data("https://api.example.com/data")
    assert "data" in result

def test_fetch_error():
    result = fetch_data("invalid-url")
    assert "error" in result

def test_fetch_timeout():
    result = fetch_data("https://slow.api.com", timeout=1)
    assert isinstance(result, dict)
""",
        ),
    ]

    print(f"Complex system decomposed into {len(mock_tasks)} atomic tasks")
    print()

    # 使用组装器
    assembler = CodeAssembler()
    modules = assembler.assemble(mock_tasks)
    files = assembler.generate_file_structure(modules)

    print("With smart assembly:")
    for filename, content in files.items():
        lines = len(content.split("\n"))
        print(f"  - {filename} ({lines} lines)")

    print()
    print("Assembly Strategy:")
    print("  - Related functions grouped into modules")
    print("  - Tests separated into test files")
    print("  - Imports consolidated at file level")
    print("  - Size optimized (50-300 lines per file)")

    print()
    print("Result:")
    print(f"  - Total files: {len(files)}")
    print(
        f"  - Average size: {sum(len(c.split(chr(10))) for c in files.values()) // len(files)} lines"
    )
    print(f"  - Benefits:")
    print(f"    * Manageable file count")
    print(f"    * Logical organization")
    print(f"    * Easy to navigate")
    print(f"    * Clean imports")


def print_comparison():
    """打印对比"""
    print("\n\n" + "=" * 70)
    print("COMPARISON")
    print("=" * 70)
    print()

    print("Without Assembly:")
    print("  Atomic tasks: 20")
    print("  Output files: 20 (1 task = 1 file)")
    print("  File sizes: 10-30 lines each")
    print("  Maintainability: POOR")
    print()

    print("With Smart Assembly:")
    print("  Atomic tasks: 20")
    print("  Output files: 3-5 (grouped by function)")
    print("  File sizes: 100-250 lines each")
    print("  Maintainability: GOOD")
    print()

    print("Key Insight:")
    print("  - Decomposition is for EXECUTION and VERIFICATION")
    print("  - Assembly is for MAINTAINABILITY")
    print("  - They serve different purposes!")


def print_architecture():
    """打印架构"""
    print("\n\n" + "=" * 70)
    print("Complete Architecture: Decompose + Assemble")
    print("=" * 70)
    print("""
Step 1: RECURSIVE DECOMPOSITION
  Complex Task
    ├── Subtask A
    │     ├── Atomic 1 (<50 lines)
    │     ├── Atomic 2 (<50 lines)
    │     └── Atomic 3 (<50 lines)
    ├── Subtask B
    │     ├── Atomic 4 (<50 lines)
    │     └── Atomic 5 (<50 lines)
    └── Subtask C
          ├── Atomic 6 (<50 lines)
          └── Atomic 7 (<50 lines)

Step 2: TDD EXECUTION
  Each atomic task:
    - Write test (Red)
    - Implement (Green)
    - Validate (Pass)

Step 3: SMART ASSEMBLY
  Group by function domain:
    
    data_fetcher.py (150 lines)
      - fetch_data()
      - validate_input()
      
    data_processor.py (180 lines)
      - parse_json()
      - transform_data()
      - validate_output()
      
    data_storage.py (120 lines)
      - save_to_db()
      - handle_error()
      - log_operation()
      
    test_data_module.py (200 lines)
      - All test functions

Result: 4 files instead of 20!
""")


def print_thresholds():
    """打印组装阈值"""
    print("\n" + "=" * 70)
    print("Assembly Thresholds")
    print("=" * 70)
    print()

    print("Target File Sizes:")
    print("  - Minimum:  50 lines (smaller will be merged)")
    print("  - Ideal:    150 lines")
    print("  - Maximum:  300 lines (larger will be split)")
    print()

    print("Grouping Rules:")
    print("  1. By functional domain (fetch, parse, store)")
    print("  2. By data flow (input -> process -> output)")
    print("  3. By cohesion (related operations together)")
    print()

    print("Separation Rules:")
    print("  1. Tests always in separate file")
    print("  2. Interface definitions can be in header")
    print("  3. Utils/helpers grouped together")


def main():
    print("=" * 70)
    print("Smart Assembly: Solving File Explosion Problem")
    print("=" * 70)
    print()
    print("Concern: Decomposition creates too many small files")
    print("Solution: Logical decomposition + Physical assembly")
    print()

    demo_without_assembly()
    demo_with_assembly()
    print_comparison()
    print_architecture()
    print_thresholds()

    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print()
    print("Decomposition: FOR AI (execution & verification)")
    print("  - Small tasks reduce hallucination")
    print("  - Each task verifiable")
    print("  - Execution trace proves completeness")
    print()
    print("Assembly: FOR HUMANS (maintenance & readability)")
    print("  - Reasonable file count")
    print("  - Logical organization")
    print("  - Easy to understand")
    print()
    print("Best of Both Worlds!")
    print("=" * 70)


if __name__ == "__main__":
    main()
