"""
Web Search Skill - 联网搜索能力
让 Mother System 能够自主搜索解决方案
"""

import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import quote_plus

sys.path.insert(0, r"D:\semds")


@dataclass
class SearchResult:
    """搜索结果"""

    title: str
    url: str
    snippet: str
    source: str  # 搜索引擎来源


class WebSearchSkill:
    """
    联网搜索技能

    支持多种搜索后端：
    - DuckDuckGo (免费，无需API Key)
    - Bing Search API (需要 Key)
    - Google Custom Search (需要 Key)
    """

    def __init__(self, backend: str = "duckduckgo"):
        self.backend = backend
        self.last_search_time = 0
        self.min_interval = 1.0  # 搜索间隔限制（秒）

    def search(
        self, query: str, num_results: int = 5, search_type: str = "general"
    ) -> List[SearchResult]:
        """
        执行搜索

        Args:
            query: 搜索查询
            num_results: 返回结果数量
            search_type: 搜索类型 (general/code/error/debug)

        Returns:
            搜索结果列表
        """
        # 速率限制
        elapsed = time.time() - self.last_search_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)

        # 根据类型优化查询
        optimized_query = self._optimize_query(query, search_type)

        print(f"[Search] {optimized_query}")

        try:
            if self.backend == "duckduckgo":
                results = self._search_duckduckgo(optimized_query, num_results)
            else:
                results = []

            self.last_search_time = time.time()
            return results

        except Exception as e:
            print(f"[Search Error] {e}")
            return []

    def _optimize_query(self, query: str, search_type: str) -> str:
        """根据搜索类型优化查询"""
        optimizations = {
            "code": lambda q: f"{q} python code example stackoverflow",
            "error": lambda q: f"{q} python solution fix",
            "debug": lambda q: f"{q} debug python github issues",
            "api": lambda q: f"{q} python api documentation",
            "tutorial": lambda q: f"{q} python tutorial guide 2024",
        }

        if search_type in optimizations:
            return optimizations[search_type](query)
        return query

    def _search_duckduckgo(self, query: str, num_results: int) -> List[SearchResult]:
        """
        使用 DuckDuckGo 搜索
        优先使用 duckduckgo-search 库，否则使用 fallback
        """
        try:
            # 尝试新版 ddgs
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=num_results):
                    results.append(
                        SearchResult(
                            title=r.get("title", ""),
                            url=r.get("href", ""),
                            snippet=r.get("body", ""),
                            source="duckduckgo",
                        )
                    )

            return results

        except ImportError:
            print("[Search] ddgs not installed, using fallback")
            print("[Tip] Install with: pip install ddgs")
            # 返回模拟结果用于演示
            return self._mock_search_results(query, num_results)

    def _search_fallback(self, query: str, num_results: int) -> List[SearchResult]:
        """
        备用搜索方案 - 使用 requests + BeautifulSoup
        注意：这可能不稳定，仅供演示
        """
        import requests
        from bs4 import BeautifulSoup

        try:
            # DuckDuckGo HTML 搜索
            url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }

            response = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(response.text, "html.parser")

            results = []
            for result in soup.select(".result")[:num_results]:
                title_elem = result.select_one(".result__title")
                snippet_elem = result.select_one(".result__snippet")
                url_elem = result.select_one(".result__url")

                if title_elem and url_elem:
                    results.append(
                        SearchResult(
                            title=title_elem.get_text(strip=True),
                            url=url_elem.get_text(strip=True),
                            snippet=(
                                snippet_elem.get_text(strip=True)
                                if snippet_elem
                                else ""
                            ),
                            source="duckduckgo_html",
                        )
                    )

            return results

        except Exception as e:
            print(f"[Fallback Search Error] {e}")
            return self._mock_search_results(query, num_results)

    def _mock_search_results(self, query: str, num_results: int) -> List[SearchResult]:
        """
        模拟搜索结果（用于演示或无网络时）
        """
        # 根据查询关键词返回相关示例结果
        mock_data = {
            "python": [
                (
                    "Python Documentation",
                    "https://docs.python.org/3/",
                    "Official Python documentation",
                ),
                (
                    "Python Tutorial - W3Schools",
                    "https://www.w3schools.com/python/",
                    "Learn Python programming",
                ),
            ],
            "error": [
                (
                    "Stack Overflow - Python Questions",
                    "https://stackoverflow.com/questions/tagged/python",
                    "Community Q&A",
                ),
                (
                    "Python Error Handling Guide",
                    "https://docs.python.org/3/tutorial/errors.html",
                    "Official error handling tutorial",
                ),
            ],
            "html": [
                (
                    "MDN Web Docs - HTML",
                    "https://developer.mozilla.org/en-US/docs/Web/HTML",
                    "HTML documentation",
                ),
                ("HTML Tutorial", "https://www.w3schools.com/html/", "Learn HTML"),
            ],
        }

        # 尝试匹配关键词
        results = []
        for keyword, data in mock_data.items():
            if keyword in query.lower():
                for title, url, snippet in data[:num_results]:
                    results.append(
                        SearchResult(
                            title=title, url=url, snippet=snippet, source="mock"
                        )
                    )

        # 默认结果
        if not results:
            results.append(
                SearchResult(
                    title=f"Search results for: {query[:30]}...",
                    url="https://duckduckgo.com",
                    snippet="This is a simulated search result. Install duckduckgo-search for real results.",
                    source="mock",
                )
            )

        return results[:num_results]

    def search_for_solution(self, error_message: str, context: str = "") -> List[Dict]:
        """
        针对错误搜索解决方案

        Args:
            error_message: 错误信息
            context: 上下文代码或描述

        Returns:
            解决方案建议列表
        """
        # 提取关键错误信息
        clean_error = self._extract_error_keywords(error_message)

        # 构建搜索查询
        query = f"python {clean_error} solution"
        if context:
            query += f" {context[:50]}"

        results = self.search(query, num_results=3, search_type="error")

        # 提取解决方案
        solutions = []
        for r in results:
            solutions.append(
                {
                    "source": r.url,
                    "title": r.title,
                    "suggestion": r.snippet[:200],
                    "confidence": self._estimate_confidence(r, error_message),
                }
            )

        # 按置信度排序
        solutions.sort(key=lambda x: x["confidence"], reverse=True)
        return solutions

    def _extract_error_keywords(self, error: str) -> str:
        """提取错误关键词"""
        # 去除文件路径和行号
        import re

        # 移除文件路径
        error = re.sub(r'File "[^"]+", line \d+', "", error)
        # 移除 traceback
        error = re.sub(r"Traceback \(most recent call last\):", "", error)
        # 清理
        error = " ".join(error.split())
        return error[:150]

    def _estimate_confidence(self, result: SearchResult, original_error: str) -> float:
        """估计搜索结果的置信度"""
        score = 0.5

        # 标题包含关键词加分
        error_keywords = original_error.lower().split()
        title_lower = result.title.lower()
        snippet_lower = result.snippet.lower()

        for keyword in error_keywords:
            if len(keyword) > 3:  # 只考虑有意义的词
                if keyword in title_lower:
                    score += 0.1
                if keyword in snippet_lower:
                    score += 0.05

        # 来源加分
        high_quality_sources = ["stackoverflow", "github", "python.org", "docs"]
        for source in high_quality_sources:
            if source in result.url.lower():
                score += 0.1
                break

        return min(score, 1.0)


