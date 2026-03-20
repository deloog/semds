"""
Intrinsic Evaluator 模块 - 静态代码质量评估

无需执行测试，仅分析代码本身的质量。
评估维度（按优先级）：
- P0: 语法正确性
- P0: 静态分析（导入、变量使用）
- P1: 代码结构（函数/类数量、嵌套深度、函数长度）
- P1: 文档完整性（文档字符串）
"""

import ast
from dataclasses import dataclass, field
from typing import Dict, List, Set


@dataclass
class EvaluationResult:
    """代码评估结果

    Attributes:
        syntax_valid: 语法是否有效
        static_score: 静态分析得分 (0-1)
        structure_score: 代码结构得分 (0-1)
        doc_score: 文档完整性得分 (0-1)
        total_score: 加权总得分 (0-1)
        syntax_errors: 语法错误列表
        warnings: 警告列表
    """

    syntax_valid: bool
    static_score: float
    structure_score: float
    doc_score: float
    total_score: float
    syntax_errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


class IntrinsicEvaluator:
    """静态代码质量评估器

    评估生成代码的内在质量，无需执行。
    使用AST进行语法和结构分析。

    Example:
        >>> evaluator = IntrinsicEvaluator()
        >>> result = evaluator.evaluate("def hello(): return 'world'")
        >>> print(f"Score: {result.total_score:.2f}")
    """

    # 权重配置
    WEIGHTS = {
        "syntax": 0.4,  # 语法正确性权重最高
        "static": 0.25,  # 静态分析
        "structure": 0.2,  # 代码结构
        "doc": 0.15,  # 文档完整性
    }

    # 结构评分阈值
    MAX_FUNCTION_LENGTH = 30  # 函数最大行数
    MAX_NESTING_DEPTH = 3  # 最大嵌套深度（在函数/类内部）

    def __init__(self) -> None:
        """初始化评估器"""
        self._warnings: List[str] = []

    def evaluate(self, code: str) -> EvaluationResult:
        """评估代码质量

        Args:
            code: 要评估的Python代码字符串

        Returns:
            EvaluationResult: 包含各维度得分的评估结果
        """
        self._warnings = []

        # 处理空代码
        if not code or not code.strip():
            return EvaluationResult(
                syntax_valid=False,
                static_score=0.0,
                structure_score=0.0,
                doc_score=0.0,
                total_score=0.0,
                syntax_errors=["Empty code provided"],
            )

        # 尝试解析AST
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return EvaluationResult(
                syntax_valid=False,
                static_score=0.0,
                structure_score=0.0,
                doc_score=0.0,
                total_score=0.0,
                syntax_errors=[f"Line {e.lineno}: {e.msg}"],
            )
        except IndentationError as e:
            return EvaluationResult(
                syntax_valid=False,
                static_score=0.0,
                structure_score=0.0,
                doc_score=0.0,
                total_score=0.0,
                syntax_errors=[f"Line {e.lineno}: IndentationError - {e.msg}"],
            )

        # 检查是否有实际代码内容（注释会被忽略，tree.body为空）
        if not tree.body:
            return EvaluationResult(
                syntax_valid=True,  # 语法上有效（注释）
                static_score=0.0,
                structure_score=0.0,
                doc_score=0.0,
                total_score=0.0,
                syntax_errors=[],
                warnings=["Code contains only comments or whitespace"],
            )

        # 语法有效，继续评估
        syntax_valid = True
        syntax_errors: List[str] = []

        # 评估各维度
        static_score = self._evaluate_static_analysis(tree, code)
        structure_score = self._evaluate_structure(tree, code)
        doc_score = self._evaluate_documentation(tree, code)

        # 计算加权总得分
        total_score = self._calculate_total_score(
            syntax_valid, static_score, structure_score, doc_score
        )

        return EvaluationResult(
            syntax_valid=syntax_valid,
            static_score=static_score,
            structure_score=structure_score,
            doc_score=doc_score,
            total_score=total_score,
            syntax_errors=syntax_errors,
            warnings=self._warnings,
        )

    def _evaluate_static_analysis(self, tree: ast.AST, code: str) -> float:
        """评估静态分析

        检查：
        - 未使用的导入
        - 未定义的变量引用（简化检查）
        - 冗余代码模式

        Returns:
            0-1之间的得分
        """
        score = 1.0

        # 收集所有导入
        imported_names: Dict[str, str] = {}  # name -> import type
        used_names: Set[str] = set()
        defined_names: Set[str] = set()

        for node in ast.walk(tree):
            # 收集导入
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names[name] = alias.name
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imported_names[name] = f"{module}.{alias.name}"

            # 收集变量定义
            elif isinstance(node, ast.FunctionDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.ClassDef):
                defined_names.add(node.name)
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                defined_names.add(node.id)
            elif isinstance(node, ast.arg):
                defined_names.add(node.arg)

            # 收集名称使用（排除导入语句本身）
            elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                used_names.add(node.id)

        # 检查未使用的导入
        for name in imported_names:
            if name not in used_names and name not in defined_names:
                self._warnings.append(f"Unused import: {name}")
                score -= 0.1  # 每个未使用导入扣0.1分

        # 检查可能的未定义变量（启发式检查）
        builtin_names = {
            "True",
            "False",
            "None",
            "abs",
            "all",
            "any",
            "bin",
            "bool",
            "bytes",
            "chr",
            "complex",
            "dict",
            "dir",
            "divmod",
            "enumerate",
            "filter",
            "float",
            "format",
            "frozenset",
            "getattr",
            "globals",
            "hasattr",
            "hash",
            "help",
            "hex",
            "id",
            "input",
            "int",
            "isinstance",
            "issubclass",
            "iter",
            "len",
            "list",
            "locals",
            "map",
            "max",
            "memoryview",
            "min",
            "next",
            "object",
            "oct",
            "open",
            "ord",
            "pow",
            "print",
            "property",
            "range",
            "repr",
            "reversed",
            "round",
            "set",
            "setattr",
            "slice",
            "sorted",
            "staticmethod",
            "str",
            "sum",
            "super",
            "tuple",
            "type",
            "vars",
            "zip",
            "__name__",
            "__file__",
            "__doc__",
            "__package__",
            "__spec__",
            "__annotations__",
            "__builtins__",
            "__cached__",
            "__loader__",
            "Exception",
            "BaseException",
            "ValueError",
            "TypeError",
            "KeyError",
            "IndexError",
            "AttributeError",
            "RuntimeError",
            "StopIteration",
            "GeneratorExit",
            "SystemExit",
            "KeyboardInterrupt",
            "ArithmeticError",
            "LookupError",
            "AssertionError",
            "BufferError",
            "EOFError",
            "ImportError",
            "ModuleNotFoundError",
            "NameError",
            "OSError",
            "IOError",
            "FileNotFoundError",
            "NotImplementedError",
            "RecursionError",
            "SyntaxError",
            "IndentationError",
            "TabError",
            "SystemError",
            "UnicodeError",
            "UnicodeDecodeError",
            "UnicodeEncodeError",
            "UnicodeTranslateError",
            "Warning",
            "UserWarning",
            "DeprecationWarning",
            "PendingDeprecationWarning",
            "SyntaxWarning",
            "RuntimeWarning",
            "FutureWarning",
            "ImportWarning",
            "UnicodeWarning",
            "BytesWarning",
            "ResourceWarning",
        }

        # 收集所有属性访问（如 obj.method）
        attribute_roots: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute):
                # 获取属性访问的根名称
                current = node.value
                while isinstance(current, ast.Attribute):
                    current = current.value
                if isinstance(current, ast.Name):
                    attribute_roots.add(current.id)

        # 检查可能的未定义变量
        for name in used_names:
            if (
                name not in imported_names
                and name not in defined_names
                and name not in builtin_names
                and name not in attribute_roots
            ):
                self._warnings.append(f"Possibly undefined: {name}")
                score -= 0.05  # 每个可能未定义扣0.05分

        return max(0.0, score)

    def _evaluate_structure(self, tree: ast.AST, code: str) -> float:
        """评估代码结构

        检查：
        - 函数数量
        - 类结构
        - 嵌套深度（在函数内部）
        - 函数长度

        Returns:
            0-1之间的得分
        """
        score = 1.0

        function_count = 0
        class_count = 0
        max_nesting_in_func = 0

        # 计算函数内部的嵌套深度
        def get_nesting_in_function(node: ast.AST) -> int:
            """计算函数内部的控制流嵌套深度"""
            max_d = 0

            def traverse(n: ast.AST, depth: int) -> int:
                nonlocal max_d
                max_d = max(max_d, depth)

                for child in ast.iter_child_nodes(n):
                    if isinstance(
                        child, (ast.For, ast.While, ast.If, ast.With, ast.Try)
                    ):
                        traverse(child, depth + 1)
                    elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        # 跳过嵌套函数，单独处理
                        pass
                    else:
                        traverse(child, depth)

                return max_d

            traverse(node, 0)
            return max_d

        # 检查函数长度和计数
        lines = code.split("\n")

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                function_count += 1

                # 计算函数行数
                func_lines = self._get_node_lines(node, lines)
                if len(func_lines) > self.MAX_FUNCTION_LENGTH:
                    self._warnings.append(
                        f"Function '{node.name}' is too long ({len(func_lines)} lines)"
                    )
                    score -= 0.15  # Penalty for long function

                # 检查函数内部嵌套深度
                func_nesting = get_nesting_in_function(node)
                max_nesting_in_func = max(max_nesting_in_func, func_nesting)

            elif isinstance(node, ast.ClassDef):
                class_count += 1

        # 嵌套深度惩罚（在函数内部）
        if max_nesting_in_func > self.MAX_NESTING_DEPTH:
            score -= 0.15 * (max_nesting_in_func - self.MAX_NESTING_DEPTH)

        # 奖励：有函数或类
        if function_count > 0 or class_count > 0:
            score = min(1.0, score + 0.1)
        else:
            # 没有函数或类（只有注释/表达式），降低得分
            score -= 0.5

        return max(0.0, min(1.0, score))

    def _evaluate_documentation(self, tree: ast.AST, code: str) -> float:
        """评估文档完整性

        检查：
        - 模块文档字符串
        - 函数/类文档字符串

        Returns:
            0-1之间的得分
        """
        # 检查模块文档
        has_module_doc = False
        if (
            tree.body  # type: ignore[attr-defined]
            and isinstance(tree.body[0], ast.Expr)  # type: ignore[attr-defined]
            and isinstance(tree.body[0].value, ast.Constant)  # type: ignore[attr-defined]
            and isinstance(tree.body[0].value.value, str)  # type: ignore[attr-defined]
        ):
            has_module_doc = True

        # 统计函数/类数量和有文档的数量
        total_items = 0
        documented_items = 0

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                total_items += 1

                # 检查是否有文档字符串
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    documented_items += 1

        # 计算得分
        if total_items == 0:
            # 没有函数/类，可能是注释-only代码
            # 如果只有模块文档（实际上是注释），得分应该较低
            if has_module_doc:
                # 检查是否为真正的文档字符串还是只是注释
                return 0.0  # 注释不算文档
            return 0.0

        doc_ratio = documented_items / total_items

        if has_module_doc:
            # 有模块文档，权重更高
            score = 0.3 + 0.7 * doc_ratio
        else:
            # 无模块文档
            score = 0.7 * doc_ratio

        return score

    def _calculate_total_score(
        self,
        syntax_valid: bool,
        static_score: float,
        structure_score: float,
        doc_score: float,
    ) -> float:
        """计算加权总得分

        Args:
            syntax_valid: 语法是否有效
            static_score: 静态分析得分
            structure_score: 结构得分
            doc_score: 文档得分

        Returns:
            加权总得分 (0-1)
        """
        if not syntax_valid:
            # 语法无效时，总得分大幅降低
            return 0.0

        # 加权平均
        total = (
            self.WEIGHTS["static"] * static_score
            + self.WEIGHTS["structure"] * structure_score
            + self.WEIGHTS["doc"] * doc_score
            + self.WEIGHTS["syntax"] * 1.0  # 语法有效贡献满分
        )

        return round(total, 2)

    def _get_node_lines(self, node: ast.AST, all_lines: List[str]) -> List[str]:
        """获取AST节点对应的源代码行

        Args:
            node: AST节点
            all_lines: 所有源代码行

        Returns:
            节点对应的行列表
        """
        if hasattr(node, "lineno") and hasattr(node, "end_lineno"):
            start = node.lineno - 1  # 转换为0-based索引
            end = node.end_lineno
            return all_lines[start:end]
        return []
