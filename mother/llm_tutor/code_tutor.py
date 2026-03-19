"""
Code Tutor - 编程教练
SEMDS 作为教练，指导本地模型改进代码
"""
import os
import sys
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict

sys.path.insert(0, 'D:\\semds')

from evolution.code_generator import CodeGenerator
from mother.skills.code_optimizer import CodeOptimizer


@dataclass
class LearningExample:
    """学习示例"""
    task: str
    bad_code: str
    good_code: str
    improvements: List[str]
    principles_applied: List[str]


@dataclass
class TutorSession:
    """教练会话"""
    session_id: str
    task: str
    iterations: List[Dict]
    final_code: str
    final_score: float
    lessons_learned: List[str]


class CodeTutor:
    """
    编程教练
    
    核心策略：
    1. 用 DeepSeek（强模型）生成黄金标准
    2. 分析本地模型代码与黄金标准的差距
    3. 生成针对性的改进建议
    4. 积累成功的学习示例
    """
    
    def __init__(self):
        # 强模型（教师）
        self.teacher = CodeGenerator(backend="deepseek")
        # 代码质量检查
        self.optimizer = CodeOptimizer()
        # 学习记录
        self.examples_db = "mother/llm_tutor/examples.json"
        self.examples = self._load_examples()
    
    def _load_examples(self) -> List[LearningExample]:
        """加载学习示例库"""
        if os.path.exists(self.examples_db):
            try:
                with open(self.examples_db, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return [LearningExample(**item) for item in data]
            except:
                pass
        return []
    
    def _save_examples(self):
        """保存学习示例"""
        os.makedirs(os.path.dirname(self.examples_db), exist_ok=True)
        with open(self.examples_db, 'w', encoding='utf-8') as f:
            json.dump([asdict(e) for e in self.examples], f, indent=2, ensure_ascii=False)
    
    def teach(
        self,
        task: str,
        student_code: str,
        max_iterations: int = 3
    ) -> TutorSession:
        """
        教学生改进代码
        """
        session_id = f"tutor_{int(time.time())}"
        iterations = []
        
        print(f"\n[Tutor] Starting session: {session_id}")
        print(f"[Tutor] Task: {task}")
        
        current_code = student_code
        
        for i in range(max_iterations):
            print(f"\n--- Iteration {i+1}/{max_iterations} ---")
            
            # 1. 评估当前代码
            assessment = self._assess_code(current_code)
            print(f"[Tutor] Score: {assessment['optimized_score']}/100")
            
            # 2. 如果已经很好了，提前结束
            if assessment['optimized_score'] >= 90:
                print("[Tutor] Code quality excellent, stopping early")
                break
            
            # 3. 生成改进建议
            feedback = self._generate_feedback(task, current_code, assessment)
            print(f"[Tutor] Feedback: {feedback['summary']}")
            
            # 4. 生成改进后的代码（用教师模型）
            improved = self._generate_improved_code(
                task, current_code, feedback
            )
            
            iterations.append({
                'iteration': i+1,
                'before_score': assessment['score'],
                'feedback': feedback,
                'improved_code': improved['code'][:200] + "...",
                'after_score': improved['score']
            })
            
            current_code = improved['code']
            
            if improved['score'] > assessment['score']:
                print(f"[Tutor] Improved: {assessment['score']} -> {improved['score']}")
        
        # 保存学习示例
        if iterations:
            self._record_learning_example(task, student_code, current_code, iterations)
        
        lessons = self._extract_lessons(iterations)
        
        session = TutorSession(
            session_id=session_id,
            task=task,
            iterations=iterations,
            final_code=current_code,
            final_score=self.optimizer.optimize(current_code)['optimized_score'],
            lessons_learned=lessons
        )
        
        print(f"\n[Tutor] Session complete")
        print(f"[Tutor] Final score: {session.final_score}/100")
        
        return session
    
    def _assess_code(self, code: str) -> Dict:
        """评估代码质量"""
        result = self.optimizer.optimize(code)
        return result
    
    def _generate_feedback(
        self,
        task: str,
        code: str,
        assessment: Dict
    ) -> Dict:
        """生成改进反馈"""
        issues = assessment['issues']
        
        feedback_points = []
        
        # 从优化器的问题中提取
        for issue in issues[:3]:
            if issue.severity == 'error':
                feedback_points.append(f"Fix {issue.code}: {issue.message}")
        
        # 检查常见缺失
        if 'isinstance(' not in code:
            feedback_points.append("Add input validation with isinstance()")
        if 'try:' not in code:
            feedback_points.append("Add error handling with try/except")
        if '"""' not in code:
            feedback_points.append("Add docstrings")
        
        return {
            'summary': f"Found {len(feedback_points)} areas to improve",
            'points': feedback_points
        }
    
    def _generate_improved_code(
        self,
        task: str,
        current_code: str,
        feedback: Dict
    ) -> Dict:
        """用教师模型生成改进后的代码"""
        task_spec = {
            "description": f"{task}\n\nCurrent code:\n{current_code}\n\nImprove following: {feedback['points']}",
            "function_signature": "def improved_function(...)",
            "requirements": [
                "Add type hints",
                "Add error handling",
                "Validate inputs",
                "Keep it minimal"
            ]
        }
        
        result = self.teacher.generate(task_spec)
        
        if result["success"]:
            improved_code = result["code"]
            new_score = self.optimizer.optimize(improved_code)['optimized_score']
            return {'code': improved_code, 'score': new_score}
        else:
            return {'code': current_code, 'score': 0}
    
    def _record_learning_example(
        self,
        task: str,
        bad_code: str,
        good_code: str,
        iterations: List[Dict]
    ):
        """记录学习示例"""
        improvements = []
        for it in iterations:
            improvements.extend(it['feedback']['points'])
        
        example = LearningExample(
            task=task,
            bad_code=bad_code[:500],
            good_code=good_code[:500],
            improvements=list(set(improvements)),
            principles_applied=["Type Safety", "Error Handling"]
        )
        
        self.examples.append(example)
        self._save_examples()
        
        print(f"[Tutor] Recorded example ({len(self.examples)} total)")
    
    def _extract_lessons(self, iterations: List[Dict]) -> List[str]:
        """提取经验教训"""
        lessons = []
        
        if not iterations:
            return lessons
        
        first_score = iterations[0]['before_score']
        last_score = iterations[-1].get('after_score', first_score)
        
        if last_score > first_score:
            improvement = last_score - first_score
            lessons.append(f"Improved by {improvement:.0f} points")
        
        return lessons
    
    def print_summary(self):
        """打印教学总结"""
        print("\n" + "="*60)
        print("Code Tutor Summary")
        print("="*60)
        print(f"Examples collected: {len(self.examples)}")
        
        if self.examples:
            print("\nRecent examples:")
            for e in self.examples[-3:]:
                print(f"  - {e.task[:50]}...")
        
        print("="*60)


if __name__ == "__main__":
    # 测试
    tutor = CodeTutor()
    
    student_code = '''
def fetch_data(url):
    import requests
    return requests.get(url).text
'''
    
    session = tutor.teach(
        task="Fetch data from URL safely",
        student_code=student_code
    )
    
    print("\nFinal code:")
    print(session.final_code[:500])
    
    tutor.print_summary()
