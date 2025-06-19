#!/usr/bin/env python3

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from model import Base, Point, Line
from service import NetworkGraphBuilder

def test_improved_conditional_paths():
    print("Testing Improved Conditional Path Finding")
    print("=" * 60)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Creating Complex Network ===")
    
    # Create a network with multiple paths
    builder = NetworkGraphBuilder(session)
    
    # Create points with different metadata
    # Network layout:
    #     D(end)
    #     |
    # A(end)--B(junction)--C(end)
    #     |       |        |
    #     E(junction)--F(junction)--G(end)
    #     |                |
    #     H(end)           I(end)
    
    points_data = [
        ((0.0, 1.0), {"type": "station", "is_end": True, "name": "Station A"}),
        ((1.0, 1.0), {"type": "junction", "is_end": False, "name": "Junction B"}),
        ((2.0, 1.0), {"type": "station", "is_end": True, "name": "Station C"}),
        ((1.0, 2.0), {"type": "station", "is_end": True, "name": "Station D"}),
        ((0.0, 0.0), {"type": "junction", "is_end": False, "name": "Junction E"}),
        ((1.0, 0.0), {"type": "junction", "is_end": False, "name": "Junction F"}),
        ((2.0, 0.0), {"type": "station", "is_end": True, "name": "Station G"}),
        ((0.0, -1.0), {"type": "station", "is_end": True, "name": "Station H"}),
        ((1.0, -1.0), {"type": "station", "is_end": True, "name": "Station I"}),
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
        # Top row
        ((0.0, 1.0), (1.0, 1.0)),  # A -> B
        ((1.0, 1.0), (2.0, 1.0)),  # B -> C
        ((1.0, 1.0), (1.0, 2.0)),  # B -> D
        
        # Vertical connections
        ((0.0, 1.0), (0.0, 0.0)),  # A -> E
        ((1.0, 1.0), (1.0, 0.0)),  # B -> F
        ((2.0, 1.0), (2.0, 0.0)),  # C -> G
        
        # Bottom row
        ((0.0, 0.0), (1.0, 0.0)),  # E -> F
        ((1.0, 0.0), (2.0, 0.0)),  # F -> G
        
        # Bottom connections
        ((0.0, 0.0), (0.0, -1.0)), # E -> H
        ((1.0, 0.0), (1.0, -1.0)), # F -> I
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print(f"Created network with {len(points_data)} points and {len(lines)} lines")
    
    # Show all points and their metadata
    print("\n=== Network Points ===")
    all_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    stations = [p for p in all_points if p.get_metadata('is_end')]
    junctions = [p for p in all_points if not p.get_metadata('is_end')]
    
    print("Stations (is_end=True):")
    for point in stations:
        print(f"  {point.coord}: {point.get_metadata('name')}")
    
    print("Junctions (is_end=False):")
    for point in junctions:
        print(f"  {point.coord}: {point.get_metadata('name')}")
    
    print("\n=== All Degree-1 Endpoints (Traditional) ===")
    all_paths = builder.get_all_endpoint_paths()
    print(f"Found {len(all_paths)} paths between degree-1 endpoints")
    
    for i, path_info in enumerate(all_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"  Path {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        print(f"    Route: {' → '.join([str(coord) for coord in path_info['path']])}")
    
    print("\n=== Filtered Paths (Only is_end=True endpoints) ===")
    endpoint_filter = {"is_end": True}
    filtered_paths = builder.get_all_endpoint_paths(endpoint_filter)
    print(f"Found {len(filtered_paths)} paths between is_end=True endpoints")
    print("(These paths avoid passing through other is_end=True points)")
    
    for i, path_info in enumerate(filtered_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"  Path {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        
        # Show point names along the path
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Route: {' → '.join(path_names)}")
        print(f"    Coords: {' → '.join([str(coord) for coord in path_info['path']])}")
    
    print("\n=== Specific Path Examples ===")
    
    # Test path from Station A to Station G
    start_coord = (0.0, 1.0)  # Station A
    end_coord = (2.0, 0.0)    # Station G
    
    print(f"\nPaths from Station A to Station G:")
    
    # Without avoidance
    print("  Without avoidance:")
    paths_no_avoid = builder.get_paths_between_endpoints(start_coord, end_coord)
    for i, path_info in enumerate(paths_no_avoid, 1):
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Path {i}: {' → '.join(path_names)}")
    
    # With avoidance of other is_end=True points
    print("  Avoiding other is_end=True points:")
    avoid_filter = {"is_end": True}
    paths_with_avoid = builder.get_paths_between_endpoints(start_coord, end_coord, avoid_filter)
    for i, path_info in enumerate(paths_with_avoid, 1):
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Path {i}: {' → '.join(path_names)}")
    
    print(f"\n  Result: {len(paths_no_avoid)} paths without avoidance, {len(paths_with_avoid)} paths with avoidance")
    
    # Test another path
    print(f"\nPaths from Station A to Station I:")
    start_coord = (0.0, 1.0)  # Station A
    end_coord = (1.0, -1.0)   # Station I
    
    paths_no_avoid = builder.get_paths_between_endpoints(start_coord, end_coord)
    paths_with_avoid = builder.get_paths_between_endpoints(start_coord, end_coord, avoid_filter)
    
    print("  Without avoidance:")
    for i, path_info in enumerate(paths_no_avoid, 1):
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Path {i}: {' → '.join(path_names)}")
    
    print("  Avoiding other is_end=True points:")
    for i, path_info in enumerate(paths_with_avoid, 1):
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Path {i}: {' → '.join(path_names)}")
    
    print(f"\n  Result: {len(paths_no_avoid)} paths without avoidance, {len(paths_with_avoid)} paths with avoidance")
    
    session.close()
    print("\n" + "=" * 60)
    print("Improved conditional path finding test completed!")

if __name__ == "__main__":
    test_improved_conditional_paths() 