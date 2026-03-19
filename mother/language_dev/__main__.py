"""
SEMDS Language Development Kit - 命令行入口

Usage:
    python -m mother.language_dev --help
    python -m mother.language_dev learn --spec mylang.json
    python -m mother.language_dev generate --lang mylang --output ./examples
    python -m mother.language_dev validate --lang mylang --file test.my
"""

import argparse
import json
import sys
from pathlib import Path

from mother.language_dev.language_learner import (
    LanguageLearner,
    LanguageSpec,
    create_ai_native_language_spec,
)
from mother.language_dev.code_generator_lang import LanguageAwareGenerator
from mother.language_dev.example_suite import ExampleSuiteGenerator


def cmd_learn(args):
    """学习新语言"""
    learner = LanguageLearner()

    if args.spec:
        # 从文件学习
        success = learner.learn_from_file(args.spec)
    elif args.create_example:
        # 创建示例语言
        spec = create_ai_native_language_spec()
        success = learner.learn_from_spec(spec)
        print(f"\nCreated example language: {spec.name}")
        print(f"Extension: {spec.file_extension}")
    else:
        print("Error: Provide --spec or --create-example")
        return 1

    if success:
        print("\n✓ Language learned successfully")
        languages = learner.list_languages()
        print(f"Known languages: {', '.join(languages)}")
    else:
        print("\n✗ Failed to learn language")
        return 1

    return 0


def cmd_generate(args):
    """生成示例代码"""
    learner = LanguageLearner()
    lang_gen = LanguageAwareGenerator(learner)
    suite_gen = ExampleSuiteGenerator(lang_gen)

    # 检查语言是否已学习
    if not learner.get_language(args.lang):
        print(f"Error: Language '{args.lang}' not learned yet")
        print("Run: python -m mother.language_dev learn --spec <file>")
        return 1

    # 生成完整套件
    output_dir = args.output or f"examples/{args.lang}"
    results = suite_gen.generate_full_suite(args.lang, output_dir)

    print("\n" + "=" * 70)
    print(f"Generated {len(results['generated_files'])} example files")
    print(f"Location: {Path(output_dir).absolute()}")
    print("=" * 70)

    return 0


def cmd_validate(args):
    """验证代码"""
    learner = LanguageLearner()
    lang_gen = LanguageAwareGenerator(learner)

    # 读取代码文件
    if not Path(args.file).exists():
        print(f"Error: File not found: {args.file}")
        return 1

    with open(args.file, "r", encoding="utf-8") as f:
        code = f.read()

    # 验证
    result = lang_gen.validate_syntax(args.lang, code)

    print(f"\nValidation Result for {args.file}:")
    print(f"  Valid: {'✓ Yes' if result['valid'] else '✗ No'}")

    if result["errors"]:
        print(f"\n  Errors:")
        for error in result["errors"]:
            print(f"    - {error}")

    if result["warnings"]:
        print(f"\n  Warnings:")
        for warning in result["warnings"]:
            print(f"    - {warning}")

    return 0 if result["valid"] else 1


def cmd_list(args):
    """列出已学习的语言"""
    learner = LanguageLearner()
    languages = learner.list_languages()

    if not languages:
        print("No languages learned yet")
        print("Run: python -m mother.language_dev learn --spec <file>")
    else:
        print("\nLearned languages:")
        for lang in languages:
            spec = learner.get_language(lang)
            print(f"  - {spec.name} (v{spec.version}) [{spec.file_extension}]")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description="SEMDS Language Development Kit - Develop AI-Native Programming Languages"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # learn command
    learn_parser = subparsers.add_parser(
        "learn", help="Learn a new programming language"
    )
    learn_parser.add_argument("--spec", help="Language specification JSON file")
    learn_parser.add_argument(
        "--create-example", action="store_true", help="Create example AILang"
    )
    learn_parser.set_defaults(func=cmd_learn)

    # generate command
    gen_parser = subparsers.add_parser("generate", help="Generate example suite")
    gen_parser.add_argument("--lang", required=True, help="Language name")
    gen_parser.add_argument("--output", "-o", help="Output directory")
    gen_parser.set_defaults(func=cmd_generate)

    # validate command
    val_parser = subparsers.add_parser("validate", help="Validate code syntax")
    val_parser.add_argument("--lang", required=True, help="Language name")
    val_parser.add_argument("--file", required=True, help="Code file to validate")
    val_parser.set_defaults(func=cmd_validate)

    # list command
    list_parser = subparsers.add_parser("list", help="List learned languages")
    list_parser.set_defaults(func=cmd_list)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
