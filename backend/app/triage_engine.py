# triage_engine.py - AI-powered medical triage system
import json
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import pickle
import os
from typing import Dict, List, Tuple
import warnings
warnings.filterwarnings('ignore')

class AITriageEngine:
    def __init__(self):
        """Initialize the AI-powered triage engine"""
        self.triage_model = None
        self.vectorizer = None
        self.urgency_levels = {
            0: "self-care",
            1: "GP", 
            2: "urgent",
            3: "emergency"
        }
        
        # Load medical knowledge base
        self._load_medical_data()
        
        # Try to load pre-trained model, otherwise train new one
        self._load_or_train_model()
        
        # Risk factors and weights
        self.risk_factors = {
            "age_risk": {"high": 0.3, "medium": 0.1, "low": 0.0},
            "chronic_conditions": {"yes": 0.2, "no": 0.0},
            "severity_multiplier": {"mild": 1.0, "moderate": 1.5, "severe": 2.0},
            "symptom_combinations": self._define_symptom_combinations()
        }

    def _load_medical_data(self):
        """Load medical knowledge bases"""
        try:
            with open("../../config/conditions_list.json") as f:
                self.conditions = json.load(f)["conditions"]
            
            with open("../../config/red_flags.json") as f:
                self.red_flags = json.load(f)["red_flags"]
                
            with open("../../config/symptom_lexicon.json") as f:
                self.symptom_lexicon = json.load(f)["symptom_lexicon"]
        except FileNotFoundError:
            # Fallback data if files not found
            self.conditions = []
            self.red_flags = []
            self.symptom_lexicon = {}

    def _define_symptom_combinations(self) -> Dict:
        """Define dangerous symptom combinations"""
        return {
            "cardiac_emergency": {
                "symptoms": ["chest pain", "shortness of breath", "sweating", "nausea"],
                "risk_score": 3.0,
                "urgency": "emergency"
            },
            "stroke_indicators": {
                "symptoms": ["sudden weakness on one side", "slurred speech", "confusion"],
                "risk_score": 3.0,
                "urgency": "emergency"
            },
            "respiratory_distress": {
                "symptoms": ["severe shortness of breath", "chest tightness", "wheezing"],
                "risk_score": 2.5,
                "urgency": "urgent"
            },
            "severe_infection": {
                "symptoms": ["high fever", "severe fatigue", "confusion", "rapid heartbeat"],
                "risk_score": 2.0,
                "urgency": "urgent"
            },
            "neurological_concern": {
                "symptoms": ["severe headache", "vision problems", "confusion", "seizure"],
                "risk_score": 2.5,
                "urgency": "urgent"
            }
        }

    def _generate_training_data(self) -> Tuple[List[str], List[int]]:
        """Generate training data for the triage model"""
        texts = []
        labels = []
        
        # Generate data from conditions
        for condition in self.conditions:
            severity_map = {
                "self-care": 0,
                "GP": 1,
                "urgent": 2,
                "emergency": 3
            }
            
            # Create training examples
            symptoms_text = " ".join(condition["symptoms"])
            texts.append(symptoms_text)
            labels.append(severity_map.get(condition["severity"], 1))
            
            # Add variations with different severity descriptors
            for severity_word in ["mild", "moderate", "severe"]:
                modified_text = f"{severity_word} {symptoms_text}"
                texts.append(modified_text)
                # Adjust label based on severity
                base_label = severity_map.get(condition["severity"], 1)
                if severity_word == "severe":
                    labels.append(min(base_label + 1, 3))
                elif severity_word == "mild":
                    labels.append(max(base_label - 1, 0))
                else:
                    labels.append(base_label)
        
        # Add red flag scenarios
        for red_flag in self.red_flags:
            symptoms_text = " ".join(red_flag.get("trigger_symptoms", []))
            texts.append(symptoms_text)
            labels.append(3)  # Emergency
        
        # Add common mild scenarios
        mild_scenarios = [
            "runny nose sneezing",
            "mild headache fatigue",
            "slight cough throat irritation",
            "minor stomach ache"
        ]
        for scenario in mild_scenarios:
            texts.append(scenario)
            labels.append(0)  # Self-care
        
        return texts, labels

    def _load_or_train_model(self):
        """Load existing model or train new one"""
        model_path = "triage_model.pkl"
        vectorizer_path = "triage_vectorizer.pkl"
        
        if os.path.exists(model_path) and os.path.exists(vectorizer_path):
            try:
                with open(model_path, 'rb') as f:
                    self.triage_model = pickle.load(f)
                with open(vectorizer_path, 'rb') as f:
                    self.vectorizer = pickle.load(f)
                print("Loaded pre-trained triage model")
                return
            except Exception as e:
                print(f"Error loading model: {e}")
        
        # Train new model
        print("Training new triage model...")
        self._train_model()

    def _train_model(self):
        """Train the triage classification model"""
        # Generate training data
        texts, labels = self._generate_training_data()
        
        if not texts:
            print("No training data available")
            return
        
        # Vectorize text data
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2)
        )
        
        X = self.vectorizer.fit_transform(texts)
        y = np.array(labels)
        
        # Train model
        self.triage_model = RandomForestClassifier(
            n_estimators=100,
            random_state=42,
            class_weight='balanced'
        )
        
        # Split data for evaluation
        if len(texts) > 10:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42, stratify=y
            )
            
            self.triage_model.fit(X_train, y_train)
            
            # Evaluate model
            y_pred = self.triage_model.predict(X_test)
            print("Model Performance:")
            print(classification_report(y_test, y_pred, 
                                      target_names=list(self.urgency_levels.values())))
        else:
            self.triage_model.fit(X, y)
        
        # Save model
        try:
            with open("triage_model.pkl", 'wb') as f:
                pickle.dump(self.triage_model, f)
            with open("triage_vectorizer.pkl", 'wb') as f:
                pickle.dump(self.vectorizer, f)
            print("Model saved successfully")
        except Exception as e:
            print(f"Error saving model: {e}")

    def intelligent_triage(self, symptoms: List[str], patient_context: Dict = None) -> Dict:
        """
        Perform intelligent triage assessment using AI
        """
        # Temporarily use fallback logic for better medical accuracy
        # The ML model needs retraining with proper medical data
        return self._fallback_triage(symptoms)
        
        # Original ML logic (commented out until model is retrained)
        """
        if not self.triage_model or not self.vectorizer:
            return self._fallback_triage(symptoms)
        
        # Prepare input text
        symptoms_text = " ".join(symptoms)
        
        try:
            # Vectorize input
            X = self.vectorizer.transform([symptoms_text])
            
            # Get prediction and probability
            urgency_pred = self.triage_model.predict(X)[0]
            urgency_proba = self.triage_model.predict_proba(X)[0]
            
            # Get base assessment
            base_urgency = self.urgency_levels[urgency_pred]
            confidence = max(urgency_proba)
            
            # Apply additional risk factors
            risk_adjusted_urgency, risk_factors = self._apply_risk_factors(
                base_urgency, symptoms, patient_context
            )
            
            # Check for dangerous symptom combinations
            combination_risk = self._check_symptom_combinations(symptoms)
            
            # Final urgency determination
            final_urgency = self._determine_final_urgency(
                risk_adjusted_urgency, combination_risk
            )
            
            # Generate detailed assessment
            assessment = self._generate_assessment(
                symptoms, final_urgency, risk_factors, combination_risk, confidence
            )
            
            return {
                "urgency_level": final_urgency,
                "confidence": float(confidence),
                "base_ml_prediction": base_urgency,
                "risk_adjusted_prediction": risk_adjusted_urgency,
                "risk_factors": risk_factors,
                "symptom_combinations": combination_risk,
                "assessment": assessment,
                "recommendations": self._get_recommendations(final_urgency),
                "follow_up_questions": self._generate_follow_up_questions(symptoms)
            }
            
        except Exception as e:
            print(f"Error in ML triage: {e}")
            return self._fallback_triage(symptoms)
        """

    def _apply_risk_factors(self, base_urgency: str, symptoms: List[str], 
                          patient_context: Dict = None) -> Tuple[str, Dict]:
        """Apply risk factors to adjust urgency level"""
        risk_score = 0.0
        applied_factors = {}
        
        if not patient_context:
            patient_context = {}
        
        # Age risk
        age = patient_context.get("age", 30)
        if age > 65:
            risk_score += self.risk_factors["age_risk"]["high"]
            applied_factors["age"] = "high_risk"
        elif age > 45:
            risk_score += self.risk_factors["age_risk"]["medium"]
            applied_factors["age"] = "medium_risk"
        
        # Chronic conditions
        if patient_context.get("chronic_conditions"):
            risk_score += self.risk_factors["chronic_conditions"]["yes"]
            applied_factors["chronic_conditions"] = True
        
        # Severity analysis from symptoms
        severity_indicators = {
            "severe": ["severe", "intense", "unbearable", "extreme"],
            "moderate": ["moderate", "considerable"],
            "mild": ["mild", "slight", "minor"]
        }
        
        detected_severity = "moderate"
        for severity, indicators in severity_indicators.items():
            if any(indicator in " ".join(symptoms).lower() for indicator in indicators):
                detected_severity = severity
                break
        
        risk_score *= self.risk_factors["severity_multiplier"][detected_severity]
        applied_factors["severity"] = detected_severity
        
        # Adjust urgency based on risk score
        urgency_map = ["self-care", "GP", "urgent", "emergency"]
        current_index = urgency_map.index(base_urgency)
        
        if risk_score > 1.5:
            adjusted_index = min(current_index + 2, 3)
        elif risk_score > 1.0:
            adjusted_index = min(current_index + 1, 3)
        else:
            adjusted_index = current_index
        
        return urgency_map[adjusted_index], applied_factors

    def _check_symptom_combinations(self, symptoms: List[str]) -> Dict:
        """Check for dangerous symptom combinations"""
        combination_alerts = {}
        
        for combo_name, combo_data in self.risk_factors["symptom_combinations"].items():
            combo_symptoms = combo_data["symptoms"]
            matches = sum(1 for symptom in symptoms 
                         if any(combo_symptom.lower() in symptom.lower() 
                               for combo_symptom in combo_symptoms))
            
            match_ratio = matches / len(combo_symptoms)
            if match_ratio >= 0.5:  # At least 50% of symptoms match
                combination_alerts[combo_name] = {
                    "match_ratio": match_ratio,
                    "risk_score": combo_data["risk_score"],
                    "urgency": combo_data["urgency"],
                    "matched_symptoms": matches
                }
        
        return combination_alerts

    def _determine_final_urgency(self, risk_adjusted_urgency: str, 
                               combination_risk: Dict) -> str:
        """Determine final urgency level"""
        urgency_levels = ["self-care", "GP", "urgent", "emergency"]
        
        # Start with risk-adjusted urgency
        current_urgency = risk_adjusted_urgency
        
        # Check combination risks
        for combo_name, combo_data in combination_risk.items():
            combo_urgency = combo_data["urgency"]
            if urgency_levels.index(combo_urgency) > urgency_levels.index(current_urgency):
                current_urgency = combo_urgency
        
        return current_urgency

    def _generate_assessment(self, symptoms: List[str], urgency: str, 
                           risk_factors: Dict, combination_risk: Dict, 
                           confidence: float) -> str:
        """Generate detailed assessment text"""
        assessment_parts = []
        
        # Base assessment
        assessment_parts.append(f"Based on the symptoms provided, the recommended care level is: {urgency.upper()}")
        
        # Confidence
        if confidence > 0.8:
            assessment_parts.append("This assessment has high confidence.")
        elif confidence > 0.6:
            assessment_parts.append("This assessment has moderate confidence.")
        else:
            assessment_parts.append("This assessment has lower confidence - please provide more details.")
        
        # Risk factors
        if risk_factors:
            risk_text = "Risk factors considered: "
            factors = []
            if "age" in risk_factors:
                factors.append(f"age category ({risk_factors['age']})")
            if risk_factors.get("chronic_conditions"):
                factors.append("existing chronic conditions")
            if "severity" in risk_factors:
                factors.append(f"symptom severity ({risk_factors['severity']})")
            
            if factors:
                risk_text += ", ".join(factors)
                assessment_parts.append(risk_text)
        
        # Combination alerts
        if combination_risk:
            alert_text = "⚠️ Important: The combination of symptoms suggests possible serious conditions. "
            high_risk_combos = [name for name, data in combination_risk.items() 
                              if data["urgency"] in ["urgent", "emergency"]]
            if high_risk_combos:
                alert_text += f"Specific concerns: {', '.join(high_risk_combos).replace('_', ' ')}"
            assessment_parts.append(alert_text)
        
        return " ".join(assessment_parts)

    def _get_recommendations(self, urgency: str) -> List[str]:
        """Get recommendations based on urgency level"""
        recommendations = {
            "self-care": [
                "Monitor symptoms and rest",
                "Stay hydrated",
                "Consider over-the-counter remedies if appropriate",
                "Seek medical advice if symptoms worsen or persist >48-72 hours"
            ],
            "GP": [
                "Schedule an appointment with your general practitioner",
                "Monitor symptoms closely",
                "Seek urgent care if symptoms worsen significantly",
                "Keep a symptom diary"
            ],
            "urgent": [
                "Seek medical attention within 2-4 hours",
                "Go to urgent care or contact your doctor immediately",
                "Do not delay seeking medical care",
                "Have someone accompany you if possible"
            ],
            "emergency": [
                "🚨 SEEK IMMEDIATE EMERGENCY CARE",
                "Call emergency services or go to ER immediately",
                "Do not drive yourself",
                "Inform medical staff of all symptoms immediately"
            ]
        }
        
        return recommendations.get(urgency, recommendations["GP"])

    def _generate_follow_up_questions(self, symptoms: List[str]) -> List[str]:
        """Generate relevant follow-up questions"""
        questions = []
        
        # General questions
        questions.extend([
            "How long have you been experiencing these symptoms?",
            "Have the symptoms gotten better, worse, or stayed the same?",
            "Are you currently taking any medications?"
        ])
        
        # Symptom-specific questions
        if any("pain" in symptom.lower() for symptom in symptoms):
            questions.append("On a scale of 1-10, how would you rate the pain intensity?")
        
        if any("fever" in symptom.lower() for symptom in symptoms):
            questions.append("What is your current temperature if measured?")
        
        if any("headache" in symptom.lower() for symptom in symptoms):
            questions.append("Is this different from your usual headaches?")
        
        return questions[:5]  # Limit to 5 questions

    def _fallback_triage(self, symptoms: List[str]) -> Dict:
        """Fallback triage when ML model is not available"""
        symptoms_text = " ".join(symptoms).lower()
        
        # Emergency symptoms - require immediate medical attention
        emergency_symptoms = ["chest pain", "shortness of breath", "severe headache", "loss of consciousness", 
                            "severe bleeding", "heart attack", "stroke", "difficulty breathing"]
        
        # Urgent symptoms - need medical attention within hours
        urgent_symptoms = ["high fever", "severe pain", "difficulty breathing", "persistent vomiting",
                         "severe abdominal pain", "rapid heartbeat", "dizziness with chest pain"]
        
        # Common illness symptoms - need GP consultation
        gp_symptoms = ["fever", "cough", "cold", "flu", "sore throat", "headache", "body ache",
                     "nausea", "diarrhea", "stomach pain", "runny nose", "congestion", "fatigue"]
        
        # Check for emergency conditions
        if any(emergency in symptoms_text for emergency in emergency_symptoms):
            urgency = "emergency"
            assessment = "Emergency symptoms detected. Seek immediate medical attention."
        
        # Check for urgent conditions  
        elif any(urgent in symptoms_text for urgent in urgent_symptoms):
            urgency = "urgent"
            assessment = "Urgent symptoms detected. Medical attention needed within few hours."
        
        # Check for common illness symptoms
        elif any(gp_symptom in symptoms_text for gp_symptom in gp_symptoms):
            urgency = "GP"
            assessment = "Common illness symptoms detected. Consult with a general practitioner."
            
            # Special handling for fever combinations
            if "fever" in symptoms_text:
                if any(combo in symptoms_text for combo in ["cough", "cold", "sore throat", "body ache"]):
                    urgency = "GP"
                    assessment = "Flu-like symptoms with fever detected. GP consultation recommended."
        
        # Multiple symptoms or unclear case
        elif len(symptoms) > 3:
            urgency = "GP"
            assessment = "Multiple symptoms detected. GP consultation recommended for proper diagnosis."
        
        # Minor or single symptoms
        else:
            urgency = "self-care"
            assessment = "Minor symptoms detected. Self-care measures may be sufficient, but monitor closely."

        # Add potential conditions based on symptoms
        potential_conditions = self._identify_potential_conditions(symptoms_text)
        
        # Generate detailed medical notes
        medical_notes = self._generate_medical_notes(symptoms, potential_conditions, urgency)
        
        return {
            "urgency": urgency,
            "urgency_level": urgency,
            "confidence": 0.7,
            "assessment": assessment,
            "potential_conditions": potential_conditions,
            "department": self._get_department_recommendation(potential_conditions),
            "notes": medical_notes,
            "recommendations": self._get_recommendations(urgency),
            "follow_up_questions": self._generate_follow_up_questions(symptoms)
        }

    def _identify_potential_conditions(self, symptoms_text: str) -> List[str]:
        """Identify potential medical conditions based on symptoms"""
        conditions = []
        
        # Common condition patterns - more comprehensive matching
        condition_patterns = {
            "Common Cold": ["cold", "runny nose", "sneezing", "congestion", "stuffy nose", "nasal"],
            "Flu (Influenza)": ["fever", "cough", "body ache", "fatigue", "headache", "chills", "body pain", "muscle ache"],
            "Upper Respiratory Infection": ["cough", "sore throat", "fever", "congestion", "throat", "respiratory"],
            "Gastroenteritis": ["nausea", "diarrhea", "stomach pain", "vomiting", "stomach", "abdominal pain", "upset stomach"],
            "Migraine": ["severe headache", "headache", "nausea", "light sensitivity", "head pain"],
            "Food Poisoning": ["nausea", "vomiting", "diarrhea", "stomach pain", "stomach cramps"],
            "Tension Headache": ["headache", "head pain", "stress", "tension"],
            "Anxiety": ["rapid heartbeat", "dizziness", "shortness of breath", "chest tightness", "anxious", "panic"],
            "Allergic Rhinitis": ["sneezing", "runny nose", "itchy", "watery eyes", "nasal congestion"],
            "Sinusitis": ["sinus", "facial pain", "headache", "congestion", "pressure"],
            "Bronchitis": ["cough", "chest congestion", "mucus", "wheezing"],
            "Viral Infection": ["fever", "fatigue", "body ache", "weakness"],
            "Dehydration": ["dizziness", "fatigue", "dry", "thirst", "weakness"],
            "Indigestion": ["stomach", "bloating", "gas", "discomfort", "heartburn"],
            "Fever": ["fever", "high temperature", "hot", "chills"]
        }
        
        # Count matches for each condition
        condition_scores = {}
        for condition, keywords in condition_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in symptoms_text)
            if matches > 0:
                condition_scores[condition] = matches
        
        # Sort by number of matches and return top matches
        if condition_scores:
            sorted_conditions = sorted(condition_scores.items(), key=lambda x: x[1], reverse=True)
            # Return conditions with at least 1 match, limit to top 3
            conditions = [cond for cond, score in sorted_conditions[:3] if score >= 1]
        
        return conditions if conditions else ["General symptom evaluation"]
    
    def _get_department_recommendation(self, potential_conditions: List[str]) -> str:
        """Recommend appropriate medical department"""
        if not potential_conditions:
            return "General Medicine"
        
        # Department mapping
        department_map = {
            "Common Cold": "General Medicine",
            "Flu": "General Medicine", 
            "Upper Respiratory Infection": "ENT",
            "Gastroenteritis": "Gastroenterology",
            "Migraine": "Neurology",
            "Food Poisoning": "General Medicine",
            "Anxiety": "Psychiatry"
        }
        
        for condition in potential_conditions:
            if condition in department_map:
                return department_map[condition]
        
        return "General Medicine"
    
    def _generate_medical_notes(self, symptoms: List[str], potential_conditions: List[str], urgency: str) -> str:
        """Generate detailed medical analysis notes"""
        # Clean symptoms list - remove technical terms
        clean_symptoms = []
        for symptom in symptoms:
            # Skip if it's a technical placeholder or internal field
            if any(skip in str(symptom).lower() for skip in ['ai_analysis', 'traditional_symptoms', 'risk_assessment', 'recommended_approach']):
                continue
            clean_symptoms.append(str(symptom))
        
        symptoms_text = ", ".join(clean_symptoms) if clean_symptoms else "the reported symptoms"
        
        # Create contextual medical analysis
        if urgency == "emergency":
            notes = f"The combination of symptoms suggests a potentially serious condition requiring immediate medical evaluation. "
            if any("chest" in s.lower() and "pain" in s.lower() for s in clean_symptoms):
                notes += "Chest pain combined with other symptoms can indicate cardiac issues or pulmonary conditions. "
            if any("breathing" in s.lower() or "breath" in s.lower() for s in clean_symptoms):
                notes += "Breathing difficulties require urgent assessment to rule out respiratory or cardiac complications. "
            notes += "Emergency department evaluation is strongly recommended."
            
        elif urgency == "urgent":
            notes = f"The presented symptoms indicate a condition that requires prompt medical attention. "
            if any("fever" in s.lower() for s in clean_symptoms) and any("severe" in s.lower() for s in clean_symptoms):
                notes += "High fever combined with other symptoms may indicate a serious infection. "
            notes += "Medical evaluation within the next few hours is recommended to prevent complications."
            
        elif urgency == "GP":
            notes = "Based on the symptoms presented, consultation with a general practitioner is recommended. "
            
            # Specific condition-based notes
            if potential_conditions:
                if "Flu" in potential_conditions or "Common Cold" in potential_conditions:
                    notes += "These symptoms are typical of viral upper respiratory infections. "
                    if any("fever" in s.lower() for s in clean_symptoms):
                        notes += "The presence of fever suggests an active infection that should be monitored. "
                    notes += "While often self-limiting, medical evaluation can provide appropriate treatment and symptom management."
                    
                elif "Gastroenteritis" in potential_conditions:
                    notes += "Gastrointestinal symptoms may indicate viral or bacterial gastroenteritis. "
                    notes += "Medical evaluation is important to assess hydration status and determine appropriate treatment."
                    
                elif "Migraine" in potential_conditions:
                    notes += "Headache pattern may suggest migraine or tension-type headache. "
                    notes += "Medical evaluation can help establish diagnosis and provide appropriate pain management strategies."
                    
                else:
                    notes += "A medical professional can provide proper diagnosis and treatment recommendations."
            else:
                notes += "Medical evaluation is recommended for proper assessment and treatment guidance."
                
        else:  # self-care
            notes = "The reported symptoms appear to be mild and may be manageable with self-care measures. "
            notes += "However, if symptoms worsen, persist, or new concerning symptoms develop, medical evaluation should be sought. "
            notes += "Monitor symptoms closely and maintain good hydration and rest."
        
        return notes

# Global instance
ai_triage = AITriageEngine()

def perform_ai_triage(symptoms: List[str], patient_context: Dict = None) -> Dict:
    """Convenience function for AI triage"""
    return ai_triage.intelligent_triage(symptoms, patient_context)

if __name__ == "__main__":
    # Test the triage engine
    test_cases = [
        (["chest pain", "shortness of breath"], {"age": 55}),
        (["mild headache", "fatigue"], {"age": 25}),
        (["severe abdominal pain", "vomiting"], {"age": 40}),
        (["runny nose", "sneezing"], {"age": 30})
    ]
    
    for symptoms, context in test_cases:
        print(f"\nTesting: {symptoms}")
        result = perform_ai_triage(symptoms, context)
        print(f"Urgency: {result['urgency_level']}")
        print(f"Confidence: {result['confidence']:.2f}")
        print(f"Assessment: {result['assessment']}")
