#!/usr/bin/env python3

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from model import Base, Point, Line
from service import NetworkGraphBuilder

def test_line_metadata():
    print("Testing Line Metadata Functionality")
    print("=" * 50)
    
    # Create in-memory database
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    print("\n=== Creating Lines with Metadata ===")
    
    # Create lines with metadata using the service
    builder = NetworkGraphBuilder(session)
    
    coordinate_pairs = [
        ((0.0, 0.0), (1.0, 0.0)),  # Highway segment
        ((1.0, 0.0), (2.0, 1.0)),  # Street segment
        ((2.0, 1.0), (3.0, 1.0))   # Residential road
    ]
    
    line_metadata = [
        {
            "road_type": "highway",
            "speed_limit": 80,
            "lanes": 4,
            "toll": True,
            "surface": "asphalt"
        },
        {
            "road_type": "street", 
            "speed_limit": 50,
            "lanes": 2,
            "toll": False,
            "traffic_lights": True
        },
        {
            "road_type": "residential",
            "speed_limit": 30,
            "lanes": 1,
            "toll": False,
            "parking": True
        }
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs, line_metadata)
    
    print(f"Created {len(lines)} lines with metadata")
    
    print("\n=== Line Metadata Details ===")
    for i, line in enumerate(lines):
        print(f"\nLine {i+1}: {line.start_coord} → {line.end_coord}")
        print(f"  Road Type: {line.get_metadata('road_type')}")
        print(f"  Speed Limit: {line.get_metadata('speed_limit')} km/h")
        print(f"  Lanes: {line.get_metadata('lanes')}")
        print(f"  Toll: {line.get_metadata('toll')}")
        
        # Show additional metadata if present
        if line.has_metadata('surface'):
            print(f"  Surface: {line.get_metadata('surface')}")
        if line.has_metadata('traffic_lights'):
            print(f"  Traffic Lights: {line.get_metadata('traffic_lights')}")
        if line.has_metadata('parking'):
            print(f"  Parking: {line.get_metadata('parking')}")
        
        print(f"  Full metadata: {line.metavar}")
    
    print("\n=== Testing Metadata Operations ===")
    
    # Test metadata operations on first line
    test_line = lines[0]
    print(f"\nTesting operations on Line 1:")
    
    # Add new metadata
    test_line.set_metadata('construction', False)
    test_line.set_metadata('last_maintained', '2024-01-15')
    print(f"Added construction and maintenance data")
    
    # Check metadata existence
    print(f"Has toll info: {test_line.has_metadata('toll')}")
    print(f"Has bike lane info: {test_line.has_metadata('bike_lane')}")
    
    # Get with default
    bike_lane = test_line.get_metadata('bike_lane', default=False)
    print(f"Bike lane (with default): {bike_lane}")
    
    # Remove metadata
    removed = test_line.remove_metadata('surface')
    print(f"Removed surface metadata: {removed}")
    
    print(f"Updated metadata: {test_line.metavar}")
    
    print("\n=== Querying Lines by Metadata ===")
    
    # Find all lines (we'll filter in Python since we don't have JSON query methods)
    all_lines = session.execute(select(Line)).scalars().all()
    
    # Filter by road type
    highways = [line for line in all_lines if line.get_metadata('road_type') == 'highway']
    print(f"Highway segments: {len(highways)}")
    
    # Filter by speed limit
    fast_roads = [line for line in all_lines if (line.get_metadata('speed_limit', 0) or 0) >= 50]
    print(f"Roads with speed limit ≥ 50 km/h: {len(fast_roads)}")
    
    # Filter by features
    toll_roads = [line for line in all_lines if line.get_metadata('toll', False)]
    print(f"Toll roads: {len(toll_roads)}")
    
    session.close()
    print("\n" + "=" * 50)
    print("Line metadata test completed!")

if __name__ == "__main__":
    test_line_metadata() 