"""
Git Manager 测试模块 - TDD Red Phase

测试 GitManager 类 - Git版本控制管理

职责：
1. 提交每一代进化代码
2. 管理分支和标签
3. 回滚到指定代
4. 获取历史记录
"""

import subprocess
from pathlib import Path

import pytest

# =============================================================================
# Test GitManager - Initialization
# =============================================================================


class TestGitManagerInitialization:
    """GitManager 初始化测试"""

    def test_initializes_with_repo_path(self, tmp_path):
        """测试使用仓库路径初始化"""
        from core.git_manager import GitManager

        # 创建临时git仓库
        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)

        manager = GitManager(str(repo_path))
        assert manager.repo_path == repo_path

    def test_initializes_with_default_path(self):
        """测试使用默认路径初始化"""
        from core.git_manager import GitManager

        manager = GitManager()
        assert manager.repo_path == Path(".")

    def test_raises_error_for_non_git_repo(self, tmp_path):
        """测试非git仓库目录抛出错误"""
        from core.git_manager import GitManager

        non_git_path = tmp_path / "not_a_repo"
        non_git_path.mkdir()

        with pytest.raises((RuntimeError, ValueError)):
            GitManager(str(non_git_path))


# =============================================================================
# Test GitManager - Commit Generation
# =============================================================================


class TestGitManagerCommitGeneration:
    """提交代代码测试（P0优先级）"""

    def test_commit_generation_creates_commit(self, tmp_path):
        """测试提交一代创建commit"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始文件
        (repo_path / "solution.py").write_text("# Initial")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))
        commit_hash = manager.commit_generation(
            task_id="test_task",
            gen_number=1,
            file_path="solution.py",
            score=0.85,
        )

        # 验证返回了有效的commit hash
        assert len(commit_hash) == 40
        assert all(c in "0123456789abcdef" for c in commit_hash)

    def test_commit_generation_updates_file_content(self, tmp_path):
        """测试提交更新文件内容"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "solution.py").write_text("# Initial")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        # 更新文件内容
        new_content = "def solution(): return 42"
        (repo_path / "solution.py").write_text(new_content)

        manager.commit_generation(
            task_id="test_task",
            gen_number=1,
            file_path="solution.py",
            score=0.85,
        )

        # 验证提交包含新内容
        result = subprocess.run(
            ["git", "show", "HEAD:solution.py"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        assert result.stdout.strip() == new_content

    def test_commit_message_includes_generation_info(self, tmp_path):
        """测试提交消息包含代信息"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 初始提交
        (repo_path / "solution.py").write_text("# Initial")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))
        manager.commit_generation(
            task_id="test_task",
            gen_number=5,
            file_path="solution.py",
            score=0.92,
        )

        # 验证提交消息
        result = subprocess.run(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=repo_path,
            capture_output=True,
            text=True,
        )
        commit_msg = result.stdout
        assert "gen-5" in commit_msg or "generation" in commit_msg.lower()
        assert "test_task" in commit_msg


# =============================================================================
# Test GitManager - Rollback
# =============================================================================


class TestGitManagerRollback:
    """回滚测试（P0优先级）"""

    def test_rollback_restores_file_content(self, tmp_path):
        """测试回滚恢复文件内容"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "solution.py").write_text("# Gen 0")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        # 创建第1代
        (repo_path / "solution.py").write_text("# Gen 1")
        hash1 = manager.commit_generation(
            task_id="test", gen_number=1, file_path="solution.py", score=0.5
        )

        # 创建第2代
        (repo_path / "solution.py").write_text("# Gen 2")
        manager.commit_generation(
            task_id="test", gen_number=2, file_path="solution.py", score=0.6
        )

        # 回滚到第1代
        manager.rollback_to_generation("solution.py", hash1)

        # 验证文件内容
        content = (repo_path / "solution.py").read_text()
        assert "# Gen 1" in content

    def test_rollback_raises_for_invalid_hash(self, tmp_path):
        """测试回滚无效hash抛出错误"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "test.txt").write_text("test")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        with pytest.raises((RuntimeError, ValueError)):
            manager.rollback_to_generation("test.txt", "invalid_hash_12345")


# =============================================================================
# Test GitManager - History
# =============================================================================


class TestGitManagerHistory:
    """历史记录测试（P1优先级）"""

    def test_get_generation_history_returns_list(self, tmp_path):
        """测试获取历史返回列表"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "solution.py").write_text("# Gen 0")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        # 创建几代
        for i in range(1, 4):
            (repo_path / "solution.py").write_text(f"# Gen {i}")
            manager.commit_generation(
                task_id="test",
                gen_number=i,
                file_path="solution.py",
                score=0.5 + i * 0.1,
            )

        history = manager.get_generation_history("solution.py")

        assert isinstance(history, list)
        assert len(history) >= 3

    def test_history_entry_has_required_fields(self, tmp_path):
        """测试历史条目包含必需字段"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "solution.py").write_text("# Gen 0")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        (repo_path / "solution.py").write_text("# Gen 1")
        manager.commit_generation(
            task_id="test_task", gen_number=1, file_path="solution.py", score=0.85
        )

        history = manager.get_generation_history("solution.py")

        if history:
            entry = history[0]
            assert "hash" in entry
            assert "generation" in entry or "gen" in entry
            assert "score" in entry
            assert "timestamp" in entry


# =============================================================================
# Test GitManager - Edge Cases
# =============================================================================


class TestGitManagerEdgeCases:
    """边界情况测试"""

    def test_handles_file_not_exist(self, tmp_path):
        """测试处理文件不存在"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "test.txt").write_text("test")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        # 尝试提交不存在的文件
        with pytest.raises((RuntimeError, FileNotFoundError)):
            manager.commit_generation(
                task_id="test",
                gen_number=1,
                file_path="nonexistent.py",
                score=0.5,
            )

    def test_commit_generation_without_changes(self, tmp_path):
        """测试无变更时提交"""
        from core.git_manager import GitManager

        repo_path = tmp_path / "repo"
        repo_path.mkdir()
        subprocess.run(["git", "init"], cwd=repo_path, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "test@test.com"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        # 创建初始提交
        (repo_path / "solution.py").write_text("# Content")
        subprocess.run(
            ["git", "add", "."], cwd=repo_path, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Initial"],
            cwd=repo_path,
            check=True,
            capture_output=True,
        )

        manager = GitManager(str(repo_path))

        # 无变更提交应该返回当前hash或抛出异常
        result = manager.commit_generation(
            task_id="test", gen_number=1, file_path="solution.py", score=0.5
        )

        # 应该返回有效的hash（可能是当前HEAD）
        assert isinstance(result, str)
