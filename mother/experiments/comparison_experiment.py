"""
Comparison Experiment: Task Decomposition vs Direct Generation
对比实验：任务分解 vs 直接生成

对比两种方式使用本地小模型开发代码：
1. 新方式：任务分解 + TDD（原子任务<50行）
2. 旧方式：直接生成（无分解）
"""
import sys
import time
sys.path.insert(0, 'D:\\semds')

from mother.task_decomposer.decomposer import TaskDecomposer
from mother.skills.code_optimizer import CodeOptimizer
from evolution.code_generator import CodeGenerator


class ComparisonExperiment:
    """对比实验"""
    
    def __init__(self):
        self.local_model = CodeGenerator(backend="ollama")
        self.optimizer = CodeOptimizer()
    
    def run_experiment(self, task: str) -> dict:
        """运行对比实验"""
        print("="*70)
        print(f"TASK: {task}")
        print("="*70)
        
        # 方法1：任务分解
        print("\n[METHOD 1] Task Decomposition + Small Chunks")
        print("-"*70)
        result1 = self._method_decomposition(task)
        
        # 方法2：直接生成
        print("\n[METHOD 2] Direct Generation")
        print("-"*70)
        result2 = self._method_direct(task)
        
        return {
            'task': task,
            'method1': result1,
            'method2': result2
        }
    
    def _method_decomposition(self, task: str) -> dict:
        """方法1：分解为小块生成"""
        start = time.time()
        
        try:
            # 分解
            print("  Decomposing...")
            decomposer = TaskDecomposer()
            graph = decomposer.decompose(task)
            
            atomic_tasks = [t for t in graph.tasks.values() 
                          if t.task_type.value in ['implement']]
            print(f"    -> {len(atomic_tasks)} atomic tasks")
            
            # 逐个生成小块
            print("  Generating small chunks...")
            codes = []
            for i, at in enumerate(atomic_tasks[:2], 1):  # 限制2个
                print(f"    Chunk {i}: {at.name[:30]}...")
                
                result = self.local_model.generate({
                    "description": at.description,
                    "requirements": ["Less than 50 lines", "Type hints"]
                })
                
                if result["success"]:
                    codes.append(result["code"])
                    lines = len(result["code"].split(chr(10)))
                    print(f"      -> {lines} lines")
            
            # 组装
            final_code = "\n\n".join(codes)
            elapsed = time.time() - start
            
            quality = self.optimizer.optimize(final_code)
            
            return {
                'success': True,
                'code': final_code,
                'quality': quality['optimized_score'],
                'time': elapsed,
                'lines': len(final_code.split('\n'))
            }
            
        except Exception as e:
            return {
                'success': False,
                'code': str(e),
                'quality': 0,
                'time': time.time() - start,
                'lines': 0
            }
    
    def _method_direct(self, task: str) -> dict:
        """方法2：直接生成"""
        start = time.time()
        
        try:
            print("  Generating complete code...")
            
            result = self.local_model.generate({
                "description": task,
                "requirements": ["Complete code", "Type hints"]
            })
            
            elapsed = time.time() - start
            
            if result["success"]:
                code = result["code"]
                quality = self.optimizer.optimize(code)
                
                return {
                    'success': True,
                    'code': code,
                    'quality': quality['optimized_score'],
                    'time': elapsed,
                    'lines': len(code.split('\n'))
                }
            else:
                return {
                    'success': False,
                    'code': result.get('error', 'Failed'),
                    'quality': 0,
                    'time': elapsed,
                    'lines': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'code': str(e),
                'quality': 0,
                'time': time.time() - start,
                'lines': 0
            }
    
    def print_comparison(self, result: dict):
        """打印对比"""
        print("\n" + "="*70)
        print("RESULTS")
        print("="*70)
        
        m1, m2 = result['method1'], result['method2']
        
        print(f"\n{'Metric':<25} {'Decomposition':<20} {'Direct':<20}")
        print("-"*65)
        
        # Success
        s1, s2 = ("[OK]" if m1['success'] else "[FAIL]"), ("[OK]" if m2['success'] else "[FAIL]")
        print(f"{'Success':<25} {s1:<20} {s2:<20}")
        
        # Quality
        print(f"{'Quality Score':<25} {m1['quality']:.1f}/100{'':<12} {m2['quality']:.1f}/100")
        
        # Lines
        print(f"{'Lines':<25} {m1['lines']:<20} {m2['lines']:<20}")
        
        # Time
        print(f"{'Time':<25} {m1['time']:.1f}s{'':<15} {m2['time']:.1f}s")
        
        # Preview
        if m1['success']:
            print("\n[Decomposition Code Preview]:")
            print(m1['code'][:200] + "..." if len(m1['code']) > 200 else m1['code'])
        
        if m2['success']:
            print("\n[Direct Code Preview]:")
            print(m2['code'][:200] + "..." if len(m2['code']) > 200 else m2['code'])


def main():
    print("="*70)
    print("COMPARISON EXPERIMENT")
    print("Task Decomposition vs Direct Generation (Local Model)")
    print("="*70)
    print()
    
    exp = ComparisonExperiment()
    
    task = "Write a function to fetch API data and parse JSON"
    result = exp.run_experiment(task)
    exp.print_comparison(result)
    
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)
    m1, m2 = result['method1'], result['method2']
    print(f"Decomposition: Quality={m1['quality']:.0f}, Lines={m1['lines']}")
    print(f"Direct: Quality={m2['quality']:.0f}, Lines={m2['lines']}")
    print()
    print("Conclusion: See which method produces better code with local model")
    print("="*70)


if __name__ == "__main__":
    main()
