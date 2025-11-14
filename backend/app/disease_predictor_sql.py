"""
SQL-based Disease Predictor using PostgreSQL database
Replaces the original CSV/JSON-based predictor with database queries
"""
import os
import sys
from typing import List, Dict, Tuple
from difflib import SequenceMatcher
from sqlalchemy import func

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import get_db_session, Disease, Symptom, DiseaseSymptom


class DiseasePredictorSQL:
    """Professional disease prediction using SQL database"""
    
    def __init__(self):
        self.db = None
        self.prevalence_multipliers = {
            'Very Common': 2.0,
            'Common': 1.5,
            'Uncommon': 1.0,
            'Rare': 0.6,
            'Very Rare': 0.3
        }
    
    def predict_diseases_professional(self, symptoms: List[str], patient_context: Dict) -> List[Dict]:
        """
        Main prediction function using SQL database
        
        Args:
            symptoms: List of symptom strings from user input
            patient_context: Dict with age, gender, chronic_conditions
        
        Returns:
            List of disease predictions with probabilities
        """
        self.db = get_db_session()
        
        try:
            # Step 1: Fuzzy match input symptoms to database symptoms
            matched_symptom_ids = self._fuzzy_match_symptoms(symptoms)
            
            if not matched_symptom_ids:
                return self._get_fallback_predictions()
            
            # Step 2: Query diseases that match these symptoms
            disease_scores = self._calculate_disease_scores(matched_symptom_ids, patient_context)
            
            if not disease_scores:
                return self._get_fallback_predictions()
            
            # Step 3: Apply scoring adjustments
            adjusted_scores = self._apply_scoring_adjustments(disease_scores, patient_context)
            
            # Step 4: Normalize to percentages and format results
            predictions = self._normalize_and_format(adjusted_scores)
            
            return predictions[:5]  # Return top 5
            
        finally:
            if self.db:
                self.db.close()
    
    def _fuzzy_match_symptoms(self, input_symptoms: List[str]) -> List[int]:
        """
        Match input symptoms to database symptoms using fuzzy matching
        Returns list of symptom IDs
        """
        matched_ids = []
        
        # Get all symptoms from database
        all_symptoms = self.db.query(Symptom).all()
        
        for input_symptom in input_symptoms:
            input_lower = input_symptom.lower().strip()
            
            for db_symptom in all_symptoms:
                # Check exact match on symptom name
                if self._similarity(input_lower, db_symptom.name.lower()) >= 0.8:
                    matched_ids.append(db_symptom.id)
                    break
                
                # Check synonyms
                synonyms = db_symptom.get_synonyms_list()
                for synonym in synonyms:
                    if self._similarity(input_lower, synonym.lower()) >= 0.8:
                        matched_ids.append(db_symptom.id)
                        break
                else:
                    continue
                break
        
        return list(set(matched_ids))  # Remove duplicates
    
    def _calculate_disease_scores(self, symptom_ids: List[int], patient_context: Dict) -> Dict:
        """
        Calculate base scores for diseases based on matched symptoms
        """
        disease_scores = {}
        
        # Query all disease-symptom relationships for matched symptoms
        results = self.db.query(
            Disease.id,
            Disease.name,
            Disease.description,
            Disease.severity,
            Disease.prevalence,
            Disease.treatment,
            Disease.when_to_see_doctor,
            DiseaseSymptom.weight,
            DiseaseSymptom.is_critical,
            func.count(DiseaseSymptom.symptom_id).label('symptom_count')
        ).join(
            DiseaseSymptom, Disease.id == DiseaseSymptom.disease_id
        ).filter(
            DiseaseSymptom.symptom_id.in_(symptom_ids)
        ).group_by(
            Disease.id,
            Disease.name,
            Disease.description,
            Disease.severity,
            Disease.prevalence,
            Disease.treatment,
            Disease.when_to_see_doctor,
            DiseaseSymptom.weight,
            DiseaseSymptom.is_critical
        ).all()
        
        # Aggregate scores by disease
        for result in results:
            disease_id = result[0]
            
            if disease_id not in disease_scores:
                disease_scores[disease_id] = {
                    'name': result[1],
                    'description': result[2],
                    'severity': result[3],
                    'prevalence': result[4],
                    'treatment': result[5],
                    'when_to_see_doctor': result[6],
                    'base_score': 0,
                    'matched_symptoms': 0,
                    'critical_symptoms': 0
                }
            
            # Add weighted score
            weight = float(result[7])
            is_critical = result[8]
            
            disease_scores[disease_id]['base_score'] += weight
            disease_scores[disease_id]['matched_symptoms'] += 1
            
            if is_critical:
                disease_scores[disease_id]['critical_symptoms'] += 1
        
        return disease_scores
    
    def _apply_scoring_adjustments(self, disease_scores: Dict, patient_context: Dict) -> Dict:
        """
        Apply prevalence, age, and pattern-based adjustments to scores
        """
        adjusted_scores = {}
        patient_age = patient_context.get('age', 30)
        chronic_conditions = patient_context.get('chronic_conditions', [])
        
        for disease_id, data in disease_scores.items():
            score = data['base_score']
            
            # 1. Prevalence multiplier
            prevalence = data.get('prevalence', 'Uncommon')
            multiplier = self.prevalence_multipliers.get(prevalence, 1.0)
            score *= multiplier
            
            # 2. Critical symptom boost
            if data['critical_symptoms'] > 0:
                score *= (1.0 + (data['critical_symptoms'] * 0.3))
            
            # 3. Age-related adjustments
            age_related_conditions = {
                'Type 2 Diabetes': (40, 70),
                'Hypertension': (45, 80),
                'Heart Attack': (50, 80),
                'Stroke': (55, 85),
                'Osteoarthritis': (50, 80)
            }
            
            if data['name'] in age_related_conditions:
                age_range = age_related_conditions[data['name']]
                if age_range[0] <= patient_age <= age_range[1]:
                    score *= 1.2
            
            # 4. Chronic condition boost
            if chronic_conditions:
                chronic_related = {
                    'diabetes': ['Type 2 Diabetes', 'Diabetic Ketoacidosis'],
                    'hypertension': ['Hypertension', 'Heart Attack', 'Stroke'],
                    'asthma': ['Asthma', 'Pneumonia', 'Bronchitis']
                }
                
                for chronic_cond in chronic_conditions:
                    chronic_lower = chronic_cond.lower()
                    for key, related_diseases in chronic_related.items():
                        if key in chronic_lower and data['name'] in related_diseases:
                            score *= 1.6
            
            # 5. Multiple symptom bonus
            if data['matched_symptoms'] >= 3:
                score *= 1.3
            elif data['matched_symptoms'] >= 5:
                score *= 1.5
            
            adjusted_scores[disease_id] = {
                'name': data['name'],
                'description': data['description'],
                'severity': data['severity'],
                'prevalence': data['prevalence'],
                'treatment': data['treatment'],
                'when_to_see_doctor': data['when_to_see_doctor'],
                'score': score,
                'matched_symptoms': data['matched_symptoms']
            }
        
        return adjusted_scores
    
    def _normalize_and_format(self, adjusted_scores: Dict) -> List[Dict]:
        """
        Normalize scores to percentages (5-95%) and format results
        """
        # Convert to list and sort by score
        predictions = list(adjusted_scores.values())
        predictions.sort(key=lambda x: x['score'], reverse=True)
        
        if not predictions:
            return []
        
        # Get score range
        max_score = predictions[0]['score']
        min_score = predictions[-1]['score'] if len(predictions) > 1 else 0
        
        # Normalize to 5-95% range
        formatted_predictions = []
        for pred in predictions:
            if max_score == min_score:
                probability = 50.0
            else:
                # Scale to 5-95 range
                normalized = (pred['score'] - min_score) / (max_score - min_score)
                probability = 5 + (normalized * 90)  # 5% to 95%
            
            formatted_predictions.append({
                'condition': pred['name'],
                'probability': round(probability, 1),
                'description': pred['description'],
                'severity': pred['severity'],
                'treatment': pred['treatment'],
                'when_to_see_doctor': pred['when_to_see_doctor'],
                'matched_symptoms': pred['matched_symptoms']
            })
        
        return formatted_predictions
    
    def _similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings"""
        return SequenceMatcher(None, str1, str2).ratio()
    
    def _get_fallback_predictions(self) -> List[Dict]:
        """Return generic predictions when no matches found"""
        return [
            {
                'condition': 'Common Cold',
                'probability': 45.0,
                'description': 'Viral infection of the upper respiratory tract',
                'severity': 'mild',
                'treatment': 'Rest, fluids, OTC pain relievers',
                'when_to_see_doctor': 'If symptoms persist beyond 10 days',
                'matched_symptoms': 0
            }
        ]


# ==================== HELPER FUNCTIONS ====================

def predict_diseases(symptoms: List[str], patient_context: Dict = None) -> List[Dict]:
    """
    Convenience function for disease prediction
    Compatible with existing API
    """
    if patient_context is None:
        patient_context = {}
    
    predictor = DiseasePredictorSQL()
    return predictor.predict_diseases_professional(symptoms, patient_context)


def get_disease_by_name(disease_name: str) -> Dict:
    """
    Get detailed information about a specific disease
    """
    db = get_db_session()
    try:
        disease = db.query(Disease).filter(Disease.name.ilike(f'%{disease_name}%')).first()
        
        if disease:
            return {
                'name': disease.name,
                'description': disease.description,
                'severity': disease.severity,
                'prevalence': disease.prevalence,
                'treatment': disease.treatment,
                'when_to_see_doctor': disease.when_to_see_doctor,
                'complications': disease.complications,
                'prevention': disease.prevention
            }
        return None
    finally:
        db.close()


def get_all_symptoms() -> List[str]:
    """
    Get list of all recognized symptoms
    """
    db = get_db_session()
    try:
        symptoms = db.query(Symptom.name).all()
        return [s[0] for s in symptoms]
    finally:
        db.close()


if __name__ == "__main__":
    # Test the SQL-based predictor
    print("🧪 Testing SQL Disease Predictor\n")
    
    test_symptoms = ["fever", "headache", "cough", "sore throat"]
    test_context = {
        'age': 35,
        'gender': 'male',
        'chronic_conditions': []
    }
    
    print(f"Test Symptoms: {test_symptoms}")
    print(f"Patient Context: {test_context}\n")
    
    predictor = DiseasePredictorSQL()
    results = predictor.predict_diseases_professional(test_symptoms, test_context)
    
    print("Predictions:")
    print("-" * 70)
    for i, pred in enumerate(results, 1):
        print(f"{i}. {pred['condition']} - {pred['probability']}%")
        print(f"   Severity: {pred['severity']}")
        print(f"   Matched Symptoms: {pred['matched_symptoms']}")
        print()
