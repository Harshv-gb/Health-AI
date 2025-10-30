import pandas as pd
import math
from typing import List, Dict, Optional, Tuple
import json

class HospitalFinder:
    """
    Find nearby hospitals based on user location and medical department needs.
    Uses Haversine formula to calculate distance between coordinates.
    """
    
    def __init__(self, hospital_csv_path: str):
        """Initialize with hospital database"""
        try:
            self.hospitals_df = pd.read_csv(hospital_csv_path)
            print(f"✅ Loaded {len(self.hospitals_df)} hospitals from database")
        except FileNotFoundError:
            print(f"⚠️ Hospital database not found at {hospital_csv_path}")
            self.hospitals_df = pd.DataFrame()
        
        # Major city coordinates for India (latitude, longitude)
        self.city_coordinates = {
            'delhi': (28.6139, 77.2090),
            'new delhi': (28.6139, 77.2090),
            'mumbai': (19.0760, 72.8777),
            'bangalore': (12.9716, 77.5946),
            'bengaluru': (12.9716, 77.5946),
            'hyderabad': (17.3850, 78.4867),
            'chennai': (13.0827, 80.2707),
            'pune': (18.5204, 73.8567),
            'gurgaon': (28.4595, 77.0266),
            'gurugram': (28.4595, 77.0266),
            'noida': (28.5355, 77.3910),
            'vellore': (12.9165, 79.1325),
            'chandigarh': (30.7333, 76.7794),
            'kolkata': (22.5726, 88.3639),
            'ahmedabad': (23.0225, 72.5714),
            'jaipur': (26.9124, 75.7873)
        }
    
    def haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate distance between two points on Earth using Haversine formula.
        Returns distance in kilometers.
        """
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distance = R * c
        return round(distance, 2)
    
    def get_city_coordinates(self, city_name: str) -> Optional[Tuple[float, float]]:
        """Get coordinates for a city name"""
        city_lower = city_name.lower().strip()
        return self.city_coordinates.get(city_lower)
    
    def find_nearby_hospitals(
        self,
        user_lat: float,
        user_lon: float,
        department: Optional[str] = None,
        max_distance: float = 50.0,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find hospitals near user location.
        
        Args:
            user_lat: User's latitude
            user_lon: User's longitude
            department: Specific medical department (optional)
            max_distance: Maximum distance in kilometers
            limit: Maximum number of hospitals to return
        
        Returns:
            List of nearby hospitals with distance information
        """
        if self.hospitals_df.empty:
            return []
        
        # Calculate distance for each hospital
        hospitals_with_distance = []
        
        for _, hospital in self.hospitals_df.iterrows():
            # Get hospital city coordinates
            city = hospital.get('city', '').strip()
            city_coords = self.get_city_coordinates(city)
            
            if not city_coords:
                continue
            
            hospital_lat, hospital_lon = city_coords
            distance = self.haversine_distance(user_lat, user_lon, hospital_lat, hospital_lon)
            
            # Filter by department if specified
            if department:
                hospital_dept = str(hospital.get('department', '')).lower()
                if department.lower() not in hospital_dept and 'multi-specialty' not in hospital_dept:
                    continue
            
            # Filter by distance
            if distance <= max_distance:
                hospital_info = {
                    'name': hospital.get('hospital_name', 'Unknown'),
                    'department': hospital.get('department', 'General'),
                    'address': hospital.get('address', ''),
                    'city': hospital.get('city', ''),
                    'state': hospital.get('state', ''),
                    'phone': hospital.get('phone', ''),
                    'emergency_services': hospital.get('emergency_services', 'Unknown'),
                    'rating': hospital.get('rating', 'N/A'),
                    'distance_km': distance
                }
                hospitals_with_distance.append(hospital_info)
        
        # Sort by distance
        hospitals_with_distance.sort(key=lambda x: x['distance_km'])
        
        # Return limited results
        return hospitals_with_distance[:limit]
    
    def find_hospitals_by_city(
        self,
        city_name: str,
        department: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict]:
        """
        Find hospitals in a specific city.
        
        Args:
            city_name: Name of the city
            department: Specific medical department (optional)
            limit: Maximum number of hospitals to return
        
        Returns:
            List of hospitals in the city
        """
        if self.hospitals_df.empty:
            return []
        
        # Get city coordinates for distance calculation
        city_coords = self.get_city_coordinates(city_name)
        if not city_coords:
            # If city not found, search by name matching
            city_lower = city_name.lower()
            filtered = self.hospitals_df[
                self.hospitals_df['city'].str.lower().str.contains(city_lower, na=False)
            ]
        else:
            # Use exact city match
            city_lower = city_name.lower()
            filtered = self.hospitals_df[
                self.hospitals_df['city'].str.lower() == city_lower
            ]
        
        # Filter by department if specified
        if department:
            filtered = filtered[
                filtered['department'].str.lower().str.contains(department.lower(), na=False) |
                filtered['department'].str.lower().str.contains('multi-specialty', na=False)
            ]
        
        # Convert to list of dicts
        hospitals = []
        for _, hospital in filtered.head(limit).iterrows():
            hospital_info = {
                'name': hospital.get('hospital_name', 'Unknown'),
                'department': hospital.get('department', 'General'),
                'address': hospital.get('address', ''),
                'city': hospital.get('city', ''),
                'state': hospital.get('state', ''),
                'phone': hospital.get('phone', ''),
                'emergency_services': hospital.get('emergency_services', 'Unknown'),
                'rating': hospital.get('rating', 'N/A')
            }
            hospitals.append(hospital_info)
        
        return hospitals
    
    def get_emergency_hospitals(
        self,
        user_lat: float,
        user_lon: float,
        max_distance: float = 20.0,
        limit: int = 5
    ) -> List[Dict]:
        """
        Find nearest hospitals with emergency services.
        Prioritizes hospitals within 20km with emergency facilities.
        """
        if self.hospitals_df.empty:
            return []
        
        # Filter for emergency services
        emergency_hospitals = self.hospitals_df[
            self.hospitals_df['emergency_services'].str.lower() == 'yes'
        ]
        
        hospitals_with_distance = []
        
        for _, hospital in emergency_hospitals.iterrows():
            city = hospital.get('city', '').strip()
            city_coords = self.get_city_coordinates(city)
            
            if not city_coords:
                continue
            
            hospital_lat, hospital_lon = city_coords
            distance = self.haversine_distance(user_lat, user_lon, hospital_lat, hospital_lon)
            
            if distance <= max_distance:
                hospital_info = {
                    'name': hospital.get('hospital_name', 'Unknown'),
                    'department': hospital.get('department', 'General'),
                    'address': hospital.get('address', ''),
                    'city': hospital.get('city', ''),
                    'state': hospital.get('state', ''),
                    'phone': hospital.get('phone', ''),
                    'emergency_services': 'Yes',
                    'rating': hospital.get('rating', 'N/A'),
                    'distance_km': distance
                }
                hospitals_with_distance.append(hospital_info)
        
        # Sort by distance
        hospitals_with_distance.sort(key=lambda x: x['distance_km'])
        
        return hospitals_with_distance[:limit]
    
    def format_hospital_response(self, hospitals: List[Dict]) -> str:
        """Format hospital list for display"""
        if not hospitals:
            return "No hospitals found matching your criteria."
        
        response = f"📍 Found {len(hospitals)} nearby hospital(s):\n\n"
        
        for i, hospital in enumerate(hospitals, 1):
            response += f"{i}. **{hospital['name']}**\n"
            response += f"   Department: {hospital['department']}\n"
            response += f"   Address: {hospital['address']}, {hospital['city']}\n"
            
            if 'distance_km' in hospital:
                response += f"   Distance: {hospital['distance_km']} km\n"
            
            response += f"   Phone: {hospital['phone']}\n"
            response += f"   Emergency: {hospital['emergency_services']}\n"
            response += f"   Rating: ⭐ {hospital['rating']}\n\n"
        
        return response


# Example usage
if __name__ == "__main__":
    finder = HospitalFinder('../data/hospitals_india.csv')
    
    # Test 1: Find hospitals near Delhi
    print("=== Test 1: Hospitals near Delhi ===")
    delhi_coords = (28.6139, 77.2090)
    hospitals = finder.find_nearby_hospitals(
        delhi_coords[0], delhi_coords[1],
        department='Cardiology',
        limit=5
    )
    print(finder.format_hospital_response(hospitals))
    
    # Test 2: Emergency hospitals in Mumbai
    print("\n=== Test 2: Emergency hospitals near Mumbai ===")
    mumbai_coords = (19.0760, 72.8777)
    emergency = finder.get_emergency_hospitals(
        mumbai_coords[0], mumbai_coords[1],
        limit=3
    )
    print(finder.format_hospital_response(emergency))
