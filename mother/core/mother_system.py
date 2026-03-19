"""
Mother System - 母体系统核心
自主任务执行引擎
"""
import os
import sys

sys.path.insert(0, r'D:\semds')

from mother.core.task_analyzer import TaskAnalyzer, ExecutionPlan
from mother.core.capability_registry import CapabilityRegistry
from mother.core.tool_generator import ToolGenerator


class MotherSystem:
    """
    SEMDS Mother System - 自主任务母体
    
    核心循环：
    1. 理解任务 -> 2. 检查能力 -> 3. 生成缺失工具 -> 4. 执行 -> 5. 验证
    """
    
    def __init__(self):
        self.analyzer = TaskAnalyzer()
        self.registry = CapabilityRegistry()
        self.generator = ToolGenerator()
        
        print("[Mother] System initialized")
        print(f"[Mother] Available capabilities: {self.registry.list_all()}")
    
    def execute(self, task_description: str) -> dict:
        """
        执行用户任务
        
        Args:
            task_description: 自然语言描述的任务
        
        Returns:
            执行结果
        """
        print(f"\n{'='*60}")
        print(f"[Mother] New Task: {task_description}")
        print(f"{'='*60}\n")
        
        # Step 1: 理解任务
        print("[Step 1] Analyzing task...")
        plan = self.analyzer.analyze(task_description)
        
        if not plan.required_capabilities:
            print("[Mother] Unknown task type, cannot proceed")
            return {"success": False, "error": "Unknown task type"}
        
        print(f"[Mother] Required capabilities: {plan.required_capabilities}")
        print(f"[Mother] Execution steps: {len(plan.steps)}")
        
        # Step 2: 检查能力
        print("\n[Step 2] Checking capabilities...")
        has_all, missing = self.registry.check(plan.required_capabilities)
        
        if missing:
            print(f"[Mother] Missing capabilities: {missing}")
            
            # Step 3: 生成缺失工具
            print("\n[Step 3] Generating missing tools...")
            for cap in missing:
                print(f"\n[ToolGen] Creating: {cap}")
                code = self.generator.generate(cap)
                if code:
                    # 重新加载注册表以包含新工具
                    self.registry._load_tool_module(cap)
                    print(f"[OK] {cap} ready")
                else:
                    print(f"[FAIL] Failed to generate {cap}")
                    return {"success": False, "error": f"Cannot generate tool: {cap}"}
        else:
            print("[Mother] All capabilities available")
        
        # Step 4: 执行计划
        print(f"\n[Step 4] Executing plan...")
        context = {}  # 存储步骤输出
        
        for i, step in enumerate(plan.steps, 1):
            print(f"\n  Step {i}/{len(plan.steps)}: [{step.action}] {step.description}")
            
            # 获取工具
            tool = self.registry.get(step.action)
            if not tool:
                return {"success": False, "error": f"Tool not found: {step.action}"}
            
            # 准备输入（替换上下文变量）
            inputs = self._resolve_inputs(step.inputs, context)
            
            # 执行
            try:
                result = tool.execute(**inputs)
                context[step.outputs] = result
                print(f"    [OK] Output -> {step.outputs}")
            except Exception as e:
                print(f"    [FAIL] {e}")
                return {"success": False, "error": str(e), "step": i}
        
        # Step 5: 返回结果
        print(f"\n{'='*60}")
        print("[Mother] Task completed successfully!")
        print(f"{'='*60}\n")
        
        return {
            "success": True,
            "outputs": context,
            "plan": {
                "task": plan.task,
                "steps": len(plan.steps),
                "capabilities_used": plan.required_capabilities
            }
        }
    
    def _resolve_inputs(self, inputs: dict, context: dict) -> dict:
        """解析输入参数，替换上下文变量"""
        resolved = {}
        for key, value in inputs.items():
            if isinstance(value, str) and value.startswith("{{") and value.endswith("}}"):
                # 从上下文获取
                var_name = value[2:-2]
                resolved[key] = context.get(var_name, value)
            else:
                resolved[key] = value
        return resolved


# 演示
if __name__ == "__main__":
    mother = MotherSystem()
    
    # 测试任务：爬取 Bing 首页图片
    result = mother.execute("爬取 https://www.bing.com 首页的图片")
    
    if result["success"]:
        print(f"\n结果: 找到 {len(result['outputs'].get('extracted_data', []))} 张图片")
        for url in result['outputs'].get('extracted_data', [])[:5]:
            print(f"  - {url}")
    else:
        print(f"失败: {result.get('error')}")
