"""
Recursive Decomposer - 递归分解器

解决复杂大任务的分解问题：
1. DeepSeek 一次分解不够细 -> 递归分解
2. 验证分解是否正确 -> 分解验证器
3. 检查是否达到原子级 -> 原子级检查器
4. 超过50行 -> 继续分解，不是截断
"""
import json
import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import sys
sys.path.insert(0, 'D:\\semds')
from mother.task_decomposer.decomposer import AtomicTask, TaskType, TaskStatus


class DecompositionLevel(Enum):
    """分解级别"""
    EPIC = "epic"           # 史诗级任务（需要多次分解）
    STORY = "story"         # 用户故事（可一次分解）
    TASK = "task"           # 任务（基本可执行）
    ATOMIC = "atomic"       # 原子任务（<50行）


@dataclass
class DecompositionNode:
    """分解树节点"""
    id: str
    description: str
    level: DecompositionLevel
    subtasks: List['DecompositionNode']
    atomic_task: Optional[AtomicTask] = None
    
    def is_leaf(self) -> bool:
        """是否是叶子节点（原子任务）"""
        return self.level == DecompositionLevel.ATOMIC or len(self.subtasks) == 0
    
    def get_all_atomic_tasks(self) -> List[AtomicTask]:
        """获取所有原子任务"""
        if self.is_leaf() and self.atomic_task:
            return [self.atomic_task]
        
        atomic_tasks = []
        for subtask in self.subtasks:
            atomic_tasks.extend(subtask.get_all_atomic_tasks())
        return atomic_tasks


class DecompositionValidator:
    """
    分解验证器
    
    验证分解是否正确、完整
    """
    
    def validate_decomposition(
        self, 
        parent_task: str, 
        subtasks: List[str]
    ) -> Tuple[bool, str]:
        """
        验证分解是否正确
        
        Returns:
            (是否有效, 原因)
        """
        # 1. 检查子任务是否覆盖父任务
        coverage = self._check_coverage(parent_task, subtasks)
        if not coverage['covered']:
            return False, f"Missing aspects: {coverage['missing']}"
        
        # 2. 检查子任务是否有重叠
        overlap = self._check_overlap(subtasks)
        if overlap:
            return False, f"Overlapping tasks: {overlap}"
        
        # 3. 检查子任务粒度是否合适
        granularity = self._check_granularity(subtasks)
        if not granularity['appropriate']:
            return False, f"Granularity issue: {granularity['reason']}"
        
        return True, "Valid decomposition"
    
    def _check_coverage(self, parent: str, subtasks: List[str]) -> Dict:
        """检查子任务是否覆盖父任务的所有方面"""
        # 提取父任务的关键词
        parent_keywords = self._extract_keywords(parent)
        
        # 提取子任务的关键词
        subtask_keywords = set()
        for subtask in subtasks:
            subtask_keywords.update(self._extract_keywords(subtask))
        
        # 检查覆盖率
        missing = parent_keywords - subtask_keywords
        
        return {
            'covered': len(missing) <= len(parent_keywords) * 0.3,  # 允许30%遗漏
            'missing': list(missing)[:5],
            'coverage_rate': 1 - len(missing) / max(len(parent_keywords), 1)
        }
    
    def _check_overlap(self, subtasks: List[str]) -> List[str]:
        """检查子任务之间是否有重叠"""
        overlaps = []
        
        for i, task1 in enumerate(subtasks):
            keywords1 = self._extract_keywords(task1)
            for j, task2 in enumerate(subtasks[i+1:], i+1):
                keywords2 = self._extract_keywords(task2)
                
                # 如果两个任务有80%以上关键词重叠，认为有重叠
                overlap = len(keywords1 & keywords2) / max(len(keywords1), 1)
                if overlap > 0.8:
                    overlaps.append(f"'{task1[:30]}...' and '{task2[:30]}...'")
        
        return overlaps
    
    def _check_granularity(self, subtasks: List[str]) -> Dict:
        """检查粒度是否合适"""
        # 如果子任务太多（>10），可能粒度太细
        if len(subtasks) > 10:
            return {'appropriate': False, 'reason': 'Too many subtasks, consider grouping'}
        
        # 如果子任务太少（<2），可能粒度太粗
        if len(subtasks) < 2:
            return {'appropriate': False, 'reason': 'Too few subtasks, needs more decomposition'}
        
        # 检查每个子任务的描述长度（太短可能不明确）
        for subtask in subtasks:
            if len(subtask) < 10:
                return {'appropriate': False, 'reason': f'Subtask too vague: {subtask}'}
        
        return {'appropriate': True, 'reason': 'Good granularity'}
    
    def _extract_keywords(self, text: str) -> set:
        """提取关键词"""
        # 简单实现：提取名词和动词
        words = re.findall(r'\b[A-Za-z_]+\b', text.lower())
        # 过滤停用词
        stop_words = {'the', 'a', 'an', 'to', 'and', 'or', 'for', 'in', 'on', 'at', 'is', 'are'}
        return set(w for w in words if len(w) > 2 and w not in stop_words)


