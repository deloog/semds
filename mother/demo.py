"""
SEMDS Mother System - Demo
母体系统演示：自主生成工具并完成任务
"""
import sys
sys.path.insert(0, r'D:\semds')

# Load environment
from dotenv import load_dotenv
load_dotenv(r'D:\semds\.env')

from mother.core.mother_system import MotherSystem


def main():
    print("="*70)
    print("SEMDS Mother System - Autonomous Task System")
    print("="*70)
    print()
    print("Core Features:")
    print("  1. Natural language task understanding")
    print("  2. Check existing capabilities")
    print("  3. Auto-generate missing tools")
    print("  4. Execute and return results")
    print()
    print("="*70)
    
    # 初始化母体
    mother = MotherSystem()
    
    # Demo tasks
    demo_tasks = [
        "Fetch images from https://www.bing.com homepage",
    ]
    
    for task in demo_tasks:
        print(f"\n{'='*70}")
        print(f"Task: {task}")
        print(f"{'='*70}\n")
        
        result = mother.execute(task)
        
        if result["success"]:
            print(f"\n[OK] Task success!")
            print(f"  Capabilities: {', '.join(result['plan']['capabilities_used'])}")
            
            # 显示结果
            if 'extracted_data' in result['outputs']:
                urls = result['outputs']['extracted_data']
                print(f"\n  Found {len(urls)} image URLs:")
                for url in urls[:5]:
                    print(f"    - {url}")
                if len(urls) > 5:
                    print(f"    ... {len(urls)-5} more")
        else:
            print(f"\n[FAIL] Task failed: {result.get('error')}")
    
    print(f"\n{'='*70}")
    print("Demo complete!")
    print("="*70)


if __name__ == "__main__":
    main()
