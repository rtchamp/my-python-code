from sqlalchemy import select, create_engine, and_
from sqlalchemy.orm import Session
from orm import Base, Point

engine = create_engine("sqlite:///:memory:", echo=True, future=True)
Base.metadata.create_all(engine)

with Session(engine) as session:
    session.add_all([
        Point(x=1, y=2),
        Point(x=3, y=4),
        Point(x=5, y=6),
    ])
    session.commit()

with Session(engine) as session:
    stmt = select(Point).where(and_(Point.x == 3, Point.y == 4))
    result = session.scalars(stmt).all()
    for point in result:
        print(point.id, point.coord) 