class KnowledgeBase:
    """
    本地知识库
    存储搜索过的解决方案，避免重复搜索
    """

    def __init__(self, kb_path: str = "mother/knowledge_base.json"):
        self.kb_path = kb_path
        self.knowledge = self._load()

    def _load(self) -> Dict:
        """加载知识库"""
        if os.path.exists(self.kb_path):
            try:
                with open(self.kb_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"solutions": {}, "patterns": {}}

    def save(self):
        """保存知识库"""
        os.makedirs(os.path.dirname(self.kb_path), exist_ok=True)
        with open(self.kb_path, "w", encoding="utf-8") as f:
            json.dump(self.knowledge, f, indent=2, ensure_ascii=False)

    def get_solution(self, error_pattern: str) -> Optional[Dict]:
        """获取已知解决方案"""
        return self.knowledge["solutions"].get(error_pattern)

    def add_solution(self, error_pattern: str, solution: Dict):
        """添加解决方案"""
        self.knowledge["solutions"][error_pattern] = {
            **solution,
            "timestamp": time.time(),
            "use_count": 0,
        }
        self.save()

    def record_usage(self, error_pattern: str, success: bool):
        """记录解决方案使用效果"""
        if error_pattern in self.knowledge["solutions"]:
            entry = self.knowledge["solutions"][error_pattern]
            entry["use_count"] += 1
            if success:
                entry["success_count"] = entry.get("success_count", 0) + 1
            self.save()


# 便捷函数
def search_solution(error: str, context: str = "") -> List[Dict]:
    """快速搜索解决方案"""
    searcher = WebSearchSkill()
    return searcher.search_for_solution(error, context)


if __name__ == "__main__":
    # 测试
    searcher = WebSearchSkill()

    # 测试普通搜索
    print("=" * 60)
    print("Test 1: General Search")
    results = searcher.search("python dataclasses tutorial", num_results=3)
    for r in results:
        print(f"\nTitle: {r.title}")
        print(f"URL: {r.url}")
        print(f"Snippet: {r.snippet[:100]}...")

    # 测试错误搜索
    print("\n" + "=" * 60)
    print("Test 2: Error Solution Search")
    error = "TypeError: 'NoneType' object is not callable"
    solutions = searcher.search_for_solution(error, "pandas dataframe")
    for s in solutions:
        print(f"\nSource: {s['source']}")
        print(f"Confidence: {s['confidence']:.2f}")
        print(f"Suggestion: {s['suggestion'][:150]}...")
