import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete, create_engine
from sqlalchemy.orm import Session
from model import Base, Point, Line
from service import NetworkGraphBuilder

def test_metadata_merge():
    print("Testing Metadata Merge During Point Merging")
    print("="*50)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    print("\n=== Creating Points with Different Metadata ===")
    
    # Create points that will be close enough to merge
    point1 = Point(x=0.0, y=0.0)
    point1.set_metadata("type", "intersection")
    point1.set_metadata("name", "Main & First")
    point1.set_metadata("traffic_light", True)
    point1.set_metadata("capacity", 100)
    point1.set_metadata("facilities", ["crosswalk", "signal"])
    
    point2 = Point(x=0.05, y=0.05)  # Close enough to merge (within 0.1 margin)
    point2.set_metadata("type", "stop_sign")
    point2.set_metadata("name", "First & Main")
    point2.set_metadata("emergency", True)
    point2.set_metadata("capacity", 150)
    point2.set_metadata("facilities", ["stop_sign", "crosswalk"])
    
    point3 = Point(x=1.0, y=0.0)  # Far enough to not merge
    point3.set_metadata("type", "building")
    point3.set_metadata("name", "Library")
    
    session.add_all([point1, point2, point3])
    session.commit()
    
    print(f"Point1 {point1.coord}:")
    print(f"  Metadata: {point1.metavar}")
    
    print(f"\nPoint2 {point2.coord}:")
    print(f"  Metadata: {point2.metavar}")
    
    print(f"\nPoint3 {point3.coord}:")
    print(f"  Metadata: {point3.metavar}")
    
    print("\n=== Before Merge ===")
    points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    print(f"Active points: {len(points)}")
    for point in points:
        print(f"  {point.coord}: {point.get_metadata('name', 'Unnamed')}")
    
    print("\n=== Performing Merge (margin=0.1) ===")
    builder = NetworkGraphBuilder(session)
    merged_points = builder.merge_nearby_points(margin=0.1)
    
    print(f"Merged {len(merged_points)} points")
    for point in merged_points:
        target = point.merged_into
        print(f"  {point.coord} merged into {target.coord}")
    
    print("\n=== After Merge ===")
    active_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    print(f"Active points: {len(active_points)}")
    
    for point in active_points:
        print(f"\nPoint {point.coord}:")
        print(f"  Name: {point.get_metadata('name')}")
        print(f"  Type: {point.get_metadata('type')}")
        print(f"  Traffic Light: {point.get_metadata('traffic_light')}")
        print(f"  Emergency: {point.get_metadata('emergency')}")
        print(f"  Capacity: {point.get_metadata('capacity')}")
        print(f"  Facilities: {point.get_metadata('facilities')}")
        print(f"  Full metadata: {point.metavar}")
    
    session.close()

def test_complex_metadata_merge():
    print("\n" + "="*50)
    print("Testing Complex Metadata Merge Scenarios")
    print("="*50)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    print("\n=== Creating Points with Various Metadata Types ===")
    
    # Point with extensive metadata
    point1 = Point(x=0.0, y=0.0)
    point1.set_metadata("name", "Central Hub")
    point1.set_metadata("capacity", 500)
    point1.set_metadata("priority_level", 8)
    point1.set_metadata("emergency", False)
    point1.set_metadata("services", ["bus", "taxi"])
    point1.set_metadata("hours", "24/7")
    
    # Point with overlapping and conflicting metadata
    point2 = Point(x=0.08, y=0.0)  # Close enough to merge
    point2.set_metadata("name", "Transit Station")
    point2.set_metadata("capacity", 300)
    point2.set_metadata("priority_level", 6)
    point2.set_metadata("emergency", True)
    point2.set_metadata("services", ["metro", "bus"])
    point2.set_metadata("wheelchair_accessible", True)
    
    # Point with minimal metadata
    point3 = Point(x=0.02, y=0.04)  # Also close enough to merge
    point3.set_metadata("name", "Bus Stop")
    point3.set_metadata("covered", True)
    
    session.add_all([point1, point2, point3])
    session.commit()
    
    print("Before merge:")
    for i, point in enumerate([point1, point2, point3], 1):
        print(f"  Point{i} {point.coord}: {point.metavar}")
    
    print("\n=== Performing Chain Merge ===")
    builder = NetworkGraphBuilder(session)
    merged_points = builder.merge_nearby_points(margin=0.1)
    
    print(f"Total merged: {len(merged_points)}")
    
    # Show final result
    active_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    print(f"\nFinal active points: {len(active_points)}")
    
    for point in active_points:
        print(f"\nFinal Point {point.coord}:")
        print(f"  Complete metadata: {point.metavar}")
        
        # Show specific merged values
        print(f"  Name: {point.get_metadata('name')}")
        print(f"  Capacity (max): {point.get_metadata('capacity')}")
        print(f"  Priority (max): {point.get_metadata('priority_level')}")
        print(f"  Emergency (any true): {point.get_metadata('emergency')}")
        print(f"  Services (combined): {point.get_metadata('services')}")
        print(f"  Wheelchair accessible: {point.get_metadata('wheelchair_accessible')}")
        print(f"  Covered: {point.get_metadata('covered')}")
        print(f"  Hours: {point.get_metadata('hours')}")
    
    session.close()

def test_metadata_preservation_in_lines():
    print("\n" + "="*50)
    print("Testing Metadata Preservation When Lines Are Updated")
    print("="*50)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    print("\n=== Creating Lines with Metadata ===")
    
    # Create points that will be merged
    point1 = Point(x=0.0, y=0.0)
    point1.set_metadata("name", "Station A")
    
    point2 = Point(x=0.05, y=0.0)  # Will merge with point1
    point2.set_metadata("name", "Platform A")
    
    point3 = Point(x=1.0, y=0.0)
    point3.set_metadata("name", "Station B")
    
    session.add_all([point1, point2, point3])
    session.commit()
    
    # Create lines connecting these points
    builder = NetworkGraphBuilder(session)
    
    coordinate_pairs = [
        ((0.0, 0.0), (1.0, 0.0)),        # point1 to point3
        ((0.05, 0.0), (1.0, 0.0)),       # point2 to point3 (will be updated after merge)
    ]
    
    line_metadata = [
        {"name": "Main Line", "type": "rail", "speed": 80},
        {"name": "Branch Line", "type": "rail", "speed": 60},
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print("Before merge:")
    for i, line in enumerate(lines, 1):
        print(f"  Line{i}: {line.start_coord} → {line.end_coord}")
    
    print("\n=== Merging Points ===")
    merged_points = builder.merge_nearby_points(margin=0.1)
    
    print(f"Merged {len(merged_points)} points")
    
    # Check line updates
    print("\nAfter merge:")
    updated_lines = session.execute(select(Line)).scalars().all()
    for i, line in enumerate(updated_lines, 1):
        print(f"  Line{i}: {line.start_coord} → {line.end_coord}")
    
    # Check merged point metadata
    active_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    print(f"\nActive points after merge:")
    for point in active_points:
        print(f"  {point.coord}: {point.get_metadata('name')} (metadata: {point.metavar})")
    
    session.close()

if __name__ == "__main__":
    test_metadata_merge()
    test_complex_metadata_merge()
    test_metadata_preservation_in_lines() 