import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import select, delete, create_engine
from sqlalchemy.orm import Session
from model import Base, Point, Line
from service import NetworkGraphBuilder

def transportation_merge_example():
    print("Transportation Infrastructure Metadata Merge Example")
    print("="*60)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    # Clear existing data
    session.execute(delete(Line))
    session.execute(delete(Point))
    session.commit()
    
    print("\n=== Creating Transportation Points ===")
    
    # Create points representing different transportation infrastructure
    # that might be close enough to merge due to GPS accuracy or design changes
    
    # Main intersection
    intersection = Point(x=0.0, y=0.0)
    intersection.set_metadata("type", "intersection")
    intersection.set_metadata("name", "Main & Oak")
    intersection.set_metadata("traffic_light", True)
    intersection.set_metadata("capacity", 1000)
    intersection.set_metadata("services", ["traffic_control"])
    intersection.set_metadata("priority", "high")
    
    # Bus stop very close to intersection (might merge due to GPS inaccuracy)
    bus_stop = Point(x=0.08, y=0.0)  # 8cm away - close enough to merge
    bus_stop.set_metadata("type", "bus_stop")
    bus_stop.set_metadata("name", "Oak Street Bus Stop")
    bus_stop.set_metadata("capacity", 50)
    bus_stop.set_metadata("services", ["bus", "shelter"])
    bus_stop.set_metadata("wheelchair_accessible", True)
    bus_stop.set_metadata("covered", True)
    
    # Taxi stand also very close
    taxi_stand = Point(x=0.0, y=0.07)  # 7cm away
    taxi_stand.set_metadata("type", "taxi_stand")
    taxi_stand.set_metadata("name", "Main Street Taxi")
    taxi_stand.set_metadata("capacity", 25)
    taxi_stand.set_metadata("services", ["taxi"])
    taxi_stand.set_metadata("emergency", True)
    taxi_stand.set_metadata("hours", "24/7")
    
    # Another point farther away (should not merge)
    parking = Point(x=1.0, y=0.0)
    parking.set_metadata("type", "parking")
    parking.set_metadata("name", "City Hall Parking")
    parking.set_metadata("capacity", 200)
    parking.set_metadata("covered", False)
    
    session.add_all([intersection, bus_stop, taxi_stand, parking])
    session.commit()
    
    print("Created infrastructure points:")
    for point in [intersection, bus_stop, taxi_stand, parking]:
        print(f"  {point.coord}: {point.get_metadata('name')} ({point.get_metadata('type')})")
        print(f"    Services: {point.get_metadata('services', [])}")
        print(f"    Capacity: {point.get_metadata('capacity')}")
        print()
    
    print("=== Before Merge Analysis ===")
    print(f"Total points: 4")
    
    # Create some connections
    builder = NetworkGraphBuilder(session)
    coordinate_pairs = [
        ((0.0, 0.0), (1.0, 0.0)),      # intersection to parking
        ((0.08, 0.0), (1.0, 0.0)),     # bus stop to parking  
        ((0.0, 0.07), (1.0, 0.0)),     # taxi stand to parking
    ]
    
    line_metadata = [
        {"name": "Main Street", "type": "road", "lanes": 2},
        {"name": "Bus Route", "type": "bus_lane", "lanes": 1},
        {"name": "Access Road", "type": "road", "lanes": 1},
    ]
    
    lines = builder.create_lines_from_coordinates(coordinate_pairs)
    
    print("=== Performing Smart Merge (margin=0.1m) ===")
    print("Merging nearby infrastructure points...")
    
    merged_points = builder.merge_nearby_points(margin=0.1)
    
    print(f"Merged {len(merged_points)} points into central locations")
    
    print("\n=== After Merge Analysis ===")
    
    # Check active points
    active_points = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()
    print(f"Active infrastructure points: {len(active_points)}")
    
    for point in active_points:
        name = point.get_metadata('name')
        point_type = point.get_metadata('type') 
        services = point.get_metadata('services', [])
        capacity = point.get_metadata('capacity')
        
        print(f"\n📍 {name} at {point.coord}")
        print(f"   Type: {point_type}")
        print(f"   Services: {', '.join(services)}")
        print(f"   Capacity: {capacity} people/vehicles")
        
        # Show additional amenities
        if point.has_metadata('wheelchair_accessible'):
            print(f"   ♿ Wheelchair accessible: {point.get_metadata('wheelchair_accessible')}")
        if point.has_metadata('covered'):
            print(f"   🏠 Covered: {point.get_metadata('covered')}")
        if point.has_metadata('traffic_light'):
            print(f"   🚦 Traffic light: {point.get_metadata('traffic_light')}")
        if point.has_metadata('emergency'):
            print(f"   🚨 Emergency access: {point.get_metadata('emergency')}")
        if point.has_metadata('hours'):
            print(f"   🕒 Hours: {point.get_metadata('hours')}")
        if point.has_metadata('priority'):
            print(f"   ⭐ Priority: {point.get_metadata('priority')}")
    
    # Check merged points for reference
    merged_points_in_db = session.execute(select(Point).where(Point.is_merged == True)).scalars().all()
    if merged_points_in_db:
        print(f"\n=== Merged Infrastructure Details ===")
        for point in merged_points_in_db:
            target_name = point.merged_into.get_metadata('name')
            print(f"🔄 {point.get_metadata('name')} ({point.coord}) → merged into {target_name}")
    
    # Show updated line connections
    print(f"\n=== Updated Transportation Network ===")
    updated_lines = session.execute(select(Line)).scalars().all()
    print(f"Active connections: {len(updated_lines)}")
    
    for line in updated_lines:
        print(f"🛣️  Line: {line.start_coord} ↔ {line.end_coord}")
    
    # Show efficiency gains
    print(f"\n=== Infrastructure Consolidation Results ===")
    original_count = 4
    final_count = len(active_points)
    
    print(f"📊 Infrastructure points: {original_count} → {final_count}")
    print(f"📈 Consolidation: {original_count - final_count} points merged")
    
    # Show total services available at merged points
    for point in active_points:
        services = point.get_metadata('services', [])
        if len(services) > 1:
            print(f"🎯 Multi-service hub at {point.coord}: {len(services)} services")
            print(f"   Combined services: {', '.join(services)}")
    
    session.close()

