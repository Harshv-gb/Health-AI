# api.py - Enhanced with AI capabilities and Hospital Finder
from flask import Flask, request, jsonify
from flask_cors import CORS
import json
import csv
import math
import os

# Import professional disease predictor
try:
    from backend.app.disease_predictor import predict_diseases_professional
    DISEASE_PREDICTOR_ENABLED = True
    print("✅ Professional disease predictor loaded successfully")
except ImportError as e:
    print(f"⚠️ Disease predictor not available: {e}")
    DISEASE_PREDICTOR_ENABLED = False

# Import AI components
try:
    from backend.app.parser import parse_symptoms_with_ai
    from backend.app.triage_engine import perform_ai_triage
    from backend.app.mistral_client import get_ai_medical_advice, get_health_education, get_diet_recommendations
    AI_ENABLED = True
    print("✅ AI components loaded successfully")
except ImportError as e:
    print(f"⚠️ AI components not available (using fallback): {e}")
    AI_ENABLED = False
    
    # Fallback implementations
    def parse_symptoms_with_ai(text):
        """Simple symptom extraction fallback"""
        return {
            "symptoms": text.split(",") if "," in text else [text],
            "severity": "moderate",
            "duration": "recent",
            "confidence": 0.7
        }
    
    def perform_ai_triage(symptoms, user_data=None):
        """Simple triage fallback"""
        return {
            "urgency": "medium",
            "department": "General Medicine",
            "notes": "Please consult a healthcare professional",
            "confidence": 0.7
        }
    
    def get_ai_medical_advice(symptoms, context=None):
        """Simple advice fallback"""
        return {
            "advice": "Based on your symptoms, consider consulting a healthcare professional for proper diagnosis and treatment.",
            "recommendations": [
                "Monitor your symptoms",
                "Stay hydrated",
                "Get adequate rest"
            ]
        }
    
    def get_health_education(topic):
        """Simple education fallback"""
        return {
            "content": f"For detailed information about {topic}, please consult with a healthcare professional or visit reputable medical websites."
        }
    
    def get_diet_recommendations(condition, patient_context=None):
        """Simple diet fallback"""
        return {
            "condition": condition,
            "diet_recommendations": f"For specific dietary recommendations for {condition}, please consult with a healthcare professional or registered dietitian.",
            "disclaimer": "Personalized nutrition advice should come from qualified healthcare providers."
        }

# Import voice and report processing modules
try:
    from backend.app.voice_processor import process_voice_input, generate_voice_response
    from backend.app.report_scanner import scan_medical_report
    VOICE_ENABLED = True
    REPORT_SCAN_ENABLED = True
    print("✅ Voice and report scanning loaded successfully")
except ImportError as e:
    print(f"⚠️ Voice/Report processing not available (using fallback): {e}")
    VOICE_ENABLED = False
    REPORT_SCAN_ENABLED = False
    
    # Fallback implementations
    def process_voice_input(audio_data):
        """Voice input fallback"""
        return {
            "success": False,
            "text": "",
            "message": "Voice input requires additional setup. Please type your symptoms instead."
        }
    
    def generate_voice_response(text):
        """Voice output fallback"""
        return {
            "success": False,
            "message": "Voice output requires additional setup. Please read the text response.",
            "audio_url": None
        }
    
    def scan_medical_report(image_data):
        """Report scanning fallback"""
        return {
            "success": False,
            "text": "",
            "message": "Report scanning requires additional setup. Please type your information."
        }

# Import medicine recommendation system
try:
    from backend.app.medicine_recommender import get_medicine_recommendations_for_condition, get_medicine_details, search_medicines_by_symptoms
    MEDICINE_ENABLED = True
    print("✅ Medicine recommendation system loaded")
except ImportError as e:
    print(f"Medicine recommendation not available: {e}")
    MEDICINE_ENABLED = False

# Import Hospital Finder
try:
    from backend.app.hospital_finder import HospitalFinder
    HOSPITAL_FINDER_ENABLED = True
    print("✅ Hospital finder loaded successfully")
