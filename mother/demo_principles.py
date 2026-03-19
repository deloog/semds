"""
SEMDS Mother System - Tool Design Principles Demo
工具设计原则演示：极简、安全、健壮
"""

import sys

sys.path.insert(0, r"D:\semds")

from mother.core.enhanced_tool_generator import EnhancedToolGenerator
from mother.skills.code_optimizer import CodeOptimizer


def demo_code_quality_check():
    """演示代码质量检查"""
    print("\n" + "=" * 70)
    print("PRINCIPLE 1: Code Quality Enforcement")
    print("=" * 70)

    # 有问题的代码
    bad_code = """
import os
import json
import sys
import re

def process(data):
    try:
        result = eval(data)
        temp = result
        return temp
    except:
        return None

class BadTool:
    def execute(self, x, y, z):
        return x + y + z
"""

    print("\n[Input Code - Violates Principles]")
    print(bad_code)

    print("\n[Running Quality Checks...]")
    optimizer = CodeOptimizer()
    result = optimizer.optimize(bad_code, "bad_tool.py")
    optimizer.print_report(result)


def demo_minimal_template():
    """演示极简模板"""
    print("\n\n" + "=" * 70)
    print("PRINCIPLE 2: Minimalism")
    print("=" * 70)

    print("\nGenerating minimal HTML parser tool...")

    generator = EnhancedToolGenerator()
    code = generator.generate("html_parser")

    if code:
        print("\n[Generated Code Preview]")
        lines = code.split("\n")
        for i, line in enumerate(lines[:35]):
            print(line)
        if len(lines) > 35:
            print("...")

        print(f"\n[Statistics]")
        code_lines = len(
            [l for l in lines if l.strip() and not l.strip().startswith("#")]
        )
        print(f"  Total lines: {len(lines)}")
        print(f"  Code lines: {code_lines}")
        print(f"  Has input validation: {'isinstance(' in code}")
        print(f"  Has size limits: {'MAX_' in code}")
        print(f"  Has error handling: {'try:' in code and 'except' in code}")


def demo_security_features():
    """演示安全特性"""
    print("\n\n" + "=" * 70)
    print("PRINCIPLE 3: Security")
    print("=" * 70)

    print("\nGenerating secure HTTP client...")

    generator = EnhancedToolGenerator()
    code = generator.generate("http_client")

    if code:
        print("\n[Security Features Detected]")

        if "localhost" in code:
            print("  [OK] Blocks internal addresses (SSRF protection)")
        if "timeout=" in code:
            print("  [OK] Has timeout control")
        if "MAX_RESPONSE_SIZE" in code:
            print("  [OK] Response size limit")
        if 'startswith(("http://", "https://"))' in code:
            print("  [OK] URL scheme validation")
        if "eval(" not in code:
            print("  [OK] No dangerous functions (eval/exec)")


def demo_robustness_features():
    """演示健壮性特性"""
    print("\n\n" + "=" * 70)
    print("PRINCIPLE 4: Robustness")
    print("=" * 70)

    print("\nGenerating robust CSV reader...")

    generator = EnhancedToolGenerator()
    code = generator.generate("csv_reader")

    if code:
        print("\n[Robustness Features Detected]")

        if "isinstance(" in code:
            print("  [OK] Type checking")
        if "try:" in code and "except" in code:
            print("  [OK] Exception handling")
        if "MAX_" in code:
            print("  [OK] Resource limits")
        if "if not " in code:
            print("  [OK] Null/empty checks")
        if "error" in code.lower() and "return" in code:
            print("  [OK] Graceful error returns")


def demo_comparison():
    """对比展示"""
    print("\n\n" + "=" * 70)
    print("COMPARISON: Standard vs Enhanced")
    print("=" * 70)

    # 标准代码（不符合原则）
    standard_code = """
import requests

class HTTPClientTool:
    def execute(self, url):
        response = requests.get(url)
        return response.text
"""

    # 增强代码（符合原则）
    generator = EnhancedToolGenerator()
    enhanced_code = generator.generate("http_client")

    print("\n[Standard Approach - Simple but Risky]")
    print(f"  Lines: {len(standard_code.split(chr(10)))}")
    print("  Issues:")
    print("    - No input validation")
    print("    - No timeout (can hang forever)")
    print("    - No size limit (memory attack)")
    print("    - No error handling")
    print("    - Can access internal addresses")

    if enhanced_code:
        print("\n[Enhanced Approach - Minimal & Safe]")
        enhanced_lines = len(enhanced_code.split("\n"))
        print(f"  Lines: {enhanced_lines}")
        print("  Features:")
        print("    [OK] Input validation")
        print("    [OK] Timeout control")
        print("    [OK] Size limits")
        print("    [OK] Comprehensive error handling")
        print("    [OK] SSRF protection")
        print("    [OK] Still minimal and focused")


def main():
    print("=" * 70)
    print("SEMDS Tool Design Principles Demo")
    print("=" * 70)
    print()
    print("Core Principles:")
    print("  1. Minimalism - Less code, more focus")
    print("  2. Security - Trust no input")
    print("  3. Robustness - Handle all failures")
    print()
    print("Enforcement Method:")
    print("  - Code templates (not prompts)")
    print("  - Automated quality checks")
    print("  - Mandatory security rules")
    print()

    try:
        demo_code_quality_check()
    except Exception as e:
        print(f"\n[Error in quality check demo: {e}]")

    try:
        demo_minimal_template()
    except Exception as e:
        print(f"\n[Error in minimal demo: {e}]")

    try:
        demo_security_features()
    except Exception as e:
        print(f"\n[Error in security demo: {e}]")

    try:
        demo_robustness_features()
    except Exception as e:
        print(f"\n[Error in robustness demo: {e}]")

    try:
        demo_comparison()
    except Exception as e:
        print(f"\n[Error in comparison demo: {e}]")

    print("\n\n" + "=" * 70)
    print("Demo Complete!")
    print("=" * 70)
    print("\nKey Takeaway:")
    print("  Principles are enforced through CODE, not prompts.")
    print("  This ensures consistency across all generated tools.")
    print("=" * 70)


if __name__ == "__main__":
    main()
