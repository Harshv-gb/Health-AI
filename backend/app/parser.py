# parser.py - AI-powered symptom extraction and analysis
import spacy
import re
import json
import os
from typing import List, Dict, Tuple

class AISymptomParser:
    def __init__(self):
        """Initialize the AI-powered symptom parser"""
        try:
            # Try to load spaCy model, download if not available
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spaCy English model...")
            os.system("python -m spacy download en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")
        
        # Load symptom lexicon for reference
        try:
            with open("../../config/symptom_lexicon.json") as f:
                self.symptom_lexicon = json.load(f)["symptom_lexicon"]
        except FileNotFoundError:
            self.symptom_lexicon = {}
        
        # Medical terms and patterns
        self.severity_indicators = {
            "mild": ["mild", "slight", "little", "minor", "light"],
            "moderate": ["moderate", "medium", "average", "normal"],
            "severe": ["severe", "intense", "terrible", "extreme", "unbearable", "very", "really bad"]
        }
        
        self.temporal_indicators = {
            "acute": ["sudden", "suddenly", "immediate", "just started", "just now"],
            "chronic": ["long time", "weeks", "months", "always", "persistent", "ongoing"],
            "intermittent": ["sometimes", "occasionally", "on and off", "comes and goes"]
        }
        
        self.body_parts = [
            "head", "neck", "chest", "stomach", "abdomen", "back", "arm", "leg", 
            "throat", "nose", "eye", "ear", "hand", "foot", "joint", "muscle"
        ]

    def extract_symptoms_with_ai(self, user_text: str) -> Dict:
        """
        Use AI to extract and analyze symptoms from natural language text
        """
        doc = self.nlp(user_text.lower())
        
        result = {
            "extracted_symptoms": [],
            "severity_assessment": {},
            "temporal_patterns": {},
            "affected_areas": [],
            "confidence_scores": {},
            "original_text": user_text,
            "processed_entities": []
        }
        
        # Extract named entities and analyze them
        for ent in doc.ents:
            if ent.label_ in ["SYMPTOM", "DISEASE", "ANATOMY"]:
                result["processed_entities"].append({
                    "text": ent.text,
                    "label": ent.label_,
                    "confidence": 0.8
                })
        
        # Advanced symptom extraction using patterns and medical keywords
        symptoms = self._extract_symptom_patterns(user_text)
        result["extracted_symptoms"] = symptoms
        
        # Severity analysis
        for symptom in symptoms:
            severity = self._analyze_severity(user_text, symptom)
            result["severity_assessment"][symptom] = severity
            
            # Confidence scoring based on context
            confidence = self._calculate_confidence(user_text, symptom)
            result["confidence_scores"][symptom] = confidence
        
        # Temporal pattern analysis
        result["temporal_patterns"] = self._analyze_temporal_patterns(user_text)
        
        # Body area detection
        result["affected_areas"] = self._detect_body_areas(user_text)
        
        return result

    def _extract_symptom_patterns(self, text: str) -> List[str]:
        """Extract symptoms using pattern matching and medical knowledge"""
        symptoms = []
        text_lower = text.lower()
        
        # Check against known symptom lexicon
        for canonical_symptom, synonyms in self.symptom_lexicon.items():
            # Check canonical form
            if canonical_symptom.lower() in text_lower:
                symptoms.append(canonical_symptom)
                continue
                
            # Check synonyms
            for synonym in synonyms:
                if synonym.lower() in text_lower:
                    symptoms.append(canonical_symptom)
                    break
        
        # Pattern-based extraction for compound symptoms
        patterns = [
            r"(pain|ache|hurt|sore)\s+in\s+(\w+)",
            r"(difficulty|trouble|problem)\s+(\w+)",
            r"(feeling|feel)\s+(sick|nauseous|dizzy|weak)",
            r"(can'?t|cannot)\s+(sleep|eat|breathe|swallow)",
            r"(burning|tingling|numbness)\s+in\s+(\w+)"
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text_lower)
            for match in matches:
                symptom_phrase = match.group(0)
                # Convert to canonical form if possible
                canonical = self._normalize_pattern_symptom(symptom_phrase)
                if canonical and canonical not in symptoms:
                    symptoms.append(canonical)
        
        return list(set(symptoms))

    def _analyze_severity(self, text: str, symptom: str) -> str:
        """Analyze severity level of a symptom"""
        text_lower = text.lower()
        
        # Check for severity indicators around the symptom
        symptom_pos = text_lower.find(symptom.lower())
        if symptom_pos != -1:
            # Look for severity words in context (±10 words)
            start = max(0, symptom_pos - 50)
            end = min(len(text_lower), symptom_pos + len(symptom) + 50)
            context = text_lower[start:end]
            
            for severity, indicators in self.severity_indicators.items():
                for indicator in indicators:
                    if indicator in context:
                        return severity
        
        return "moderate"  # Default severity

    def _analyze_temporal_patterns(self, text: str) -> Dict:
        """Analyze temporal patterns of symptoms"""
        text_lower = text.lower()
        patterns = {}
        
        for pattern_type, indicators in self.temporal_indicators.items():
            for indicator in indicators:
                if indicator in text_lower:
                    patterns[pattern_type] = True
                    break
        
        # Extract duration information
        duration_pattern = r"(\d+)\s*(day|week|month|hour)s?"
        duration_matches = re.findall(duration_pattern, text_lower)
        if duration_matches:
            patterns["duration"] = duration_matches[0]
        
        return patterns

    def _detect_body_areas(self, text: str) -> List[str]:
        """Detect affected body areas"""
        text_lower = text.lower()
        detected_areas = []
        
        for body_part in self.body_parts:
            if body_part in text_lower:
                detected_areas.append(body_part)
        
        return detected_areas

    def _calculate_confidence(self, text: str, symptom: str) -> float:
        """Calculate confidence score for extracted symptom"""
        base_confidence = 0.7
        
        # Increase confidence if symptom appears multiple times
        occurrences = text.lower().count(symptom.lower())
        if occurrences > 1:
            base_confidence += 0.1
        
        # Increase confidence if severity is mentioned
        if any(word in text.lower() for severity_words in self.severity_indicators.values() 
               for word in severity_words):
            base_confidence += 0.1
        
        # Increase confidence if body part is mentioned
        if any(part in text.lower() for part in self.body_parts):
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)

    def _normalize_pattern_symptom(self, pattern_symptom: str) -> str:
        """Convert pattern-matched phrases to canonical symptoms"""
        mappings = {
            "pain in": "pain",
            "ache in": "pain", 
            "difficulty breathing": "shortness of breath",
            "trouble breathing": "shortness of breath",
            "feeling sick": "nausea",
            "feel nauseous": "nausea",
            "can't sleep": "insomnia",
            "cannot sleep": "insomnia",
            "burning in": "burning sensation"
        }
        
        for phrase, canonical in mappings.items():
            if phrase in pattern_symptom:
                return canonical
        
        return pattern_symptom

    def enhanced_symptom_extraction(self, user_text: str) -> Dict:
        """
        Main method that combines AI analysis with traditional rule-based approach
        """
        # Get AI analysis
        ai_result = self.extract_symptoms_with_ai(user_text)
        
        # Combine with traditional approach for robustness
        traditional_symptoms = self._traditional_normalize_symptoms(user_text)
        
        # Merge results
        all_symptoms = list(set(ai_result["extracted_symptoms"] + traditional_symptoms))
        
        # Enhanced result
        enhanced_result = {
            "symptoms": all_symptoms,
            "ai_analysis": ai_result,
            "traditional_symptoms": traditional_symptoms,
            "recommended_approach": self._recommend_approach(ai_result),
            "risk_assessment": self._assess_risk_level(all_symptoms, ai_result)
        }
        
        return enhanced_result

    def _traditional_normalize_symptoms(self, user_text: str) -> List[str]:
        """Traditional rule-based symptom extraction (fallback)"""
        normalized = []
        text = user_text.lower()
        
        for canonical, synonyms in self.symptom_lexicon.items():
            if canonical.lower() in text:
                normalized.append(canonical)
            else:
                for syn in synonyms:
                    if syn.lower() in text:
                        normalized.append(canonical)
                        break
        
        return list(set(normalized))

    def _recommend_approach(self, ai_analysis: Dict) -> str:
        """Recommend medical approach based on AI analysis"""
        if ai_analysis["temporal_patterns"].get("acute"):
            return "urgent_care"
        elif any(severity == "severe" for severity in ai_analysis["severity_assessment"].values()):
            return "medical_consultation"
        elif ai_analysis["temporal_patterns"].get("chronic"):
            return "scheduled_appointment"
        else:
            return "self_monitoring"

    def _assess_risk_level(self, symptoms: List[str], ai_analysis: Dict) -> str:
        """Assess overall risk level"""
        high_risk_symptoms = ["chest pain", "shortness of breath", "severe headache", "confusion"]
        
        if any(symptom in symptoms for symptom in high_risk_symptoms):
            return "high"
        elif any(severity == "severe" for severity in ai_analysis["severity_assessment"].values()):
            return "medium"
        else:
            return "low"

# Global instance for easy access
ai_parser = AISymptomParser()

def parse_symptoms_with_ai(user_text: str) -> Dict:
    """Convenience function for AI-powered symptom parsing"""
    return ai_parser.enhanced_symptom_extraction(user_text)

if __name__ == "__main__":
    # Test the AI parser
    test_cases = [
        "I have severe headache and nausea for 2 days",
        "Sudden chest pain with shortness of breath",
        "Mild cough and runny nose since yesterday",
        "I can't sleep and feeling very anxious"
    ]
    
    for test in test_cases:
        print(f"\nTesting: {test}")
        result = parse_symptoms_with_ai(test)
        print(f"Symptoms: {result['symptoms']}")
        print(f"Risk Level: {result['risk_assessment']}")
        print(f"Approach: {result['recommended_approach']}")
