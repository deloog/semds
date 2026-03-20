"""
Example Suite Generator - 为语言生成完整示例套件

生成覆盖语言各特性的示例代码，帮助学习和完善语言。
"""

import json
from pathlib import Path
from typing import Dict, List


class ExampleSuiteGenerator:
    """
    示例套件生成器

    为编程语言生成完整的示例集合，包括：
    - 基础语法示例
    - 标准库使用
    - 设计模式实现
    - 实际应用场景
    """

    def __init__(self, language_generator):
        """
        Args:
            language_generator: LanguageAwareGenerator实例
        """
        self.generator = language_generator

    def generate_full_suite(self, language: str, output_dir: str) -> Dict:
        """
        生成完整的示例套件

        Args:
            language: 目标语言
            output_dir: 输出目录

        Returns:
            生成的文件列表
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        results = {"language": language, "generated_files": [], "categories": {}}

        print(f"[ExampleSuite] Generating full suite for {language}...")

        # 1. 基础示例
        print("\n[1/5] Basic syntax examples...")
        basics = self._generate_basics(language, output_path / "01_basics")
        results["categories"]["basics"] = basics

        # 2. 数据结构与算法
        print("\n[2/5] Data structures and algorithms...")
        algorithms = self._generate_algorithms(language, output_path / "02_algorithms")
        results["categories"]["algorithms"] = algorithms

        # 3. 标准库使用
        print("\n[3/5] Standard library examples...")
        stdlib = self._generate_stdlib(language, output_path / "03_stdlib")
        results["categories"]["stdlib"] = stdlib

        # 4. 设计模式
        print("\n[4/5] Design patterns...")
        patterns = self._generate_patterns(language, output_path / "04_patterns")
        results["categories"]["patterns"] = patterns

        # 5. 实际应用
        print("\n[5/5] Real-world applications...")
        applications = self._generate_applications(
            language, output_path / "05_applications"
        )
        results["categories"]["applications"] = applications

        # 生成索引文件
        self._generate_index(output_path, results)

        print(
            f"\n[ExampleSuite] ✓ Complete! Generated {len(results['generated_files'])} files"
        )
        print(f"  Location: {output_path.absolute()}")

        return results

    def _generate_basics(self, language: str, output_dir: Path) -> List[str]:
        """生成基础语法示例"""
        output_dir.mkdir(exist_ok=True)
        files = []

        topics = [
            ("hello_world", "Hello World program"),
            ("variables", "Variable declaration and types"),
            ("operators", "Arithmetic and logical operators"),
            ("control_flow", "If/else, loops, pattern matching"),
            ("functions", "Function definition and calling"),
            ("collections", "Lists, dictionaries, sets"),
            ("strings", "String manipulation and interpolation"),
            ("error_handling", "Try/catch or equivalent"),
        ]

        for filename, description in topics:
            try:
                code = self.generator.generate_code(
                    language,
                    f"Demonstrate {description} in {language}",
                    context={"difficulty": "beginner"},
                )

                filepath = output_dir / f"{filename}.{self._get_extension(language)}"
                self._write_file(filepath, code, description)
                files.append(str(filepath))
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")

        return files

    def _generate_algorithms(self, language: str, output_dir: Path) -> List[str]:
        """生成算法示例"""
        output_dir.mkdir(exist_ok=True)
        files = []

        algorithms = [
            ("sorting", "Implement quicksort and mergesort"),
            ("searching", "Binary search and linear search"),
            ("graph", "DFS and BFS traversal"),
            ("dynamic_programming", "Fibonacci with memoization"),
            ("data_structures", "Stack, queue, linked list implementation"),
        ]

        for filename, description in algorithms:
            try:
                code = self.generator.generate_code(
                    language,
                    f"{description} in {language}",
                    context={"difficulty": "intermediate"},
                )

                filepath = output_dir / f"{filename}.{self._get_extension(language)}"
                self._write_file(filepath, code, description)
                files.append(str(filepath))
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")

        return files

    def _generate_stdlib(self, language: str, output_dir: Path) -> List[str]:
        """生成标准库使用示例"""
        output_dir.mkdir(exist_ok=True)
        files = []

        topics = [
            ("file_io", "Reading and writing files"),
            ("json", "JSON parsing and serialization"),
            ("datetime", "Date and time handling"),
            ("networking", "HTTP client/server basics"),
            ("regex", "Regular expressions"),
            ("math", "Mathematical operations"),
        ]

        for filename, description in topics:
            try:
                code = self.generator.generate_code(
                    language,
                    f"Demonstrate {description} using {language} standard library",
                )

                filepath = output_dir / f"{filename}.{self._get_extension(language)}"
                self._write_file(filepath, code, description)
                files.append(str(filepath))
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")

        return files

    def _generate_patterns(self, language: str, output_dir: Path) -> List[str]:
        """生成设计模式示例"""
        output_dir.mkdir(exist_ok=True)
        files = []

        patterns = [
            ("singleton", "Singleton pattern implementation"),
            ("factory", "Factory pattern for object creation"),
            ("observer", "Observer pattern for event handling"),
            ("strategy", "Strategy pattern for algorithm selection"),
            ("pipeline", "Pipeline pattern for data processing"),
        ]

        for filename, description in patterns:
            try:
                code = self.generator.generate_code(
                    language,
                    f"{description} in {language} style",
                    context={"difficulty": "advanced", "paradigm": "object_oriented"},
                )

                filepath = output_dir / f"{filename}.{self._get_extension(language)}"
                self._write_file(filepath, code, description)
                files.append(str(filepath))
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")

        return files

    def _generate_applications(self, language: str, output_dir: Path) -> List[str]:
        """生成实际应用示例"""
        output_dir.mkdir(exist_ok=True)
        files = []

        apps = [
            ("cli_tool", "Command line argument parser"),
            ("web_server", "Simple HTTP server"),
            ("data_processor", "CSV data processing pipeline"),
            ("chat_server", "WebSocket chat server"),
            ("ml_inference", "Machine learning model serving"),
        ]

        for filename, description in apps:
            try:
                code = self.generator.generate_code(
                    language,
                    f"Build a {description} in {language}",
                    context={"difficulty": "advanced", "real_world": True},
                )

                filepath = output_dir / f"{filename}.{self._get_extension(language)}"
                self._write_file(filepath, code, description)
                files.append(str(filepath))
                print(f"  ✓ {filename}")
            except Exception as e:
                print(f"  ✗ {filename}: {e}")

        return files

    def _write_file(self, filepath: Path, code: str, description: str):
        """写入文件并添加头部注释"""
        lang_spec = self.generator.language_learner.get_language(
            filepath.suffix.lstrip(".")
        )

        # 根据语言选择注释符号
        comment_char = "#"
        if lang_spec:
            # 可以尝试从spec中获取注释符号
            pass

        header = f"""{comment_char} {filepath.name}
{comment_char} {description}
{comment_char} Generated by SEMDS Language Development Kit
{comment_char} Language: {lang_spec.name if lang_spec else 'Unknown'}