class AtomicChecker:
    """
    原子级检查器
    
    检查任务是否达到原子级别（<50行，可独立完成）
    """
    
    def check_atomic_level(self, task_description: str, code: str = None) -> Dict:
        """
        检查是否达到原子级
        
        Returns:
            {
                'is_atomic': bool,
                'issues': List[str],
                'suggested_action': str,  # 'keep', 'decompose', 'refine'
                'estimated_lines': int
            }
        """
        issues = []
        
        # 1. 检查描述复杂度
        complexity_score = self._assess_description_complexity(task_description)
        
        # 2. 如果有代码，检查代码行数
        if code:
            line_count = len([l for l in code.split('\n') if l.strip()])
            if line_count > 50:
                issues.append(f"Code too long: {line_count} lines (max 50)")
        else:
            # 估算代码行数
            line_count = self._estimate_code_lines(task_description)
        
        # 3. 检查是否包含多个动作
        actions = self._count_actions(task_description)
        if actions > 2:
            issues.append(f"Too many actions: {actions} (max 2 for atomic task)")
        
        # 4. 检查是否涉及多个概念
        concepts = self._count_concepts(task_description)
        if concepts > 3:
            issues.append(f"Too many concepts: {concepts} (max 3 for atomic task)")
        
        # 判断结果
        is_atomic = len(issues) == 0 and line_count <= 50 and complexity_score <= 5
        
        # 建议操作
        if is_atomic:
            suggested_action = 'keep'
        elif line_count > 50 or actions > 3:
            suggested_action = 'decompose'
        else:
            suggested_action = 'refine'
        
        return {
            'is_atomic': is_atomic,
            'issues': issues,
            'suggested_action': suggested_action,
            'estimated_lines': line_count,
            'complexity_score': complexity_score,
            'action_count': actions,
            'concept_count': concepts
        }
    
    def _assess_description_complexity(self, description: str) -> int:
        """评估描述复杂度（0-10）"""
        score = 0
        
        # 长度
        if len(description) > 100:
            score += 2
        if len(description) > 200:
            score += 2
        
        # 关键词复杂度
        complex_keywords = ['and', 'or', 'then', 'if', 'when', 'while', 'after', 'before']
        for kw in complex_keywords:
            if kw in description.lower():
                score += 1
        
        # 句子数
        sentences = len([s for s in description.split('.') if s.strip()])
        score += sentences
        
        return min(score, 10)
    
    def _estimate_code_lines(self, description: str) -> int:
        """估算代码行数"""
        # 基于描述估算
        base_lines = 20  # 基础代码
        
        # 功能点增加行数
        features = {
            'error handling': 10,
            'input validation': 5,
            'logging': 5,
            'async': 10,
            'caching': 10,
            'retry': 8,
            'timeout': 3,
        }
        
        estimated = base_lines
        for feature, lines in features.items():
            if feature in description.lower():
                estimated += lines
        
        return estimated
    
    def _count_actions(self, description: str) -> int:
        """计数动作数量"""
        action_verbs = [
            'write', 'create', 'implement', 'add', 'modify', 'update',
            'delete', 'remove', 'fetch', 'get', 'post', 'send',
            'parse', 'convert', 'transform', 'validate', 'check',
            'load', 'save', 'read', 'write'
        ]
        
        count = 0
        for verb in action_verbs:
            if verb in description.lower():
                count += 1
        
        return count
    
    def _count_concepts(self, description: str) -> int:
        """计数概念数量"""
        # 基于命名实体估算
        words = re.findall(r'\b[A-Z][a-z]+(?:[A-Z][a-z]+)*\b', description)
        return len(set(words))


