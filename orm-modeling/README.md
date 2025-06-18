# ORM Modeling for Network Graphs

This directory contains an Object-Relational Mapping (ORM) implementation for modeling geometric networks using SQLAlchemy. The implementation focuses on managing points and lines in a 2D coordinate system with capabilities for merging nearby points, splitting lines at intersections, and building graph representations.

## Key Features

### Hybrid Properties for Coordinate Access

The models include sophisticated hybrid properties that work both at the Python instance level and SQL query level:

**Point Model:**
- `coord` property: Returns coordinates as `(x, y)` tuple, with SQL expression support
- `coord_matches(coord)`: Class method for SQL coordinate filtering (accepts `tuple[float, float]`)
- `distance_to_point(coord)`: Calculate distance to another point (accepts `tuple[float, float]`)
- `is_endpoint`: Boolean field indicating if point is a line endpoint (True) or middle point (False)
- `update_endpoint_status(session)`: Update endpoint status based on line relationships
- `update_all_endpoint_status(session)`: Class method to update all points' endpoint status
- `to_shapely`: Convert to Shapely Point geometry

**Line Model:**
- `coords` property: Returns line coordinates as `((x1, y1), (x2, y2))` tuple
- `start_coord` and `end_coord`: Access line endpoints as tuples
- `has_endpoint(coord)`: Check if line has specific endpoint (accepts `tuple[float, float]`)
- `start_matches(coord)` and `end_matches(coord)`: Specific endpoint matching (accepts `tuple[float, float]`)
- `update_endpoint(old_coord, new_coord)`: Update line endpoints (accepts `tuple[float, float]`)
- `to_shapely`: Convert to Shapely LineString geometry

### Endpoint Classification

The `is_endpoint` field automatically categorizes points based on their role in the network:

- **True Endpoints** (`is_endpoint=True`):
  - Original points created from coordinate pairs
  - Terminal points (connected to exactly 1 line)
  - Junction/intersection points (connected to 3+ lines)

- **Middle Points** (`is_endpoint=False`):
  - Points inserted during line splitting
  - Connected to exactly 2 lines (continuation points)

## Dependencies

- SQLAlchemy 2.0+
- Shapely
- igraph-python

Install with:
```bash
pip install sqlalchemy shapely igraph
```

## Usage Examples

### Basic Coordinate Access

```python
# Instance level - returns tuples
point = Point(x=3.0, y=4.0)
print(point.coord)  # (3.0, 4.0)

line = Line(x1=0.0, y1=0.0, x2=1.0, y2=1.0)
print(line.coords)  # ((0.0, 0.0), (1.0, 1.0))
print(line.start_coord)  # (0.0, 0.0)
print(line.end_coord)  # (1.0, 1.0)
```

### SQL Query Operations

```python
from sqlalchemy import select

# Find point by coordinates
stmt = select(Point).where(Point.coord_matches((3.0, 4.0)))
point = session.execute(stmt).scalar_one_or_none()

# Find lines with specific endpoint
stmt = select(Line).where(Line.has_endpoint((3.0, 4.0)))
lines = session.execute(stmt).scalars().all()

# Find lines starting at specific coordinates
stmt = select(Line).where(Line.start_matches((0.0, 0.0)))
lines = session.execute(stmt).scalars().all()

# Get all points that are not merged
stmt = select(Point).where(Point.is_merged == False)
points = session.execute(stmt).scalars().all()
```

### Python-Level Filtering

```python
# Filter points by coordinate comparison
stmt = select(Point)
points = session.execute(stmt).scalars().all()
nearby_points = [p for p in points if p.coord == (3.0, 4.0)]

# Calculate distances
distance = point1.distance_to_point(point2.coord)
```

### Geometric Operations with Shapely

```python
# Convert to Shapely geometries
point_geom = point.to_shapely
line_geom = line.to_shapely

# Calculate distance between geometries
distance = point_geom.distance(line_geom)

# Check if point is within tolerance of line
is_near = line_geom.dwithin(point_geom, tolerance=0.1)
```

### Endpoint Classification and Filtering

