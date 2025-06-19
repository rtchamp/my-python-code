#!/usr/bin/env python3

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from model import Base, Point, Line
from service import NetworkGraphBuilder

def test_conditional_paths():
    print("Testing Conditional Path Finding")
    print("=" * 50)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Creating Network with Special Endpoints ===")
    
    # Create a network with various points
    builder = NetworkGraphBuilder(session)
    
    # Create points with different metadata
    points_data = [
        ((0.0, 0.0), {"type": "station", "is_end": True, "name": "Station A"}),
        ((1.0, 0.0), {"type": "junction", "is_end": False, "name": "Junction 1"}),
        ((2.0, 0.0), {"type": "station", "is_end": True, "name": "Station B"}),
        ((3.0, 0.0), {"type": "junction", "is_end": False, "name": "Junction 2"}),
        ((4.0, 0.0), {"type": "station", "is_end": True, "name": "Station C"}),
        ((2.0, 1.0), {"type": "station", "is_end": True, "name": "Station D"}),
        ((2.0, -1.0), {"type": "junction", "is_end": False, "name": "Junction 3"}),
    ]
    
    # Create points
    for coord, metadata in points_data:
        point = Point(x=coord[0], y=coord[1])
        for key, value in metadata.items():
            point.set_metadata(key, value)
        session.add(point)
    
    session.commit()
    
    # Create lines connecting the points
    coordinate_pairs = [
        ((0.0, 0.0), (1.0, 0.0)),  # Station A -> Junction 1
        ((1.0, 0.0), (2.0, 0.0)),  # Junction 1 -> Station B
        ((2.0, 0.0), (3.0, 0.0)),  # Station B -> Junction 2
        ((3.0, 0.0), (4.0, 0.0)),  # Junction 2 -> Station C
        ((2.0, 0.0), (2.0, 1.0)),  # Station B -> Station D
        ((2.0, 0.0), (2.0, -1.0)), # Station B -> Junction 3
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print(f"Created network with {len(points_data)} points and {len(lines)} lines")
    
    # Show all points and their metadata
    print("\n=== Network Points ===")
    all_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    for point in all_points:
        print(f"  {point.coord}: {point.get_metadata('name')} (is_end: {point.get_metadata('is_end')})")
    
    print("\n=== All Possible Paths (No Filter) ===")
    all_paths = builder.get_all_endpoint_paths()
    print(f"Found {len(all_paths)} paths between all endpoints")
    
    for i, path_info in enumerate(all_paths, 1):
        print(f"  Path {i}: {path_info['start']} → {path_info['end']}")
        print(f"    Route: {' → '.join([str(coord) for coord in path_info['path']])}")
        print(f"    Length: {path_info['length']} edges")
    
    print("\n=== Filtered Paths (Only is_end=True endpoints) ===")
    endpoint_filter = {"is_end": True}
    filtered_paths = builder.get_all_endpoint_paths(endpoint_filter)
    print(f"Found {len(filtered_paths)} paths between is_end=True endpoints")
    
    for i, path_info in enumerate(filtered_paths, 1):
        print(f"  Path {i}: {path_info['start']} → {path_info['end']}")
        print(f"    Route: {' → '.join([str(coord) for coord in path_info['path']])}")
        print(f"    Length: {path_info['length']} edges")
        
        # Show point names along the path
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Names: {' → '.join(path_names)}")
    
    print("\n=== Testing Specific Path with Avoidance ===")
    # Test specific path between two stations, avoiding other is_end=True points
    start_coord = (0.0, 0.0)  # Station A
    end_coord = (4.0, 0.0)    # Station C
    
    print(f"\nPaths from Station A {start_coord} to Station C {end_coord}:")
    
    # Without avoidance
    print("\n  Without avoidance:")
    paths_no_avoid = builder.get_paths_between_endpoints(start_coord, end_coord)
    for i, path_info in enumerate(paths_no_avoid, 1):
        print(f"    Path {i}: {' → '.join([str(coord) for coord in path_info['path']])}")
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Names: {' → '.join(path_names)}")
    
    # With avoidance of other is_end=True points
    print("\n  Avoiding other is_end=True points:")
    avoid_filter = {"is_end": True}
    paths_with_avoid = builder.get_paths_between_endpoints(start_coord, end_coord, avoid_filter)
    for i, path_info in enumerate(paths_with_avoid, 1):
        print(f"    Path {i}: {' → '.join([str(coord) for coord in path_info['path']])}")
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Names: {' → '.join(path_names)}")
    
    print(f"\n  Result: {len(paths_no_avoid)} paths without avoidance, {len(paths_with_avoid)} paths with avoidance")
    
    session.close()
    print("\n" + "=" * 50)
    print("Conditional path finding test completed!")

if __name__ == "__main__":
    test_conditional_paths() 