except ImportError as e:
    print(f"Hospital finder not available: {e}")
    HOSPITAL_FINDER_ENABLED = False
    HospitalFinder = None

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Get the project root directory
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

# -------------------------
# Load JSON knowledge bases
# -------------------------
with open(os.path.join(project_root, "config", "symptom_lexicon.json")) as f:
    symptom_lexicon = json.load(f)

with open(os.path.join(project_root, "config", "red_flags.json")) as f:
    red_flags = json.load(f)

with open(os.path.join(project_root, "config", "conditions_list.json")) as f:
    conditions = json.load(f)

with open(os.path.join(project_root, "config", "department_map.json")) as f:
    departments = json.load(f)

# -------------------------
# Load hospital dataset (CSV)
# -------------------------
hospitals = []
with open(os.path.join(project_root, "data", "hospitals.csv"), newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        hospitals.append(row)

# -------------------------
# Initialize Hospital Finder
# -------------------------
hospital_finder = None
if HOSPITAL_FINDER_ENABLED:
    try:
        hospital_csv_path = os.path.join(project_root, "data", "hospitals_india.csv")
        hospital_finder = HospitalFinder(hospital_csv_path=hospital_csv_path)
        print(f"✅ Hospital finder initialized successfully")
    except Exception as e:
        print(f"❌ Error initializing hospital finder: {e}")
        hospital_finder = None


# -------------------------
# Utility: Haversine formula
# -------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


# -------------------------
# AI-Enhanced Symptom Processing
# -------------------------
def normalize_symptoms(user_text):
    """Traditional symptom normalization"""
    normalized = []
    text = user_text.lower()
    for canonical, synonyms in symptom_lexicon["symptom_lexicon"].items():
        if canonical.lower() in text:
            normalized.append(canonical)
        else:
            for syn in synonyms:
                if syn.lower() in text:
                    normalized.append(canonical)
                    break
    return list(set(normalized))

def process_symptoms_with_ai(user_text, patient_context=None):
    """Process symptoms using AI if available, fallback to traditional method"""
    if AI_ENABLED:
        try:
            # Use AI-powered symptom extraction
            ai_result = parse_symptoms_with_ai(user_text)
            symptoms = ai_result["symptoms"]
            
            # Perform AI triage if symptoms found
            if symptoms:
                triage_result = perform_ai_triage(symptoms, patient_context)
                
                return {
                    "symptoms": symptoms,
                    "ai_analysis": ai_result.get("ai_analysis", {}),
                    "triage": triage_result,
                    "ai_enhanced": True
                }
            else:
                # No symptoms extracted, use traditional fallback
                print("AI found no symptoms, falling back to traditional processing")
                return process_symptoms_traditional(user_text)
                
        except Exception as e:
            print(f"AI processing failed, using fallback: {e}")
            return process_symptoms_traditional(user_text)
    else:
        return process_symptoms_traditional(user_text)

def process_symptoms_traditional(user_text):
    """Traditional rule-based symptom processing"""
    normalized = normalize_symptoms(user_text)
    
    # Check red flags
    red_flag = check_red_flags(normalized)
    if red_flag:
        return {
            "symptoms": normalized,
            "red_flag": red_flag,
            "urgency": "emergency",
            "ai_enhanced": False
        }
    
    # Match condition
    condition = match_condition(normalized)
    return {
        "symptoms": normalized,
        "condition": condition,
        "urgency": condition["severity"] if condition else "GP",
        "ai_enhanced": False
    }


# -------------------------
# Check red flags
# -------------------------
def check_red_flags(symptoms):
    for flag in red_flags["red_flags"]:
        for trigger in flag["trigger_symptoms"]:
            if any(trigger.lower() in s.lower() for s in symptoms):
                return flag
    return None


# -------------------------
# Match condition
# -------------------------
def match_condition(symptoms):
    best_match = None
    best_score = 0
    for cond in conditions["conditions"]:
        overlap = len(set(cond["symptoms"]).intersection(symptoms))
        if overlap > best_score:
            best_score = overlap
            best_match = cond
    return best_match


# -------------------------
# Find nearest hospitals
# -------------------------
def find_hospitals(lat, lon, department):
    matches = []
    for hosp in hospitals:
        try:
            hosp_lat = float(hosp["location_lat"])
            hosp_lon = float(hosp["location_lon"])
            distance = haversine(float(lat), float(lon), hosp_lat, hosp_lon)

            if department in hosp["departments_available"]:
                matches.append(
                    {
                        "hospital": hosp["hospital_name"],
                        "city": hosp["city"],
                        "department": department,
                        "contact": hosp["contact_number"],
                        "distance_km": round(distance, 2),
                    }
                )
        except Exception as e:
            print("Error parsing hospital row:", e)
            continue

    return sorted(matches, key=lambda x: x["distance_km"])[:3]


# -------------------------
# Enhanced API Endpoints
# -------------------------
@app.route("/api/query", methods=["POST"])
def query():
    """Enhanced API endpoint with Professional Disease Prediction"""
    try:
        data = request.json
        text = data.get("text", "")
        lat = float(data.get("lat", 0))
        lon = float(data.get("lon", 0))
        
        # Optional patient context for disease prediction
        patient_context = data.get("patient_context", {})
        conversation_mode = data.get("conversation_mode", False)
        chat_history = data.get("chat_history", [])
        
        if not text:
            return jsonify({"error": "No symptoms provided"}), 400
        
        # Process symptoms with AI enhancement to extract clean symptom list
        symptom_result = process_symptoms_with_ai(text, patient_context)
        symptoms = symptom_result.get("symptoms", [])
        
        if not symptoms:
            # Fallback: split by comma or use the whole text
            symptoms = [s.strip() for s in text.split(",")] if "," in text else [text]
        
        # Check for red flags first (emergency situations)
        if "red_flag" in symptom_result:
            department = symptom_result["red_flag"]["department"]
            nearby = find_hospitals(lat, lon, department)
            
            response = {
                "status": "emergency",
                "condition": "Emergency Alert",
                "department": department,
                "notes": symptom_result["red_flag"]["notes"],
                "message": "⚠️ This appears to be a medical emergency. Seek immediate care!",
                "hospitals": nearby,
                "predictions": [],
                "professional_analysis": True
            }
            return jsonify(response)
        
        # Use Professional Disease Predictor
        if DISEASE_PREDICTOR_ENABLED:
            try:
                # Run professional disease prediction
                prediction_result = predict_diseases_professional(symptoms, patient_context)
                
                if prediction_result["predictions"]:
                    # Get top prediction for primary department
                    top_prediction = prediction_result["predictions"][0]
                    department = top_prediction["department"]
                    nearby = find_hospitals(lat, lon, department)
                    
                    # Build comprehensive response
                    response = {
                        "status": top_prediction["severity"],
                        "condition": top_prediction["disease"],
                        "department": department,
                        "probability": top_prediction["probability"],
                        "confidence": top_prediction["confidence"],
                        
                        # Professional analysis
                        "professional_analysis": prediction_result["analysis"],
                        
                        # All predictions with probabilities
                        "disease_predictions": prediction_result["predictions"],
                        
                        # Matched symptoms detail
                        "symptoms_analyzed": prediction_result["symptoms_provided"],
                        "input_symptoms": prediction_result["input_symptoms"],
                        
                        # Hospital recommendations
                        "hospitals": nearby,
                        
                        # Additional info from top prediction
                        "description": top_prediction.get("description", ""),
                        "treatment_info": top_prediction.get("treatment_info", []),
                        "when_to_see_doctor": top_prediction.get("when_to_see_doctor", ""),
                        "duration": top_prediction.get("duration", ""),
                        
                        # Flags
                        "has_critical_symptoms": top_prediction.get("has_critical_symptoms", False),
                        "age_related": top_prediction.get("age_related", False),
                        "professional_analysis_enabled": True
                    }
                    
                    # Add conversational AI if requested
                    if conversation_mode and AI_ENABLED:
                        try:
                            ai_context = {
                                "symptoms": symptoms,
                                "top_diagnosis": top_prediction["disease"],
                                "probability": top_prediction["probability"],
                                "urgency": top_prediction["severity"]
                            }
                            ai_advice = get_ai_medical_advice(text, ai_context, chat_history)
                            response["ai_conversation"] = ai_advice
                        except Exception as e:
                            print(f"AI conversation failed: {e}")
                    
                    return jsonify(response)
                else:
                    # No predictions found
                    response = {
                        "status": "unknown",
                        "message": "Unable to match symptoms to known conditions. Please consult a healthcare professional.",
                        "department": "General Medicine",
                        "input_symptoms": symptoms,
                        "hospitals": find_hospitals(lat, lon, "General Medicine"),
                        "professional_analysis_enabled": True
                    }
                    return jsonify(response)
                    
            except Exception as e:
                print(f"Professional disease predictor failed: {e}")
                # Fall through to legacy system
        
        # Legacy fallback system (if disease predictor not available or failed)
        if symptom_result.get("ai_enhanced") and "triage" in symptom_result:
            # AI-enhanced processing
            triage = symptom_result["triage"]
            
            # Match condition for department mapping
            condition = match_condition(symptoms) if symptoms else None
            
            if condition:
                department = condition["department"]
                nearby = find_hospitals(lat, lon, department)
                
                response = {
                    "status": triage["urgency_level"],
                    "condition": condition["condition"],
                    "department": department,
                    "notes": condition["notes"],
                    "ai_assessment": triage["assessment"],
                    "ai_confidence": triage["confidence"],
                    "ai_recommendations": triage["recommendations"],
                    "follow_up_questions": triage.get("follow_up_questions", []),
                    "hospitals": nearby,
                    "ai_enhanced": True,
                    "risk_factors": triage.get("risk_factors", {}),
                    "professional_analysis_enabled": False
                }
                return jsonify(response)
        
        # Final fallback: Traditional processing
        condition = match_condition(symptoms)
        
        if not condition:
            return jsonify({
                "status": "unknown", 
                "message": "No clear match found. Please consult General Medicine.",
                "ai_enhanced": False
            })
        
        nearby = find_hospitals(lat, lon, condition["department"])
        
        response = {
            "status": condition["severity"],
            "condition": condition["condition"],
            "department": condition["department"],
            "notes": condition["notes"],
            "hospitals": nearby,
            "professional_analysis_enabled": False
        }
        
        return jsonify(response)
        
    except Exception as e:
        print(f"Error in query endpoint: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/api/conversation", methods=["POST"])
def conversation():
    """Dedicated endpoint for conversational AI with diet detection"""
    try:
        data = request.json
        user_message = data.get("message", "")
        symptom_context = data.get("symptom_context", {})
        chat_history = data.get("chat_history", [])
        
        if not user_message:
            return jsonify({"error": "No message provided"}), 400
        
        if not AI_ENABLED:
            return jsonify({"error": "AI conversation not available"}), 503
        
        # Check if user is asking about diet recommendations
        diet_keywords = ["diet", "food", "eat", "nutrition", "meal", "avoid eating", "what to eat", "what should i eat"]
        user_message_lower = user_message.lower()
        is_diet_query = any(keyword in user_message_lower for keyword in diet_keywords)
        
        # If it's a diet query and we have a diagnosed condition, provide diet recommendations
        if is_diet_query and symptom_context.get("top_condition"):
            condition = symptom_context.get("top_condition")
            patient_context = symptom_context.get("patient_context", {})
            
            # Get diet recommendations
            diet_response = get_diet_recommendations(condition, patient_context)
            
            return jsonify({
                "ai_response": f"Based on your diagnosis of {condition}, here are personalized diet recommendations:\n\n{diet_response['diet_recommendations']}",
                "diet_recommendations": diet_response,
                "is_diet_response": True,
                "follow_up_suggestions": [
                    "Are there specific foods you're concerned about?",
                    "Do you have any dietary restrictions or allergies?",
                    "Would you like meal planning tips?",
                    "Tell me more about your eating habits"
                ],
                "safety_disclaimer": diet_response.get("disclaimer", ""),
                "conversation_context": chat_history + [
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": f"Providing diet recommendations for {condition}"}
                ]
            })
        
        # Regular conversational AI response
        ai_response = get_ai_medical_advice(user_message, symptom_context, chat_history)
        
        return jsonify({
            "ai_response": ai_response["ai_response"],
            "is_diet_response": False,
            "follow_up_suggestions": ai_response["follow_up_suggestions"],
            "safety_disclaimer": ai_response["safety_disclaimer"],
            "conversation_context": ai_response["conversation_context"]
        })
        
    except Exception as e:
        return jsonify({"error": f"Conversation error: {str(e)}"}), 500

@app.route("/api/health-education", methods=["POST"])
def health_education():
    """Endpoint for health education content"""
    try:
        data = request.json
        condition = data.get("condition", "")
        symptoms = data.get("symptoms", [])
        
        if not condition:
            return jsonify({"error": "No condition specified"}), 400
        
        if not AI_ENABLED:
            # Fallback educational content
            return jsonify({
                "educational_content": f"For information about {condition}, please consult with healthcare professionals.",
                "disclaimer": "This system cannot provide detailed medical education without AI capabilities.",
                "condition": condition
            })
        
        # Get AI-generated educational content
        education_response = get_health_education(condition, symptoms)
        
        return jsonify(education_response)
        
    except Exception as e:
        return jsonify({"error": f"Education error: {str(e)}"}), 500

@app.route("/api/diet-recommendations", methods=["POST"])
def diet_recommendations():
    """Endpoint for personalized diet recommendations based on diagnosed condition"""
    try:
        data = request.json
        condition = data.get("condition", "")
        patient_context = data.get("patient_context", {})
        
        if not condition:
            return jsonify({"error": "No condition specified"}), 400
        
        # Get diet recommendations (works with or without AI)
        diet_response = get_diet_recommendations(condition, patient_context)
        
        return jsonify(diet_response)
        
    except Exception as e:
        return jsonify({"error": f"Diet recommendation error: {str(e)}"}), 500

@app.route("/api/voice-input", methods=["POST"])
def voice_input():
    """Process voice input and return transcribed text"""
    try:
        if not VOICE_ENABLED:
            return jsonify({"error": "Voice processing not available"}), 503
        
        # Check if audio file is provided
        if 'audio' not in request.files:
            return jsonify({"error": "No audio file provided"}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({"error": "No audio file selected"}), 400
        
        # Process voice input
        audio_data = audio_file.read()
        result = process_voice_input(audio_data)
        
        if result['success']:
            return jsonify({
                "text": result['text'],
                "confidence": result.get('confidence', 1.0),
                "message": "Voice transcription successful"
            })
        else:
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        return jsonify({"error": f"Voice processing error: {str(e)}"}), 500

@app.route("/api/voice-response", methods=["POST"])
def voice_response():
    """Generate voice response for diagnosis result"""
    try:
        if not VOICE_ENABLED:
            return jsonify({"error": "Voice processing not available"}), 503
        
        data = request.json
        diagnosis_result = data.get("diagnosis_result", {})
        
        if not diagnosis_result:
            return jsonify({"error": "No diagnosis result provided"}), 400
        
        # Generate voice response
        result = generate_voice_response(diagnosis_result)
        
        if result['success']:
            return jsonify({
                "message": "Voice response generated successfully",
                "audio_available": True
            })
        else:
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        return jsonify({"error": f"Voice response error: {str(e)}"}), 500

@app.route("/api/scan-report", methods=["POST"])
def scan_report():
    """Scan and analyze medical reports"""
    try:
        if not REPORT_SCAN_ENABLED:
            return jsonify({"error": "Report scanning not available"}), 503
        
        # Check if report file is provided
        if 'report' not in request.files:
            return jsonify({"error": "No report file provided"}), 400
        
        report_file = request.files['report']
        if report_file.filename == '':
            return jsonify({"error": "No report file selected"}), 400
        
        # Process the report
        file_data = report_file.read()
        filename = report_file.filename
        
        result = scan_medical_report(file_data, filename)
        
        if result['success']:
            return jsonify({
                "extracted_text": result['extracted_text'],
                "medical_info": result['medical_info'],
                "analysis": result['analysis'],
                "medical_analysis": result['medical_analysis'],
                "message": "Report scanned successfully"
            })
        else:
            return jsonify({"error": result['error']}), 400
            
    except Exception as e:
        return jsonify({"error": f"Report scanning error: {str(e)}"}), 500

@app.route("/api/status", methods=["GET"])
@app.route('/api/status', methods=['GET'])
def status():
    """API status endpoint"""
    return jsonify({
        "status": "online",
        "ai_enabled": AI_ENABLED,
        "voice_enabled": VOICE_ENABLED,
        "report_scan_enabled": REPORT_SCAN_ENABLED,
        "medicine_enabled": MEDICINE_ENABLED,
        "version": "3.0.0",
        "features": {
            "ai_symptom_parsing": AI_ENABLED,
            "ai_triage": AI_ENABLED,
            "conversational_ai": AI_ENABLED,
            "health_education": AI_ENABLED,
            "voice_input": VOICE_ENABLED,
            "voice_output": VOICE_ENABLED,
            "report_scanning": REPORT_SCAN_ENABLED,
            "medicine_recommendations": MEDICINE_ENABLED,
            "traditional_fallback": True
        }
    })

# ===============================
# MEDICINE RECOMMENDATION ENDPOINTS
# ===============================

@app.route('/api/medicine/recommendations', methods=['POST'])
def get_medicine_recommendations():
    """Get medicine recommendations for a diagnosed condition"""
    if not MEDICINE_ENABLED:
        return jsonify({
            "success": False,
            "error": "Medicine recommendation system not available"
        }), 503
    
    try:
        data = request.json
        condition = data.get('condition', '').strip()
        
        if not condition:
            return jsonify({
                "success": False,
                "error": "Condition is required"
            }), 400
        
        # Get patient context for safety checks
        patient_context = {
            "age": data.get('age'),
            "pregnant": data.get('pregnant', False),
            "allergies": data.get('allergies', []),
            "current_medications": data.get('current_medications', []),
            "urgency": data.get('urgency', 'normal')
        }
        
        # Get medicine recommendations
        recommendations = get_medicine_recommendations_for_condition(condition, patient_context)
        
        return jsonify(recommendations)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Medicine recommendation failed: {str(e)}"
        }), 500

