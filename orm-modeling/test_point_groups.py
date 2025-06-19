#!/usr/bin/env python3

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from model import Base, Point, Line
from service import NetworkGraphBuilder
from typing import List, Dict, Any

def find_start_candidates(session, builder) -> List[tuple[float, float]]:
    """
    Find start point candidates: degree=1 AND (no is_end OR is_end=False)
    """
    points_stmt = select(Point).where(Point.is_merged == False)
    points = session.execute(points_stmt).scalars().all()
    
    graph = builder.create_igraph()
    start_candidates = []
    
    for i, point in enumerate(points):
        # Check degree=1 condition
        if graph.degree(i) == 1:
            # Check is_end condition
            is_end_value = point.get_metadata('is_end')
            if is_end_value is None or is_end_value == False:
                start_candidates.append(point.coord)
    
    return start_candidates

def find_end_candidates(session, end_conditions: Dict[str, Any]) -> List[tuple[float, float]]:
    """
    Find end point candidates based on metadata conditions
    """
    points_stmt = select(Point).where(Point.is_merged == False)
    points = session.execute(points_stmt).scalars().all()
    
    end_candidates = []
    
    for point in points:
        # Check if point matches all end conditions
        matches = True
        for key, expected_value in end_conditions.items():
            actual_value = point.get_metadata(key)
            if actual_value != expected_value:
                matches = False
                break
        
        if matches:
            end_candidates.append(point.coord)
    
    return end_candidates

def find_points_by_conditions(session, conditions: Dict[str, Any]) -> List[tuple[float, float]]:
    """
    Generic function to find points matching given conditions
    """
    points_stmt = select(Point).where(Point.is_merged == False)
    points = session.execute(points_stmt).scalars().all()
    
    candidates = []
    
    for point in points:
        # Check if point matches all conditions
        matches = True
        for key, expected_value in conditions.items():
            actual_value = point.get_metadata(key)
            if actual_value != expected_value:
                matches = False
                break
        
        if matches:
            candidates.append(point.coord)
    
    return candidates

def test_point_groups():
    print("Testing Point Group Path Finding")
    print("=" * 50)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Creating Network ===")
    
    # Create a more complex network
    # Terminal A (degree=1, no is_end) -> Junction B -> Station C (is_end=True)
    #                                      |            |
    # Terminal D (degree=1, no is_end) -> Junction E -> Station F (is_end=True)
    #                                      |
    #                                   Station G (is_end=True)
    
    builder = NetworkGraphBuilder(session)
    
    # Create points with different metadata
    points_data = [
        ((0.0, 0.0), {"type": "terminal", "name": "Terminal A"}),  # Start candidate
        ((1.0, 0.0), {"type": "junction", "is_end": False, "name": "Junction B"}),
        ((2.0, 0.0), {"type": "station", "is_end": True, "name": "Station C"}),  # End candidate
        ((0.0, -1.0), {"type": "terminal", "name": "Terminal D"}),  # Start candidate
        ((1.0, -1.0), {"type": "junction", "is_end": False, "name": "Junction E"}),
        ((2.0, -1.0), {"type": "station", "is_end": True, "name": "Station F"}),  # End candidate
        ((1.0, -2.0), {"type": "station", "is_end": True, "name": "Station G"}),  # End candidate
    ]
    
    # Create points
    for coord, metadata in points_data:
        point = Point(x=coord[0], y=coord[1])
        for key, value in metadata.items():
            point.set_metadata(key, value)
        session.add(point)
    
    session.commit()
    
    # Create lines
    coordinate_pairs = [
        ((0.0, 0.0), (1.0, 0.0)),   # Terminal A -> Junction B
        ((1.0, 0.0), (2.0, 0.0)),   # Junction B -> Station C
        ((0.0, -1.0), (1.0, -1.0)), # Terminal D -> Junction E
        ((1.0, -1.0), (2.0, -1.0)), # Junction E -> Station F
        ((1.0, 0.0), (1.0, -1.0)),  # Junction B -> Junction E
        ((2.0, 0.0), (2.0, -1.0)),  # Station C -> Station F
        ((1.0, -1.0), (1.0, -2.0)), # Junction E -> Station G
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print(f"Created network with {len(points_data)} points and {len(lines)} lines")
    
    # Show all points and their metadata
    print("\n=== Network Points ===")
    all_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    
    graph = builder.create_igraph()
    
    for i, point in enumerate(all_points):
        is_end = point.get_metadata('is_end')
        degree = graph.degree(i)
        print(f"  {point.coord}: {point.get_metadata('name')} (is_end: {is_end}, degree: {degree})")
    
    print("\n=== Finding Start and End Candidates ===")
    
    # Find start candidates using helper function
    start_candidates = find_start_candidates(session, builder)
    print(f"Start candidates (degree=1 & no is_end): {len(start_candidates)}")
    for coord in start_candidates:
        point = next((p for p in all_points if p.coord == coord), None)
        if point:
            print(f"  {coord}: {point.get_metadata('name')}")
    
    # Find end candidates using helper function
    end_conditions = {"is_end": True}
    end_candidates = find_end_candidates(session, end_conditions)
    print(f"\nEnd candidates (is_end=True): {len(end_candidates)}")
    for coord in end_candidates:
        point = next((p for p in all_points if p.coord == coord), None)
        if point:
            print(f"  {coord}: {point.get_metadata('name')}")
    
    print("\n=== Finding All Paths Between Groups ===")
    
    # Use the new service method
    all_paths = builder.get_paths_between_point_groups(start_candidates, end_candidates)
    
    print(f"Found {len(all_paths)} paths from start group to end group")
    
    for i, path_info in enumerate(all_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"\nPath {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        
        # Show point names along the path
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"  Route: {' → '.join(path_names)}")
        print(f"  Length: {path_info['length']} edges")
    
    print("\n=== Testing with Intermediate Avoidance ===")
    
    # Avoid passing through other end points
    avoid_filter = {"is_end": True}
    filtered_paths = builder.get_paths_between_point_groups(
        start_candidates, 
        end_candidates, 
        avoid_intermediate_filter=avoid_filter
    )
    
    print(f"Found {len(filtered_paths)} paths avoiding other end points")
    
    for i, path_info in enumerate(filtered_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"\nFiltered Path {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"  Route: {' → '.join(path_names)}")
        print(f"  Length: {path_info['length']} edges")
    
    print("\n=== Testing Custom Point Groups ===")
    
    # Example: Find paths from terminals to stations
    terminal_points = find_points_by_conditions(session, {"type": "terminal"})
    station_points = find_points_by_conditions(session, {"type": "station"})
    
    print(f"Terminal points: {len(terminal_points)}")
    print(f"Station points: {len(station_points)}")
    
    custom_paths = builder.get_paths_between_point_groups(terminal_points, station_points)
    print(f"Found {len(custom_paths)} paths from terminals to stations")
    
    session.close()
    print("\n" + "=" * 50)
    print("Point group path finding test completed!")

if __name__ == "__main__":
    test_point_groups() 