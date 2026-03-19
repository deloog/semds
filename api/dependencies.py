"""FastAPI依赖注入配置

提供API层所需的依赖注入函数，包括数据库会话管理等。
"""

from typing import Generator

from sqlalchemy.orm import Session

__all__ = ["get_db_session"]


def get_db_session() -> Generator[Session, None, None]:
    """
    获取数据库会话依赖

    用于FastAPI的Depends注入，提供请求级别的数据库会话。
    会话在请求结束时自动关闭。

    Yields:
        Session: SQLAlchemy Session对象

    Example:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db_session)):
            return db.query(Item).all()
    """
    from storage.database import get_session_factory

    SessionFactory = get_session_factory()
    db = SessionFactory()
    try:
        yield db
    finally:
        db.close()
