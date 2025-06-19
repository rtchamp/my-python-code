#!/usr/bin/env python3

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from model import Base, Point, Line
from service import NetworkGraphBuilder

def test_start_end_filters():
    print("Testing Separate Start and End Point Filters")
    print("=" * 60)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Creating Network ===")
    
    # Create a simple network
    # 0 (degree=1, no is_end) -> 1 (junction) -> 2 (is_end=True)
    #                             |
    #                             3 (is_end=True)
    
    builder = NetworkGraphBuilder(session)
    
    # Create points with different metadata
    points_data = [
        ((0.0, 0.0), {"type": "terminal", "name": "Terminal 0"}),  # No is_end = start candidate
        ((1.0, 0.0), {"type": "junction", "is_end": False, "name": "Junction 1"}),  # Junction
        ((2.0, 0.0), {"type": "station", "is_end": True, "name": "Station 2"}),  # End point
        ((1.0, 1.0), {"type": "station", "is_end": True, "name": "Station 3"}),  # End point
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
        ((0.0, 0.0), (1.0, 0.0)),  # Terminal 0 -> Junction 1
        ((1.0, 0.0), (2.0, 0.0)),  # Junction 1 -> Station 2
        ((1.0, 0.0), (1.0, 1.0)),  # Junction 1 -> Station 3
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print(f"Created network with {len(points_data)} points and {len(lines)} lines")
    
    # Show all points and their metadata
    print("\n=== Network Points ===")
    all_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    
    # Create graph to check degrees
    graph = builder.create_igraph()
    
    for i, point in enumerate(all_points):
        is_end = point.get_metadata('is_end')
        degree = graph.degree(i)
        print(f"  Point {i}: {point.coord} - {point.get_metadata('name')}")
        print(f"    is_end: {is_end}, degree: {degree}")
        
        # Check if it qualifies as start point
        if degree == 1 and (is_end is None or is_end == False):
            print(f"    ✓ Qualifies as START point")
        
        # Check if it qualifies as end point
        if is_end == True:
            print(f"    ✓ Qualifies as END point")
    
    print("\n=== Traditional Endpoint Paths (degree=1) ===")
    traditional_paths = builder.get_all_endpoint_paths()
    print(f"Found {len(traditional_paths)} traditional paths")
    
    for i, path_info in enumerate(traditional_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"  Path {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Route: {' → '.join(path_names)}")
    
    print("\n=== Filtered Paths (Start: degree=1 & no is_end, End: is_end=True) ===")
    
    # Start filter: empty dict means accept all that meet degree=1 and is_end criteria
    start_filter = {}  # Accept all points that are degree=1 and (no is_end OR is_end=False)
    end_filter = {"is_end": True}  # Only points with is_end=True
    
    filtered_paths = builder.get_all_endpoint_paths(
        start_filter=start_filter,
        end_filter=end_filter
    )
    
    print(f"Found {len(filtered_paths)} filtered paths")
    print("(From degree=1 non-end points TO is_end=True points, avoiding other is_end=True points)")
    
    for i, path_info in enumerate(filtered_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"  Path {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Route: {' → '.join(path_names)}")
    
    print("\n=== Testing with Additional Start Filter ===")
    
    # More specific start filter
    start_filter_specific = {"type": "terminal"}
    
    specific_paths = builder.get_all_endpoint_paths(
        start_filter=start_filter_specific,
        end_filter=end_filter
    )
    
    print(f"Found {len(specific_paths)} paths with specific start filter")
    print("(From degree=1 terminals TO is_end=True points)")
    
    for i, path_info in enumerate(specific_paths, 1):
        start_point = next((p for p in all_points if p.coord == path_info['start']), None)
        end_point = next((p for p in all_points if p.coord == path_info['end']), None)
        print(f"  Path {i}: {start_point.get_metadata('name')} → {end_point.get_metadata('name')}")
        
        path_names = []
        for coord in path_info['path']:
            point = next((p for p in all_points if p.coord == coord), None)
            if point:
                path_names.append(point.get_metadata('name'))
        print(f"    Route: {' → '.join(path_names)}")
    
    session.close()
    print("\n" + "=" * 60)
    print("Start/End filter test completed!")

if __name__ == "__main__":
    test_start_end_filters() 