```python
# Filter points by endpoint status
endpoint_points = session.execute(
    select(Point).where(Point.is_endpoint == True)
).scalars().all()

middle_points = session.execute(
    select(Point).where(Point.is_endpoint == False)
).scalars().all()

# Update endpoint status after line operations
Point.update_all_endpoint_status(session)
session.commit()

# Check individual point status
for point in points:
    if point.is_endpoint:
        print(f"Endpoint: {point.coord}")
    else:
        print(f"Middle point: {point.coord}")
```

### Advanced Service Operations

```python
# Using the NetworkGraphBuilder with hybrid properties
builder = NetworkGraphBuilder(session)

# Create lines using coordinate tuples
coordinate_pairs = [
    ((0.0, 0.0), (1.0, 1.0)),
    ((1.0, 1.0), (2.0, 0.0))
]
lines = builder.create_lines_from_coordinates(coordinate_pairs)

# Merge nearby points within tolerance
merged = builder.merge_nearby_points(margin=0.1)

# Split lines at intersection points
new_lines = builder.split_lines_on_points(tolerance=0.01)

# Build igraph representation
graph = builder.create_igraph()
```

## Implementation Notes

### Hybrid Property Benefits

The hybrid properties provide several advantages:

1. **Concise Code**: Coordinate access becomes more readable and intuitive
2. **SQL Compatibility**: Helper methods like `coord_matches()` work in database queries
3. **Type Safety**: Proper tuple typing for coordinate operations
4. **Unified Interface**: Same property works for both Python and SQL contexts

### Service Layer Improvements

The NetworkGraphBuilder service has been refactored to use these hybrid properties and includes performance optimizations:

- `Point.coord_matches()` replaces manual `x == x_val, y == y_val` filtering
- `Line.has_endpoint()` simplifies complex endpoint matching queries
- `Line.update_endpoint()` encapsulates coordinate update logic
- `Line.start_coord` and `Line.end_coord` provide cleaner coordinate access
- **STRtree spatial indexing** for efficient line splitting operations (O(n log n) vs O(n²))

### Performance Optimization

The line splitting algorithm uses Shapely's STRtree for spatial indexing:

```python
# Create spatial index of points
point_geoms = [point.to_shapely for point in points]
point_tree = STRtree(point_geoms)

# Efficiently find points near each line
nearby_indices = point_tree.query(line_geom.buffer(tolerance))
```

**Performance Benefits:**
- **Small datasets** (100 points): ~0.04s
- **Medium datasets** (500 points): ~0.24s  
- **Large datasets** (1000 points): ~0.69s
- **Very large datasets** (2000 points): ~2.31s

This provides significant performance improvements over the previous O(n²) nested loop approach, especially for large datasets.

### Database Compatibility

The implementation uses SQLite-compatible functions:
- `func.printf()` for string formatting in coordinate expressions
- Standard SQL operators for coordinate matching
- Cross-database compatible helper methods

## Testing

The models support comprehensive testing scenarios:
- Instance-level coordinate access and manipulation
- SQL query generation and execution
- Python-level filtering and operations
- Geometric calculations with Shapely integration

## Files

- `model.py`: SQLAlchemy model definitions with hybrid properties
- `service.py`: NetworkGraphBuilder service using the hybrid properties
- `main.py`: Database setup and basic usage examples
- `example_usage.py`: Comprehensive examples and test scenarios

## Features

- Point model with x, y coordinates and tuple/Shapely property accessors
- Line model with start/end coordinates and Shapely LineString integration
- Automatic Point deduplication when creating Lines from coordinate pairs
- Point merging based on distance margin with relationship tracking
- Merged points accessible via `merged_points` attribute on the target Point
- Line splitting when points are found on line segments using dwithin tolerance
- Split lines marked with `is_split = True` and excluded from igraph generation
- Lines automatically updated when points are merged
- igraph creation from active (non-merged) Points and active (non-split) Lines
- Vertex names use string representation of coordinate tuples
- Database tables use `tbl_` prefix with singular names

## Point Merging

Points within a specified distance margin can be merged using `merge_nearby_points(margin)`. When merged:
- One point remains active, the other is marked `is_merged = True`
- The merged point references the target via `merged_into` relationship
- All lines using the merged point are updated to use the target point coordinates
- Merged points can be accessed via the `merged_points` list on the target point