@app.route('/api/medicine/details/<medicine_name>', methods=['GET'])
def get_medicine_information(medicine_name):
    """Get detailed information about a specific medicine"""
    if not MEDICINE_ENABLED:
        return jsonify({
            "success": False,
            "error": "Medicine information system not available"
        }), 503
    
    try:
        medicine_details = get_medicine_details(medicine_name)
        return jsonify(medicine_details)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get medicine details: {str(e)}"
        }), 500

@app.route('/api/medicine/search', methods=['POST'])
def search_medicines():
    """Search for medicines based on symptoms"""
    if not MEDICINE_ENABLED:
        return jsonify({
            "success": False,
            "error": "Medicine search system not available"
        }), 503
    
    try:
        data = request.json
        symptoms = data.get('symptoms', [])
        
        if not symptoms:
            return jsonify({
                "success": False,
                "error": "Symptoms list is required"
            }), 400
        
        # Search medicines by symptoms
        search_results = search_medicines_by_symptoms(symptoms)
        
        return jsonify(search_results)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Medicine search failed: {str(e)}"
        }), 500

@app.route('/api/medicine/analyze', methods=['POST'])
def analyze_with_medicine_recommendations():
    """Complete analysis with diagnosis and medicine recommendations"""
    try:
        data = request.json
        symptoms = data.get('symptoms', [])
        location = data.get('location', '')
        lat = data.get('lat')
        lon = data.get('lon')
        age = data.get('age')
        gender = data.get('gender', 'other')
        
        print(f"\n=== ANALYZE REQUEST ===")
        print(f"Symptoms received: {symptoms}")
        print(f"Location: {location}")
        
        if not symptoms:
            return jsonify({
                "success": False,
                "error": "Symptoms are required"
            }), 400
        
        # Get AI-enhanced symptom analysis
        analysis_result = {}
        
        if AI_ENABLED:
            # Parse symptoms with AI
            symptom_text = ' '.join(symptoms) if isinstance(symptoms, list) else symptoms
            print(f"Processing symptom text: {symptom_text}")
            
            parsed_result = parse_symptoms_with_ai(symptom_text)
            print(f"Parsed result: {parsed_result}")
            
            # Extract just the symptom list from the parsed result
            if isinstance(parsed_result, dict) and 'symptoms' in parsed_result:
                parsed_symptoms = parsed_result['symptoms']
            else:
                parsed_symptoms = parsed_result
            
            print(f"Extracted symptoms list: {parsed_symptoms}")
            
            # Perform AI triage
            triage_result = perform_ai_triage(parsed_symptoms, {
                "age": age,
                "gender": gender,
                "location": location
            })
            print(f"Triage result: {triage_result}")
            
            analysis_result = {
                "symptoms": parsed_symptoms,
                "triage": triage_result,
                "ai_enhanced": True,
                "original_input": symptom_text  # Add original input for debugging
            }
            
            # Get potential conditions from triage
            potential_conditions = triage_result.get('potential_conditions', [])
            
            # If no conditions found, try traditional matching
            if not potential_conditions or len(potential_conditions) == 0:
                print("No AI conditions found, trying traditional matching...")
                # Normalize and match symptoms traditionally
                normalized_symptoms = normalize_symptoms(symptom_text)
                traditional_condition = match_condition(normalized_symptoms)
                if traditional_condition:
                    potential_conditions = [traditional_condition.get('condition', 'General symptom relief')]
                    triage_result['potential_conditions'] = potential_conditions
                    triage_result['department'] = traditional_condition.get('department', 'General Medicine')
                    print(f"Traditional match found: {potential_conditions}")
            
            print(f"Potential conditions: {potential_conditions}")
            
        else:
            # Fallback to traditional analysis
            analysis_result = {
                "symptoms": symptoms,
                "ai_enhanced": False,
                "potential_conditions": ["General symptom relief"]
            }
            potential_conditions = ["General symptom relief"]
        
        # Get medicine recommendations for top conditions
        medicine_recommendations = {}
        if MEDICINE_ENABLED and potential_conditions:
            patient_context = {
                "age": age,
                "pregnant": data.get('pregnant', False),
                "allergies": data.get('allergies', []),
                "urgency": analysis_result.get('triage', {}).get('urgency', 'normal')
            }
            
            for condition in potential_conditions[:3]:  # Top 3 conditions
                recommendations = get_medicine_recommendations_for_condition(condition, patient_context)
                if recommendations.get('success') and recommendations.get('recommendations'):
                    medicine_recommendations[condition] = recommendations
        
        # Find nearby hospitals
        nearby_hospitals = []
        if lat is not None and lon is not None:
            # Determine department based on triage results
            department = "General Medicine"  # Default
            if analysis_result.get('triage', {}).get('department'):
                department = analysis_result['triage']['department']
            
            nearby_hospitals = find_hospitals(lat, lon, department)
        
        return jsonify({
            "success": True,
            "analysis": analysis_result,
            "medicine_recommendations": medicine_recommendations,
            "hospitals": nearby_hospitals,
            "timestamp": str(data.get('timestamp', '')),
            "comprehensive_analysis": True
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Comprehensive analysis failed: {str(e)}"
        }), 500

