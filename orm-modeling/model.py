from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, and_, func, select
from sqlalchemy.ext.hybrid import hybrid_property
from shapely.geometry import Point as ShapelyPoint, LineString as ShapelyLineString
from typing import List, Optional

class Base(DeclarativeBase):
    pass

class Point(Base):
    __tablename__ = "tbl_point"

    id: Mapped[int] = mapped_column(primary_key=True)
    x: Mapped[float]
    y: Mapped[float]
    is_merged: Mapped[bool] = mapped_column(default=False)
    merged_into_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tbl_point.id"), default=None)
    
    merged_into: Mapped[Optional["Point"]] = relationship("Point", remote_side=[id], back_populates="merged_points")
    merged_points: Mapped[List["Point"]] = relationship("Point", back_populates="merged_into")

    @hybrid_property
    def coord(self) -> tuple[float, float]:  # type: ignore
        return (self.x, self.y)
    
    @coord.setter  # type: ignore
    def coord(self, value: tuple[float, float]):  # type: ignore
        self.x, self.y = value

    @classmethod
    def coord_matches(cls, coord: tuple[float, float]):
        x_val, y_val = coord
        return and_(cls.x == x_val, cls.y == y_val)

    def distance_to_point(self, other_coord: tuple[float, float]) -> float:
        other_x, other_y = other_coord
        return ((self.x - other_x) ** 2 + (self.y - other_y) ** 2) ** 0.5



    @property
    def to_shapely(self) -> ShapelyPoint:
        return ShapelyPoint(self.x, self.y)

class Line(Base):
    __tablename__ = "tbl_line"

    id: Mapped[int] = mapped_column(primary_key=True)
    x1: Mapped[float]
    y1: Mapped[float]
    x2: Mapped[float]
    y2: Mapped[float]
    is_split: Mapped[bool] = mapped_column(default=False)

    @hybrid_property
    def coords(self) -> tuple[tuple[float, float], tuple[float, float]]:  # type: ignore
        return ((self.x1, self.y1), (self.x2, self.y2))
    
    @coords.setter
    def coords(self, value: tuple[tuple[float, float], tuple[float, float]]):  # type: ignore
        (x1, y1), (x2, y2) = value
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2

    @hybrid_property
    def start_coord(self) -> tuple[float, float]:  # type: ignore
        return (self.x1, self.y1)

    @hybrid_property
    def end_coord(self) -> tuple[float, float]:  # type: ignore
        return (self.x2, self.y2)

    @classmethod
    def has_endpoint(cls, coord: tuple[float, float]):
        x, y = coord
        return ((cls.x1 == x) & (cls.y1 == y)) | ((cls.x2 == x) & (cls.y2 == y))

    @classmethod
    def start_matches(cls, coord: tuple[float, float]):
        x, y = coord
        return and_(cls.x1 == x, cls.y1 == y)

    @classmethod
    def end_matches(cls, coord: tuple[float, float]):
        x, y = coord
        return and_(cls.x2 == x, cls.y2 == y)

    def update_endpoint(self, old_coord: tuple[float, float], new_coord: tuple[float, float]):
        old_x, old_y = old_coord
        new_x, new_y = new_coord
        if self.x1 == old_x and self.y1 == old_y:
            self.x1 = new_x
            self.y1 = new_y
        if self.x2 == old_x and self.y2 == old_y:
            self.x2 = new_x
            self.y2 = new_y

    @property
    def to_shapely(self) -> ShapelyLineString:
        return ShapelyLineString([(self.x1, self.y1), (self.x2, self.y2)]) 