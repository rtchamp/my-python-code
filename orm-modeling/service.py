from sqlalchemy.orm import Session
from sqlalchemy import and_, select
from typing import List, Tuple, Dict, Any, Optional
import igraph as ig
import math
from shapely.geometry import Point as ShapelyPoint, LineString as ShapelyLineString
from shapely import STRtree
from model import Point, Line, Base

class NetworkGraphBuilder:
    def __init__(self, session: Session):
        self.session = session
        self._point_cache: Dict[Tuple[float, float], Point] = {}
    
    def create_lines_from_coordinates(
        self, 
        coordinate_pairs: List[Tuple[Tuple[float, float], Tuple[float, float]]], 
        line_metadata: Optional[List[Dict[str, Any]]] = None
    ) -> List[Line]:
        created_lines = []
        
        unique_coords = set()
        for p0, p1 in coordinate_pairs:
            unique_coords.add(p0)
            unique_coords.add(p1)
        
        for coord in unique_coords:
            if coord not in self._point_cache:
                point = self._get_or_create_point(coord[0], coord[1])
                self._point_cache[coord] = point
        
        for i, (p0, p1) in enumerate(coordinate_pairs):
            point0 = self._point_cache[p0]
            point1 = self._point_cache[p1]
            
            line = Line()
            line.coords = (point0.coord, point1.coord)
            
            # Add metadata if provided
            if line_metadata and i < len(line_metadata):
                for key, value in line_metadata[i].items():
                    line.set_metadata(key, value)
            
            self.session.add(line)
            created_lines.append(line)
        
        self.session.commit()
        
        return created_lines
    
    def _get_or_create_point(self, x: float, y: float) -> Point:
        stmt = select(Point).where(Point.coord_matches((x, y)))
        existing_point = self.session.execute(stmt).scalar_one_or_none()
        
        if existing_point:
            return existing_point
        
        new_point = Point(x=x, y=y)
        self.session.add(new_point)
        self.session.flush()
        
        return new_point
    
    def _merge_point_metadata(self, target_point: Point, source_point: Point) -> None:
        if source_point.metavar is None:
            return
        
        if target_point.metavar is None:
            target_point.metavar = {}
        
        # Merge metadata from source to target
        for key, value in source_point.metavar.items():
            if key not in target_point.metavar:
                # Add new metadata if key doesn't exist
                target_point.set_metadata(key, value)
            else:
                # Handle conflicts - you can customize this logic
                existing_value = target_point.get_metadata(key)
                merged_value = self._merge_metadata_values(key, existing_value, value)
                target_point.set_metadata(key, merged_value)
        
        # Mark the target_point as modified for SQLAlchemy to track the change
        from sqlalchemy.orm import attributes
        attributes.flag_modified(target_point, 'metavar')
    
    def _merge_metadata_values(self, key: str, existing_value: Any, new_value: Any) -> Any:
        # Default merge strategy - you can customize this based on your needs
        
        # For lists, concatenate and remove duplicates
        if isinstance(existing_value, list) and isinstance(new_value, list):
            combined = existing_value + new_value
            return list(dict.fromkeys(combined))  # Remove duplicates while preserving order
        
        # For numbers, take the maximum (useful for capacity, priority, etc.)
        if isinstance(existing_value, (int, float)) and isinstance(new_value, (int, float)):
            if key in ['capacity', 'priority_level', 'area', 'beds']:
                return max(existing_value, new_value)
        
        # For booleans, use OR logic (if either is True, result is True)
        if isinstance(existing_value, bool) and isinstance(new_value, bool):
            if key in ['emergency', 'parking', 'traffic_light']:
                return existing_value or new_value
        
        # For strings, concatenate with separator if different
        if isinstance(existing_value, str) and isinstance(new_value, str):
            if existing_value != new_value:
                if key in ['name', 'type']:
                    return f"{existing_value} / {new_value}"
                
        # Default: keep existing value (first wins)
        return existing_value
    
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
                    # Merge metadata from point2 to point1
                    self._merge_point_metadata(point1, point2)
                    
                    point2.is_merged = True
                    point2.merged_into = point1
                    merged_points.append(point2)
                    
                    # Force SQLAlchemy to track the metadata changes
                    self.session.flush()
                    
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
                
                # Points that split lines are automatically handled by degree calculation
                
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
        graph.add_edges(edges)
        
        return graph

    def get_all_endpoint_paths(
        self, 
        endpoint_filter: Optional[Dict[str, Any]] = None,
        start_filter: Optional[Dict[str, Any]] = None,
        end_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        graph = self.create_igraph()
        
        # Get all points for filtering
        points_stmt = select(Point).where(Point.is_merged == False)
        points = self.session.execute(points_stmt).scalars().all()
        
        # Determine start and end points
        if start_filter is not None or end_filter is not None:
            # Use separate start and end filters
            start_indices = []
            end_indices = []
            
            for i in range(len(graph.vs)):
                coord = graph.vs[i]["coord"]
                point = next((p for p in points if p.coord == coord), None)
                if not point:
                    continue
                
                # Check for start points
                if start_filter is not None:
                    # Start condition: degree=1 AND (no is_end OR is_end=False)
                    if graph.degree(i) == 1:
                        is_end_value = point.get_metadata('is_end')
                        if is_end_value is None or is_end_value == False:
                            # If start_filter is empty dict, accept all that meet degree+is_end criteria
                            if not start_filter or self._matches_filter(point, start_filter):
                                start_indices.append(i)
                
                # Check for end points
                if end_filter is not None:
                    if self._matches_filter(point, end_filter):
                        end_indices.append(i)
            
            # Use the filtered start and end points
            start_points = start_indices
            end_points = end_indices
            
        else:
            # Fall back to original behavior: degree-1 endpoints
            endpoint_indices = [i for i in range(len(graph.vs)) if graph.degree(i) == 1]
            
            # Apply legacy endpoint filter if provided
            if endpoint_filter:
                filtered_endpoints = []
                
                for idx in endpoint_indices:
                    coord = graph.vs[idx]["coord"]
                    point = next((p for p in points if p.coord == coord), None)
                    if point and self._matches_filter(point, endpoint_filter):
                        filtered_endpoints.append(idx)
                
                endpoint_indices = filtered_endpoints
            
            # Use same points for both start and end
            start_points = endpoint_indices
            end_points = endpoint_indices
        
        all_paths = []
        
        # Find paths from start points to end points
        for start_idx in start_points:
            for end_idx in end_points:
                # Skip if start and end are the same point
                if start_idx == end_idx:
                    continue
                
                # If using separate start/end filters, prevent end-to-end connections
                if start_filter is not None or end_filter is not None:
                    # Check if start point is also an end point (should be excluded)
                    start_coord = graph.vs[start_idx]["coord"]
                    start_point = next((p for p in points if p.coord == start_coord), None)
                    if start_point and end_filter and self._matches_filter(start_point, end_filter):
                        continue  # Skip if start point is also an end point
                
                try:
                    # Find all simple paths between start and end
                    paths = graph.get_all_simple_paths(start_idx, end_idx)
                    
                    for path_indices in paths:
                        # Check if path passes through forbidden intermediate nodes
                        forbidden_filter = end_filter if (start_filter is not None or end_filter is not None) else endpoint_filter
                        if forbidden_filter and self._path_has_forbidden_intermediate(path_indices, graph, forbidden_filter):
                            continue
                            
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

    def get_paths_between_endpoints(
        self, 
        start_coord: tuple[float, float], 
        end_coord: tuple[float, float], 
        avoid_intermediate_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
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
                # Check if path passes through forbidden intermediate nodes
                if avoid_intermediate_filter and self._path_has_forbidden_intermediate(path_indices, graph, avoid_intermediate_filter):
                    continue
                    
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

    def _matches_filter(self, point: Point, filter_conditions: Dict[str, Any]) -> bool:
        """Check if a point matches the given filter conditions"""
        if not point.metavar:
            return False
        
        for key, expected_value in filter_conditions.items():
            actual_value = point.get_metadata(key)
            if actual_value != expected_value:
                return False
        
        return True
    
    def _path_has_forbidden_intermediate(self, path_indices: List[int], graph: ig.Graph, endpoint_filter: Dict[str, Any]) -> bool:
        """Check if path passes through intermediate nodes that match the endpoint filter"""
        if len(path_indices) <= 2:
            return False  # No intermediate nodes
        
        # Get all points for checking
        points_stmt = select(Point).where(Point.is_merged == False)
        points = self.session.execute(points_stmt).scalars().all()
        
        # Check intermediate nodes (excluding start and end)
        for idx in path_indices[1:-1]:
            coord = graph.vs[idx]["coord"]
            point = next((p for p in points if p.coord == coord), None)
            if point and self._matches_filter(point, endpoint_filter):
                return True  # Found forbidden intermediate node
        
        return False
    
    def get_paths_between_point_groups(
        self, 
        start_points: List[tuple[float, float]], 
        end_points: List[tuple[float, float]],
        avoid_intermediate_filter: Optional[Dict[str, Any]] = None
    ) -> List[Dict]:
        """
        Find all paths from any start point to any end point.
        
        Args:
            start_points: List of coordinate tuples for start points
            end_points: List of coordinate tuples for end points  
            avoid_intermediate_filter: Optional filter to avoid certain intermediate nodes
            
        Returns:
            List of path dictionaries with start, end, path, length, vertex_indices
        """
        graph = self.create_igraph()
        
        # Convert coordinates to graph indices
        start_indices = []
        end_indices = []
        
        for coord in start_points:
            for i, graph_coord in enumerate(graph.vs["coord"]):
                if graph_coord == coord:
                    start_indices.append(i)
                    break
        
        for coord in end_points:
            for i, graph_coord in enumerate(graph.vs["coord"]):
                if graph_coord == coord:
                    end_indices.append(i)
                    break
        
        all_paths = []
        
        # Find paths from each start point to each end point
        for start_idx in start_indices:
            for end_idx in end_indices:
                # Skip if start and end are the same point
                if start_idx == end_idx:
                    continue
                
                try:
                    # Find all simple paths between start and end
                    paths = graph.get_all_simple_paths(start_idx, end_idx)
                    
                    for path_indices in paths:
                        # Check if path passes through forbidden intermediate nodes
                        if avoid_intermediate_filter and self._path_has_forbidden_intermediate(path_indices, graph, avoid_intermediate_filter):
                            continue
                            
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
                    # No path exists between these points
                    continue
        
        return all_paths

    def clear_cache(self):
        self._point_cache.clear() 