def custom_merge_strategies_example():
    print("\n" + "="*60)
    print("Custom Metadata Merge Strategies Example")
    print("="*60)
    
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(engine)
    session = Session(engine)
    
    print("\n=== Creating Points with Complex Metadata ===")
    
    # Point with rich metadata
    station1 = Point(x=0.0, y=0.0)
    station1.set_metadata("name", "Central Station")
    station1.set_metadata("capacity", 500)
    station1.set_metadata("priority_level", 9)
    station1.set_metadata("emergency", False)
    station1.set_metadata("services", ["metro", "bus"])
    station1.set_metadata("facilities", ["escalator", "elevator"])
    station1.set_metadata("operating_hours", "5:00-24:00")
    
    # Nearby point with overlapping services
    station2 = Point(x=0.06, y=0.0)
    station2.set_metadata("name", "Metro Platform")
    station2.set_metadata("capacity", 300) 
    station2.set_metadata("priority_level", 7)
    station2.set_metadata("emergency", True)
    station2.set_metadata("services", ["metro", "taxi"])
    station2.set_metadata("facilities", ["elevator", "waiting_area"])
    station2.set_metadata("wifi", True)
    
    session.add_all([station1, station2])
    session.commit()
    
    print("Before merge:")
    print(f"Station 1: {station1.metavar}")
    print(f"Station 2: {station2.metavar}")
    
    builder = NetworkGraphBuilder(session)
    merged = builder.merge_nearby_points(margin=0.1)
    
    active = session.execute(select(Point).where(Point.is_merged == False)).scalars().all()[0]
    
    print(f"\nAfter intelligent merge:")
    print(f"Merged station: {active.metavar}")
    
    print(f"\n=== Merge Strategy Analysis ===")
    print(f"📛 Name: Combined both names")
    print(f"📊 Capacity: Used maximum value ({active.get_metadata('capacity')})")
    print(f"⭐ Priority: Used maximum level ({active.get_metadata('priority_level')})")
    print(f"🚨 Emergency: Used OR logic ({active.get_metadata('emergency')})")
    print(f"🚌 Services: Combined unique services ({active.get_metadata('services')})")
    print(f"🏢 Facilities: Combined all facilities ({active.get_metadata('facilities')})")
    print(f"📶 WiFi: Added new feature ({active.get_metadata('wifi')})")
    print(f"🕒 Hours: Kept original schedule ({active.get_metadata('operating_hours')})")
    
    session.close()

if __name__ == "__main__":
    transportation_merge_example()
    custom_merge_strategies_example() 