from sqlalchemy import select, create_engine, and_
from sqlalchemy.orm import Session
from model import Base, Point, Line
from shapely.geometry import Point as ShapelyPoint

engine = create_engine("sqlite:///:memory:", echo=True, future=True)
Base.metadata.create_all(engine)

with Session(engine) as session:
    session.add_all([
        Point(x=1, y=2),
        Point(x=3, y=4),
        Point(x=5, y=6),
    ])
    session.commit()

# Test regular query
print("=== Regular Query ===")
with Session(engine) as session:
    stmt = select(Point).where(and_(Point.x == 3, Point.y == 4))
    result = session.scalars(stmt).all()
    for point in result:
        print(f"Point {point.id}: coord = {point.coord}")

# Test hybrid property in instance access
print("\n=== Instance Access ===")
with Session(engine) as session:
    points = session.scalars(select(Point)).all()
    for point in points:
        print(f"Point {point.id}: coord = {point.coord}")

# Test hybrid property setter functionality
print("\n=== Hybrid Property Setter ===")
with Session(engine) as session:
    point = session.scalars(select(Point).where(Point.id == 1)).first()
    if point:
        print(f"Before: Point {point.id}: coord = {point.coord}")
        # Use the setter to change coordinates
        point.coord = (10.5, 20.7)
        print(f"After setter: Point {point.id}: coord = {point.coord}")
        print(f"Individual values: x={point.x}, y={point.y}")
        session.commit()
        print("Changes committed to database")

# Test hybrid property expression in SQL queries
print("\n=== Hybrid Property Expression in SQL ===")
with Session(engine) as session:
    # Query using the hybrid property expression directly
    coord_string = "10.500000,20.700000"
    stmt = select(Point).where(Point.coord == coord_string)
    result = session.scalars(stmt).all()
    for point in result:
        print(f"Found point with coord expression '{coord_string}': Point {point.id}")
    
    # Show what the expression generates
    print(f"SQL expression for Point.coord: {Point.coord}")

# Test Python-level coordinate filtering
print("\n=== Python-level Coordinate Filtering ===")
with Session(engine) as session:
    points = session.scalars(select(Point)).all()
    target_coord = (10.5, 20.7)
    matching_points = [p for p in points if p.coord == target_coord]
    for point in matching_points:
        print(f"Found point with coord {target_coord}: Point {point.id}")

# Test Line hybrid property with expression
print("\n=== Line Hybrid Property with Expression ===")
with Session(engine) as session:
    line = Line(x1=0, y1=0, x2=10, y2=10)
    session.add(line)
    session.commit()
    
    print(f"Line {line.id}: coords = {line.coords}")
    
    # Use the setter to change line coordinates
    line.coords = ((1.5, 2.5), (8.5, 9.5))
    print(f"After setter: Line {line.id}: coords = {line.coords}")
    session.commit()
    
    # Test line expression query
    line_coord_string = "1.500000,2.500000|8.500000,9.500000"
    stmt = select(Line).where(Line.coords == line_coord_string)
    result = session.scalars(stmt).all()
    for line_obj in result:
        print(f"Found line with coords expression '{line_coord_string}': Line {line_obj.id}")

# Test shapely integration
print("\n=== Shapely Integration ===")  
with Session(engine) as session:
    point = session.scalars(select(Point).where(Point.id == 1)).first()
    if point:
        shapely_point = point.to_shapely
        print(f"Point {point.id}: shapely = {shapely_point}, coords = {shapely_point.coords[:]}")
        origin = ShapelyPoint(0, 0)
        print(f"Shapely distance from (0,0): {shapely_point.distance(origin):.2f}")
        
    line = session.scalars(select(Line).where(Line.id == 1)).first()
    if line:
        shapely_line = line.to_shapely
        print(f"Line {line.id}: shapely = {shapely_line}")
        print(f"Line length: {shapely_line.length:.2f}")

# Test Python vs SQL Expression Behavior
print("\n=== Python vs SQL Expression Behavior ===")
with Session(engine) as session:
    point = session.scalars(select(Point).where(Point.id == 1)).first()
    if point:
        print(f"Python level: point.coord = {point.coord} (type: {type(point.coord)})")
        print(f"SQL level: Point.coord expression = {Point.coord}")
        
        # Show that the same property behaves differently at class vs instance level
        print(f"Instance access returns tuple: {isinstance(point.coord, tuple)}")
        print(f"Class access returns SQL expression: {type(Point.coord)}") 