# -------------------------
# Hospital Finder API - Live Location (Main Feature)
# -------------------------
@app.route('/api/hospitals/nearby', methods=['POST'])
def find_nearby_hospitals_live():
    """Find hospitals near user's live location - MAIN PROJECT FEATURE"""
    try:
        data = request.get_json()
        
        # Extract location from request
        user_lat = data.get('latitude')
        user_lon = data.get('longitude')
        department = data.get('department', None)
        urgency = data.get('urgency', 'normal')
        max_distance = data.get('max_distance', 20)
        limit = data.get('limit', 10)
        
        # Validate coordinates
        if user_lat is None or user_lon is None:
            return jsonify({
                "status": "error",
                "message": "Latitude and longitude are required"
            }), 400
        
        # Validate coordinates range
        if not (-90 <= user_lat <= 90) or not (-180 <= user_lon <= 180):
            return jsonify({
                "status": "error",
                "message": "Invalid coordinates"
            }), 400
        
        # Check if hospital finder is available
        if not HOSPITAL_FINDER_ENABLED or hospital_finder is None:
            return jsonify({
                "status": "error",
                "message": "Hospital finder service unavailable"
            }), 503
        
        # Find hospitals based on urgency
        if urgency == 'emergency':
            nearby_hospitals = hospital_finder.get_emergency_hospitals(
                user_lat=user_lat,
                user_lon=user_lon,
                max_distance=max_distance,
                limit=limit
            )
        else:
            nearby_hospitals = hospital_finder.find_nearby_hospitals(
                user_lat=user_lat,
                user_lon=user_lon,
                department=department,
                max_distance=max_distance,
                limit=limit
            )
        
        return jsonify({
            "status": "success",
            "user_location": {
                "latitude": user_lat,
                "longitude": user_lon
            },
            "hospitals_found": len(nearby_hospitals),
            "hospitals": nearby_hospitals,
            "search_params": {
                "department": department,
                "urgency": urgency,
                "max_distance_km": max_distance,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error finding hospitals: {str(e)}"
        }), 500

@app.route('/api/hospitals/by-city', methods=['POST'])
def find_hospitals_by_city():
    """Find hospitals in a specific city"""
    try:
        data = request.get_json()
        city_name = data.get('city', '').title()
        department = data.get('department', None)
        limit = data.get('limit', 10)
        
        if not city_name:
            return jsonify({
                "status": "error",
                "message": "City name is required"
            }), 400
        
        if not HOSPITAL_FINDER_ENABLED or hospital_finder is None:
            return jsonify({
                "status": "error",
                "message": "Hospital finder service unavailable"
            }), 503
        
        # Get city coordinates
        coords = hospital_finder.get_city_coordinates(city_name)
        if coords is None:
            return jsonify({
                "status": "error",
                "message": f"City '{city_name}' not found in our database"
            }), 404
        
        # Find hospitals near city center
        nearby_hospitals = hospital_finder.find_nearby_hospitals(
            user_lat=coords['lat'],
            user_lon=coords['lon'],
            department=department,
            max_distance=50,  # Search within 50km of city center
            limit=limit
        )
        
        return jsonify({
            "status": "success",
            "city": city_name,
            "city_coordinates": coords,
            "hospitals_found": len(nearby_hospitals),
            "hospitals": nearby_hospitals,
            "search_params": {
                "department": department,
                "limit": limit
            }
        })
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error finding hospitals: {str(e)}"
        }), 500

if __name__ == '__main__':
    print("\n🏥 Smart Symptom Checker v3.0 with Medicine Recommendations & Hospital Finder")
    print("=" * 60)
    print(f"AI Features: {'✅ Enabled (Fallback)' if not AI_ENABLED else '✅ Enabled (Full)'}")
    print(f"Voice Processing: {'✅ Enabled (Fallback)' if not VOICE_ENABLED else '✅ Enabled (Full)'}")
    print(f"Report Scanning: {'✅ Enabled (Fallback)' if not REPORT_SCAN_ENABLED else '✅ Enabled (Full)'}")
    print(f"Medicine Recommendations: {'✅ Enabled' if MEDICINE_ENABLED else '❌ Disabled'}")
    print(f"Hospital Finder (MAIN FEATURE): {'✅ Enabled' if HOSPITAL_FINDER_ENABLED else '❌ Disabled'}")
    print("=" * 60)
    print("💡 Note: Fallback modes provide basic functionality without heavy dependencies")
    print("=" * 60)
    print("🚀 Starting server...")
    app.run(debug=True, host='0.0.0.0', port=5000)
