from orm import Base, Point, Line
from service import NetworkGraphBuilder
from db import DatabaseManager

db_manager = DatabaseManager("sqlite:///:memory:", echo=True)
db_manager.initialize()

coordinate_pairs = [
    ((0.0, 0.0), (10.0, 0.0)),
    ((5.0, -2.0), (5.0, 2.0)),
    ((2.0, -1.0), (8.0, 1.0)),
]

with db_manager.get_session() as session:
    builder = NetworkGraphBuilder(session)
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print(f"Created {len(lines)} lines")
    
    points = session.query(Point).all()
    print(f"Created {len(points)} total points")
    
    for i, point in enumerate(points, 1):
        print(f"Point {i}: {point.coord}")
    
    for i, line in enumerate(lines, 1):
        print(f"Line {i}: {line.coord}")
    
    print("\nSplitting lines on nearby points with tolerance 0.5...")
    new_lines = builder.split_lines_on_points(0.5)
    print(f"Created {len(new_lines)} new line segments")
    
    all_lines = session.query(Line).all()
    active_lines = session.query(Line).filter(Line.is_split == False).all()
    split_lines = session.query(Line).filter(Line.is_split == True).all()
    
    print(f"\nTotal lines in database: {len(all_lines)}")
    print(f"Active lines: {len(active_lines)}")
    print(f"Split lines: {len(split_lines)}")
    
    print("\nActive lines:")
    for i, line in enumerate(active_lines, 1):
        print(f"  Line {i}: {line.coord}")
    
    print("\nSplit lines (excluded from graph):")
    for i, line in enumerate(split_lines, 1):
        print(f"  Split line {i}: {line.coord}")
    
    graph = builder.create_igraph()
    print(f"\nCreated igraph with {graph.vcount()} vertices and {graph.ecount()} edges")
    print(f"Vertex names: {graph.vs['name']}")
    print(f"Edges: {graph.get_edgelist()}")

print(f"\nDatabase info: {db_manager.get_info()}")
db_manager.close() 