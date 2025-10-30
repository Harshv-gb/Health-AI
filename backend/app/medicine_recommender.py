# medicine_recommender.py - AI-powered Medicine Recommendation System
import json
import os
from typing import List, Dict, Any, Optional

class MedicineRecommender:
    def __init__(self):
        """Initialize the medicine recommendation system"""
        self.medicine_db = None
        self.load_medicine_database()
        
    def load_medicine_database(self):
        """Load medicine database from JSON file"""
        try:
            # Get the project root directory
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
            medicine_db_path = os.path.join(project_root, "config", "medicine_database.json")
            
            with open(medicine_db_path, 'r', encoding='utf-8') as f:
                self.medicine_db = json.load(f)
            print("✅ Medicine database loaded successfully")
            
        except Exception as e:
            print(f"⚠️ Failed to load medicine database: {e}")
            self.medicine_db = None
    
    def get_medicine_recommendations(self, condition: str, patient_context: Dict = None) -> Dict[str, Any]:
        """Get medicine recommendations for a given condition"""
        if not self.medicine_db:
            return {
                "success": False,
                "error": "Medicine database not available",
                "recommendations": []
            }
        
        try:
            # Get condition mappings
            condition_mappings = self.medicine_db.get("condition_medicine_mapping", {})
            medicine_database = self.medicine_db.get("medicine_database", {})
            
            # Find medicines for the condition
            recommended_medicines = condition_mappings.get(condition, [])
            
            if not recommended_medicines:
                # Try partial matching if exact condition not found
                for cond_name, medicines in condition_mappings.items():
                    if condition.lower() in cond_name.lower() or cond_name.lower() in condition.lower():
                        recommended_medicines = medicines
                        break
            
            if not recommended_medicines:
                return {
                    "success": True,
                    "condition": condition,
                    "recommendations": [],
                    "message": "No specific medication recommendations available for this condition. Please consult a healthcare professional."
                }
            
            # Process recommendations
            recommendations = []
            for medicine_name in recommended_medicines:
                medicine_info = self._find_medicine_info(medicine_name, medicine_database)
                if medicine_info:
                    # Apply safety checks and filters
                    safety_check = self._perform_safety_check(medicine_info, patient_context)
                    
                    recommendation = {
                        "medicine_name": medicine_info["generic_name"],
                        "brand_names": medicine_info.get("brand_names", []),
                        "type": medicine_info.get("type", ""),
                        "dosage": medicine_info.get("dosage", {}),
                        "otc_available": medicine_info.get("otc", False),
                        "pregnancy_safe": medicine_info.get("pregnancy_safe", False),
                        "side_effects": medicine_info.get("side_effects", []),
                        "safety_check": safety_check,
                        "priority": self._calculate_priority(medicine_info, condition)
                    }
                    
                    recommendations.append(recommendation)
            
            # Sort by priority and safety
            recommendations.sort(key=lambda x: (-x["priority"], x["safety_check"]["safe"]))
            
            return {
                "success": True,
                "condition": condition,
                "recommendations": recommendations,
                "disclaimers": self._get_relevant_disclaimers(recommendations),
                "safety_warnings": self._get_safety_warnings(recommendations, patient_context)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Error generating recommendations: {str(e)}",
                "recommendations": []
            }
    
    def _find_medicine_info(self, medicine_name: str, medicine_database: Dict) -> Optional[Dict]:
        """Find medicine information in the database"""
        for category, medicines in medicine_database.items():
            if medicine_name in medicines:
                return medicines[medicine_name]
        return None
    
    def _perform_safety_check(self, medicine_info: Dict, patient_context: Dict = None) -> Dict[str, Any]:
        """Perform safety checks for the medicine"""
        safety_check = {
            "safe": True,
            "warnings": [],
            "contraindications": []
        }
        
        if not patient_context:
            return safety_check
        
        # Age restrictions
        patient_age = patient_context.get("age")
        if patient_age and medicine_info.get("generic_name"):
            age_restrictions = self.medicine_db.get("age_restrictions", {})
            medicine_key = medicine_info["generic_name"].lower()
            
            for restricted_medicine, restriction in age_restrictions.items():
                if restricted_medicine in medicine_key:
                    min_age = restriction.get("min_age", 0)
                    if patient_age < min_age:
                        safety_check["safe"] = False
                        safety_check["contraindications"].append(
                            f"Not recommended for age {patient_age}. Minimum age: {min_age}. Reason: {restriction['reason']}"
                        )
        
        # Pregnancy check
        is_pregnant = patient_context.get("pregnant", False)
        if is_pregnant and not medicine_info.get("pregnancy_safe", False):
            safety_check["warnings"].append("Consult doctor before use during pregnancy")
        
        # Add general contraindications
        contraindications = medicine_info.get("contraindications", [])
        for contraindication in contraindications:
            safety_check["warnings"].append(f"Contraindicated in: {contraindication}")
        
        return safety_check
    
    def _calculate_priority(self, medicine_info: Dict, condition: str) -> int:
        """Calculate medicine priority based on effectiveness and safety"""
        priority = 5  # Base priority
        
        # Higher priority for OTC medicines
        if medicine_info.get("otc", False):
            priority += 3
        
        # Higher priority for pregnancy-safe medicines
        if medicine_info.get("pregnancy_safe", False):
            priority += 2
        
        # Lower priority for medicines with many side effects
        side_effects_count = len(medicine_info.get("side_effects", []))
        if side_effects_count > 3:
            priority -= 1
        
        # Condition-specific priorities
        if condition.lower() in ["emergency", "severe", "acute"]:
            if "emergency" in medicine_info.get("type", "").lower():
                priority += 5
        
        return max(1, priority)  # Minimum priority of 1
    
    def _get_relevant_disclaimers(self, recommendations: List[Dict]) -> List[str]:
        """Get relevant medical disclaimers"""
        disclaimers = []
        disclaimer_db = self.medicine_db.get("medical_disclaimers", {})
        
        # Always include general disclaimer
        disclaimers.append(disclaimer_db.get("general", ""))
        
        # Add specific disclaimers based on recommendations
        has_prescription = any(not rec.get("otc_available", True) for rec in recommendations)
        if has_prescription:
            disclaimers.append(disclaimer_db.get("prescription", ""))
        
        # Add other relevant disclaimers
        disclaimers.append(disclaimer_db.get("allergies", ""))
        
        return [d for d in disclaimers if d]  # Remove empty disclaimers
    
    def _get_safety_warnings(self, recommendations: List[Dict], patient_context: Dict = None) -> List[str]:
        """Generate safety warnings based on recommendations and patient context"""
        warnings = []
        
        # Check for emergency conditions
        if patient_context and patient_context.get("urgency") == "emergency":
            warnings.append("⚠️ For emergency conditions, seek immediate medical attention. Medications are supportive only.")
        
        # Check for multiple medicine interactions
        if len(recommendations) > 2:
            warnings.append("⚠️ If taking multiple medications, consult pharmacist for drug interactions.")
        
        # Check for prescription medicines
        prescription_meds = [rec for rec in recommendations if not rec.get("otc_available", True)]
        if prescription_meds:
            warnings.append("⚠️ Some recommendations require prescription. Consult healthcare provider.")
        
        # General safety warning
        warnings.append("⚠️ Always read medication labels and follow dosing instructions.")
        warnings.append("⚠️ Stop medication and seek help if you experience severe side effects.")
        
        return warnings
    
    def get_medicine_details(self, medicine_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific medicine"""
        if not self.medicine_db:
            return {"success": False, "error": "Medicine database not available"}
        
        medicine_database = self.medicine_db.get("medicine_database", {})
        medicine_info = self._find_medicine_info(medicine_name, medicine_database)
        
        if not medicine_info:
            return {"success": False, "error": f"Medicine '{medicine_name}' not found"}
        
        return {
            "success": True,
            "medicine_info": medicine_info,
            "drug_interactions": self._get_drug_interactions(medicine_name),
            "disclaimers": self.medicine_db.get("medical_disclaimers", {})
        }
    
    def _get_drug_interactions(self, medicine_name: str) -> List[str]:
        """Get drug interactions for a medicine"""
        interactions_db = self.medicine_db.get("drug_interactions", {})
        
        for medicine_key, interactions in interactions_db.items():
            if medicine_key.lower() in medicine_name.lower():
                return interactions
        
        return []
    
    def search_medicines_by_symptom(self, symptoms: List[str]) -> Dict[str, Any]:
        """Search for medicines based on symptoms"""
        if not self.medicine_db:
            return {"success": False, "error": "Medicine database not available"}
        
        medicine_database = self.medicine_db.get("medicine_database", {})
        matching_medicines = []
        
        # Search through all medicines for symptom matches
        for category, medicines in medicine_database.items():
            for medicine_name, medicine_info in medicines.items():
                medicine_conditions = medicine_info.get("conditions", [])
                
                # Check if any symptoms match medicine conditions
                for symptom in symptoms:
                    for condition in medicine_conditions:
                        if symptom.lower() in condition.lower() or condition.lower() in symptom.lower():
                            if medicine_info not in matching_medicines:
                                matching_medicines.append({
                                    "medicine_name": medicine_info["generic_name"],
                                    "brand_names": medicine_info.get("brand_names", []),
                                    "type": medicine_info.get("type", ""),
                                    "matching_conditions": [c for c in medicine_conditions if any(s.lower() in c.lower() for s in symptoms)],
                                    "otc_available": medicine_info.get("otc", False)
                                })
                            break
        
        return {
            "success": True,
            "symptoms": symptoms,
            "matching_medicines": matching_medicines,
            "disclaimer": "These are potential matches based on symptoms. Always consult healthcare professionals for proper diagnosis and treatment."
        }

# Helper functions for API integration
def get_medicine_recommendations_for_condition(condition: str, patient_context: Dict = None) -> Dict[str, Any]:
    """Main function to get medicine recommendations"""
    recommender = MedicineRecommender()
    return recommender.get_medicine_recommendations(condition, patient_context)

def get_medicine_details(medicine_name: str) -> Dict[str, Any]:
    """Get detailed medicine information"""
    recommender = MedicineRecommender()
    return recommender.get_medicine_details(medicine_name)

def search_medicines_by_symptoms(symptoms: List[str]) -> Dict[str, Any]:
    """Search medicines by symptoms"""
    recommender = MedicineRecommender()
    return recommender.search_medicines_by_symptom(symptoms)