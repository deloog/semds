"""
Self Reflection - 自我反思与学习
让 Mother System 能够从经验中学习
"""
import os
import sys
import json
import time
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

sys.path.insert(0, r'D:\semds')


@dataclass
class TaskExecution:
    """任务执行记录"""
    task_id: str
    task_description: str
    timestamp: float
    duration: float
    success: bool
    capabilities_used: List[str]
    errors_encountered: List[str]
    solutions_applied: List[Dict]
    lessons_learned: List[str]


@dataclass
class ErrorPattern:
    """错误模式"""
    error_type: str
    error_message: str
    context: str
    solution: str
    success_rate: float
    occurrence_count: int


class SelfReflection:
    """
    自我反思系统
    
    功能：
    1. 记录每次任务执行
    2. 分析错误模式
    3. 积累解决方案
    4. 生成改进建议
    """
    
    def __init__(self, memory_path: str = "mother/memory"):
        self.memory_path = memory_path
        self.execution_history: List[TaskExecution] = []
        self.error_patterns: Dict[str, ErrorPattern] = {}
        self.knowledge_base: Dict[str, Any] = {}
        
        os.makedirs(memory_path, exist_ok=True)
        self._load_memory()
    
    def _load_memory(self):
        """加载历史记忆"""
        # 加载执行历史
        history_file = os.path.join(self.memory_path, "execution_history.json")
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.execution_history = [
                        TaskExecution(**item) for item in data
                    ]
            except Exception as e:
                print(f"[Memory] Failed to load history: {e}")
        
        # 加载错误模式
        patterns_file = os.path.join(self.memory_path, "error_patterns.json")
        if os.path.exists(patterns_file):
            try:
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.error_patterns = {
                        k: ErrorPattern(**v) for k, v in data.items()
                    }
            except Exception as e:
                print(f"[Memory] Failed to load patterns: {e}")
        
        # 加载知识库
        kb_file = os.path.join(self.memory_path, "knowledge_base.json")
        if os.path.exists(kb_file):
            try:
                with open(kb_file, 'r', encoding='utf-8') as f:
                    self.knowledge_base = json.load(f)
            except Exception as e:
                print(f"[Memory] Failed to load knowledge: {e}")
    
    def _save_memory(self):
        """保存记忆"""
        try:
            # 保存执行历史（只保留最近 100 条）
            history_file = os.path.join(self.memory_path, "execution_history.json")
            recent_history = self.execution_history[-100:]
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [asdict(item) for item in recent_history],
                    f, indent=2, ensure_ascii=False
                )
            
            # 保存错误模式
            patterns_file = os.path.join(self.memory_path, "error_patterns.json")
            with open(patterns_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {k: asdict(v) for k, v in self.error_patterns.items()},
                    f, indent=2, ensure_ascii=False
                )
            
            # 保存知识库
            kb_file = os.path.join(self.memory_path, "knowledge_base.json")
            with open(kb_file, 'w', encoding='utf-8') as f:
                json.dump(self.knowledge_base, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            print(f"[Memory] Failed to save: {e}")
    
    def record_execution(
        self,
        task_description: str,
        success: bool,
        duration: float,
        capabilities_used: List[str],
        errors: List[str] = None,
        solutions: List[Dict] = None
    ) -> TaskExecution:
        """
        记录任务执行
        
        Args:
            task_description: 任务描述
            success: 是否成功
            duration: 执行时长（秒）
            capabilities_used: 使用的能力列表
            errors: 遇到的错误
            solutions: 应用的解决方案
        """
        task_id = f"task_{int(time.time())}_{hash(task_description) % 10000}"
        
        # 生成经验教训
        lessons = self._extract_lessons(success, errors or [], solutions or [])
        
        execution = TaskExecution(
            task_id=task_id,
            task_description=task_description,
            timestamp=time.time(),
            duration=duration,
            success=success,
            capabilities_used=capabilities_used,
            errors_encountered=errors or [],
            solutions_applied=solutions or [],
            lessons_learned=lessons
        )
        
        self.execution_history.append(execution)
        
        # 更新错误模式
        for error in errors or []:
            self._update_error_pattern(error, success)
        
        self._save_memory()
        
        return execution
    
    def _extract_lessons(
        self,
        success: bool,
        errors: List[str],
        solutions: List[Dict]
    ) -> List[str]:
        """从执行中提取经验教训"""
        lessons = []
        
        if success:
            if solutions:
                lessons.append("Web search helped solve the problem")
            if not errors:
                lessons.append("Clean execution without errors")
        else:
            if errors:
                lessons.append(f"Failed due to: {errors[0][:50]}")
        
        return lessons
    
    def _update_error_pattern(self, error: str, resolved: bool):
        """更新错误模式统计"""
        # 简化错误作为键
        error_key = self._normalize_error(error)
        
        if error_key not in self.error_patterns:
            self.error_patterns[error_key] = ErrorPattern(
                error_type=self._classify_error(error),
                error_message=error[:200],
                context="",
                solution="",
                success_rate=1.0 if resolved else 0.0,
                occurrence_count=1
            )
        else:
            pattern = self.error_patterns[error_key]
            pattern.occurrence_count += 1
            # 更新成功率
            old_success = pattern.success_rate * (pattern.occurrence_count - 1)
            new_success = old_success + (1.0 if resolved else 0.0)
            pattern.success_rate = new_success / pattern.occurrence_count
    
    def _normalize_error(self, error: str) -> str:
        """标准化错误信息用于索引"""
        # 提取错误类型和关键信息
        lines = error.strip().split('\n')
        if not lines:
            return "unknown"
        
        # 取最后几行（通常是实际错误）
        key_line = lines[-1][:100]
        # 移除具体值（如文件名、行号）
        import re
        key_line = re.sub(r'File "[^"]+"', 'File "..."', key_line)
        key_line = re.sub(r'line \d+', 'line X', key_line)
        return key_line.lower()
    
    def _classify_error(self, error: str) -> str:
        """分类错误类型"""
        error_lower = error.lower()
        
        if 'import' in error_lower or 'module' in error_lower:
            return "ImportError"
        elif 'syntax' in error_lower:
            return "SyntaxError"
        elif 'type' in error_lower or 'attribute' in error_lower:
            return "TypeError"
        elif 'key' in error_lower:
            return "KeyError"
        elif 'index' in error_lower:
            return "IndexError"
        elif 'connection' in error_lower or 'timeout' in error_lower:
            return "NetworkError"
        else:
            return "RuntimeError"
    
    def get_known_solution(self, error: str) -> Optional[str]:
        """获取已知错误的解决方案"""
        error_key = self._normalize_error(error)
        
        if error_key in self.error_patterns:
            pattern = self.error_patterns[error_key]
            if pattern.success_rate > 0.5 and pattern.solution:
                return pattern.solution
        
        return None
    
    def generate_reflection_report(self) -> Dict:
        """
        生成反思报告
        
        Returns:
            包含统计数据和改进建议的报告
        """
        if not self.execution_history:
            return {
                'total_tasks': 0,
                'message': 'No execution history yet'
            }
        
        # 统计
        total = len(self.execution_history)
        successful = sum(1 for e in self.execution_history if e.success)
        failed = total - successful
        
        avg_duration = sum(e.duration for e in self.execution_history) / total
        
        # 最常用的能力
        capability_usage = {}
        for e in self.execution_history:
            for cap in e.capabilities_used:
                capability_usage[cap] = capability_usage.get(cap, 0) + 1
        top_capabilities = sorted(
            capability_usage.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]
        
        # 常见错误
        common_errors = sorted(
            self.error_patterns.items(),
            key=lambda x: x[1].occurrence_count,
            reverse=True
        )[:5]
        
        # 生成建议
        suggestions = self._generate_suggestions(
            successful, failed, common_errors
        )
        
        return {
            'total_tasks': total,
            'success_rate': successful / total * 100,
            'failed_tasks': failed,
            'avg_duration': avg_duration,
            'top_capabilities': top_capabilities,
            'common_errors': [
                {
                    'type': p.error_type,
                    'count': p.occurrence_count,
                    'success_rate': p.success_rate
                }
                for _, p in common_errors
            ],
            'suggestions': suggestions
        }
    
    def _generate_suggestions(
        self,
        successful: int,
        failed: int,
        common_errors: List
    ) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于成功率的建议
        if failed > successful:
            suggestions.append(
                "Success rate is low. Consider improving error handling and retry logic."
            )
        
        # 基于常见错误的建议
        for error_key, pattern in common_errors:
            if pattern.success_rate < 0.3:
                suggestions.append(
                    f"'{pattern.error_type}' occurs frequently with low resolution rate. "
                    f"Consider adding specialized handling for this error."
                )
        
        # 基于历史的建议
        recent = self.execution_history[-10:]
        recent_errors = sum(1 for e in recent if not e.success)
        if recent_errors > 5:
            suggestions.append(
                "Recent tasks have high failure rate. May need to review capability implementation."
            )
        
        if not suggestions:
            suggestions.append("System is performing well. Keep monitoring.")
        
        return suggestions
    
    def learn_from_search(
        self,
        query: str,
        results: List[Dict],
        success: bool
    ):
        """
        从搜索结果学习
        
        记录有效的搜索查询和结果
        """
        if 'search_queries' not in self.knowledge_base:
            self.knowledge_base['search_queries'] = {}
        
        # 记录这个查询的效果
        if query not in self.knowledge_base['search_queries']:
            self.knowledge_base['search_queries'][query] = {
                'attempts': 0,
                'successes': 0,
                'results': []
            }
        
        entry = self.knowledge_base['search_queries'][query]
        entry['attempts'] += 1
        if success:
            entry['successes'] += 1
        
        # 保存有效的结果
        if success and results:
            entry['results'].extend([
                {'url': r.get('url', ''), 'title': r.get('title', '')}
                for r in results[:2]
            ])
            # 去重
            seen = set()
            unique = []
            for r in entry['results']:
                if r['url'] not in seen:
                    seen.add(r['url'])
                    unique.append(r)
            entry['results'] = unique[:5]  # 只保留前5个
        
        self._save_memory()
    
    def print_report(self):
        """打印反思报告"""
        report = self.generate_reflection_report()
        
        print("\n" + "="*60)
        print("Self Reflection Report")
        print("="*60)
        
        if report['total_tasks'] == 0:
            print("No execution history yet.")
            return
        
        print(f"Total Tasks: {report['total_tasks']}")
        print(f"Success Rate: {report['success_rate']:.1f}%")
        print(f"Avg Duration: {report['avg_duration']:.2f}s")
        print()
        
        print("Top Capabilities:")
        for cap, count in report['top_capabilities']:
            print(f"  - {cap}: {count} uses")
        
        if report['common_errors']:
            print("\nCommon Errors:")
            for e in report['common_errors']:
                print(f"  - {e['type']}: {e['count']} times "
                      f"({e['success_rate']*100:.0f}% resolved)")
        
        print("\nSuggestions:")
        for s in report['suggestions']:
            print(f"  * {s}")
        
        print("="*60)


# 便捷函数
def reflect_on_task(
    task: str,
    success: bool,
    duration: float,
    capabilities: List[str],
    errors: List[str] = None
) -> TaskExecution:
    """快速记录任务执行"""
    reflection = SelfReflection()
    return reflection.record_execution(
        task_description=task,
        success=success,
        duration=duration,
        capabilities_used=capabilities,
        errors=errors
    )


if __name__ == "__main__":
    # 测试
    reflection = SelfReflection()
    
    # 模拟一些执行记录
    reflection.record_execution(
        task_description="Fetch weather data",
        success=True,
        duration=2.5,
        capabilities_used=["http_client", "json_parser"],
        errors=[]
    )
    
    reflection.record_execution(
        task_description="Parse HTML table",
        success=False,
        duration=1.2,
        capabilities_used=["html_parser"],
        errors=["ModuleNotFoundError: No module named 'bs4'"]
    )
    
    reflection.print_report()
