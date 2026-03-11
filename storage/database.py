"""
SEMDS Database - Storage Layer

SQLite数据库连接管理，对应规格文档第六章。

本模块提供：
- init_database: 初始化数据库
- get_session: 获取数据库会话
- get_engine: 获取数据库引擎
"""

import os
from pathlib import Path
from typing import Any, Generator, Optional

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from storage.models import Base, Generation, Task

# 数据库文件路径（相对于storage目录）
DEFAULT_DB_PATH = Path(__file__).parent / "semds.db"

# 全局引擎和会话工厂
_engine = None
_SessionFactory = None


def get_db_path() -> str:
    """
    获取数据库文件路径。

    优先从环境变量SEMDS_DB_PATH读取，否则使用默认路径。

    Returns:
        数据库文件的绝对路径
    """
    env_path = os.environ.get("SEMDS_DB_PATH")
    if env_path:
        return os.path.abspath(env_path)
    return str(DEFAULT_DB_PATH.absolute())


def get_engine(db_path: Optional[str] = None) -> Engine:
    """
    获取或创建数据库引擎。

    Args:
        db_path: 数据库文件路径（如果为None，使用get_db_path()）

    Returns:
        SQLAlchemy引擎实例
    """
    global _engine

    if _engine is None:
        path = db_path or get_db_path()

        # 确保目录存在（仅对文件路径，不适用于:memory:）
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

        # 创建引擎
        # SQLite连接字符串格式: sqlite:///path/to/database.db
        connection_string = f"sqlite:///{path}"

        _engine = create_engine(
            connection_string,
            echo=False,  # 设置为True可查看SQL语句
            connect_args={
                "check_same_thread": False,  # 允许多线程访问（SQLite限制）
            },
        )

        # 启用外键约束（SQLite默认关闭）
        @event.listens_for(_engine, "connect")
        def set_sqlite_pragma(dbapi_conn: Any, connection_record: Any) -> None:
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return _engine


def init_database(db_path: Optional[str] = None) -> Engine:
    """
    初始化数据库，创建所有表。

    Args:
        db_path: 数据库文件路径（如果为None，使用get_db_path()）

    Returns:
        初始化后的数据库引擎
    """
    engine = get_engine(db_path)

    # 创建所有表
    Base.metadata.create_all(engine)

    return engine


def get_session_factory(db_path: Optional[str] = None) -> sessionmaker:
    """
    获取或创建会话工厂。

    Args:
        db_path: 数据库文件路径（如果为None，使用get_db_path()）

    Returns:
        SQLAlchemy会话工厂
    """
    global _SessionFactory

    if _SessionFactory is None:
        engine = get_engine(db_path)
        _SessionFactory = sessionmaker(bind=engine)

    return _SessionFactory


def get_session(db_path: Optional[str] = None) -> Session:
    """
    获取一个新的数据库会话。

    Args:
        db_path: 数据库文件路径（如果为None，使用get_db_path()）

    Returns:
        新的数据库会话
    """
    factory = get_session_factory(db_path)
    session: Session = factory()
    return session


def get_db_session(
    db_path: Optional[str] = None,
) -> Generator[Session, None, None]:
    """
    获取数据库会话的生成器（用于依赖注入）。

    Args:
        db_path: 数据库文件路径

    Yields:
        数据库会话
    """
    session = get_session(db_path)
    try:
        yield session
    finally:
        session.close()


def reset_database(db_path: Optional[str] = None) -> None:
    """
    重置数据库，删除所有表并重新创建。

    警告：这将删除所有数据！

    Args:
        db_path: 数据库文件路径（如果为None，使用get_db_path()）
    """
    engine = get_engine(db_path)

    # 删除所有表
    Base.metadata.drop_all(engine)

    # 重新创建
    Base.metadata.create_all(engine)


def close_database() -> None:
    """
    关闭数据库连接，清理资源。

    在应用程序退出时调用。
    """
    global _engine, _SessionFactory

    if _engine:
        _engine.dispose()
        _engine = None

    _SessionFactory = None


if __name__ == "__main__":
    # 简单测试
    print(f"Database path: {get_db_path()}")

    # 初始化数据库
    engine = init_database()
    print("Database initialized successfully")

    # 获取会话
    session = get_session()

    # 测试：创建任务
    task = Task(
        name="demo_task",
        description="A demo task for testing",
        target_function_signature="def demo() -> str:",
        status="pending",
    )

    session.add(task)
    session.commit()

    print(f"Created task: {task.id}")
    print(f"Task dict: {task.to_dict()}")

    # 测试：创建代
    gen = Generation(
        task_id=task.id,
        gen_number=0,
        code="def demo(): return 'hello'",
        intrinsic_score=1.0,
        test_pass_rate=1.0,
        execution_time_ms=100.0,
    )

    session.add(gen)
    session.commit()

    print(f"Created generation: {gen.id}")

    # 查询
    tasks = session.query(Task).all()
    print(f"Total tasks: {len(tasks)}")

    for t in tasks:
        print(f"  - {t.name} ({t.status})")
        for g in t.generations:
            print(f"    - Gen {g.gen_number}: score={g.intrinsic_score}")

    session.close()
    print("Test completed successfully")
