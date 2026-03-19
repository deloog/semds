"""
Capability Registry - 能力注册表
管理可用工具，检查缺失能力
"""
import os
import sys
import importlib.util
from typing import Dict, List, Tuple, Optional, Any


class Capability:
    """Capability / Tool base class"""
    def __init__(self, name: str = None, description: str = None):
        self.name = name or self.__class__.__name__
        self.description = description or "Auto-generated tool"
    
    def execute(self, **kwargs) -> Any:
        """执行能力"""
        raise NotImplementedError


class HTTPClient(Capability):
    """HTTP 客户端能力"""
    def __init__(self):
        super().__init__("http_client", "发送 HTTP 请求")
    
    def execute(self, url: str, method: str = "GET", **kwargs) -> str:
        import requests
        response = requests.request(method, url, **kwargs)
        return response.text


class CapabilityRegistry:
    """能力注册表"""
    
    def __init__(self, tools_dir: str = "mother/tools"):
        self.capabilities: Dict[str, Capability] = {}
        self.tools_dir = tools_dir
        
        # 注册基础能力
        self._register_builtin_capabilities()
        
        # 加载已生成的工具
        self._load_generated_tools()
    
    def _register_builtin_capabilities(self):
        """注册内置能力"""
        self.register("http_client", HTTPClient())
    
    def _load_generated_tools(self):
        """从 tools 目录加载已生成的工具"""
        if not os.path.exists(self.tools_dir):
            return
        
        for filename in os.listdir(self.tools_dir):
            if filename.endswith(".py") and not filename.startswith("_"):
                tool_name = filename[:-3]
                self._load_tool_module(tool_name)
    
    def _load_tool_module(self, tool_name: str):
        """动态加载工具模块"""
        try:
            tool_path = os.path.join(self.tools_dir, f"{tool_name}.py")
            if not os.path.exists(tool_path):
                return
            
            spec = importlib.util.spec_from_file_location(tool_name, tool_path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[tool_name] = module
            spec.loader.exec_module(module)
            
            # 查找能力类（假设以 Tool 结尾）
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and 
                    issubclass(attr, Capability) and 
                    attr != Capability):
                    instance = attr()
                    self.register(tool_name, instance)
                    break
        except Exception as e:
            print(f"[Registry] Failed to load {tool_name}: {e}")
    
    def register(self, name: str, capability: Capability):
        """注册能力"""
        self.capabilities[name] = capability
        print(f"[Registry] Registered: {name}")
    
    def has(self, name: str) -> bool:
        """检查是否拥有某能力"""
        return name in self.capabilities
    
    def get(self, name: str) -> Optional[Capability]:
        """获取能力实例"""
        return self.capabilities.get(name)
    
    def check(self, required: List[str]) -> Tuple[bool, List[str]]:
        """
        检查是否满足所需能力
        
        Returns:
            (是否全部满足, 缺失的能力列表)
        """
        missing = [c for c in required if not self.has(c)]
        return len(missing) == 0, missing
    
    def list_all(self) -> List[str]:
        """列出所有可用能力"""
        return list(self.capabilities.keys())


if __name__ == "__main__":
    # 测试
    registry = CapabilityRegistry()
    print(f"Available capabilities: {registry.list_all()}")
    
    # 检查能力
    has_all, missing = registry.check(["http_client", "html_parser"])
    print(f"Has all: {has_all}")
    print(f"Missing: {missing}")
