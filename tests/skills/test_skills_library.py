"""
Skills Library 测试模块 - TDD Red Phase

测试 SkillsLibrary 类 - 技能库管理

职责：
1. 管理Prompt模板（加载、渲染）
2. 管理已验证的策略（注册、查询）
3. 按任务类型组织策略
"""

# =============================================================================
# Test Template Management
# =============================================================================


class TestTemplateManagement:
    """模板管理测试（P0优先级）"""

    def test_load_template_from_file(self, tmp_path):
        """测试从文件加载模板"""
        from skills.skills_library import SkillsLibrary

        # 创建模板目录和文件
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "test_prompt.j2").write_text("Hello {{ name }}!")

        library = SkillsLibrary(str(templates_dir))
        template = library.load_template("test_prompt.j2")

        assert template is not None

    def test_render_template_with_context(self, tmp_path):
        """测试使用上下文渲染模板"""
        from skills.skills_library import SkillsLibrary

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        (templates_dir / "greeting.j2").write_text("Hello {{ name }}!")

        library = SkillsLibrary(str(templates_dir))
        result = library.render_template("greeting.j2", {"name": "World"})

        assert result == "Hello World!"

    def test_render_template_with_multiple_variables(self, tmp_path):
        """测试渲染多变量模板"""
        from skills.skills_library import SkillsLibrary

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        template_content = "Task: {{ task }}, Gen: {{ generation }}, Score: {{ score }}"
        (templates_dir / "evolution.j2").write_text(template_content)

        library = SkillsLibrary(str(templates_dir))
        result = library.render_template(
            "evolution.j2",
            {"task": "calculator", "generation": 5, "score": 0.85},
        )

        assert "calculator" in result
        assert "5" in result
        assert "0.85" in result

    def test_raises_error_for_missing_template(self, tmp_path):
        """测试缺失模板抛出错误"""
        from skills.skills_library import SkillsLibrary

        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()

        library = SkillsLibrary(str(templates_dir))

        try:
            library.load_template("nonexistent.j2")
            assert False, "Should have raised an exception"
        except (FileNotFoundError, ValueError):
            pass  # Expected


# =============================================================================
# Test Strategy Registry
# =============================================================================


class TestStrategyRegistry:
    """策略注册表测试（P0优先级）"""

    def test_register_verified_strategy(self):
        """测试注册已验证策略"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        strategy = {
            "mutation_type": "conservative",
            "validation_mode": "comprehensive",
            "generation_temperature": 0.5,
        }

        library.register_verified_strategy(strategy, task_type="math")

        # 验证策略已注册
        strategies = library.get_strategies_for_task("math")
        assert len(strategies) == 1
        assert strategies[0]["mutation_type"] == "conservative"

    def test_get_strategies_returns_list(self):
        """测试获取策略返回列表"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        # 注册多个策略
        for i in range(3):
            library.register_verified_strategy(
                {"mutation_type": f"type_{i}", "score": 0.8 + i * 0.05},
                task_type="math",
            )

        strategies = library.get_strategies_for_task("math")

        assert isinstance(strategies, list)
        assert len(strategies) == 3

    def test_strategies_are_isolated_by_task_type(self):
        """测试策略按任务类型隔离"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        library.register_verified_strategy(
            {"mutation_type": "math_strategy"}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "string_strategy"}, task_type="string"
        )

        math_strategies = library.get_strategies_for_task("math")
        string_strategies = library.get_strategies_for_task("string")

        assert len(math_strategies) == 1
        assert len(string_strategies) == 1
        assert math_strategies[0]["mutation_type"] == "math_strategy"
        assert string_strategies[0]["mutation_type"] == "string_strategy"

    def test_get_strategies_returns_empty_list_for_unknown_task(self):
        """测试未知任务返回空列表"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        strategies = library.get_strategies_for_task("unknown_task")

        assert strategies == []


# =============================================================================
# Test Strategy Scoring and Ranking
# =============================================================================


class TestStrategyRanking:
    """策略排名测试（P1优先级）"""

    def test_get_best_strategy_returns_highest_score(self):
        """测试获取最佳策略返回最高得分"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        # 注册不同得分的策略
        library.register_verified_strategy(
            {"mutation_type": "low", "score": 0.6}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "high", "score": 0.9}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "medium", "score": 0.75}, task_type="math"
        )

        best = library.get_best_strategy("math")

        assert best is not None
        assert best["mutation_type"] == "high"

    def test_get_best_strategy_returns_none_for_empty(self):
        """测试空策略时返回None"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        best = library.get_best_strategy("unknown")

        assert best is None

    def test_strategies_sorted_by_score(self):
        """测试策略按得分排序"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        library.register_verified_strategy(
            {"mutation_type": "c", "score": 0.7}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "a", "score": 0.9}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "b", "score": 0.8}, task_type="math"
        )

        strategies = library.get_strategies_for_task("math", sorted_by_score=True)

        scores = [s["score"] for s in strategies]
        assert scores == sorted(scores, reverse=True)


# =============================================================================
# Test Strategy Statistics
# =============================================================================


class TestStrategyStatistics:
    """策略统计测试（P1优先级）"""

    def test_get_strategy_stats_returns_dict(self):
        """测试获取策略统计返回字典"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        library.register_verified_strategy(
            {"mutation_type": "type1", "score": 0.8}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "type2", "score": 0.9}, task_type="math"
        )

        stats = library.get_strategy_stats("math")

        assert isinstance(stats, dict)
        assert "count" in stats
        assert stats["count"] == 2

    def test_get_strategy_stats_includes_average_score(self):
        """测试统计包含平均得分"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        library.register_verified_strategy(
            {"mutation_type": "type1", "score": 0.8}, task_type="math"
        )
        library.register_verified_strategy(
            {"mutation_type": "type2", "score": 0.9}, task_type="math"
        )

        stats = library.get_strategy_stats("math")

        assert "average_score" in stats
        assert stats["average_score"] == 0.85


# =============================================================================
# Test Edge Cases
# =============================================================================


class TestSkillsLibraryEdgeCases:
    """边界情况测试"""

    def test_handles_empty_strategy_registration(self):
        """测试处理空策略注册"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        # 应该允许注册最小策略
        library.register_verified_strategy({}, task_type="test")

        strategies = library.get_strategies_for_task("test")
        assert len(strategies) == 1

    def test_handles_missing_score_in_strategy(self):
        """测试处理策略缺失得分"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        library.register_verified_strategy(
            {"mutation_type": "no_score"}, task_type="test"
        )

        # 应该能够获取策略（可能默认得分为0或None）
        strategies = library.get_strategies_for_task("test")
        assert len(strategies) == 1

    def test_default_templates_dir(self):
        """测试默认模板目录"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        # 应该使用默认路径
        assert library.templates_dir is not None

    def test_multiple_registrations_same_strategy(self):
        """测试同一策略多次注册"""
        from skills.skills_library import SkillsLibrary

        library = SkillsLibrary()

        strategy = {"mutation_type": "conservative", "score": 0.85}

        library.register_verified_strategy(strategy, task_type="math")
        library.register_verified_strategy(strategy, task_type="math")

        # 应该允许重复注册（或覆盖，取决于设计）
        strategies = library.get_strategies_for_task("math")
        assert len(strategies) >= 1
