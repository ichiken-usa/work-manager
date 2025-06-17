"""
このモジュールは、SQLAlchemyを使用してデータベース接続を管理します。

Attributes:
    SQLALCHEMY_DATABASE_URL (str): データベース接続URL。
    engine (Engine): SQLAlchemyのデータベースエンジン。
    SessionLocal (sessionmaker): データベースセッションを作成するためのファクトリ。
    Base (DeclarativeMeta): ORMモデルの基底クラス。
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# SQLiteを使用（本番環境ではPostgreSQLなどに切り替え可能）
SQLALCHEMY_DATABASE_URL = "sqlite:///./attendance.db"

# データベースエンジンを作成
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# セッションローカルを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ベースクラスを作成
Base = declarative_base()

