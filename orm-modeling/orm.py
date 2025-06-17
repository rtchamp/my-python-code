from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey
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

    @property
    def coord(self) -> tuple[float, float]:
        return (self.x, self.y)

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

    @property
    def coord(self) -> tuple[tuple[float, float], tuple[float, float]]:
        return ((self.x1, self.y1), (self.x2, self.y2))

    @property
    def to_shapely(self) -> ShapelyLineString:
        return ShapelyLineString([(self.x1, self.y1), (self.x2, self.y2)]) 