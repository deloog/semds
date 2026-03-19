"""
SEMDS Mother System - Skills Demo
技能展示：搜索、代码质量、自我反思
"""
import sys
sys.path.insert(0, r'D:\semds')

from mother.skills.web_search import WebSearchSkill
from mother.skills.code_quality import check_code, fix_code
from mother.skills.self_reflection import SelfReflection


def demo_web_search():
    """演示联网搜索"""
    print("\n" + "="*70)
    print("SKILL 1: Web Search")
    print("="*70)
    
    searcher = WebSearchSkill()
    
    # 搜索代码示例
    print("\n[Query] Python requests tutorial")
    results = searcher.search("Python requests tutorial", num_results=3)
    
    print(f"\nFound {len(results)} results:")
    for i, r in enumerate(results, 1):
        print(f"\n  {i}. {r.title}")
        print(f"     URL: {r.url}")
        print(f"     {r.snippet[:80]}...")
    
    # 搜索错误解决方案
    print("\n" + "-"*70)
    print("\n[Query] Error solution search")
    error = "TypeError: 'NoneType' object is not subscriptable"
    solutions = searcher.search_for_solution(error, "dictionary access")
    
    print(f"\nError: {error}")
    print(f"Found {len(solutions)} potential solutions:")
    for s in solutions:
        print(f"\n  Confidence: {s['confidence']:.0%}")
        print(f"  Source: {s['source']}")
        print(f"  Suggestion: {s['suggestion'][:100]}...")


def demo_code_quality():
    """演示代码质量检查"""
    print("\n\n" + "="*70)
    print("SKILL 2: Code Quality Checker")
    print("="*70)
    
    # 有问题的代码示例
    bad_code = '''
def process_data(data):
    result = eval(data)  # Security issue!
    return result

class DataHandler:
    def method(self, x):
        try:
            return x[0]
        except:  # Bare except
            return None

def bad_func(x,y):  # Missing types, spaces
    return x+y
'''
    
    print("\n[Input Code]")
    print(bad_code)
    
    print("\n[Running Quality Checks...]")
    result = check_code(bad_code, "test.py")
    
    print(f"\nScore: {result['score']:.1f}/100")
    print(f"Passed: {result['passed']}")
    print(f"Issues Found: {len(result['issues'])}")
    
    print("\n[Issues by Severity]")
    errors = [i for i in result['issues'] if i.severity == 'error']
    warnings = [i for i in result['issues'] if i.severity == 'warning']
    
    if errors:
        print(f"\n  ERRORS ({len(errors)}):")
        for e in errors:
            print(f"    Line {e.line}: {e.code}")
            print(f"      -> {e.message}")
    
    if warnings:
        print(f"\n  WARNINGS ({len(warnings)}):")
        for w in warnings[:3]:  # 只显示前3个
            print(f"    Line {w.line}: {w.code}")
            print(f"      -> {w.message}")


def demo_self_reflection():
    """演示自我反思"""
    print("\n\n" + "="*70)
    print("SKILL 3: Self Reflection")
    print("="*70)
    
    reflection = SelfReflection()
    
    # 模拟一些执行记录
    print("\n[Simulating task executions...]")
    
    tasks = [
        ("Fetch weather data", True, ["http_client"], []),
        ("Parse HTML table", False, ["html_parser"], 
         ["ImportError: No module named 'bs4'"]),
        ("Calculate statistics", True, ["csv_reader", "math"], []),
        ("Generate chart", False, ["chart_generator"], 
         ["ValueError: invalid data format"]),
        ("Send email", True, ["smtp_client"], []),
    ]
    
    for desc, success, caps, errors in tasks:
        reflection.record_execution(
            task_description=desc,
            success=success,
            duration=2.0,
            capabilities_used=caps,
            errors=errors
        )
        status = "OK" if success else "FAIL"
        print(f"  [{status}] {desc}")
    
    # 生成报告
    print("\n[Generating Reflection Report...]")
    report = reflection.generate_reflection_report()
    
    print(f"\nTotal Tasks: {report['total_tasks']}")
    print(f"Success Rate: {report['success_rate']:.1f}%")
    print(f"Avg Duration: {report['avg_duration']:.2f}s")
    
    print("\nTop Capabilities:")
    for cap, count in report['top_capabilities']:
        print(f"  - {cap}: {count} uses")
    
    if report['common_errors']:
        print("\nCommon Errors:")
        for e in report['common_errors']:
            print(f"  - {e['type']}: {e['count']} times")
    
    print("\nSuggestions:")
    for s in report['suggestions']:
        print(f"  * {s}")


def main():
    print("="*70)
    print("SEMDS Mother System - Skills Showcase")
    print("="*70)
    print()
    print("This demo showcases the self-improvement capabilities:")
    print("  1. Web Search - Find solutions on the internet")
    print("  2. Code Quality - Enforce coding standards")
    print("  3. Self Reflection - Learn from experience")
    
    try:
        demo_web_search()
    except Exception as e:
        print(f"\n[Web Search Demo Error: {e}]")
    
    try:
        demo_code_quality()
    except Exception as e:
        print(f"\n[Code Quality Demo Error: {e}]")
    
    try:
        demo_self_reflection()
    except Exception as e:
        print(f"\n[Self Reflection Demo Error: {e}]")
    
    print("\n\n" + "="*70)
    print("Skills Demo Complete!")
    print("="*70)


if __name__ == "__main__":
    main()
