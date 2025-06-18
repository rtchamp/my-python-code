import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete, create_engine
from sqlalchemy.orm import Session
from model import Base, Point, Line
from service import NetworkGraphBuilder

def create_test_network():
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    # Create a simple network: A---B---C---D with branch E---B
    points_data = [
        (0.0, 0.0),  # A (endpoint)
        (1.0, 0.0),  # B (junction)
        (2.0, 0.0),  # C (middle)
        (3.0, 0.0),  # D (endpoint)
        (1.0, 1.0),  # E (endpoint)
    ]
    
    lines_data = [
        ((0.0, 0.0), (1.0, 0.0)),  # A-B
        ((1.0, 0.0), (2.0, 0.0)),  # B-C
        ((2.0, 0.0), (3.0, 0.0)),  # C-D
        ((1.0, 0.0), (1.0, 1.0)),  # B-E
    ]
    
    # Add points
    for x, y in points_data:
        point = Point(x=x, y=y)
        session.add(point)
    
    # Add lines
    for (x1, y1), (x2, y2) in lines_data:
        line = Line(x1=x1, y1=y1, x2=x2, y2=y2)
        session.add(line)
    
    session.commit()
    
    # Update endpoint status
    builder = NetworkGraphBuilder(session)
    Point.update_all_endpoint_status(session)
    session.commit()
    
    return session, builder

def test_path_finding():
    print("Creating test network...")
    session, builder = create_test_network()
    
    print("\n=== Network Structure ===")
    # Show all points and their status
    points = session.execute(select(Point)).scalars().all()
    for point in points:
        status = "endpoint" if point.is_endpoint else "middle"
        print(f"Point {point.coord}: {status}")
    
    print("\n=== All Endpoint Pairs ===")
    endpoint_pairs = builder.get_endpoint_pairs()
    for i, (start, end) in enumerate(endpoint_pairs):
        print(f"{i+1}. {start} -> {end}")
    
    print("\n=== All Paths Between Endpoints ===")
    all_paths = builder.get_all_endpoint_paths()
    
    for i, path_info in enumerate(all_paths):
        print(f"\nPath {i+1}: {path_info['start']} -> {path_info['end']}")
        print(f"  Route: {' -> '.join([str(coord) for coord in path_info['path']])}")
        print(f"  Length: {path_info['length']} edges")
    
    print(f"\nTotal paths found: {len(all_paths)}")
    
    print("\n=== Specific Path Query ===")
    # Find paths between specific endpoints
    start_coord = (0.0, 0.0)  # Point A
    end_coord = (3.0, 0.0)    # Point D
    
    specific_paths = builder.get_paths_between_endpoints(start_coord, end_coord)
    print(f"Paths from {start_coord} to {end_coord}:")
    
    for i, path_info in enumerate(specific_paths):
        print(f"  Path {i+1}: {' -> '.join([str(coord) for coord in path_info['path']])}")
        print(f"    Length: {path_info['length']} edges")
    
    session.close()

def test_complex_network():
    print("\n" + "="*50)
    print("Testing Complex Network with Multiple Paths")
    print("="*50)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    # Create a more complex network with multiple paths
    # A---B---C
    # |   |   |
    # D---E---F
    
    points_data = [
        (0.0, 2.0),  # A
        (1.0, 2.0),  # B
        (2.0, 2.0),  # C
        (0.0, 1.0),  # D
        (1.0, 1.0),  # E
        (2.0, 1.0),  # F
    ]
    
    lines_data = [
        ((0.0, 2.0), (1.0, 2.0)),  # A-B
        ((1.0, 2.0), (2.0, 2.0)),  # B-C
        ((0.0, 1.0), (1.0, 1.0)),  # D-E
        ((1.0, 1.0), (2.0, 1.0)),  # E-F
        ((0.0, 2.0), (0.0, 1.0)),  # A-D
        ((1.0, 2.0), (1.0, 1.0)),  # B-E
        ((2.0, 2.0), (2.0, 1.0)),  # C-F
    ]
    
    # Add points
    for x, y in points_data:
        point = Point(x=x, y=y)
        session.add(point)
    
    # Add lines
    for (x1, y1), (x2, y2) in lines_data:
        line = Line(x1=x1, y1=y1, x2=x2, y2=y2)
        session.add(line)
    
    session.commit()
    
    # Update endpoint status
    builder = NetworkGraphBuilder(session)
    Point.update_all_endpoint_status(session)
    session.commit()
    
    print("\n=== Complex Network Structure ===")
    points = session.execute(select(Point)).scalars().all()
    for point in points:
        status = "endpoint" if point.is_endpoint else "junction"
        print(f"Point {point.coord}: {status}")
    
    print("\n=== All Paths in Complex Network ===")
    all_paths = builder.get_all_endpoint_paths()
    
    for i, path_info in enumerate(all_paths):
        print(f"\nPath {i+1}: {path_info['start']} -> {path_info['end']}")
        print(f"  Route: {' -> '.join([str(coord) for coord in path_info['path']])}")
        print(f"  Length: {path_info['length']} edges")
    
    print(f"\nTotal paths found: {len(all_paths)}")
    
    session.close()

if __name__ == "__main__":
    test_path_finding()
    test_complex_network() 