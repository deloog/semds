"""
Language-Aware Code Generator - 针对特定语言的代码生成

基于LanguageLearner学习的语言规格，生成该语言的代码。
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from evolution.code_generator import CodeGenerator
from mother.language_dev.language_learner import LanguageLearner


class LanguageAwareGenerator:
    """
    语言感知代码生成器

    能够基于已学习的语言规格生成代码。
    """

    def __init__(self, language_learner: Optional[LanguageLearner] = None):
        self.language_learner = language_learner or LanguageLearner()
        self._generators: Dict[str, CodeGenerator] = {}

    def generate_code(
        self, language: str, task_description: str, context: Optional[Dict] = None
    ) -> str:
        """
        为指定语言生成代码

        Args:
            language: 语言名称（如 "ailang", "python", "rust"）
            task_description: 任务描述
            context: 额外上下文（函数签名、类型要求等）

        Returns:
            生成的代码
        """
        # 检查是否学习了该语言
        lang_spec = self.language_learner.get_language(language)

        if lang_spec:
            # 使用语言特定的prompt
            base_prompt = self.language_learner.generate_prompt_template(language)
            prompt = f"{base_prompt}\n\nTASK: {task_description}"
        else:
            # 回退到通用prompt
            print(f"[WARNING] Language '{language}' not learned, using generic prompt")
            prompt = f"Write {language} code for: {task_description}"

        if context:
            if context.get("function_signature"):
                prompt += f"\nFunction signature: {context['function_signature']}"
            if context.get("types"):
                prompt += f"\nRequired types: {context['types']}"
            if context.get("constraints"):
                prompt += f"\nConstraints: {context['constraints']}"

        # 获取或创建该语言的生成器
        if language not in self._generators:
            self._generators[language] = CodeGenerator(backend="deepseek")

        generator = self._generators[language]

        # 生成代码
        print(
            f"[LangGenerator] Generating {language} code for: {task_description[:50]}..."
        )
        code = generator.generate(prompt)

        return code

    def generate_example_suite(
        self, language: str, difficulty_levels: List[str] = None
    ) -> Dict[str, List[str]]:
        """
        生成完整的示例代码套件

        Args:
            language: 目标语言
            difficulty_levels: 难度级别 ["beginner", "intermediate", "advanced"]

        Returns:
            按难度分类的代码示例
        """
        if difficulty_levels is None:
            difficulty_levels = ["beginner", "intermediate", "advanced"]

        examples = {"beginner": [], "intermediate": [], "advanced": []}

        tasks = {
            "beginner": [
                "Hello World program",
                "Variable declaration and basic operations",
                "Simple function with parameters",
                "Basic conditional statement",
                "Loop iteration example",
            ],
            "intermediate": [
                "Data structure implementation (list/dict)",
                "File I/O operations",
                "Error handling example",
                "Higher-order functions",
                "Basic module/package structure",
            ],
            "advanced": [
                "Concurrent/parallel programming",
                "Generic type implementation",
                "Complex algorithm (sorting/searching)",
                "DSL (Domain Specific Language) fragment",
                "Performance optimization example",
            ],
        }

        for level in difficulty_levels:
            print(f"\n[LangGenerator] Generating {level} examples...")
            for task in tasks.get(level, []):
                try:
                    code = self.generate_code(language, task)
                    examples[level].append({"task": task, "code": code})
                    print(f"  ✓ {task}")
                except Exception as e:
                    print(f"  ✗ {task}: {e}")

        return examples

    def generate_test_cases(
        self, language: str, code: str, function_name: str
    ) -> List[str]:
        """
        为生成的代码生成测试用例

        Args:
            language: 目标语言
            code: 被测试的代码
            function_name: 函数名

        Returns:
            测试用例列表
        """
        spec = self.language_learner.get_language(language)

        prompt = f"""
You are writing test cases for {language} code.

CODE TO TEST:
```{spec.file_extension if spec else language}
{code}
```

Generate 3-5 test cases for function `{function_name}`.
Include:
1. Normal case
2. Edge case
3. Error case (if applicable)

Output only the test code.
"""

        generator = self._generators.get(language) or CodeGenerator(backend="deepseek")
        test_code = generator.generate(prompt)

        return test_code

    def generate_documentation(
        self, language: str, code: str, doc_type: str = "inline"
    ) -> str:
        """
        为代码生成文档

        Args:
            language: 目标语言
            code: 源代码
            doc_type: 文档类型 ("inline", "api", "tutorial")

        Returns:
            生成的文档
        """
        prompts = {
            "inline": f"Add inline comments to this {language} code explaining each part:",
            "api": f"Generate API documentation for this {language} code:",
            "tutorial": f"Write a tutorial explaining this {language} code step by step:",
        }

        prompt = (
            f"{prompts.get(doc_type, prompts['inline'])}\n\n```{language}\n{code}\n```"
        )

        generator = self._generators.get(language) or CodeGenerator(backend="deepseek")
        documentation = generator.generate(prompt)

        return documentation

    def validate_syntax(self, language: str, code: str) -> Dict:
        """
        验证代码语法（基于学习的语言规格）

        Args:
            language: 目标语言
            code: 待验证代码

        Returns:
            验证结果
        """
        spec = self.language_learner.get_language(language)

        if not spec:
            return {
                "valid": True,
                "warnings": ["Language spec not found, skipping validation"],
            }

        errors = []
        warnings = []

        # 基本检查
        # 1. 检查是否使用了未定义的关键字
        import re

        words = re.findall(r"\b[a-zA-Z_]+\b", code)

        for word in words:
            if word in spec.keywords:
                continue  # 合法关键字
            # 其他单词可能是变量名，不报错

        # 2. 检查基本语法结构
        if spec.syntax_rules.get("function_declaration"):
            if "fn " in code or "function " in code or "def " in code:
                # 有函数定义，检查括号匹配
                if code.count("(") != code.count(")"):
                    errors.append("Unmatched parentheses in function definition")
                if code.count("{") != code.count("}"):
                    errors.append("Unmatched braces")

        return {"valid": len(errors) == 0, "errors": errors, "warnings": warnings}


if __name__ == "__main__":
    # 演示
    from mother.language_dev.language_learner import create_ai_native_language_spec

    # 1. 学习语言
    learner = LanguageLearner()
    spec = create_ai_native_language_spec()
    learner.learn_from_spec(spec)

    # 2. 创建语言感知生成器
    generator = LanguageAwareGenerator(learner)

    # 3. 生成代码示例
    print("\n" + "=" * 70)
    print("Generating AILang Examples")
    print("=" * 70)

    examples = generator.generate_example_suite("ailang", ["beginner", "intermediate"])

    for level, codes in examples.items():
        print(f"\n{level.upper()} EXAMPLES:")
        for example in codes:
            print(f"\n--- {example['task']} ---")
            print(
                example["code"][:500] + "..."
                if len(example["code"]) > 500
                else example["code"]
            )
