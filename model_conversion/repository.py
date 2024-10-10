from sqlalchemy.orm import Session
from orm import User

class UserRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, name: str, email: str) -> User:
        existing_user = self.session.query(User).filter_by(email=email).first()
        if existing_user:
            raise ValueError(f"이미 존재하는 이메일입니다: {email}")
        
        new_user = User(name=name, email=email)
        self.session.add(new_user)
        self.session.commit()
        return new_user

    def get_by_id(self, user_id: int) -> User:
        return self.session.query(User).filter(User.id == user_id).first()

    def get_all(self) -> list[User]:
        return self.session.query(User).all()

    def update(self, user_id: int, name: str = None, email: str = None) -> User:
        user = self.get_by_id(user_id)
        if user:
            if name:
                user.name = name
            if email:
                user.email = email
            self.session.commit()