class RecursiveDecomposer:
    """
    递归分解器
    
    处理复杂大任务：
    1. 识别任务级别（EPIC/STORY/TASK/ATOMIC）
    2. 递归分解直到原子级
    3. 每轮分解都验证
    4. 超过50行继续分解，不是截断
    """
    
    def __init__(self, max_depth: int = 3):
        self.max_depth = max_depth
        self.validator = DecompositionValidator()
        self.atomic_checker = AtomicChecker()
        self.decomposition_history = []
    
    def decompose(self, task_description: str, depth: int = 0) -> DecompositionNode:
        """
        递归分解任务
        
        Args:
            task_description: 任务描述
            depth: 当前递归深度
        
        Returns:
            分解树节点
        """
        print(f"{'  ' * depth}[Decompose] {task_description[:50]}...")
        
        # 1. 识别任务级别
        level = self._identify_level(task_description, depth)
        print(f"{'  ' * depth}  Level: {level.value}")
        
        # 2. 如果是原子级，直接返回
        if level == DecompositionLevel.ATOMIC:
            atomic_check = self.atomic_checker.check_atomic_level(task_description)
            if atomic_check['is_atomic']:
                atomic_task = self._create_atomic_task(task_description)
                return DecompositionNode(
                    id=f"atomic_{len(self.decomposition_history)}",
                    description=task_description,
                    level=level,
                    subtasks=[],
                    atomic_task=atomic_task
                )
        
        # 3. 如果达到最大深度，强制转为原子任务
        if depth >= self.max_depth:
            print(f"{'  ' * depth}  Max depth reached, forcing atomic")
            atomic_task = self._create_atomic_task(task_description, force=True)
            return DecompositionNode(
                id=f"forced_atomic_{len(self.decomposition_history)}",
                description=task_description,
                level=DecompositionLevel.ATOMIC,
                subtasks=[],
                atomic_task=atomic_task
            )
        
        # 4. 分解为子任务
        subtask_descriptions = self._decompose_once(task_description)
        print(f"{'  ' * depth}  Subtasks: {len(subtask_descriptions)}")
        
        # 5. 验证分解
        is_valid, reason = self.validator.validate_decomposition(
            task_description, subtask_descriptions
        )
        
        if not is_valid:
            print(f"{'  ' * depth}  Invalid decomposition: {reason}")
            print(f"{'  ' * depth}  Retrying with simpler approach...")
            # 简化分解策略
            subtask_descriptions = self._simplified_decomposition(task_description)
        
        # 6. 递归分解子任务
        subtasks = []
        for i, subdesc in enumerate(subtask_descriptions):
            subtask = self.decompose(subdesc, depth + 1)
            subtasks.append(subtask)
        
        # 7. 创建当前节点
        node = DecompositionNode(
            id=f"node_{depth}_{len(self.decomposition_history)}",
            description=task_description,
            level=level,
            subtasks=subtasks
        )
        
        self.decomposition_history.append({
            'task': task_description,
            'level': level.value,
            'subtasks': len(subtask_descriptions)
        })
        
        return node
    
    def _identify_level(self, description: str, depth: int) -> DecompositionLevel:
        """识别任务级别"""
        # 基于深度和描述复杂度判断
        
        if depth == 0 and len(description) > 200:
            return DecompositionLevel.EPIC
        
        if depth <= 1 and len(description) > 100:
            return DecompositionLevel.STORY
        
        # 检查是否已经是原子级
        atomic_check = self.atomic_checker.check_atomic_level(description)
        if atomic_check['is_atomic']:
            return DecompositionLevel.ATOMIC
        
        if atomic_check['estimated_lines'] <= 50:
            return DecompositionLevel.TASK
        
        return DecompositionLevel.STORY
    
    def _decompose_once(self, task_description: str) -> List[str]:
        """单次分解（可以用 DeepSeek 或规则）"""
        # 这里使用基于规则的简单分解
        # 实际可以用 DeepSeek API
        
        # 检测任务类型
        desc_lower = task_description.lower()
        
        # 系统级任务分解
        if 'system' in desc_lower or 'application' in desc_lower:
            return [
                f"Design architecture for: {task_description}",
                f"Implement core module for: {task_description}",
                f"Implement data layer for: {task_description}",
                f"Implement API layer for: {task_description}",
                f"Write tests for: {task_description}",
                f"Integrate and validate: {task_description}",
            ]
        
        # 功能分解
        if 'and' in desc_lower or 'then' in desc_lower:
            parts = re.split(r'\s+(?:and|then|after)\s+', desc_lower)
            return [p.strip().capitalize() for p in parts if len(p.strip()) > 10]
        
        # 默认分解
        return [
            f"Analyze requirements for: {task_description}",
            f"Design solution for: {task_description}",
            f"Implement: {task_description}",
            f"Test and validate: {task_description}",
        ]
    
    def _simplified_decomposition(self, task_description: str) -> List[str]:
        """简化分解策略（当正常分解失败时）"""
        return [
            f"Part 1 of: {task_description}",
            f"Part 2 of: {task_description}",
            f"Part 3 of: {task_description}",
        ]
    
    def _create_atomic_task(
        self, 
        description: str, 
        force: bool = False
    ) -> AtomicTask:
        """创建原子任务"""
        task_id = f"atomic_{len(self.decomposition_history)}"
        
        # 确定任务类型
        task_type = self._determine_task_type(description)
        
        return AtomicTask(
            id=task_id,
            name=description[:50],
            description=description,
            task_type=task_type,
            validation_criteria=["Code is less than 50 lines", "All tests pass"],
            max_lines=50,
            max_tokens=500
        )
    
    def _determine_task_type(self, description: str) -> TaskType:
        """确定任务类型"""
        desc_lower = description.lower()
        
        if 'test' in desc_lower:
            return TaskType.TEST
        elif any(word in desc_lower for word in ['design', 'architecture', 'analyze']):
            return TaskType.ANALYSIS
        elif any(word in desc_lower for word in ['interface', 'api', 'signature']):
            return TaskType.INTERFACE
        elif 'refactor' in desc_lower:
            return TaskType.REFACTOR
        else:
            return TaskType.IMPLEMENT
    
    def print_decomposition_tree(self, node: DecompositionNode, indent: int = 0):
        """打印分解树"""
        prefix = "  " * indent
        
        if node.is_leaf():
            print(f"{prefix}[ATOMIC] {node.description[:60]}...")
        else:
            print(f"{prefix}[{node.level.value.upper()}] {node.description[:60]}...")
            for subtask in node.subtasks:
                self.print_decomposition_tree(subtask, indent + 1)
    
    def get_statistics(self) -> Dict:
        """获取分解统计"""
        total_tasks = len(self.decomposition_history)
        
        level_counts = {}
        for entry in self.decomposition_history:
            level = entry['level']
            level_counts[level] = level_counts.get(level, 0) + 1
        
        return {
            'total_decompositions': total_tasks,
            'level_distribution': level_counts,
            'max_depth': self.max_depth
        }


# 便捷函数
def recursive_decompose(task_description: str, max_depth: int = 3) -> DecompositionNode:
    """快速递归分解"""
    decomposer = RecursiveDecomposer(max_depth=max_depth)
    return decomposer.decompose(task_description)


if __name__ == "__main__":
    # 测试
    decomposer = RecursiveDecomposer(max_depth=3)
    
    # 测试不同复杂度的任务
    test_tasks = [
        "Write a function to fetch data",  # 简单，一次分解
        "Build a complete web scraping system with data processing and storage",  # 复杂，递归分解
        "Implement a data pipeline that downloads files, parses CSV, validates data, transforms format, and saves to database",  # 非常复杂
    ]
    
    for task in test_tasks:
        print("\n" + "="*70)
        print(f"Task: {task}")
        print("="*70)
        
        root = decomposer.decompose(task)
        
        print("\nDecomposition Tree:")
        decomposer.print_decomposition_tree(root)
        
        atomic_tasks = root.get_all_atomic_tasks()
        print(f"\nTotal atomic tasks: {len(atomic_tasks)}")
        
        stats = decomposer.get_statistics()
        print(f"Statistics: {stats}")
        
        # 清空历史，准备下一个任务
        decomposer.decomposition_history = []
