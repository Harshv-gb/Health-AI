"""
SQL-based Hospital Finder using PostgreSQL database with geospatial queries
Replaces the original CSV-based hospital finder
"""
import os
import sys
import math
from typing import List, Dict, Optional
from sqlalchemy import func, and_, or_

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db_session, Hospital, HospitalDepartment


class HospitalFinderSQL:
    """Find nearby hospitals using SQL database with efficient geospatial queries"""
    
    def __init__(self):
        self.db = None
    
    def find_nearby_hospitals(
        self,
        latitude: float,
        longitude: float,
        department: Optional[str] = None,
        radius_km: int = 50,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find hospitals near a location using Haversine formula in SQL
        
        Args:
            latitude: User's latitude
            longitude: User's longitude
            department: Filter by department (optional)
            radius_km: Search radius in kilometers
            limit: Maximum number of results
        
        Returns:
            List of hospitals sorted by distance
        """
        self.db = get_db_session()
        
        try:
            # Haversine formula in SQL for distance calculation
            # Earth radius ~6371 km
            earth_radius = 6371
            
            # Convert degrees to radians
            lat_rad = func.radians(latitude)
            lat_col_rad = func.radians(Hospital.latitude)
            lon_diff_rad = func.radians(Hospital.longitude - longitude)
            
            # Haversine formula
            # a = sin²(Δlat/2) + cos(lat1) * cos(lat2) * sin²(Δlon/2)
            # c = 2 * atan2(√a, √(1−a))
            # distance = R * c
            
            distance_expr = earth_radius * 2 * func.asin(
                func.sqrt(
                    func.pow(func.sin((lat_col_rad - lat_rad) / 2), 2) +
                    func.cos(lat_rad) * func.cos(lat_col_rad) *
                    func.pow(func.sin(lon_diff_rad / 2), 2)
                )
            )
            
            # Build base query
            query = self.db.query(
                Hospital,
                distance_expr.label('distance_km')
            )
            
            # Filter by department if specified
            if department:
                query = query.join(Hospital.departments).filter(
                    HospitalDepartment.department_name.ilike(f'%{department}%')
                )
            
            # Filter by radius
            query = query.filter(distance_expr <= radius_km)
            
            # Remove null coordinates
            query = query.filter(
                and_(
                    Hospital.latitude.isnot(None),
                    Hospital.longitude.isnot(None)
                )
            )
            
            # Order by distance and limit results
            query = query.order_by('distance_km').limit(limit)
            
            # Execute query
            results = query.all()
            
            # Format results
            hospitals = []
            for hospital, distance in results:
                # Get all departments for this hospital
                departments = self.db.query(HospitalDepartment.department_name).filter(
                    HospitalDepartment.hospital_id == hospital.id
                ).all()
                
                dept_list = [dept[0] for dept in departments]
                
                hospitals.append({
                    'name': hospital.name,
                    'city': hospital.city or 'Unknown',
                    'state': hospital.state or 'Unknown',
                    'distance_km': round(distance, 2),
                    'contact': hospital.contact_number or 'Not available',
                    'departments': dept_list,
                    'latitude': float(hospital.latitude) if hospital.latitude else None,
                    'longitude': float(hospital.longitude) if hospital.longitude else None
                })
            
            return hospitals
            
        finally:
            if self.db:
                self.db.close()
    
    def find_hospitals_by_name(self, search_term: str, limit: int = 10) -> List[Dict]:
        """
        Search hospitals by name
        """
        self.db = get_db_session()
        
        try:
            hospitals = self.db.query(Hospital).filter(
                Hospital.name.ilike(f'%{search_term}%')
            ).limit(limit).all()
            
            results = []
            for hospital in hospitals:
                departments = self.db.query(HospitalDepartment.department_name).filter(
                    HospitalDepartment.hospital_id == hospital.id
                ).all()
                
                results.append({
                    'name': hospital.name,
                    'city': hospital.city,
                    'state': hospital.state,
                    'contact': hospital.contact_number,
                    'departments': [dept[0] for dept in departments],
                    'latitude': float(hospital.latitude) if hospital.latitude else None,
                    'longitude': float(hospital.longitude) if hospital.longitude else None
                })
            
            return results
            
        finally:
            if self.db:
                self.db.close()
    
    def get_available_departments(self) -> List[str]:
        """
        Get list of all available departments across all hospitals
        """
        self.db = get_db_session()
        
        try:
            departments = self.db.query(
                HospitalDepartment.department_name
            ).distinct().order_by(
                HospitalDepartment.department_name
            ).all()
            
            return [dept[0] for dept in departments]
            
        finally:
            if self.db:
                self.db.close()
    
    def get_hospitals_by_city(self, city: str) -> List[Dict]:
        """
        Get all hospitals in a specific city
        """
        self.db = get_db_session()
        
        try:
            hospitals = self.db.query(Hospital).filter(
                Hospital.city.ilike(f'%{city}%')
            ).all()
            
            results = []
            for hospital in hospitals:
                departments = self.db.query(HospitalDepartment.department_name).filter(
                    HospitalDepartment.hospital_id == hospital.id
                ).all()
                
                results.append({
                    'name': hospital.name,
                    'city': hospital.city,
                    'state': hospital.state,
                    'contact': hospital.contact_number,
                    'departments': [dept[0] for dept in departments],
                    'latitude': float(hospital.latitude) if hospital.latitude else None,
                    'longitude': float(hospital.longitude) if hospital.longitude else None
                })
            
            return results
            
        finally:
            if self.db:
                self.db.close()


# ==================== HELPER FUNCTIONS ====================

def find_nearby_hospitals(
    latitude: float,
    longitude: float,
    department: Optional[str] = None,
    radius_km: int = 50
) -> List[Dict]:
    """
    Convenience function for finding nearby hospitals
    Compatible with existing API
    """
    finder = HospitalFinderSQL()
    return finder.find_nearby_hospitals(latitude, longitude, department, radius_km)


def calculate_distance_simple(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Simple Haversine distance calculation in Python
    For verification and fallback purposes
    """
    R = 6371  # Earth radius in kilometers
    
    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    delta_lat = math.radians(lat2 - lat1)
    delta_lon = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = (math.sin(delta_lat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(delta_lon / 2) ** 2)
    
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    
    return distance


def search_hospitals(search_term: str) -> List[Dict]:
    """
    Search hospitals by name or location
    """
    finder = HospitalFinderSQL()
    return finder.find_hospitals_by_name(search_term)


def get_departments() -> List[str]:
    """
    Get all available hospital departments
    """
    finder = HospitalFinderSQL()
    return finder.get_available_departments()


if __name__ == "__main__":
    # Test the SQL-based hospital finder
    print("🧪 Testing SQL Hospital Finder\n")
    
    # Test coordinates (Delhi, India)
    test_lat = 28.6139
    test_lon = 77.2090
    
    print(f"Searching hospitals near Delhi ({test_lat}, {test_lon})")
    print("-" * 70)
    
    finder = HospitalFinderSQL()
    
    # Test 1: Find nearby hospitals
    print("\n1. Nearby Hospitals (50km radius):")
    hospitals = finder.find_nearby_hospitals(test_lat, test_lon, radius_km=50, limit=5)
    
    if hospitals:
        for i, hospital in enumerate(hospitals, 1):
            print(f"\n{i}. {hospital['name']}")
            print(f"   Location: {hospital['city']}, {hospital['state']}")
            print(f"   Distance: {hospital['distance_km']} km")
            print(f"   Contact: {hospital['contact']}")
            print(f"   Departments: {', '.join(hospital['departments'][:3])}...")
    else:
        print("No hospitals found")
    
    # Test 2: Filter by department
    print("\n\n2. Hospitals with Cardiology:")
    cardio_hospitals = finder.find_nearby_hospitals(
        test_lat, test_lon,
        department='Cardiology',
        radius_km=100,
        limit=3
    )
    
    for i, hospital in enumerate(cardio_hospitals, 1):
        print(f"\n{i}. {hospital['name']} - {hospital['distance_km']} km")
    
    # Test 3: Get available departments
    print("\n\n3. Available Departments:")
    departments = finder.get_available_departments()
    print(f"Total departments: {len(departments)}")
    print(f"Sample: {', '.join(departments[:10])}")
