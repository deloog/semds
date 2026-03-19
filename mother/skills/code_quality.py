"""
Code Quality Checker - 代码质量检查
强制执行 Mother System 开发规范
"""
import ast
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass


@dataclass
class CodeIssue:
    """代码问题"""
    line: int
    column: int
    code: str
    message: str
    severity: str  # error, warning, info
    fix_suggestion: str


class CodeQualityChecker:
    """
    代码质量检查器
    
    检查项：
    1. 类型注解
    2. 文档字符串
    3. 错误处理
    4. 代码风格
    5. 安全问题
    """
    
    SEVERITY_WEIGHTS = {
        'error': 3,
        'warning': 2,
        'info': 1
    }
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def check(self, code: str, filename: str = "<generated>") -> Dict:
        """
        全面检查代码质量
        
        Returns:
            {
                'passed': bool,
                'score': float,  # 0-100
                'issues': List[CodeIssue],
                'summary': str
            }
        """
        self.issues = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                line=e.lineno or 1,
                column=e.offset or 0,
                code='SYNTAX_ERROR',
                message=f"Syntax error: {e.msg}",
                severity='error',
                fix_suggestion="Check for missing colons, brackets, or quotes"
            ))
            return self._build_result()
        
        # 运行所有检查
        self._check_type_annotations(tree, code)
        self._check_docstrings(tree)
        self._check_error_handling(tree)
        self._check_code_style(code)
        self._check_security(tree, code)
        
        return self._build_result()
    
    def _check_type_annotations(self, tree: ast.AST, code: str):
        """检查类型注解"""
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 检查函数参数类型
                if node.name.startswith('_'):
                    continue  # 私有函数可以跳过
                
                has_annotation = any(
                    arg.annotation for arg in node.args.args
                )
                has_return = node.returns is not None
                
                if not has_annotation and node.args.args:
                    self.issues.append(CodeIssue(
                        line=node.lineno,
                        column=node.col_offset,
                        code='MISSING_TYPE_ANNOTATION',
                        message=f"Function '{node.name}' missing parameter type annotations",
                        severity='warning',
                        fix_suggestion="Add type hints like: def func(x: int) -> str:"
                    ))
                
                if not has_return:
                    self.issues.append(CodeIssue(
                        line=node.lineno,
                        column=node.col_offset,
                        code='MISSING_RETURN_TYPE',
                        message=f"Function '{node.name}' missing return type annotation",
                        severity='warning',
                        fix_suggestion="Add return type: def func() -> ReturnType:"
                    ))
                
                # 检查 Any 类型使用
                func_code = ast.get_source_segment(code, node) or ''
                if 'Any' in func_code and 'from typing import' in func_code:
                    self.issues.append(CodeIssue(
                        line=node.lineno,
                        column=node.col_offset,
                        code='AVOID_ANY_TYPE',
                        message="Avoid using 'Any' type, use specific types or Union",
                        severity='info',
                        fix_suggestion="Replace Any with specific type or use Union[Type1, Type2]"
                    ))
    
    def _check_docstrings(self, tree: ast.AST):
        """检查文档字符串"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                if node.name.startswith('_'):
                    continue
                
                has_docstring = (
                    ast.get_docstring(node) is not None
                )
                
                if not has_docstring:
                    node_type = 'Function' if isinstance(node, ast.FunctionDef) else 'Class'
                    self.issues.append(CodeIssue(
                        line=node.lineno,
                        column=node.col_offset,
                        code='MISSING_DOCSTRING',
                        message=f"{node_type} '{node.name}' missing docstring",
                        severity='warning',
                        fix_suggestion=f'Add """Description here.""" after definition'
                    ))
    
    def _check_error_handling(self, tree: ast.AST, code: str = None):
        """检查错误处理"""
        for node in ast.walk(tree):
            if isinstance(node, ast.Try):
                # 检查裸 except
                for handler in node.handlers:
                    if handler.type is None:
                        self.issues.append(CodeIssue(
                            line=handler.lineno,
                            column=handler.col_offset,
                            code='BARE_EXCEPT',
                            message="Bare 'except:' clause found, should catch specific exceptions",
                            severity='error',
                            fix_suggestion="Use 'except SpecificException:' instead of 'except:'"
                        ))
                    elif isinstance(handler.type, ast.Name):
                        if handler.type.id == 'Exception' and len(node.handlers) == 1:
                            self.issues.append(CodeIssue(
                                line=handler.lineno,
                                column=handler.col_offset,
                                code='BROAD_EXCEPTION',
                                message="Catching broad 'Exception', be more specific",
                                severity='warning',
                                fix_suggestion="Catch specific exceptions like ValueError, KeyError, etc."
                            ))
    
    def _check_code_style(self, code: str):
        """检查代码风格"""
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 行长度检查
            if len(line) > 100:
                self.issues.append(CodeIssue(
                    line=i,
                    column=100,
                    code='LINE_TOO_LONG',
                    message=f"Line {i} exceeds 100 characters ({len(line)} chars)",
                    severity='warning',
                    fix_suggestion="Break line into multiple lines"
                ))
            
            # 检查尾随空格
            if line.rstrip() != line:
                self.issues.append(CodeIssue(
                    line=i,
                    column=len(line),
                    code='TRAILING_WHITESPACE',
                    message=f"Trailing whitespace on line {i}",
                    severity='info',
                    fix_suggestion="Remove trailing spaces"
                ))
        
        # 检查导入格式
        if '\nimport ' in code and 'from ' in code:
            # 简单的导入分组检查
            pass  # 可以扩展更复杂的检查
    
    def _check_security(self, tree: ast.AST, code: str):
        """安全检查"""
        dangerous_functions = ['eval', 'exec', 'compile', '__import__']
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in dangerous_functions:
                        self.issues.append(CodeIssue(
                            line=node.lineno,
                            column=node.col_offset,
                            code='DANGEROUS_FUNCTION',
                            message=f"Potentially dangerous function '{node.func.id}' used",
                            severity='error',
                            fix_suggestion=f"Avoid using {node.func.id}(), use safer alternatives"
                        ))
            
            # 检查硬编码密钥
            if isinstance(node, ast.Constant):
                if isinstance(node.value, str):
                    value = node.value.lower()
                    if any(keyword in value for keyword in ['api_key', 'password', 'secret', 'token']):
                        if len(node.value) > 10:  # 看起来像真正的密钥
                            self.issues.append(CodeIssue(
                                line=node.lineno,
                                column=node.col_offset,
                                code='HARDCODED_SECRET',
                                message="Possible hardcoded secret detected",
                                severity='error',
                                fix_suggestion="Use environment variables: os.environ.get('API_KEY')"
                            ))
    
    def _build_result(self) -> Dict:
        """构建检查结果"""
        if not self.issues:
            return {
                'passed': True,
                'score': 100.0,
                'issues': [],
                'summary': 'All checks passed! Code quality: Excellent'
            }
        
        # 计算分数
        total_weight = sum(
            self.SEVERITY_WEIGHTS[i.severity] for i in self.issues
        )
        score = max(0, 100 - total_weight * 5)
        
        # 统计
        errors = sum(1 for i in self.issues if i.severity == 'error')
        warnings = sum(1 for i in self.issues if i.severity == 'warning')
        
        summary = f"Found {errors} errors, {warnings} warnings. Score: {score:.1f}/100"
        
        return {
            'passed': errors == 0 and score >= 70,
            'score': score,
            'issues': self.issues,
            'summary': summary
        }
    
    def get_fixes(self, code: str) -> str:
        """
        尝试自动修复代码问题
        
        Returns:
            修复后的代码
        """
        lines = code.split('\n')
        
        # 简单的自动修复
        for issue in self.issues:
            if issue.code == 'TRAILING_WHITESPACE':
                lines[issue.line - 1] = lines[issue.line - 1].rstrip()
        
        return '\n'.join(lines)
    
    def print_report(self, result: Dict):
        """打印检查报告"""
        print("\n" + "="*60)
        print(f"Code Quality Report - Score: {result['score']:.1f}/100")
        print("="*60)
        print(result['summary'])
        print()
        
        # 按严重性分组
        errors = [i for i in result['issues'] if i.severity == 'error']
        warnings = [i for i in result['issues'] if i.severity == 'warning']
        infos = [i for i in result['issues'] if i.severity == 'info']
        
        if errors:
            print("\nERRORS (Must Fix):")
            for i in errors[:5]:  # 最多显示5个
                print(f"  Line {i.line}: {i.code}")
                print(f"    {i.message}")
                print(f"    Fix: {i.fix_suggestion}")
        
        if warnings:
            print(f"\nWARNINGS ({len(warnings)} issues)")
        
        if infos:
            print(f"\nINFO ({len(infos)} issues)")
        
        print("="*60)


class AutoFixer:
    """
    自动修复器
    根据检查结果自动修复代码
    """
    
    def __init__(self):
        self.checker = CodeQualityChecker()
    
    def fix(self, code: str, max_iterations: int = 3) -> Tuple[str, Dict]:
        """
        自动修复代码
        
        Returns:
            (fixed_code, result)
        """
        current_code = code
        
        for i in range(max_iterations):
            result = self.checker.check(current_code)
            
            if result['passed'] or not result['issues']:
                return current_code, result
            
            print(f"[AutoFix] Iteration {i+1}: {result['summary']}")
            
            # 应用自动修复
            current_code = self._apply_fixes(current_code, result['issues'])
        
        return current_code, self.checker.check(current_code)
    
    def _apply_fixes(self, code: str, issues: List[CodeIssue]) -> str:
        """应用修复"""
        lines = code.split('\n')
        
        for issue in issues:
            if issue.line > len(lines):
                continue
            
            line_idx = issue.line - 1
            
            if issue.code == 'TRAILING_WHITESPACE':
                lines[line_idx] = lines[line_idx].rstrip()
            
            elif issue.code == 'MISSING_DOCSTRING':
                # 添加简单 docstring
                indent = len(lines[line_idx]) - len(lines[line_idx].lstrip())
                docstring = ' ' * indent + '"""TODO: Add description."""'
                lines.insert(line_idx + 1, docstring)
            
            elif issue.code == 'LINE_TOO_LONG':
                # 简单的行分割
                line = lines[line_idx]
                if '(' in line and ')' in line:
                    # 尝试在括号处换行
                    # 这是一个简化版本，实际可能需要更复杂的逻辑
                    pass
        
        return '\n'.join(lines)


# 便捷函数
def check_code(code: str, filename: str = "<generated>") -> Dict:
    """快速检查代码"""
    checker = CodeQualityChecker()
    return checker.check(code, filename)


def fix_code(code: str) -> Tuple[str, Dict]:
    """自动修复代码"""
    fixer = AutoFixer()
    return fixer.fix(code)


if __name__ == "__main__":
    # 测试
    test_code = '''
def bad_function(x, y):
    result = eval(x)  # Dangerous!
    return result

class MyClass:
    def method(self):
        try:
            pass
        except:  # Bare except
            pass
'''
    
    print("Testing Code Quality Checker...")
    result = check_code(test_code)
    
    checker = CodeQualityChecker()
    checker.print_report(result)
