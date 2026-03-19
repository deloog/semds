"""
Code Assembler - 代码组装器

解决"分解导致文件爆炸"问题：
- 逻辑上：任务分解为原子任务（便于验证）
- 物理上：智能合并为合适的模块（便于维护）

组装策略：
1. 相关原子任务合并为函数
2. 相关函数合并为类
3. 相关类合并为模块
4. 保持单一职责，但避免过度拆分
"""
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from mother.task_decomposer.decomposer import AtomicTask, TaskType


class ModuleType(Enum):
    """模块类型"""
    FUNCTION = "function"       # 单个函数（最简单）
    CLASS = "class"             # 类（包含多个方法）
    MODULE = "module"           # 模块（包含多个函数/类）
    PACKAGE = "package"         # 包（多个模块）


@dataclass
class CodeModule:
    """代码模块"""
    name: str
    module_type: ModuleType
    content: str
    tasks: List[AtomicTask]     # 包含的原子任务
    dependencies: List[str]     # 依赖的其他模块
    lines: int
    
    def is_reasonable_size(self) -> bool:
        """检查是否合理大小"""
        if self.module_type == ModuleType.FUNCTION:
            return self.lines <= 50
        elif self.module_type == ModuleType.CLASS:
            return 50 <= self.lines <= 200
        elif self.module_type == ModuleType.MODULE:
            return 100 <= self.lines <= 500
        return True


