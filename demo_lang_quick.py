"""
SEMDS Language Development Kit - 快速演示（非交互式）
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mother.language_dev.language_learner import LanguageLearner, LanguageSpec
from mother.language_dev.code_generator_lang import LanguageAwareGenerator


def main():
    print("="*70)
    print("SEMDS Language Development Kit - Quick Demo")
    print("="*70)
    
    # 1. 创建语言规格
    print("\n[Step 1] Creating FlowLang specification...")
    
    spec = LanguageSpec(
        name="FlowLang",
        version="0.1.0",
        file_extension=".flow",
        syntax_rules={
            "variable": "let <name>: <type> = <value>",
            "pipeline": "source |> transform |> sink",
            "function": "fn <name>(<params>) -> <return> { <body> }",
        },
        keywords=["let", "fn", "stream", "pipeline", "source", "sink", "map", "filter"],
        operators=["|>", "->", "=>"],
        type_system={
            "int": "Integer",
            "float": "Floating point", 
            "stream<T>": "Stream of T",
        },
        control_structures={
            "if": "if condition { ... }",
            "for": "for item in stream { ... }",
        },
        function_syntax="fn name(params) -> return_type { body }",
        module_syntax="module Name { ... }",
        example_programs=[
            {
                "description": "Simple pipeline",
                "code": "let data = [1, 2, 3]\ndata |> map(x -> x * 2) |> print"
            }
        ],
        design_philosophy="FlowLang is for data flow processing",
        target_use_cases=["ETL pipelines", "Stream processing"]
    )
    
    print(f"  Name: {spec.name}")
    print(f"  Version: {spec.version}")
    print(f"  Keywords: {len(spec.keywords)}")
    print(f"  Syntax rules: {len(spec.syntax_rules)}")
    
    # 2. 学习语言
    print("\n[Step 2] SEMDS is learning FlowLang...")
    learner = LanguageLearner()
    success = learner.learn_from_spec(spec)
    
    if success:
        print("  [OK] FlowLang learned successfully!")
    else:
        print("  [FAIL] Failed to learn")
        return
    
    # 3. 生成Prompt模板
    print("\n[Step 3] Generating code generation prompt...")
    template = learner.generate_prompt_template("flowlang")
    
    print("  Prompt template preview (first 800 chars):")
    print("  " + "-"*66)
    for line in template[:800].split('\n')[:15]:
        print(f"  {line}")
    print("  " + "-"*66)
    print(f"  ... (total {len(template)} characters)")
    
    # 4. 列出已学习的语言
    print("\n[Step 4] SEMDS now knows these languages:")
    languages = learner.list_languages()
    for lang in languages:
        spec = learner.get_language(lang)
        print(f"  - {spec.name} (v{spec.version}) [{spec.file_extension}]")
    
    # 5. 说明下一步
    print("\n" + "="*70)
    print("Next Steps:")
    print("="*70)
    print("""
1. Generate complete example suite:
   python -m mother.language_dev generate --lang flowlang

2. Or in Python code:
   from mother.language_dev import ExampleSuiteGenerator
   suite_gen = ExampleSuiteGenerator(lang_gen)
   results = suite_gen.generate_full_suite("flowlang", "examples/flowlang")

3. Use the generated examples to:
   - Test your compiler/parser
   - Write language documentation
   - Create tutorials
   - Validate syntax design

4. Iterate: Update language spec based on testing feedback
""")
    
    print("="*70)
    print("FlowLang spec saved to: storage/languages/flowlang.json")
    print("="*70)


if __name__ == "__main__":
    main()
