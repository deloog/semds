"""
SEMDS Language Development Kit - 演示

展示如何使用SEMDS来开发和完善一个新的编程语言。

流程:
1. 定义你的语言规格（语法、关键字、特性）
2. 让SEMDS学习这个语言
3. SEMDS生成完整的示例代码套件
4. SEMDS验证生成的代码
5. 根据实际运行情况改进语言规格
6. 重复步骤2-5，直到语言完善
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mother.language_dev.language_learner import LanguageLearner, LanguageSpec
from mother.language_dev.code_generator_lang import LanguageAwareGenerator
from mother.language_dev.example_suite import ExampleSuiteGenerator


def demo_create_custom_language():
    """
    演示：创建一个自定义编程语言

    假设你要创建一个叫 "FlowLang" 的语言，专注于数据流处理。
    """
    print("=" * 70)
    print("SEMDS Language Development Kit Demo")
    print("=" * 70)
    print("\nScenario: Developing a new programming language called 'FlowLang'")
    print("Focus: Data flow processing and pipeline operations")

    # Step 1: 定义语言规格
    print("\n" + "─" * 70)
    print("STEP 1: Define Language Specification")
    print("─" * 70)

    flowlang_spec = LanguageSpec(
        name="FlowLang",
        version="0.1.0",
        file_extension=".flow",
        syntax_rules={
            "variable": "let <name>: <type> = <value>",
            "pipeline": "source |> transform1 |> transform2 |> sink",
            "function": "fn <name>(<params>) -> <return> { <body> }",
            "stream": "stream<T> for continuous data",
            "node": "node <name> { inputs..., outputs..., process }",
        },
        keywords=[
            "let",
            "fn",
            "stream",
            "node",
            "pipeline",
            "source",
            "sink",
            "map",
            "filter",
            "reduce",
            "merge",
            "split",
            "buffer",
            "window",
            "trigger",
            "async",
            "await",
            "parallel",
            "batch",
        ],
        operators=[
            "|>",  # Pipeline operator
            "->",  # Arrow for function types
            "=>",  # Lambda
            "++",  # Stream concatenation
            "**",  # Parallel execution
        ],
        type_system={
            "int": "Integer",
            "float": "Floating point",
            "string": "UTF-8 string",
            "stream<T>": "Continuous stream of T",
            "node": "Processing node",
            "pipeline": "Connected processing pipeline",
            "batch<T>": "Batch of T for processing",
        },
        control_structures={
            "if": "if condition { ... } else { ... }",
            "for": "for item in stream { ... }",
            "match": "match value { pattern => action }",
            "when": "when event { action }  # Event-driven",
        },
        function_syntax="fn name(params) -> return_type { body }",
        module_syntax="module Name { nodes..., pipelines..., exports }",
        example_programs=[
            {
                "description": "Simple data pipeline",
                "code": """
# Read data, transform, output
let source = file_source("data.csv")
let pipeline = source
    |> parse_csv()
    |> filter(row -> row.value > 0)
    |> transform(row -> {{ value: row.value * 2 }})
    |> json_sink("output.json")

pipeline.run()
""",
            },
            {
                "description": "Stream processing node",
                "code": """