class CodeAssembler:
    """
    代码组装器
    
    将原子任务智能组装为可维护的代码结构
    """
    
    # 组装阈值
    TARGET_FILE_SIZE = {
        'min': 50,      # 小于50行：考虑合并
        'ideal': 150,   # 理想大小：150行
        'max': 300,     # 大于300行：考虑拆分
    }
    
    def __init__(self):
        self.assembly_rules = self._load_rules()
    
    def _load_rules(self) -> Dict:
        """加载组装规则"""
        return {
            # 分析类任务不生成代码
            TaskType.ANALYSIS: {'output': 'document', 'merge': False},
            
            # 接口定义可以和其他合并
            TaskType.INTERFACE: {'output': 'code', 'merge': True},
            
            # 测试代码单独文件
            TaskType.TEST: {'output': 'test_file', 'merge': False},
            
            # 实现代码需要智能组装
            TaskType.IMPLEMENT: {'output': 'code', 'merge': True},
            
            # 验证不产生代码
            TaskType.VALIDATE: {'output': 'report', 'merge': False},
            
            # 重构是优化现有代码
            TaskType.REFACTOR: {'output': 'code', 'merge': True},
        }
    
    def assemble(self, atomic_tasks: List[AtomicTask]) -> List[CodeModule]:
        """
        组装原子任务为代码模块
        
        Args:
            atomic_tasks: 原子任务列表
        
        Returns:
            代码模块列表
        """
        print(f"\n[Assembler] Assembling {len(atomic_tasks)} atomic tasks...")
        
        # 1. 分类任务
        code_tasks = [t for t in atomic_tasks 
                     if self.assembly_rules.get(t.task_type, {}).get('output') == 'code']
        test_tasks = [t for t in atomic_tasks 
                     if t.task_type == TaskType.TEST]
        doc_tasks = [t for t in atomic_tasks 
                    if t.task_type == TaskType.ANALYSIS]
        
        print(f"  Code tasks: {len(code_tasks)}")
        print(f"  Test tasks: {len(test_tasks)}")
        print(f"  Doc tasks: {len(doc_tasks)}")
        
        modules = []
        
        # 2. 组装实现代码
        if code_tasks:
            code_modules = self._assemble_code_tasks(code_tasks)
            modules.extend(code_modules)
        
        # 3. 组装测试代码
        if test_tasks:
            test_module = self._assemble_test_tasks(test_tasks)
            modules.append(test_module)
        
        # 4. 组装文档
        if doc_tasks:
            doc_module = self._assemble_doc_tasks(doc_tasks)
            modules.append(doc_module)
        
        # 5. 优化模块大小
        modules = self._optimize_module_sizes(modules)
        
        print(f"[Assembler] Generated {len(modules)} modules")
        for m in modules:
            print(f"  - {m.name} ({m.module_type.value}): {m.lines} lines")
        
        return modules
    
    def _assemble_code_tasks(self, tasks: List[AtomicTask]) -> List[CodeModule]:
        """组装实现代码任务"""
        
        # 策略1: 按功能域分组
        groups = self._group_by_function(tasks)
        
        modules = []
        for group_name, group_tasks in groups.items():
            # 合并代码
            merged_code = self._merge_task_code(group_tasks)
            
            # 决定模块类型
            if len(group_tasks) == 1:
                module_type = ModuleType.FUNCTION
            elif self._should_be_class(group_tasks):
                module_type = ModuleType.CLASS
            else:
                module_type = ModuleType.MODULE
            
            # 创建模块
            module = CodeModule(
                name=group_name,
                module_type=module_type,
                content=merged_code,
                tasks=group_tasks,
                dependencies=self._extract_dependencies(merged_code),
                lines=len(merged_code.split('\n'))
            )
            
            modules.append(module)
        
        return modules
    
    def _group_by_function(self, tasks: List[AtomicTask]) -> Dict[str, List[AtomicTask]]:
        """按功能域分组任务"""
        groups = {}
        
        for task in tasks:
            # 提取功能域
            domain = self._extract_domain(task.description)
            
            if domain not in groups:
                groups[domain] = []
            groups[domain].append(task)
        
        # 如果组太多，合并相关组
        if len(groups) > 5:
            groups = self._merge_small_groups(groups)
        
        return groups
    
    def _extract_domain(self, description: str) -> str:
        """提取功能域"""
        # 基于关键词提取
        keywords = {
            'fetch': 'data_fetcher',
            'parse': 'data_parser',
            'validate': 'data_validator',
            'transform': 'data_transformer',
            'save': 'data_storage',
            'load': 'data_loader',
            'process': 'data_processor',
        }
        
        desc_lower = description.lower()
        for keyword, domain in keywords.items():
            if keyword in desc_lower:
                return domain
        
        return 'core_module'
    
    def _merge_small_groups(self, groups: Dict) -> Dict:
        """合并小组"""
        # 按任务数量排序
        sorted_groups = sorted(groups.items(), key=lambda x: len(x[1]))
        
        # 合并少于2个任务的小组
        merged = {}
        small_groups = []
        
        for name, tasks in sorted_groups:
            if len(tasks) >= 2:
                merged[name] = tasks
            else:
                small_groups.extend(tasks)
        
        # 将小组任务合并到"utils"或现有组
        if small_groups:
            if len(merged) > 0:
                # 合并到第一个组
                first_key = list(merged.keys())[0]
                merged[first_key].extend(small_groups)
            else:
                merged['utils'] = small_groups
        
        return merged
    
    def _should_be_class(self, tasks: List[AtomicTask]) -> bool:
        """判断是否应该组织为类"""
        # 如果有多个任务操作同一类数据，组织为类
        descriptions = ' '.join([t.description for t in tasks])
        
        # 检查是否有"初始化"、"方法"等关键词
        class_indicators = ['init', 'method', 'attribute', 'state']
        return any(ind in descriptions.lower() for ind in class_indicators)
    
    def _merge_task_code(self, tasks: List[AtomicTask]) -> str:
        """合并任务代码"""
        parts = []
        
        # 添加文件头
        parts.append('"""')
        parts.append(f'Auto-generated module')
        parts.append(f'Contains {len(tasks)} atomic tasks')
        parts.append('"""')
        parts.append('')
        
        # 合并导入
        imports = self._extract_imports(tasks)
        parts.extend(imports)
        parts.append('')
        
        # 合并代码
        for task in tasks:
            if task.actual_output:
                # 清理代码
                code = self._clean_code(task.actual_output)
                parts.append(code)
                parts.append('')
                parts.append('')
        
        return '\n'.join(parts)
    
    def _extract_imports(self, tasks: List[AtomicTask]) -> List[str]:
        """提取并去重导入语句"""
        imports = set()
        
        for task in tasks:
            if task.actual_output:
                # 提取 import 语句
                for line in task.actual_output.split('\n'):
                    if line.strip().startswith(('import ', 'from ')):
                        imports.add(line.strip())
        
        return sorted(list(imports))
    
    def _clean_code(self, code: str) -> str:
        """清理代码，移除重复导入等"""
        lines = code.split('\n')
        cleaned = []
        
        for line in lines:
            # 跳过导入语句（已经在文件头）
            if line.strip().startswith(('import ', 'from ')):
                continue
            # 跳过文件级别的文档字符串
            if line.strip() in ('"""', "'''"):
                continue
            cleaned.append(line)
        
        return '\n'.join(cleaned).strip()
    
    def _assemble_test_tasks(self, tasks: List[AtomicTask]) -> CodeModule:
        """组装测试任务"""
        merged_code = self._merge_task_code(tasks)
        
        return CodeModule(
            name='test_module',
            module_type=ModuleType.MODULE,
            content=merged_code,
            tasks=tasks,
            dependencies=[],
            lines=len(merged_code.split('\n'))
        )
    
    def _assemble_doc_tasks(self, tasks: List[AtomicTask]) -> CodeModule:
        """组装文档任务"""
        parts = ['# Documentation\n']
        
        for task in tasks:
            if task.actual_output:
                parts.append(f"## {task.name}")
                parts.append(task.actual_output)
                parts.append('')
        
        content = '\n'.join(parts)
        
        return CodeModule(
            name='README',
            module_type=ModuleType.MODULE,
            content=content,
            tasks=tasks,
            dependencies=[],
            lines=len(content.split('\n'))
        )
    
    def _extract_dependencies(self, code: str) -> List[str]:
        """提取代码依赖"""
        deps = []
        
        # 简单的依赖检测
        if 'requests' in code:
            deps.append('requests')
        if 'json' in code:
            deps.append('json')
        if 'csv' in code:
            deps.append('csv')
        
        return deps
    
    def _optimize_module_sizes(self, modules: List[CodeModule]) -> List[CodeModule]:
        """优化模块大小"""
        optimized = []
        
        for module in modules:
            if module.lines > self.TARGET_FILE_SIZE['max']:
                # 模块太大，拆分
                print(f"  [Optimize] Splitting {module.name} ({module.lines} lines)")
                split_modules = self._split_large_module(module)
                optimized.extend(split_modules)
            elif module.lines < self.TARGET_FILE_SIZE['min']:
                # 模块太小，考虑合并（如果可能）
                if optimized and self._can_merge(optimized[-1], module):
                    print(f"  [Optimize] Merging {module.name} into {optimized[-1].name}")
                    optimized[-1] = self._merge_modules(optimized[-1], module)
                else:
                    optimized.append(module)
            else:
                optimized.append(module)
        
        return optimized
    
    def _split_large_module(self, module: CodeModule) -> List[CodeModule]:
        """拆分大模块"""
        # 简单策略：按函数拆分
        functions = self._split_by_functions(module.content)
        
        mid = len(functions) // 2
        
        part1 = CodeModule(
            name=f"{module.name}_part1",
            module_type=module.module_type,
            content='\n\n'.join(functions[:mid]),
            tasks=module.tasks[:len(module.tasks)//2],
            dependencies=module.dependencies,
            lines=sum(len(f.split('\n')) for f in functions[:mid])
        )
        
        part2 = CodeModule(
            name=f"{module.name}_part2",
            module_type=module.module_type,
            content='\n\n'.join(functions[mid:]),
            tasks=module.tasks[len(module.tasks)//2:],
            dependencies=module.dependencies,
            lines=sum(len(f.split('\n')) for f in functions[mid:])
        )
        
        return [part1, part2]
    
    def _split_by_functions(self, code: str) -> List[str]:
        """按函数拆分代码"""
        # 简单实现：按 def 和 class 拆分
        pattern = r'((?:def|class)\s+\w+.*?(?=\n(?:def|class|\Z)))'
        parts = re.split(pattern, code, flags=re.DOTALL)
        return [p.strip() for p in parts if p.strip()]
    
    def _can_merge(self, module1: CodeModule, module2: CodeModule) -> bool:
        """检查是否可以合并"""
        # 相同类型可以合并
        if module1.module_type != module2.module_type:
            return False
        
        # 合并后不超过最大限制
        combined_lines = module1.lines + module2.lines
        return combined_lines <= self.TARGET_FILE_SIZE['max']
    
    def _merge_modules(self, module1: CodeModule, module2: CodeModule) -> CodeModule:
        """合并两个模块"""
        return CodeModule(
            name=module1.name,
            module_type=module1.module_type,
            content=module1.content + '\n\n' + module2.content,
            tasks=module1.tasks + module2.tasks,
            dependencies=list(set(module1.dependencies + module2.dependencies)),
            lines=module1.lines + module2.lines
        )
    
    def generate_file_structure(self, modules: List[CodeModule]) -> Dict[str, str]:
        """
        生成文件结构
        
        Returns:
            {文件名: 文件内容}
        """
        files = {}
        
        for i, module in enumerate(modules):
            if module.module_type == ModuleType.FUNCTION:
                filename = f"{module.name}.py"
            elif module.module_type == ModuleType.CLASS:
                filename = f"{module.name}.py"
            elif module.module_type == ModuleType.MODULE:
                filename = f"{module.name}.py"
            else:
                filename = f"module_{i}.py"
            
            files[filename] = module.content
        
        return files


# 便捷函数
def assemble_atomic_tasks(tasks: List[AtomicTask]) -> Dict[str, str]:
    """快速组装原子任务为文件"""
    assembler = CodeAssembler()
    modules = assembler.assemble(tasks)
    return assembler.generate_file_structure(modules)


if __name__ == "__main__":
    # 测试
    from mother.task_decomposer.decomposer import AtomicTask, TaskType
    
    # 模拟原子任务
    mock_tasks = [
        AtomicTask(
            id="t1",
            name="fetch_data",
            description="Fetch data from API",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def fetch_data(url: str) -> dict:
    import requests
    response = requests.get(url)
    return response.json()
'''
        ),
        AtomicTask(
            id="t2",
            name="parse_data",
            description="Parse JSON data",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def parse_data(raw: dict) -> list:
    return raw.get('items', [])
'''
        ),
        AtomicTask(
            id="t3",
            name="save_data",
            description="Save to database",
            task_type=TaskType.IMPLEMENT,
            actual_output='''
def save_data(items: list) -> bool:
    # Save logic
    return True
'''
        ),
        AtomicTask(
            id="t4",
            name="test_fetch",
            description="Test fetch_data",
            task_type=TaskType.TEST,
            actual_output='''
def test_fetch_data():
    result = fetch_data("http://api.example.com")
    assert result is not None
'''
        ),
    ]
    
    assembler = CodeAssembler()
    modules = assembler.assemble(mock_tasks)
    files = assembler.generate_file_structure(modules)
    
    print("\n" + "="*70)
    print("Generated Files:")
    print("="*70)
    for filename, content in files.items():
        lines = len(content.split('\n'))
        print(f"\n{filename} ({lines} lines):")
        print("-"*70)
        print(content[:500])
        if len(content) > 500:
            print("...")
