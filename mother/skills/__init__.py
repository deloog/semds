"""
Mother System Skills Package
自主代理技能集合
"""

from mother.skills.web_search import WebSearchSkill, search_solution
from mother.skills.code_quality import CodeQualityChecker, check_code, fix_code
from mother.skills.self_reflection import SelfReflection, reflect_on_task

__all__ = [
    "WebSearchSkill",
    "search_solution",
    "CodeQualityChecker",
    "check_code",
    "fix_code",
    "SelfReflection",
    "reflect_on_task",
]


# 技能元数据
SKILL_REGISTRY = {
    "web_search": {
        "name": "Web Search",
        "description": "Search the internet for solutions and information",
        "class": WebSearchSkill,
        "requirements": ["duckduckgo-search"],
        "auto_activate": True,
    },
    "code_quality": {
        "name": "Code Quality Checker",
        "description": "Enforce coding standards and best practices",
        "class": CodeQualityChecker,
        "requirements": [],
        "auto_activate": True,
    },
    "self_reflection": {
        "name": "Self Reflection",
        "description": "Learn from experience and improve over time",
        "class": SelfReflection,
        "requirements": [],
        "auto_activate": True,
    },
}


def list_skills():
    """列出所有可用技能"""
    print("\n[Available Skills]")
    for skill_id, info in SKILL_REGISTRY.items():
        print(f"  - {info['name']}: {info['description']}")
        if info.get("auto_activate"):
            print(f"    [Auto-activated]")
    print()


def get_skill(skill_id: str):
    """获取技能实例"""
    if skill_id in SKILL_REGISTRY:
        return SKILL_REGISTRY[skill_id]["class"]()
    return None


if __name__ == "__main__":
    list_skills()