## Line Splitting

Lines can be split when points are found on their segments using `split_lines_on_points(tolerance)`. When split:
- Original line is marked `is_split = True` but preserved in database
- New line segments are created connecting consecutive points along the original line
- Points are ordered by their projection distance along the original line
- Split lines are excluded from igraph generation to avoid redundancy

## Example Usage

```bash
python example_usage.py
```

This will create Points and Lines from coordinate pairs, demonstrate line splitting when points intersect line segments, and generate an igraph representation using only the active line segments.

## ORM Modeling

SQLAlchemy ORM models for geometric entities with advanced hybrid property support.

## Models

### Point
- Database table: `tbl_point`
- Fields: id, x, y, is_merged, merged_into_id
- Self-referencing relationship for point merging
- **Hybrid Property**: `coord` - returns (x, y) tuple with SQL expression support

### Line  
- Database table: `tbl_line`
- Fields: id, x1, y1, x2, y2, is_split
- **Hybrid Property**: `coords` - returns ((x1, y1), (x2, y2)) with SQL expression support

## Features

### Advanced Hybrid Properties
The hybrid properties are implemented using SQLAlchemy's standard pattern:

#### Instance Level (Python)
```python
point = Point(x=1.0, y=2.0)
coord = point.coord  # Returns (1.0, 2.0) tuple
point.coord = (3.0, 4.0)  # Setter support
```

#### Class Level (SQL Expression)
```python
# Direct SQL query using hybrid property expression
stmt = select(Point).where(Point.coord == "3.000000,4.000000")
```

#### Implementation Pattern
```python
@hybrid_property
def coord(self) -> tuple[float, float]:
    return (self.x, self.y)

@coord.setter  # type: ignore
def coord(self, value: tuple[float, float]):  # type: ignore
    self.x, self.y = value

@coord.expression  # type: ignore
def coord(cls):  # type: ignore
    return func.printf("%.6f,%.6f", cls.x, cls.y)
```

### Query Methods
- Direct hybrid property queries: `Point.coord == "formatted_string"`
- Individual field access: `Point.x`, `Point.y`

### Shapely Integration
- `Point.to_shapely`: Converts to Shapely Point object
- `Line.to_shapely`: Converts to Shapely LineString object

## Usage Examples

### Basic Operations
```python
# Create and access
point = Point(x=1.0, y=2.0)
print(point.coord)  # (1.0, 2.0)

# Setter functionality
point.coord = (3.0, 4.0)
print(f"x={point.x}, y={point.y}")  # x=3.0, y=4.0
```

### SQL Queries
```python
# Using individual fields
stmt = select(Point).where(and_(Point.x == 3.0, Point.y == 4.0))

# Using hybrid property expression
coord_string = "3.000000,4.000000"
stmt = select(Point).where(Point.coord == coord_string)
```

### Python vs SQL Behavior
```python
# Instance level - returns tuple
point.coord  # (3.0, 4.0)

# Class level - returns SQL expression
Point.coord  # <sqlalchemy.sql.functions.Function>
```

## Implementation Notes

### Naming Convention
- **Point**: `coord` (singular) - represents one coordinate point
- **Line**: `coords` (plural) - represents multiple coordinate points

### SQLAlchemy Hybrid Property Pattern
- **Same Method Names**: All three methods (getter, setter, expression) must have the same name
- **Type Ignore Comments**: `# type: ignore` is used to suppress Pylance warnings
- **Normal Behavior**: The "method declaration obscured" warnings are expected and normal

### SQLite Compatibility
- Uses `func.printf()` for formatted string output
- Point format: `"x.xxxxxx,y.yyyyyy"`
- Line format: `"x1.xxxxxx,y1.yyyyyy|x2.xxxxxx,y2.yyyyyy"`

### Linter Notes
- **Expected Warnings**: "Method declaration obscured" warnings are normal for hybrid properties
- **Type Ignore**: `# type: ignore` comments suppress these expected warnings
- **Standard Pattern**: This follows the official SQLAlchemy documentation pattern

// All comments in the code are written in English. 