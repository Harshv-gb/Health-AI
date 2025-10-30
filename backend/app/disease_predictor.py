# disease_predictor.py - Professional-grade disease prediction with probability scoring
import json
import csv
import numpy as np
from collections import defaultdict
from typing import Dict, List, Tuple
import os

class ProfessionalDiseasePredictor:
    """
    Advanced disease prediction system that provides:
    - Multiple disease possibilities with probabilities
    - Symptom matching confidence scores
    - Severity-based adjustments
    - Age and demographic factors
    - Professional medical reasoning
    """
    
    def __init__(self):
        """Initialize the disease prediction system"""
        self.diseases = {}
        self.symptom_disease_map = defaultdict(list)
        self.symptom_weights = {}
        
        # Load medical databases
        self._load_disease_knowledge_base()
        self._load_symptom_disease_mapping()
        self._build_symptom_index()
        
        # Define symptom severity multipliers
        self.severity_multipliers = {
            "mild": 0.7,
            "moderate": 1.0,
            "severe": 1.4,
            "intense": 1.5,
            "extreme": 1.6,
            "unbearable": 1.7
        }
        
        # Disease prevalence multipliers (more common = higher multiplier)
        self.prevalence_multipliers = {
            "Very Common": 2.0,  # Increased from 1.5
            "Common": 1.5,       # Increased from 1.2
            "Seasonal": 1.3,     # Increased from 1.1
            "Pandemic": 1.3,
            "Moderate": 1.0,
            "Rare": 0.6,         # Decreased from 0.7
            "Very Rare": 0.3     # Decreased from 0.5
        }
        
        # Common symptom patterns that should prioritize specific diseases
        self.common_patterns = {
            ("fever", "cough"): ["Common Cold", "Influenza (Flu)", "COVID-19", "Bronchitis"],
            ("fever", "headache"): ["Influenza (Flu)", "Common Cold", "Tension Headache", "Migraine"],
            ("runny nose", "sneezing"): ["Common Cold", "Allergic Rhinitis"],
            ("sore throat", "fever"): ["Common Cold", "Influenza (Flu)", "Tonsillitis"],
            ("headache", "fever"): ["Influenza (Flu)", "Common Cold", "Tension Headache"],
            ("cough", "sore throat"): ["Common Cold", "Bronchitis", "Influenza (Flu)"],
            ("body ache", "fever"): ["Influenza (Flu)", "Common Cold"],
            ("fatigue", "fever"): ["Influenza (Flu)", "Common Cold", "COVID-19"],
            ("headache", "nausea"): ["Migraine", "Tension Headache"],
            ("chest pain", "shortness of breath"): ["Heart Attack", "Angina", "Pneumonia"],
        }
        
        # Age risk factors for diseases
        self.age_risk_factors = {
            "0-12": ["Common Cold", "Influenza (Flu)", "Asthma", "Type 1 Diabetes"],
            "13-25": ["Migraine", "Type 1 Diabetes", "PCOS", "IBS"],
            "26-40": ["Migraine", "IBS", "PCOS", "Multiple Sclerosis", "Crohn's Disease"],
            "41-60": ["Hypertension", "Type 2 Diabetes", "Rheumatoid Arthritis", "Gout"],
            "61+": ["Hypertension", "Type 2 Diabetes", "Heart Failure", "Stroke", "Alzheimer's Disease", "Osteoporosis"]
        }
        
        # Critical symptom indicators (increase probability significantly)
        self.critical_symptoms = {
            "chest pain": ["Heart Attack", "Angina", "Pneumonia"],
            "severe chest pain": ["Heart Attack"],
            "shortness of breath": ["Pneumonia", "Asthma", "COPD", "Heart Failure", "Heart Attack"],
            "slurred speech": ["Stroke"],
            "facial drooping": ["Stroke"],
            "sudden weakness": ["Stroke"],
            "severe headache": ["Stroke", "Migraine"],
            "loss of consciousness": ["Epilepsy", "Stroke"],
            "seizures": ["Epilepsy"],
            "coughing blood": ["Tuberculosis", "Pneumonia"],
            "blood in urine": ["Kidney Stones", "UTI"],
            "severe abdominal pain": ["Appendicitis", "Gallstones"],
            "jaundice": ["Hepatitis", "Cirrhosis", "Gallstones"]
        }
    
    def _load_disease_knowledge_base(self):
        """Load disease information from JSON knowledge base"""
        try:
            config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config", "disease_knowledge_base.json")
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.disease_knowledge = data.get("disease_database", {})
                print(f"✅ Loaded {len(self.disease_knowledge)} diseases from knowledge base")
        except Exception as e:
            print(f"⚠️ Could not load disease knowledge base: {e}")
            self.disease_knowledge = {}
    
    def _load_symptom_disease_mapping(self):
        """Load comprehensive symptom-disease mapping from CSV"""
        try:
            csv_path = os.path.join(os.path.dirname(__file__), "..", "..", "data", "comprehensive_symptom_disease_mapping.csv")
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    condition = row['condition']
                    
                    # Parse primary symptoms
                    primary_symptoms = [s.strip() for s in row['primary_symptoms'].split(',')]
                    # Parse secondary symptoms
                    secondary_symptoms = [s.strip() for s in row.get('secondary_symptoms', '').split(',') if s.strip()]
                    
                    self.diseases[condition] = {
                        'name': condition,
                        'primary_symptoms': primary_symptoms,
                        'secondary_symptoms': secondary_symptoms,
                        'all_symptoms': primary_symptoms + secondary_symptoms,
                        'department': row.get('department', 'General Medicine'),
                        'severity': row.get('severity', 'GP'),
                        'description': row.get('description', ''),
                        'age_group': row.get('common_age_group', 'All ages'),
                        'prevalence': row.get('prevalence', 'Common')
                    }
                    
                print(f"✅ Loaded {len(self.diseases)} conditions from CSV mapping")
        except Exception as e:
            print(f"⚠️ Could not load symptom-disease mapping: {e}")
    
    def _build_symptom_index(self):
        """Build reverse index: symptom -> list of diseases"""
        for disease_name, disease_info in self.diseases.items():
            # Primary symptoms get higher weight
            for symptom in disease_info['primary_symptoms']:
                symptom_lower = symptom.lower()
                self.symptom_disease_map[symptom_lower].append({
                    'disease': disease_name,
                    'weight': 2.0,  # Primary symptoms are more important
                    'type': 'primary'
                })
            
            # Secondary symptoms get lower weight
            for symptom in disease_info['secondary_symptoms']:
                symptom_lower = symptom.lower()
                self.symptom_disease_map[symptom_lower].append({
                    'disease': disease_name,
                    'weight': 1.0,  # Secondary symptoms
                    'type': 'secondary'
                })
        
        print(f"✅ Built symptom index with {len(self.symptom_disease_map)} unique symptoms")
    
    def _extract_severity_from_text(self, text: str) -> float:
        """Extract severity multiplier from symptom description"""
        text_lower = text.lower()
        multiplier = 1.0
        
        for severity_word, mult in self.severity_multipliers.items():
            if severity_word in text_lower:
                multiplier = max(multiplier, mult)
        
        return multiplier
    
    def _get_age_group(self, age: int) -> str:
        """Determine age group from age"""
        if age <= 12:
            return "0-12"
        elif age <= 25:
            return "13-25"
        elif age <= 40:
            return "26-40"
        elif age <= 60:
            return "41-60"
        else:
            return "61+"
    
    def _fuzzy_symptom_match(self, input_symptom: str, symptom_list: List[str]) -> Tuple[str, float]:
        """
        Fuzzy match input symptom against known symptoms
        Returns: (matched_symptom, confidence_score)
        """
        input_lower = input_symptom.lower()
        input_words = set(input_lower.split())
        
        best_match = None
        best_score = 0.0
        
        for known_symptom in symptom_list:
            known_lower = known_symptom.lower()
            known_words = set(known_lower.split())
            
            # Exact match
            if input_lower == known_lower:
                return known_symptom, 1.0
            
            # Substring match
            if input_lower in known_lower or known_lower in input_lower:
                score = 0.9
                if score > best_score:
                    best_score = score
                    best_match = known_symptom
            
            # Word overlap
            if input_words and known_words:
                overlap = len(input_words.intersection(known_words))
                total = len(input_words.union(known_words))
                if total > 0:
                    score = overlap / total * 0.8
                    if score > best_score:
                        best_score = score
                        best_match = known_symptom
        
        return best_match, best_score
    
    def predict_diseases(self, symptoms: List[str], patient_context: Dict = None) -> Dict:
        """
        Professional disease prediction with probabilities
        
        Args:
            symptoms: List of symptom strings
            patient_context: Dict with 'age', 'gender', 'chronic_conditions', etc.
        
        Returns:
            Dict with disease predictions, probabilities, and analysis
        """
        if not symptoms:
            return {
                "predictions": [],
                "message": "No symptoms provided for analysis"
            }
        
        if not patient_context:
            patient_context = {}
        
        age = patient_context.get('age', 30)
        gender = patient_context.get('gender', 'unknown')
        chronic_conditions = patient_context.get('chronic_conditions', [])
        
        # Score accumulator for each disease
        disease_scores = defaultdict(lambda: {
            'score': 0.0,
            'matched_symptoms': [],
            'matched_primary': 0,
            'matched_secondary': 0,
            'total_possible_primary': 0,
            'total_possible_secondary': 0,
            'severity_adjustment': 1.0,
            'age_adjustment': 1.0,
            'critical_match': False
        })
        
        # Get all known symptoms for fuzzy matching
        all_known_symptoms = list(self.symptom_disease_map.keys())
        
        # Analyze each input symptom
        for symptom in symptoms:
            if not symptom or symptom.strip() == "":
                continue
            
            # Extract severity from symptom text
            severity_multiplier = self._extract_severity_from_text(symptom)
            
            # Fuzzy match to known symptoms
            matched_symptom, confidence = self._fuzzy_symptom_match(symptom, all_known_symptoms)
            
            if matched_symptom and confidence > 0.5:
                # Get diseases associated with this symptom
                disease_links = self.symptom_disease_map[matched_symptom]
                
                for link in disease_links:
                    disease_name = link['disease']
                    weight = link['weight']
                    symptom_type = link['type']
                    
                    # Calculate symptom contribution
                    contribution = weight * confidence * severity_multiplier
                    
                    disease_scores[disease_name]['score'] += contribution
                    disease_scores[disease_name]['matched_symptoms'].append({
                        'input': symptom,
                        'matched': matched_symptom,
                        'confidence': confidence,
                        'type': symptom_type,
                        'severity_multiplier': severity_multiplier
                    })
                    
                    if symptom_type == 'primary':
                        disease_scores[disease_name]['matched_primary'] += 1
                    else:
                        disease_scores[disease_name]['matched_secondary'] += 1
                    
                    disease_scores[disease_name]['severity_adjustment'] = max(
                        disease_scores[disease_name]['severity_adjustment'],
                        severity_multiplier
                    )
                
                # Check for critical symptoms
                symptom_lower = symptom.lower()
                for critical_symptom, critical_diseases in self.critical_symptoms.items():
                    if critical_symptom in symptom_lower:
                        for disease_name in critical_diseases:
                            if disease_name in disease_scores:
                                disease_scores[disease_name]['critical_match'] = True
                                disease_scores[disease_name]['score'] *= 1.5  # Boost score significantly
        
        # Calculate total possible symptoms for each disease
        for disease_name, scores in disease_scores.items():
            if disease_name in self.diseases:
                disease_info = self.diseases[disease_name]
                scores['total_possible_primary'] = len(disease_info['primary_symptoms'])
                scores['total_possible_secondary'] = len(disease_info['secondary_symptoms'])
        
        # Apply age-based adjustments
        age_group = self._get_age_group(age)
        age_related_diseases = self.age_risk_factors.get(age_group, [])
        
        for disease_name in disease_scores:
            if disease_name in age_related_diseases:
                disease_scores[disease_name]['age_adjustment'] = 1.2
                disease_scores[disease_name]['score'] *= 1.2
        
        # Apply prevalence-based adjustments (favor more common diseases)
        for disease_name in disease_scores:
            if disease_name in self.diseases:
                prevalence = self.diseases[disease_name].get('prevalence', 'Common')
                prevalence_multiplier = self.prevalence_multipliers.get(prevalence, 1.0)
                disease_scores[disease_name]['prevalence_adjustment'] = prevalence_multiplier
                disease_scores[disease_name]['score'] *= prevalence_multiplier
        
        # Apply common symptom pattern boosts
        symptom_set = set([s.lower().strip() for s in symptoms])
        for pattern_symptoms, boosted_diseases in self.common_patterns.items():
            # Check if the pattern symptoms are present in user's symptoms
            pattern_match = all(
                any(pattern_symptom in user_symptom for user_symptom in symptom_set)
                for pattern_symptom in pattern_symptoms
            )
            
            if pattern_match:
                for disease_name in boosted_diseases:
                    if disease_name in disease_scores:
                        # Boost common diseases that match typical patterns
                        disease_scores[disease_name]['score'] *= 2.5  # Increased from 1.8
                        disease_scores[disease_name]['pattern_boost'] = True
        
        # Apply chronic condition adjustments
        if chronic_conditions:
            chronic_disease_boost = {
                "diabetes": ["Type 2 Diabetes", "Type 1 Diabetes", "Chronic Kidney Disease", "Heart Attack", "Stroke"],
                "hypertension": ["Hypertension", "Heart Attack", "Stroke", "Chronic Kidney Disease", "Heart Failure"],
                "high blood pressure": ["Hypertension", "Heart Attack", "Stroke", "Chronic Kidney Disease"],
                "asthma": ["Asthma", "COPD", "Bronchitis", "Pneumonia"],
                "heart disease": ["Heart Attack", "Angina", "Heart Failure", "Arrhythmia"],
                "kidney": ["Chronic Kidney Disease", "Kidney Stones", "UTI"],
                "thyroid": ["Hyperthyroidism", "Hypothyroidism"],
                "arthritis": ["Rheumatoid Arthritis", "Osteoarthritis", "Gout"],
            }
            
            for condition in chronic_conditions:
                condition_lower = condition.lower()
                for condition_keyword, related_diseases in chronic_disease_boost.items():
                    if condition_keyword in condition_lower:
                        for disease_name in related_diseases:
                            if disease_name in disease_scores:
                                # Boost diseases related to chronic conditions
                                disease_scores[disease_name]['score'] *= 1.6
                                disease_scores[disease_name]['chronic_condition_boost'] = True
        
        # Calculate probabilities
        predictions = []
        total_score = sum(scores['score'] for scores in disease_scores.values())
        
        if total_score == 0:
            return {
                "predictions": [],
                "message": "Unable to match symptoms to known conditions. Please consult a healthcare professional.",
                "input_symptoms": symptoms
            }
        
        for disease_name, scores in disease_scores.items():
            if disease_name not in self.diseases:
                continue
            
            disease_info = self.diseases[disease_name]
            
            # Calculate probability
            raw_probability = (scores['score'] / total_score) * 100
            
            # Calculate confidence based on symptom match quality
            if scores['total_possible_primary'] > 0:
                primary_match_ratio = scores['matched_primary'] / scores['total_possible_primary']
            else:
                primary_match_ratio = 0
            
            confidence_score = (
                primary_match_ratio * 0.6 +  # Primary symptoms are most important
                (len(scores['matched_symptoms']) / max(len(symptoms), 1)) * 0.4  # Overall match coverage
            ) * 100
            
            # Adjust for critical symptoms
            if scores['critical_match']:
                raw_probability *= 1.3
                confidence_score = min(confidence_score * 1.2, 95)
            
            # Normalize probability (cap at reasonable values)
            probability = min(raw_probability, 95)
            
            # Only include diseases with reasonable probability
            if probability >= 5:  # At least 5% probability
                prediction = {
                    'disease': disease_name,
                    'probability': round(probability, 1),
                    'confidence': round(confidence_score, 1),
                    'department': disease_info['department'],
                    'severity': disease_info['severity'],
                    'description': disease_info['description'],
                    'matched_symptoms': len(scores['matched_symptoms']),
                    'total_symptoms': len(disease_info['all_symptoms']),
                    'primary_symptoms_matched': scores['matched_primary'],
                    'secondary_symptoms_matched': scores['matched_secondary'],
                    'has_critical_symptoms': scores['critical_match'],
                    'age_related': disease_name in age_related_diseases,
                    'symptom_details': scores['matched_symptoms']
                }
                
                # Add additional information from knowledge base
                if disease_name in self.disease_knowledge:
                    kb_info = self.disease_knowledge[disease_name]
                    prediction['treatment_info'] = kb_info.get('treatment', [])
                    prediction['when_to_see_doctor'] = kb_info.get('when_to_see_doctor', '')
                    prediction['duration'] = kb_info.get('duration', '')
                
                predictions.append(prediction)
        
        # Sort by probability (descending)
        predictions.sort(key=lambda x: x['probability'], reverse=True)
        
        # Take top 5 predictions
        top_predictions = predictions[:5]
        
        # Generate professional analysis
        analysis = self._generate_professional_analysis(top_predictions, symptoms, patient_context)
        
        return {
            "predictions": top_predictions,
            "analysis": analysis,
            "total_conditions_analyzed": len(self.diseases),
            "symptoms_provided": len(symptoms),
            "input_symptoms": symptoms,
            "patient_context": patient_context
        }
    
    def _generate_professional_analysis(self, predictions: List[Dict], symptoms: List[str], patient_context: Dict) -> Dict:
        """Generate professional medical analysis"""
        if not predictions:
            return {
                "summary": "No clear diagnosis could be determined from the provided symptoms.",
                "recommendation": "Please consult a healthcare professional for proper evaluation."
            }
        
        top_prediction = predictions[0]
        
        # Determine urgency
        urgency_map = {
            "emergency": "IMMEDIATE MEDICAL ATTENTION REQUIRED",
            "urgent": "Seek medical care within 24 hours",
            "GP": "Schedule appointment with primary care physician",
            "self-care": "Monitor symptoms, self-care measures may be sufficient"
        }
        
        urgency = urgency_map.get(top_prediction['severity'], "Consult healthcare professional")
        
        # Build summary
        if len(predictions) == 1:
            summary = f"Based on symptom analysis, {top_prediction['disease']} is the most likely condition ({top_prediction['probability']}% probability)."
        else:
            summary = f"Differential diagnosis suggests {top_prediction['disease']} ({top_prediction['probability']}% probability) as the primary concern. "
            summary += f"Other possibilities include {predictions[1]['disease']} ({predictions[1]['probability']}% probability)"
            if len(predictions) > 2:
                summary += f" and {predictions[2]['disease']} ({predictions[2]['probability']}% probability)."
            else:
                summary += "."
        
        # Symptom match analysis
        symptom_analysis = f"Matched {top_prediction['matched_symptoms']} out of {len(symptoms)} reported symptoms. "
        if top_prediction['has_critical_symptoms']:
            symptom_analysis += "⚠️ Critical symptoms detected that require prompt medical attention. "
        
        # Age-related notes
        age_note = ""
        if top_prediction.get('age_related'):
            age = patient_context.get('age', '')
            age_note = f"This condition is commonly seen in your age group{f' ({age} years)' if age else ''}. "
        
        return {
            "summary": summary,
            "urgency": urgency,
            "urgency_level": top_prediction['severity'],
            "department": top_prediction['department'],
            "symptom_analysis": symptom_analysis,
            "age_note": age_note,
            "recommendation": f"Recommended department: {top_prediction['department']}. {urgency}",
            "confidence_level": "High" if top_prediction['confidence'] >= 70 else "Moderate" if top_prediction['confidence'] >= 50 else "Low",
            "next_steps": top_prediction.get('when_to_see_doctor', 'Consult with healthcare professional for proper diagnosis and treatment plan.')
        }

# Global instance
_predictor_instance = None

def get_disease_predictor():
    """Get or create disease predictor instance"""
    global _predictor_instance
    if _predictor_instance is None:
        _predictor_instance = ProfessionalDiseasePredictor()
    return _predictor_instance

def predict_diseases_professional(symptoms: List[str], patient_context: Dict = None) -> Dict:
    """
    Main function to predict diseases with professional-grade analysis
    
    Args:
        symptoms: List of symptom strings
        patient_context: Optional dict with patient information (age, gender, etc.)
    
    Returns:
        Dict with predictions and professional analysis
    """
    predictor = get_disease_predictor()
    return predictor.predict_diseases(symptoms, patient_context)
