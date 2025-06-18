import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete, create_engine
from sqlalchemy.orm import Session
from model import Base, Point, Line
from service import NetworkGraphBuilder

def test_degree_based_endpoints():
    print("Testing Degree-Based Endpoint Detection (Clean)")
    print("="*50)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    # Create a test network: A---B---C---D with branch E---B
    #                       A(degree=1) B(degree=3) C(degree=2) D(degree=1) E(degree=1)
    points_data = [
        (0.0, 0.0),  # A
        (1.0, 0.0),  # B  
        (2.0, 0.0),  # C
        (3.0, 0.0),  # D
        (1.0, 1.0),  # E
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
    
    # Create graph and analyze degrees
    builder = NetworkGraphBuilder(session)
    graph = builder.create_igraph()
    
    print("\n=== Point Analysis (Degree-Based Only) ===")
    points = session.execute(select(Point)).scalars().all()
    
    for i, point in enumerate(points):
        degree = graph.degree(i)
        is_endpoint_degree = degree == 1
        
        node_type = "endpoint" if is_endpoint_degree else f"junction/middle (degree={degree})"
        
        print(f"Point {point.coord}:")
        print(f"  Degree: {degree}")
        print(f"  Type: {node_type}")
        print()
    
    print("=== Degree-Based Endpoint Pairs ===")
    endpoint_pairs = builder.get_endpoint_pairs()
    for i, (start, end) in enumerate(endpoint_pairs):
        print(f"{i+1}. {start} -> {end}")
    
    print(f"\nTotal endpoint pairs: {len(endpoint_pairs)}")
    
    print("\n=== Degree-Based Paths ===")
    all_paths = builder.get_all_endpoint_paths()
    
    for i, path_info in enumerate(all_paths):
        print(f"\nPath {i+1}: {path_info['start']} -> {path_info['end']}")
        print(f"  Route: {' -> '.join([str(coord) for coord in path_info['path']])}")
        print(f"  Length: {path_info['length']} edges")
    
    print(f"\nTotal paths found: {len(all_paths)}")
    
    session.close()

def test_complex_degree_network():
    print("\n" + "="*60)
    print("Testing Complex Network (No True Endpoints)")
    print("="*60)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    # Create a complex network:
    # A---B---C
    # |   |   |
    # D---E---F
    # Expected degrees: A(2), B(4), C(2), D(2), E(4), F(2)
    # All nodes have degree > 1, so no true endpoints!
    
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
    
    # Create graph and analyze degrees
    builder = NetworkGraphBuilder(session)
    graph = builder.create_igraph()
    
    print("\n=== Complex Network Point Analysis ===")
    points = session.execute(select(Point)).scalars().all()
    
    for i, point in enumerate(points):
        degree = graph.degree(i)
        is_endpoint_degree = degree == 1
        
        node_type = "endpoint" if is_endpoint_degree else f"junction/middle (degree={degree})"
        
        print(f"Point {point.coord}:")
        print(f"  Degree: {degree}")
        print(f"  Type: {node_type}")
        print()
    
    print("=== Degree-Based Endpoint Detection Results ===")
    endpoint_pairs = builder.get_endpoint_pairs()
    print(f"Endpoint pairs found: {len(endpoint_pairs)}")
    
    if endpoint_pairs:
        for i, (start, end) in enumerate(endpoint_pairs):
            print(f"{i+1}. {start} -> {end}")
    else:
        print("No endpoints found (all nodes have degree > 1)")
    
    all_paths = builder.get_all_endpoint_paths()
    print(f"Paths found: {len(all_paths)}")
    
    session.close()

if __name__ == "__main__":
    test_degree_based_endpoints()
    test_complex_degree_network() 