# Define a processing node
node Counter {
    input: stream<int> numbers
    output: stream<int> counts
    
    process {
        let count = 0
        for n in numbers {
            count = count + 1
            emit count
        }
    }
}
""",
            },
        ],
        design_philosophy="""
        FlowLang is designed for data flow processing:
        1. Everything is a stream or node
        2. Pipeline syntax for clear data flow
        3. Event-driven and async by default
        4. Type-safe stream operations
        5. Easy parallelization with ** operator
        """,
        target_use_cases=[
            "ETL data pipelines",
            "Real-time stream processing",
            "IoT data ingestion",
            "Event-driven applications",
            "Dataflow programming",
        ],
    )

    print(f"\nLanguage: {flowlang_spec.name} v{flowlang_spec.version}")
    print(f"Extension: {flowlang_spec.file_extension}")
    print(f"Keywords: {len(flowlang_spec.keywords)}")
    print(f"Syntax rules: {len(flowlang_spec.syntax_rules)}")

    input("\nPress Enter to continue...")

    # Step 2: 让SEMDS学习这个语言
    print("\n" + "─" * 70)
    print("STEP 2: SEMDS Learns FlowLang")
    print("─" * 70)

    learner = LanguageLearner()
    success = learner.learn_from_spec(flowlang_spec)

    if not success:
        print("Failed to learn language!")
        return

    print("\n✓ SEMDS has learned FlowLang")
    print(f"  Known languages: {', '.join(learner.list_languages())}")

    input("\nPress Enter to continue...")

    # Step 3: 生成示例代码套件
    print("\n" + "─" * 70)
    print("STEP 3: Generate Example Code Suite")
    print("─" * 70)

    lang_gen = LanguageAwareGenerator(learner)
    suite_gen = ExampleSuiteGenerator(lang_gen)

    output_dir = "examples/flowlang"
    print(f"\nGenerating examples to: {output_dir}")
    print("This will create 20-30 example files covering:")
    print("  - Basic syntax")
    print("  - Data structures")
    print("  - Stream operations")
    print("  - Pipeline patterns")
    print("  - Real-world applications")

    # 注意：实际生成会调用DeepSeek API，可能需要时间
    print("\n[NOTE] In demo mode, showing expected structure...")
    print("  To generate real examples, run:")
    print(
        f"    python -m mother.language_dev generate --lang flowlang --output {output_dir}"
    )

    # 模拟生成结构
    expected_structure = {
        "01_basics": ["hello_world.flow", "variables.flow", "pipelines.flow"],
        "02_algorithms": ["stream_processing.flow", "data_transformation.flow"],
        "03_stdlib": ["file_io.flow", "network.flow"],
        "04_patterns": ["pipeline_pattern.flow", "node_pattern.flow"],
        "05_applications": ["etl_pipeline.flow", "realtime_processor.flow"],
    }

    print("\nExpected structure:")
    for category, files in expected_structure.items():
        print(f"  {category}/")
        for f in files:
            print(f"    - {f}")

    input("\nPress Enter to continue...")

    # Step 4: 展示如何使用生成的示例
    print("\n" + "─" * 70)
    print("STEP 4: Using Generated Examples")
    print("─" * 70)

    print("\nGenerated examples serve multiple purposes:")
    print("\n1. Language Documentation")
    print("   - Shows idiomatic usage patterns")
    print("   - Demonstrates best practices")
    print("   - Serves as tutorial material")

    print("\n2. Compiler/Interpreter Testing")
    print("   - Validates parser implementation")
    print("   - Tests semantic analysis")
    print("   - Checks code generation")

    print("\n3. Learning Resource")
    print("   - New users can study examples")
    print("   - Shows progression from basic to advanced")
    print("   - Common patterns are documented")

    input("\nPress Enter to continue...")

    # Step 5: 迭代改进
    print("\n" + "─" * 70)
    print("STEP 5: Iterative Improvement")
    print("─" * 70)

    print("\nThe development cycle:")
    print("""
    Define Language Spec
           ↓
    SEMDS Learns Language
           ↓
    Generate Examples
           ↓
    Test with Real Compiler
           ↓
    Identify Issues
           ↓
    Update Language Spec
           ↓
    [Repeat]
    """)

    print("\nExample improvements based on testing:")
    print("  Issue: Pipeline operator |> is ambiguous")
    print("  Fix: Update syntax_rules to clarify precedence")
    print("  ")
    print("  Issue: Missing error handling in streams")
    print("  Fix: Add try/catch or Result<T, E> type")
    print("  ")
    print("  Issue: Keywords conflict with common variable names")
    print("  Fix: Rename keywords (e.g., 'node' -> 'processor')")

    input("\nPress Enter to continue...")

    # Summary
    print("\n" + "=" * 70)
    print("DEMO COMPLETE")
    print("=" * 70)

    print("\nFlowLang specification saved to:")
    print(f"  storage/languages/flowlang.json")

    print("\nNext steps:")
    print("  1. Review and refine the language spec")
    print("  2. Generate full example suite:")
    print("     python -m mother.language_dev generate --lang flowlang")
    print("  3. Build compiler/interpreter using examples as test cases")
    print("  4. Iterate based on implementation feedback")

    print("\nSEMDS accelerates language development by:")
    print("  ✓ Auto-generating comprehensive examples")
    print("  ✓ Ensuring consistency across examples")
    print("  ✓ Providing validation and testing")
    print("  ✓ Enabling rapid iteration on language design")


if __name__ == "__main__":
    try:
        demo_create_custom_language()
    except KeyboardInterrupt:
        print("\n\nDemo interrupted.")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback

        traceback.print_exc()
