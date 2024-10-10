from db import Base, engine, SessionLocal
from repository import UserRepository
from sqlalchemy.orm import sessionmaker

# 데이터베이스 테이블 생성
def init_db():
    Base.metadata.create_all(bind=engine)

# 예제 사용자 생성 및 데이터베이스에 삽입
Session = sessionmaker(bind=engine)

def create_sample_user():
    repo = UserRepository(Session())
    try:
        new_user = repo.create(name="홍길동", email="hong@example.com")
        print(f"새 사용자가 생성되었습니다: {new_user}")
    except ValueError as e:
        print(f"사용자 생성 실패: {e}")

# 모든 사용자 조회
def get_all_users():
    with SessionLocal() as session:
        repo = UserRepository(session)
        users = repo.get_all()
        for user in users:
            print(f"사용자: ID={user.id}, 이름={user.name}, 이메일={user.email}")

if __name__ == "__main__":
    print("데이터베이스 초기화 중...")
    init_db()
    print("데이터베이스 초기화 완료")

    print("\n예제 사용자 생성 중...")
    create_sample_user()

    print("\n모든 사용자 조회:")
    get_all_users()
