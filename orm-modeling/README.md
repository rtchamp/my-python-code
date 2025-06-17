# SQLAlchemy 2.0 ORM with Geometry and Graph Integration

This directory demonstrates SQLAlchemy 2.0 ORM models for geometric data with Shapely integration, point merging, line splitting, and igraph creation functionality.

## Files

- `orm.py`: Defines `Point` and `Line` models with coordinate properties, Shapely integration, merge relationships, and split tracking (tables: `tbl_point`, `tbl_line`)
- `service.py`: `NetworkGraphBuilder` class for creating Lines, merging nearby Points, splitting lines on points, and generating igraphs
- `main.py`: Basic example of Point model usage and querying
- `example_usage.py`: Comprehensive example showing NetworkGraphBuilder usage, point merging, line splitting, and igraph creation

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

// All comments in the code are written in English. 