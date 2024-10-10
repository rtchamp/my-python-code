from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 데이터베이스 URL을 여기에 지정하세요
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# PostgreSQL을 사용하는 경우:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
# SQLite를 사용하는 경우에만 connect_args가 필요합니다. 다른 데이터베이스에서는 이 인자를 제거하세요.

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 데이터베이스 세션을 얻는 함수
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
