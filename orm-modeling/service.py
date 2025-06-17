from sqlalchemy.orm import Session
from sqlalchemy import and_
from typing import List, Tuple, Dict
import igraph as ig
import math
from shapely.geometry import Point as ShapelyPoint, LineString as ShapelyLineString
from .orm import Point, Line, Base

class NetworkGraphBuilder:
    def __init__(self, session: Session):
        self.session = session
        self._point_cache: Dict[Tuple[float, float], Point] = {}
    
    def create_lines_from_coordinates(self, coordinate_pairs: List[Tuple[Tuple[float, float], Tuple[float, float]]]) -> List[Line]:
        created_lines = []
        
        unique_coords = set()
        for p0, p1 in coordinate_pairs:
            unique_coords.add(p0)
            unique_coords.add(p1)
        
        for coord in unique_coords:
            if coord not in self._point_cache:
                point = self._get_or_create_point(coord[0], coord[1])
                self._point_cache[coord] = point
        
        for p0, p1 in coordinate_pairs:
            point0 = self._point_cache[p0]
            point1 = self._point_cache[p1]
            
            line = Line(
                x1=point0.x,
                y1=point0.y,
                x2=point1.x,
                y2=point1.y
            )
            self.session.add(line)
            created_lines.append(line)
        
        self.session.commit()
        
        return created_lines
    
    def _get_or_create_point(self, x: float, y: float) -> Point:
        existing_point = self.session.query(Point).filter(
            Point.x == x, Point.y == y
        ).first()
        
        if existing_point:
            return existing_point
        
        new_point = Point(x=x, y=y)
        self.session.add(new_point)
        self.session.flush()
        
        return new_point
    
    def merge_nearby_points(self, margin: float) -> List[Point]:
        points = self.session.query(Point).filter(Point.is_merged == False).all()
        merged_points = []
        
        for i, point1 in enumerate(points):
            if point1.is_merged:
                continue
                
            for j, point2 in enumerate(points[i+1:], start=i+1):
                if point2.is_merged:
                    continue
                
                distance = math.sqrt((point1.x - point2.x)**2 + (point1.y - point2.y)**2)
                
                if distance <= margin:
                    point2.is_merged = True
                    point2.merged_into = point1
                    merged_points.append(point2)
                    
                    lines_to_update = self.session.query(Line).filter(
                        and_(
                            ((Line.x1 == point2.x) & (Line.y1 == point2.y)) |
                            ((Line.x2 == point2.x) & (Line.y2 == point2.y))
                        )
                    ).all()
                    
                    for line in lines_to_update:
                        if line.x1 == point2.x and line.y1 == point2.y:
                            line.x1 = point1.x
                            line.y1 = point1.y
                        if line.x2 == point2.x and line.y2 == point2.y:
                            line.x2 = point1.x
                            line.y2 = point1.y
        
        self.session.commit()
        return merged_points
    
    def split_lines_on_points(self, tolerance: float) -> List[Line]:
        points = self.session.query(Point).filter(Point.is_merged == False).all()
        lines = self.session.query(Line).filter(Line.is_split == False).all()
        
        new_lines = []
        
        for line in lines:
            line_geom = line.to_shapely
            line_endpoints = {(line.x1, line.y1), (line.x2, line.y2)}
            points_on_line = []
            
            for point in points:
                point_coord = (point.x, point.y)
                if point_coord in line_endpoints:
                    continue
                
                point_geom = point.to_shapely
                if line_geom.dwithin(point_geom, tolerance):
                    points_on_line.append(point)
            
            if points_on_line:
                line.is_split = True
                
                all_points = [(line.x1, line.y1)]
                for p in points_on_line:
                    all_points.append((p.x, p.y))
                all_points.append((line.x2, line.y2))
                
                line_start = ShapelyLineString([(line.x1, line.y1), (line.x2, line.y2)])
                all_points.sort(key=lambda p: line_start.project(ShapelyPoint(p)))
                
                for i in range(len(all_points) - 1):
                    x1, y1 = all_points[i]
                    x2, y2 = all_points[i + 1]
                    
                    new_line = Line(x1=x1, y1=y1, x2=x2, y2=y2)
                    self.session.add(new_line)
                    new_lines.append(new_line)
        
        self.session.commit()
        return new_lines
    
    def create_igraph(self) -> ig.Graph:
        points = self.session.query(Point).filter(Point.is_merged == False).all()
        lines = self.session.query(Line).filter(Line.is_split == False).all()
        
        point_to_index = {}
        vertex_names = []
        
        for i, point in enumerate(points):
            coord_str = str(point.coord)
            vertex_names.append(coord_str)
            point_to_index[point.coord] = i
        
        edges = []
        for line in lines:
            start_coord = (line.x1, line.y1)
            end_coord = (line.x2, line.y2)
            
            if start_coord in point_to_index and end_coord in point_to_index:
                start_idx = point_to_index[start_coord]
                end_idx = point_to_index[end_coord]
                edges.append((start_idx, end_idx))
        
        graph = ig.Graph()
        graph.add_vertices(len(points))
        graph.vs["name"] = vertex_names
        graph.add_edges(edges)
        
        return graph
    
    def clear_cache(self):
        self._point_cache.clear() 