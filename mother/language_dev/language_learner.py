"""
Language Learner - 让 SEMDS 学习新编程语言

输入语言规格（语法、语义、特性），SEMDS 学习后生成该语言的代码。
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class LanguageSpec:
    """编程语言规格"""
    name: str
    version: str
    file_extension: str
    
    # 语法定义
    syntax_rules: Dict[str, str] = field(default_factory=dict)
    keywords: List[str] = field(default_factory=list)
    operators: List[str] = field(default_factory=list)
    
    # 类型系统
    type_system: Dict[str, str] = field(default_factory=dict)
    
    # 控制结构
    control_structures: Dict[str, str] = field(default_factory=dict)
    
    # 函数/模块定义
    function_syntax: str = ""
    module_syntax: str = ""
    
    # 示例代码（用于 few-shot learning）
    example_programs: List[Dict] = field(default_factory=list)
    
    # 设计哲学（影响代码生成风格）
    design_philosophy: str = ""
    
    # 目标场景
    target_use_cases: List[str] = field(default_factory=list)


class LanguageLearner:
    """
    语言学习器
    
    学习新的编程语言规格，为后续代码生成做准备。
    """
    
    def __init__(self, storage_dir: str = "storage/languages"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._languages: Dict[str, LanguageSpec] = {}
        self._load_all_languages()
    
    def learn_from_spec(self, spec: LanguageSpec) -> bool:
        """
        学习新语言规格
        
        Args:
            spec: 语言规格定义
            
        Returns:
            是否成功学习
        """
        print(f"[LanguageLearner] Learning {spec.name} v{spec.version}...")
        
        # 验证规格完整性
        if not self._validate_spec(spec):
            print(f"[ERROR] Invalid language spec")
            return False
        
        # 保存到内存
        self._languages[spec.name.lower()] = spec
        
        # 持久化到文件
        self._save_language(spec)
        
        print(f"[LanguageLearner] [OK] Learned {spec.name}")
        print(f"  - Syntax rules: {len(spec.syntax_rules)}")
        print(f"  - Keywords: {len(spec.keywords)}")
        print(f"  - Example programs: {len(spec.example_programs)}")
        
        return True
    
    def learn_from_file(self, spec_file: str) -> bool:
        """从JSON文件学习语言规格"""
        path = Path(spec_file)
        if not path.exists():
            print(f"[ERROR] Spec file not found: {spec_file}")
            return False
        
        try:
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            spec = LanguageSpec(**data)
            return self.learn_from_spec(spec)
            
        except Exception as e:
            print(f"[ERROR] Failed to load spec: {e}")
            return False
    
    def get_language(self, name: str) -> Optional[LanguageSpec]:
        """获取已学习的语言"""
        return self._languages.get(name.lower())
    
    def list_languages(self) -> List[str]:
        """列出所有已学习的语言"""
        return list(self._languages.keys())
    
    def generate_prompt_template(self, lang_name: str) -> str:
        """
        为指定语言生成代码生成的Prompt模板
        
        这个模板会被CodeGenerator使用来生成该语言的代码
        """
        spec = self.get_language(lang_name)
        if not spec:
            raise ValueError(f"Language not learned: {lang_name}")
        
        template = f"""You are an expert programmer writing code in {spec.name} (v{spec.version}).

LANGUAGE SPECIFICATION:
Name: {spec.name}
File Extension: {spec.file_extension}
Design Philosophy: {spec.design_philosophy}
Target Use Cases: {', '.join(spec.target_use_cases)}

