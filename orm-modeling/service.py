from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from typing import List, Tuple, Dict
import igraph as ig
import math
from shapely.geometry import Point as ShapelyPoint, LineString as ShapelyLineString
from shapely import STRtree
from model import Point, Line, Base

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
                point.is_endpoint = True
                self._point_cache[coord] = point
        
        for p0, p1 in coordinate_pairs:
            point0 = self._point_cache[p0]
            point1 = self._point_cache[p1]
            
            line = Line()
            line.coords = (point0.coord, point1.coord)
            self.session.add(line)
            created_lines.append(line)
        
        self.session.commit()
        
        return created_lines
    
    def _get_or_create_point(self, x: float, y: float, is_endpoint: bool = True) -> Point:
        stmt = select(Point).where(Point.coord_matches((x, y)))
        existing_point = self.session.execute(stmt).scalar_one_or_none()
        
        if existing_point:
            return existing_point
        
        new_point = Point(x=x, y=y, is_endpoint=is_endpoint)
        self.session.add(new_point)
        self.session.flush()
        
        return new_point
    
    def merge_nearby_points(self, margin: float) -> List[Point]:
        stmt = select(Point).where(Point.is_merged == False)
        points = self.session.execute(stmt).scalars().all()
        merged_points = []
        
        for i, point1 in enumerate(points):
            if point1.is_merged:
                continue
                
            for j, point2 in enumerate(points[i+1:], start=i+1):
                if point2.is_merged:
                    continue
                
                distance = point1.distance_to_point(point2.coord)
                
                if distance <= margin:
                    point2.is_merged = True
                    point2.merged_into = point1
                    merged_points.append(point2)
                    
                    lines_stmt = select(Line).where(Line.has_endpoint(point2.coord))
                    lines_to_update = self.session.execute(lines_stmt).scalars().all()
                    
                    for line in lines_to_update:
                        line.update_endpoint(point2.coord, point1.coord)
        
        self.session.commit()
        return merged_points
    
    def split_lines_on_points(self, tolerance: float) -> List[Line]:
        points_stmt = select(Point).where(Point.is_merged == False)
        points = self.session.execute(points_stmt).scalars().all()
        
        lines_stmt = select(Line).where(Line.is_split == False)
        lines = self.session.execute(lines_stmt).scalars().all()
        
        if not points or not lines:
            return []
        
        # Create STRtree with point geometries
        point_geoms = [point.to_shapely for point in points]
        point_tree = STRtree(point_geoms)
        
        new_lines = []
        
        for line in lines:
            line_geom = line.to_shapely
            line_endpoints = {line.start_coord, line.end_coord}
            
            # Use STRtree to find points within tolerance of the line
            nearby_indices = list(point_tree.query(line_geom.buffer(tolerance)))
            points_on_line = []
            
            for idx in nearby_indices:
                point = points[int(idx)]
                
                # Skip if point is already an endpoint of this line
                if point.coord in line_endpoints:
                    continue
                
                # Check if point is actually within tolerance using dwithin
                if line_geom.dwithin(point.to_shapely, tolerance):
                    points_on_line.append(point)
            
            if points_on_line:
                line.is_split = True
                
                # Mark points that split lines as non-endpoints
                for point in points_on_line:
                    point.is_endpoint = False
                
                # Create ordered list of all points along the line
                all_points = [line.start_coord]
                for p in points_on_line:
                    all_points.append(p.coord)
                all_points.append(line.end_coord)
                
                # Sort points by their position along the line
                all_points.sort(key=lambda p: line_geom.project(ShapelyPoint(p)))
                
                # Create new line segments between consecutive points
                for i in range(len(all_points) - 1):
                    new_line = Line()
                    new_line.coords = (all_points[i], all_points[i + 1])
                    self.session.add(new_line)
                    new_lines.append(new_line)
        
        self.session.commit()
        
        # Update all endpoint statuses after splitting
        Point.update_all_endpoint_status(self.session)
        self.session.commit()
        
        return new_lines
    
    def create_igraph(self) -> ig.Graph:
        points_stmt = select(Point).where(Point.is_merged == False)
        points = self.session.execute(points_stmt).scalars().all()
        
        lines_stmt = select(Line).where(Line.is_split == False)
        lines = self.session.execute(lines_stmt).scalars().all()
        
        point_to_index = {}
        vertex_names = []
        
        for i, point in enumerate(points):
            coord_str = str(point.coord)
            vertex_names.append(coord_str)
            point_to_index[point.coord] = i
        
        edges = []
        for line in lines:
            start_coord = line.start_coord
            end_coord = line.end_coord
            
            if start_coord in point_to_index and end_coord in point_to_index:
                start_idx = point_to_index[start_coord]
                end_idx = point_to_index[end_coord]
                edges.append((start_idx, end_idx))
        
        graph = ig.Graph()
        graph.add_vertices(len(points))
        graph.vs["name"] = vertex_names
        graph.vs["coord"] = [point.coord for point in points]
        graph.vs["is_endpoint"] = [point.is_endpoint for point in points]
        graph.add_edges(edges)
        
        return graph

    def get_all_endpoint_paths(self) -> List[Dict]:
        graph = self.create_igraph()
        
        # Find endpoints based on graph degree (nodes with only 1 connection)
        endpoint_indices = [i for i in range(len(graph.vs)) if graph.degree(i) == 1]
        
        all_paths = []
        
        # Find paths between all pairs of endpoints
        for i, start_idx in enumerate(endpoint_indices):
            for end_idx in endpoint_indices[i+1:]:  # Avoid duplicate pairs
                try:
                    # Find all simple paths between endpoints
                    paths = graph.get_all_simple_paths(start_idx, end_idx)
                    
                    for path_indices in paths:
                        path_coords = [graph.vs[idx]["coord"] for idx in path_indices]
                        path_info = {
                            "start": graph.vs[start_idx]["coord"],
                            "end": graph.vs[end_idx]["coord"], 
                            "path": path_coords,
                            "length": len(path_indices) - 1,  # Number of edges
                            "vertex_indices": path_indices
                        }
                        all_paths.append(path_info)
                        
                except Exception:
                    # No path exists between these endpoints
                    continue
        
        return all_paths

    def get_paths_between_endpoints(self, start_coord: tuple[float, float], end_coord: tuple[float, float]) -> List[Dict]:
        graph = self.create_igraph()
        
        # Find vertex indices for start and end coordinates
        start_idx = None
        end_idx = None
        
        for i, coord in enumerate(graph.vs["coord"]):
            if coord == start_coord:
                start_idx = i
            if coord == end_coord:
                end_idx = i
        
        if start_idx is None or end_idx is None:
            return []
        
        try:
            paths = graph.get_all_simple_paths(start_idx, end_idx)
            
            path_results = []
            for path_indices in paths:
                path_coords = [graph.vs[idx]["coord"] for idx in path_indices]
                path_info = {
                    "start": start_coord,
                    "end": end_coord,
                    "path": path_coords,
                    "length": len(path_indices) - 1,
                    "vertex_indices": path_indices
                }
                path_results.append(path_info)
            
            return path_results
            
        except Exception:
            return []

    def get_endpoint_pairs(self) -> List[tuple[tuple[float, float], tuple[float, float]]]:
        graph = self.create_igraph()
        
        # Find endpoints based on graph degree (nodes with only 1 connection)
        endpoint_indices = [i for i in range(len(graph.vs)) if graph.degree(i) == 1]
        endpoint_coords = [graph.vs[i]["coord"] for i in endpoint_indices]
        
        pairs = []
        for i, coord1 in enumerate(endpoint_coords):
            for coord2 in endpoint_coords[i+1:]:
                pairs.append((coord1, coord2))
        
        return pairs

    def clear_cache(self):
        self._point_cache.clear() 