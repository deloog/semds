"""
Test: Tool Design Principles Enforcement
测试工具设计原则的强制执行
"""

import sys

sys.path.insert(0, "D:\\semds")

from mother.core.enhanced_tool_generator import EnhancedToolGenerator
from mother.skills.code_optimizer import CodeOptimizer


def test_all_templates():
    """测试所有模板生成"""
    print("=" * 70)
    print("Testing Tool Generation with Principles Enforcement")
    print("=" * 70)

    generator = EnhancedToolGenerator()

    tools_to_test = [
        "html_parser",
        "csv_reader",
        "json_parser",
        "http_client",
        "file_reader",
    ]

    results = []

    for tool_name in tools_to_test:
        print(f"\n--- Testing: {tool_name} ---")
        code = generator.generate(tool_name)

        if code:
            # 检查关键特性
            checks = {
                "input_validation": "isinstance(" in code,
                "size_limits": "MAX_" in code or "max_" in code.lower(),
                "error_handling": "try:" in code and "except" in code,
                "no_eval": "eval(" not in code and "exec(" not in code,
                "has_docstring": '"""' in code or "'''" in code,
            }

            score = sum(checks.values()) / len(checks) * 100
            results.append({"name": tool_name, "score": score, "checks": checks})

            print(f"  Score: {score:.0f}%")
            for check, passed in checks.items():
                status = "OK" if passed else "FAIL"
                print(f"    [{status}] {check}")
        else:
            print(f"  Generation failed")
            results.append({"name": tool_name, "score": 0, "checks": {}})

    # 汇总
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)

    total_score = sum(r["score"] for r in results) / len(results)
    print(f"\nOverall Score: {total_score:.1f}%")

    for r in results:
        status = "PASS" if r["score"] >= 80 else "WARN" if r["score"] >= 60 else "FAIL"
        print(f"  [{status}] {r['name']}: {r['score']:.0f}%")

    if total_score >= 80:
        print("\n[OK] All tools meet design principles")
    else:
        print("\n[WARN] Some tools need improvement")

    return results


def test_code_optimizer():
    """测试代码优化器"""
    print("\n\n" + "=" * 70)
    print("Testing Code Optimizer")
    print("=" * 70)

    optimizer = CodeOptimizer()

    # 测试有问题的代码
    bad_code = """
import os
import json
import sys

def bad_function(data):
    result = eval(data)
    temp = result
    return temp

class TestTool:
    def execute(self, x):
        try:
            return x[0]
        except:
            return None
"""

    result = optimizer.optimize(bad_code, "bad_tool.py")

    print(f"\nOriginal Score: {result['original_score']}/100")
    print(f"Optimized Score: {result['optimized_score']}/100")
    print(f"Passed: {result['passed']}")

    errors = [i for i in result["issues"] if i.severity == "error"]
    warnings = [i for i in result["issues"] if i.severity == "warning"]

    print(f"Errors: {len(errors)}")
    print(f"Warnings: {len(warnings)}")

    if result["optimized_score"] > result["original_score"]:
        print("\n[OK] Auto-fix improved the code")
    else:
        print("\n[INFO] Code could not be significantly improved")

    return result


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("SEMDS Tool Design Principles Test Suite")
    print("=" * 70)
    print()
    print("Principles:")
    print("  1. Minimalism - Less code, more focus")
    print("  2. Security - Trust no input, validate everything")
    print("  3. Robustness - Handle errors gracefully")
    print()
    print("Enforcement: Code templates + Automated checks")
    print("=" * 70)

    try:
        test_all_templates()
    except Exception as e:
        print(f"\n[Error in template test: {e}]")
        import traceback

        traceback.print_exc()

    try:
        test_code_optimizer()
    except Exception as e:
        print(f"\n[Error in optimizer test: {e}]")
        import traceback

        traceback.print_exc()

    print("\n\n" + "=" * 70)
    print("Test Complete")
    print("=" * 70)
