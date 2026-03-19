"""
Git Manager 模块 - Git版本控制管理

管理代码进化过程中的版本控制：
1. 提交每一代进化代码
2. 管理进化历史
3. 支持回滚到指定代
4. 查询提交历史
"""

import subprocess
from pathlib import Path
from typing import Any, Dict, List


class GitManager:
    """Git版本控制管理器

    管理SEMDS进化过程中的代码版本。

    Example:
        >>> manager = GitManager("/path/to/repo")
        >>> hash = manager.commit_generation(
        ...     task_id="calculator",
        ...     gen_number=5,
        ...     file_path="solution.py",
        ...     score=0.92
        ... )
        >>> manager.rollback_to_generation("solution.py", hash)
    """

    def __init__(self, repo_path: str = "."):
        """初始化Git管理器

        Args:
            repo_path: Git仓库路径，默认为当前目录

        Raises:
            RuntimeError: 如果路径不是有效的Git仓库
        """
        self.repo_path = Path(repo_path)

        # 验证是Git仓库
        if not (self.repo_path / ".git").exists():
            raise RuntimeError(f"Not a git repository: {self.repo_path}")

    def _run_git(
        self, args: List[str], check: bool = True
    ) -> subprocess.CompletedProcess[str]:
        """运行Git命令

        Args:
            args: Git命令参数
            check: 是否检查返回码

        Returns:
            CompletedProcess对象
        """
        cmd = ["git"] + args
        return subprocess.run(
            cmd,
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            check=check,
        )

    def commit_generation(
        self,
        task_id: str,
        gen_number: int,
        file_path: str,
        score: float,
    ) -> str:
        """提交一代进化代码

        Args:
            task_id: 任务ID
            gen_number: 代数
            file_path: 文件路径
            score: 当前得分

        Returns:
            提交哈希值（40字符）

        Raises:
            FileNotFoundError: 如果文件不存在
            RuntimeError: 如果提交失败
        """
        file_full_path = self.repo_path / file_path

        # 检查文件是否存在
        if not file_full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # 添加文件到暂存区
        self._run_git(["add", file_path])

        # 构建提交消息
        commit_msg = (
            f"[{task_id}] Gen-{gen_number}: score={score:.4f}\n\n"
            f"Task: {task_id}\n"
            f"Generation: {gen_number}\n"
            f"Score: {score:.4f}"
        )

        # 提交（即使无变更也创建空提交以记录进化历史）
        try:
            self._run_git(["commit", "--allow-empty", "-m", commit_msg])
        except subprocess.CalledProcessError as e:
            output = (e.stdout or "") + (e.stderr or "")
            raise RuntimeError(f"Git commit failed: {output}")

        # 获取提交哈希
        result = self._run_git(["rev-parse", "HEAD"])
        return result.stdout.strip()

    def rollback_to_generation(self, file_path: str, commit_hash: str) -> None:
        """回滚到指定代

        Args:
            file_path: 文件路径
            commit_hash: 提交哈希值

        Raises:
            RuntimeError: 如果回滚失败或hash无效
        """
        # 验证hash是否有效
        try:
            self._run_git(["cat-file", "-t", commit_hash])
        except subprocess.CalledProcessError:
            raise RuntimeError(f"Invalid commit hash: {commit_hash}")

        # 恢复文件到指定版本
        try:
            self._run_git(["checkout", commit_hash, "--", file_path])
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Rollback failed: {e.stderr}")

    def get_generation_history(self, file_path: str) -> List[Dict[str, Any]]:
        """获取文件的历史记录

        Args:
            file_path: 文件路径

        Returns:
            历史记录列表，每项包含hash、generation、score、timestamp
        """
        # 使用git log获取历史
        format_str = "%H|%s|%ai"
        try:
            result = self._run_git(
                [
                    "log",
                    f"--format={format_str}",
                    "--follow",
                    "--",
                    file_path,
                ],
                check=False,
            )
        except subprocess.CalledProcessError:
            return []

        if result.returncode != 0:
            return []

        history = []
        for line in result.stdout.strip().split("\n"):
            if not line:
                continue

            parts = line.split("|", 2)
            if len(parts) < 3:
                continue

            commit_hash, subject, timestamp_str = parts

            # 解析代数和得分
            gen_number = None
            score = None

            # 从主题行解析 [task] Gen-N: score=X.XXXX
            if "Gen-" in subject:
                try:
                    gen_part = subject.split("Gen-")[1].split(":")[0]
                    gen_number = int(gen_part)
                except (IndexError, ValueError):
                    pass

            if "score=" in subject:
                try:
                    score_part = subject.split("score=")[1].split()[0]
                    score = float(score_part)
                except (IndexError, ValueError):
                    pass

            history.append(
                {
                    "hash": commit_hash,
                    "generation": gen_number,
                    "score": score,
                    "timestamp": timestamp_str,
                    "message": subject,
                }
            )

        return history

    def get_current_hash(self) -> str:
        """获取当前HEAD的哈希值

        Returns:
            当前提交的哈希值
        """
        result = self._run_git(["rev-parse", "HEAD"])
        return result.stdout.strip()
