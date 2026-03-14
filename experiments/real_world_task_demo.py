#!/usr/bin/env python3
"""
真实任务测试 - 代码重构场景

测试场景：重构一个有缺陷的函数，验证自进化系统能否自动修复
"""

import sys
import tempfile
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from core.env_loader import load_env
load_env()

from evolution.meta_learner import MetaLearner
from evolution.test_runner import TestRunner


class RealWorldTaskDemo:
    """真实任务演示"""
    
    def __init__(self):
        self.meta_learner = MetaLearner(storage_path="experiments/real_world_meta_db.json")
        self.test_runner = TestRunner(timeout_seconds=30)
        self.meta_learner.patterns = {}
        self.meta_learner.strategies = {}
    
    def run_demo(self):
        """运行演示"""
        print("="*70)
        print("REAL-WORLD TASK DEMO: Config File Parser")
        print("="*70)
        print()
        
        # 有缺陷的实现 - 注释包含=时会错误解析
        buggy_code = '''
def parse_config(filepath: str) -> dict:
    """解析配置文件（有缺陷版本）"""
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # 缺陷1: 注释如果包含=会被错误解析
            # 缺陷2: 不检查是否以#开头
            if '=' in line:
                key, value = line.split('=')
                result[key.strip()] = value.strip()
    return result
'''
        
        # 正确的实现
        fixed_code = '''
def parse_config(filepath: str) -> dict:
    """解析配置文件（修复版本）"""
    result = {}
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            # 修复1: 跳过空行
            if not line:
                continue
            # 修复2: 跳过注释
            if line.startswith('#'):
                continue
            # 修复3: 正确处理key=value
            if '=' in line:
                key, value = line.split('=', 1)
                result[key.strip()] = value.strip()
    return result
'''
        
        # 测试代码
        # 测试代码 - 关键测试：注释包含=号
        test_code = '''
from solution import parse_config
import tempfile
import os

def test_comment_with_equals():
    """测试：注释包含=号时不应被解析"""
    # 这一行是注释但包含=，有缺陷的代码会错误解析它
    content = "# comment = value" + chr(10) + "name=John"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.conf', delete=False) as f:
        f.write(content)
        path = f.name
    
    try:
        r = parse_config(path)
        # 关键断言：注释不应该被当作key
        assert '# comment' not in r, "Comment was parsed as key: " + str(r)
        assert 'name' in r, "name not in result: " + str(list(r.keys()))
        assert r['name'] == 'John'
    finally:
        os.unlink(path)
'''
        
        print("[Round 1] Testing buggy implementation...")
        result1 = self._run_test(buggy_code, test_code)
        print(f"  Score: {result1['pass_rate']:.0%}")
        
        print("\n[Round 2] Testing fixed implementation...")
        result2 = self._run_test(fixed_code, test_code)
        print(f"  Score: {result2['pass_rate']:.0%}")
        
        if result2['pass_rate'] > result1['pass_rate']:
            print("\n[Round 3] Recording pattern to MetaLearner...")
            pattern_id = self.meta_learner.record_failure_and_fix(
                task_type="file_parser",
                error_type="assertion",
                original_code=buggy_code,
                fixed_code=fixed_code,
                error_message="Comments and empty lines not handled",
                fix_description="Add continue statements to skip empty lines and lines starting with #"
            )
            print(f"  Pattern recorded: {pattern_id}")
            
            print("\n[Round 4] Querying pattern for similar task...")
            patterns = self.meta_learner.find_applicable_patterns(
                task_type="file_parser",
                error_type="assertion",
                error_message="config parsing error"
            )
            print(f"  Found {len(patterns)} applicable patterns")
            for p in patterns:
                print(f"    - {p.fix_description}")
        
        self._print_final_report(result1, result2)
    
    def _run_test(self, code: str, test_code: str) -> dict:
        """运行测试"""
        with tempfile.TemporaryDirectory() as tmpdir:
            solution_path = Path(tmpdir) / "solution.py"
            with open(solution_path, 'w', encoding='utf-8') as f:
                f.write(code)
            
            test_path = Path(tmpdir) / "test_solution.py"
            with open(test_path, 'w', encoding='utf-8') as f:
                f.write(test_code)
            
            result = self.test_runner.run_tests(str(test_path), str(solution_path), tmpdir)
        
        return result
    
    def _print_final_report(self, result1: dict, result2: dict):
        """打印最终报告"""
        print("\n" + "="*70)
        print("REAL-WORLD DEMO RESULT")
        print("="*70)
        print(f"Buggy Code Score:  {result1['pass_rate']:.0%}")
        print(f"Fixed Code Score:  {result2['pass_rate']:.0%}")
        print(f"Improvement:       +{result2['pass_rate'] - result1['pass_rate']:.0%}")
        
        summary = self.meta_learner.get_learning_summary()
        print(f"\nMetaLearner Stats:")
        print(f"  Patterns recorded: {summary['total_patterns']}")
        
        print("\n" + "="*70)
        if result2['pass_rate'] == 1.0:
            print("[SUCCESS] Real-world task demo completed!")
        else:
            print("[PARTIAL] Task completed with issues.")
        print("="*70)


if __name__ == "__main__":
    demo = RealWorldTaskDemo()
    demo.run_demo()