SYNTAX RULES:
"""
        
        for rule_name, rule_def in spec.syntax_rules.items():
            template += f"- {rule_name}: {rule_def}\n"
        
        template += f"\nKEYWORDS: {', '.join(spec.keywords)}\n"
        template += f"OPERATORS: {', '.join(spec.operators)}\n"
        
        if spec.type_system:
            template += f"\nTYPE SYSTEM:\n"
            for type_name, type_def in spec.type_system.items():
                template += f"- {type_name}: {type_def}\n"
        
        if spec.control_structures:
            template += f"\nCONTROL STRUCTURES:\n"
            for struct_name, struct_def in spec.control_structures.items():
                template += f"- {struct_name}: {struct_def}\n"
        
        template += f"\nFUNCTION SYNTAX: {spec.function_syntax}\n"
        template += f"MODULE SYNTAX: {spec.module_syntax}\n"
        
        # 添加示例程序（few-shot learning）
        if spec.example_programs:
            template += f"\nEXAMPLE PROGRAMS:\n"
            for i, example in enumerate(spec.example_programs[:3], 1):  # 最多3个示例
                template += f"\nExample {i}: {example.get('description', 'No description')}\n"
                template += f"```{spec.file_extension}\n{example.get('code', '')}\n```\n"
        
        template += f"\nINSTRUCTION:\nWrite clean, idiomatic {spec.name} code following the above syntax rules.\n"
        template += f"Only output the code, no explanation.\n"
        
        return template
    
    def _validate_spec(self, spec: LanguageSpec) -> bool:
        """验证语言规格完整性"""
        if not spec.name or not spec.file_extension:
            return False
        if len(spec.syntax_rules) < 2:
            print(f"[WARNING] Very few syntax rules defined")
        return True
    
    def _save_language(self, spec: LanguageSpec):
        """保存语言规格到文件"""
        file_path = self.storage_dir / f"{spec.name.lower()}.json"
        
        # 转换为字典
        data = {
            "name": spec.name,
            "version": spec.version,
            "file_extension": spec.file_extension,
            "syntax_rules": spec.syntax_rules,
            "keywords": spec.keywords,
            "operators": spec.operators,
            "type_system": spec.type_system,
            "control_structures": spec.control_structures,
            "function_syntax": spec.function_syntax,
            "module_syntax": spec.module_syntax,
            "example_programs": spec.example_programs,
            "design_philosophy": spec.design_philosophy,
            "target_use_cases": spec.target_use_cases,
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_all_languages(self):
        """加载所有已保存的语言"""
        if not self.storage_dir.exists():
            return
        
        for file_path in self.storage_dir.glob("*.json"):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                spec = LanguageSpec(**data)
                self._languages[spec.name.lower()] = spec
                print(f"[LanguageLearner] [OK] Loaded {spec.name} from storage")
            except Exception as e:
                print(f"[WARNING] Failed to load {file_path}: {e}")


def create_ai_native_language_spec() -> LanguageSpec:
    """
    创建一个示例：AI-Native 编程语言规格
    
    你可以基于这个模板修改，定义你自己的语言。
    """
    return LanguageSpec(
        name="AILang",
        version="0.1.0",
        file_extension=".ai",
        
        syntax_rules={
            "variable_declaration": "let <name>: <type> = <value>",
            "function_declaration": "fn <name>(<params>) -> <return_type> { <body> }",
            "comment": "# single line, ### multi-line ###",
            "string_interpolation": '"Hello {name}"',
            "list_comprehension": "[x * 2 for x in items if x > 0]",
        },
        
        keywords=[
            "fn", "let", "const", "if", "else", "for", "in", "while",
            "return", "match", "type", "impl", "trait", "import", "export",
            "async", "await", "parallel", "pipeline", "model", "train", "infer"
        ],
        
        operators=[
            "+", "-", "*", "/", "%", "**",
            "==", "!=", "<", ">", "<=", ">=",
            "&&", "||", "!",
            "|>", "->", "=>",
            "??", "?:"
        ],
        
        type_system={
            "int": "Integer type",
            "float": "Floating point",
            "string": "UTF-8 string",
            "bool": "Boolean",
            "list<T>": "Generic list",
            "dict<K,V>": "Generic dictionary",
            "tensor": "Multi-dimensional array for AI",
            "model": "ML model type",
            "promise<T>": "Async promise"
        },
        
        control_structures={
            "if": "if condition { ... } else { ... }",
            "for": "for item in iterable { ... }",
            "while": "while condition { ... }",
            "match": "match value { pattern => expr, _ => default }",
            "pipeline": "data |> step1 |> step2 |> step3"
        },
        
        function_syntax="fn name(params) -> return_type { body }",
        module_syntax="module Name { imports... exports... }",
        
        example_programs=[
            {
                "description": "Hello World",
                "code": '''
# Hello World in AILang
fn main() {
    print("Hello, AI-Native World!")
}
'''
            },
            {
                "description": "Data Pipeline",
                "code": '''
# Data processing pipeline
fn process_data(raw_data: list<float>) -> list<float> {
    raw_data
    |> normalize()
    |> remove_outliers()
    |> smooth(window=5)
}
'''
            },
            {
                "description": "Model Inference",
                "code": '''
# AI model inference
fn predict(input: tensor) -> tensor {
    let model = load_model("resnet50")
    return model.infer(input)
}
'''
            }
        ],
        
        design_philosophy="""
        AILang is designed for AI-first programming:
        1. Built-in support for tensor operations and ML pipelines
        2. Concise syntax for data transformation
        3. First-class async and parallel execution
        4. Type safety with powerful inference
        5. Composable functions via pipeline operator
        """,
        
        target_use_cases=[
            "Machine Learning pipelines",
            "Data processing and ETL",
            "AI model serving",
            "Scientific computing",
            "Distributed computing"
        ]
    )


if __name__ == "__main__":
    # 演示
    learner = LanguageLearner()
    
    # 创建示例语言规格
    spec = create_ai_native_language_spec()
    
    # 学习这个语言
    learner.learn_from_spec(spec)
    
    # 生成prompt模板
    print("\n" + "="*70)
    print("Generated Prompt Template:")
    print("="*70)
    template = learner.generate_prompt_template("ailang")
    print(template)