"""

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(header + code)

        return filepath

    def _generate_index(self, output_dir: Path, results: Dict):
        """生成索引文件"""
        index_file = output_dir / "INDEX.md"

        content = f"""# {results['language']} Example Suite

Generated by SEMDS Language Development Kit

## Structure

"""

        for category, files in results["categories"].items():
            content += f"\n### {category.replace('_', ' ').title()}\n\n"
            for f in files:
                filename = Path(f).name
                content += f"- [{filename}]({f})\n"

        content += f"""

## Statistics

- Total files: {len(results['generated_files'])}
- Categories: {len(results['categories'])}

## Usage

Browse the examples by category, or start with `01_basics/hello_world`.

## Learning Path

1. Start with `01_basics/` - Learn syntax fundamentals
2. Continue to `02_algorithms/` - See language capabilities
3. Explore `03_stdlib/` - Master standard library
4. Study `04_patterns/` - Learn idiomatic patterns
5. Build from `05_applications/` - Real-world examples
"""

        with open(index_file, "w", encoding="utf-8") as f:
            f.write(content)

        print(f"\n  Generated index: {index_file}")

    def _get_extension(self, language: str) -> str:
        """获取文件扩展名"""
        spec = self.generator.language_learner.get_language(language)
        if spec:
            return spec.file_extension.lstrip(".")
        return language


if __name__ == "__main__":
    # 演示
    from mother.language_dev.code_generator_lang import LanguageAwareGenerator
    from mother.language_dev.language_learner import (
        LanguageLearner,
        create_ai_native_language_spec,
    )

    # 学习语言
    learner = LanguageLearner()
    spec = create_ai_native_language_spec()
    learner.learn_from_spec(spec)

    # 创建生成器
    lang_gen = LanguageAwareGenerator(learner)
    suite_gen = ExampleSuiteGenerator(lang_gen)

    # 生成完整套件
    results = suite_gen.generate_full_suite("ailang", "examples/ailang")

    print("\n" + "=" * 70)
    print("Example suite generation complete!")
    print("=" * 70)
    print(f"Files: {len(results['generated_files'])}")
    print(f"Location: examples/ailang/")
