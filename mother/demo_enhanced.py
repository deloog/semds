"""
SEMDS Enhanced Mother System - Demo
增强版母体系统演示
"""

import sys

sys.path.insert(0, r"D:\semds")

from dotenv import load_dotenv

load_dotenv(r"D:\semds\.env")

from mother.core.enhanced_mother import EnhancedMotherSystem


def main():
    print("=" * 70)
    print("SEMDS Enhanced Mother System - Autonomous Agent Demo")
    print("=" * 70)
    print()
    print("New Capabilities:")
    print("  1. Auto Web Search - Finds solutions when stuck")
    print("  2. Code Quality Check - Enforces coding standards")
    print("  3. Self Reflection - Learns from experience")
    print("  4. Auto Fix - Repairs code issues automatically")
    print()
    print("Standards Enforced:")
    print("  - Type annotations required")
    print("  - Docstrings mandatory")
    print("  - No bare except clauses")
    print("  - Security scanning enabled")
    print()
    print("=" * 70)

    mother = EnhancedMotherSystem()

    # Demo 1: 基本任务（应该成功）
    print("\n\n" + "=" * 70)
    print("DEMO 1: Basic Web Scraping Task")
    print("=" * 70)

    result1 = mother.execute("Fetch images from https://www.bing.com homepage")

    if result1["success"]:
        urls = result1["outputs"].get("extracted_data", [])
        print(f"\n[SUCCESS] Found {len(urls)} images")
    else:
        print(f"\n[FAIL] {result1.get('error')}")

    # Demo 2: 未知任务（会触发搜索学习）
    print("\n\n" + "=" * 70)
    print("DEMO 2: Unknown Task (Triggers Search)")
    print("=" * 70)

    result2 = mother.execute("Analyze sentiment of text using transformers")

    if result2["success"]:
        print("\n[SUCCESS] Task completed")
    else:
        print(f"\n[INFO] Task needs new capability")
        if "search_results" in result2.get("outputs", {}):
            print("Search results found - system can learn from these")

    # 打印自我报告
    print("\n\n" + "=" * 70)
    print("SELF REFLECTION REPORT")
    print("=" * 70)
    mother.print_self_report()

    print("\n" + "=" * 70)
    print("Demo Complete!")
    print("Check mother/memory/ for learning data")
    print("=" * 70)


if __name__ == "__main__":
    main()
