# 📁 Health-AI Project - File Structure & Documentation

## 🎯 Project Overview
Smart Medical Diagnosis System with AI-powered disease prediction, diet recommendations, and hospital finder.

---

## 📂 ROOT DIRECTORY

### Documentation Files

#### `README.md`
- **Purpose:** Project documentation and overview
- **Contains:** Features, setup instructions, technology stack
- **Audience:** Anyone viewing the GitHub repository
- **When to update:** When adding new features or changing setup process

#### `EXECUTION_GUIDE.md`
- **Purpose:** Step-by-step guide to run the project
- **Contains:** Installation, configuration, running backend/frontend
- **Audience:** Developers setting up for first time
- **When to update:** When deployment process changes

### Configuration Files

#### `.gitignore`
- **Purpose:** Specifies files Git should ignore
- **Ignores:**
  - `.venv/` - Virtual environment
  - `__pycache__/` - Python cache
  - `.env` - Secret keys
  - `*.log` - Log files
  - `*.pkl` - ML model files
- **Why:** Keeps repo clean, prevents uploading sensitive/large files

#### `.env.sample`
- **Purpose:** Template for environment variables
- **Contains:**
  ```
  MISTRAL_API_KEY=your_mistral_key_here
  OPENAI_API_KEY=your_openai_key_here
  ```
- **Usage:** Copy to `.env` and add real API keys
- **Security:** ✅ Safe to commit (no real keys)

#### `.env` (Not in Git)
- **Purpose:** Your actual API keys
- **Contains:** Real MISTRAL_API_KEY, OPENAI_API_KEY
- **Security:** ❌ NEVER commit (contains secrets)

---

## 🐍 BACKEND DIRECTORY (`backend/`)

### `backend/requirements.txt`
**Purpose:** Python dependencies list
**Contents:**
```
Flask==2.3.0
requests==2.31.0
scikit-learn==1.3.0
pandas==2.0.3
numpy==1.24.3
python-dotenv==1.0.0
flask-cors==4.0.0
```
**Usage:** `pip install -r requirements.txt`
**When to update:** When adding new Python packages

### `backend/.env.template`
**Purpose:** Backup environment template
**Similar to:** Root `.env.sample`

---

## 🔧 BACKEND APP (`backend/app/`)

### Core Files

#### `api.py` (1040 lines) 🔴 CRITICAL
**Purpose:** Flask REST API server - Heart of backend

**What it does:**
- Handles all HTTP requests from frontend
- Routes requests to appropriate modules
- Integrates all backend components
- Returns JSON responses

**Key Endpoints:**
```python
POST /api/query
  - Main symptom analysis
  - Input: symptoms, location, patient_context
  - Output: disease predictions, recommendations

POST /api/conversation
  - AI chat with context
  - Detects diet queries automatically
  - Maintains conversation history

POST /api/diet-recommendations
  - Personalized diet plans
  - Input: condition, patient_context
  - Output: foods to eat/avoid, hydration, tips

POST /api/hospitals/nearby
  - Find nearby hospitals
  - Input: lat, lon, department
  - Output: sorted by distance

POST /api/medicine/recommendations
  - Medicine suggestions
  - Input: condition
  - Output: medicines with dosage, side effects

GET /api/status
  - Server health check
  - Shows enabled features
```

**Imports:**
- `disease_predictor.py` - Disease prediction
- `mistral_client.py` - AI chat
- `hospital_finder.py` - Location services
- `medicine_recommender.py` - Medicine info
- `parser.py` - Symptom parsing
- `triage_engine.py` - Urgency detection

**When to modify:** Adding new API endpoints or features

---

#### `disease_predictor.py` (500+ lines) 🔴 CRITICAL
**Purpose:** Professional disease prediction engine

**What it does:**
- Predicts diseases from symptoms with probability percentages
- Uses fuzzy matching for symptom recognition (0.8-1.0 confidence)
- Applies intelligent scoring:
  - **Prevalence multipliers:**
    - Very Common (Cold, Flu): 2.0x
    - Common (Diabetes): 1.5x
    - Uncommon: 1.0x
    - Rare: 0.6x
    - Very Rare: 0.3x
  - **Age adjustments:** 1.2x for age-related conditions
  - **Pattern matching:** 2.5x for known symptom combinations
  - **Chronic conditions:** 1.6x boost for related diseases
- Provides differential diagnosis (top 5 predictions)
- Identifies critical symptoms

**Key Functions:**
```python
predict_diseases_professional(symptoms, patient_context)
  - Main prediction function
  - Returns: disease predictions with probabilities

_fuzzy_symptom_match(input_symptom, known_symptom)
  - Matches variations of symptoms
  - Example: "tummy ache" matches "abdominal pain"

_calculate_score(disease, matched_symptoms, patient_context)
  - Calculates final probability score
  - Applies all multipliers
```

**Data Sources:**
- `config/disease_knowledge_base.json` - 15 detailed diseases
- `data/comprehensive_symptom_disease_mapping.csv` - 92 conditions, 290 symptoms

**Algorithm Flow:**
```
1. Parse input symptoms
2. Fuzzy match against known symptoms
3. Find matching diseases
4. Calculate base scores
5. Apply prevalence multipliers
6. Apply age adjustments
7. Apply pattern boosts
8. Apply chronic condition boosts
9. Normalize to percentages (5-95%)
10. Sort by probability
11. Return top 5 predictions
```

**When to modify:** 
- Adding new diseases
- Adjusting probability weights
- Improving symptom matching

---

#### `mistral_client.py` (485 lines) 🟠 HIGH
**Purpose:** AI chatbot and diet recommendation system

**What it does:**
- Connects to Mistral AI or OpenAI APIs
- Generates conversational medical advice
- Creates personalized diet recommendations
- Maintains chat context
- Detects diet-related keywords

**Key Features:**
1. **Conversational AI**
   - Contextual medical advice
   - Follow-up suggestions
   - Safety disclaimers
   - Mental health support detection

2. **Diet Recommendations**
   - Condition-specific diets
   - Patient context integration (age, gender, chronic conditions)
   - Structured format:
     - Foods to Include (5-7 items)
     - Foods to Avoid (3-5 items)
     - Hydration Guidelines
     - Meal Timing & Frequency
     - Additional Tips
   - Medical disclaimers

**Functions:**
```python
get_ai_medical_advice(message, symptom_context, chat_history)
  - General medical chat
  - Returns: AI response, follow-up suggestions

generate_diet_recommendations(condition, patient_context)
  - Creates diet plans
  - Returns: formatted diet advice

generate_health_education(condition, symptoms)
  - Educational content about conditions
```

**API Configuration:**
- **Primary:** Mistral AI (mistral-medium)
- **Fallback:** OpenAI (gpt-3.5-turbo)
- **No API:** Built-in responses for common conditions
- **Temperature:** 0.3 (low for medical accuracy)
- **Max Tokens:** 500

**Built-in Diets (No API needed):**
- Common Cold
- Influenza (Flu)
- Type 2 Diabetes
- Generic fallback

**When to modify:**
- Adding more built-in diets
- Changing AI model parameters
- Updating prompt templates

---

#### `hospital_finder.py` 🟡 MEDIUM
**Purpose:** Location-based hospital search

**What it does:**
- Finds hospitals near user's location
- Filters by department/specialty
- Calculates distances using Haversine formula
- Sorts by proximity
- Returns contact information

**Key Functions:**
```python
find_nearby_hospitals(lat, lon, department, radius_km)
  - Searches within radius
  - Returns: sorted hospital list

calculate_distance(lat1, lon1, lat2, lon2)
  - Haversine formula for Earth distances
  - Returns: distance in kilometers
```

**Data Source:** `data/hospitals_india.csv`
- Hospital names
- GPS coordinates (lat, lon)
- Available departments
- Contact numbers
- City information

**When to modify:**
- Adding new hospital data
- Changing search radius
- Adding filters (rating, services)

---

#### `medicine_recommender.py` 🟡 MEDIUM
**Purpose:** Medicine recommendations and information

**What it does:**
- Suggests medicines for conditions
- Provides dosage information
- Lists side effects
- Safety checks for interactions
- Generic/brand name mapping

**Key Functions:**
```python
get_medicine_recommendations_for_condition(condition)
  - Returns: medicine list with details

get_medicine_details(medicine_name)
  - Returns: full medicine information

search_medicines_by_symptoms(symptoms)
  - Returns: medicines that treat symptoms
```

**Data Source:** `config/medicine_database.json`
```json
{
  "medicine_name": {
    "generic_name": "...",
    "indications": ["condition1", "condition2"],
    "dosage": "...",
    "side_effects": ["effect1", "effect2"],
    "contraindications": ["..."],
    "interactions": ["drug1", "drug2"]
  }
}
```

**Safety Features:**
- Drug interaction warnings
- Contraindication alerts
- Age-appropriate dosing recommendations

**When to modify:**
- Adding new medicines
- Updating drug information
- Adding interaction checks

---

#### `triage_engine.py` 🟠 HIGH
**Purpose:** AI-powered symptom triage and urgency detection

**What it does:**
- Determines urgency level from symptoms
- Uses machine learning classification
- Identifies emergency situations
- Routes to appropriate care level

**Urgency Levels:**
```
1. EMERGENCY (🚨)
   - Immediate life threat
   - Call ambulance
   - Examples: Chest pain, severe bleeding, difficulty breathing

2. URGENT (⚠️)
   - Needs care within hours
   - Go to urgent care/ER
   - Examples: High fever, severe pain, injury

3. GP (📋)
   - Schedule doctor appointment
   - Within days
   - Examples: Persistent cough, minor infection

4. SELF-CARE (🏠)
   - Monitor at home
   - OTC remedies
   - Examples: Mild cold, minor headache
```

**ML Model:**
- **File:** `triage_model.pkl` (not in Git)
- **Type:** Classification model (scikit-learn)
- **Input:** Symptom text
- **Output:** Urgency category + confidence

**Vectorizer:**
- **File:** `triage_vectorizer.pkl` (not in Git)
- **Purpose:** Converts text to numerical features

**When to modify:**
- Retraining ML model
- Adjusting urgency criteria
- Adding new triage categories

---

#### `parser.py` 🟠 HIGH
**Purpose:** Natural language symptom extraction

**What it does:**
- Extracts symptoms from casual text
- Normalizes to medical terminology
- Handles multiple symptoms in one sentence
- Fuzzy matching for variations

**Examples:**
```
Input: "I have a really bad headache and feel sick to my stomach"
Output: ["headache", "nausea"]

Input: "running nose, coughing a lot, feeling hot"
Output: ["runny nose", "cough", "fever"]

Input: "tummy hurts after eating"
Output: ["abdominal pain"]
```

**Techniques:**
- Synonym mapping
- Keyword extraction
- Context analysis
- Medical term normalization

**Data Source:** `config/symptom_lexicon.json`, `config/enhanced_symptom_lexicon.json`

**When to modify:**
- Adding new symptom synonyms
- Improving parsing accuracy
- Supporting multiple languages

---

#### `department_mapper.py` 🟡 MEDIUM
**Purpose:** Maps conditions to medical departments

**What it does:**
- Determines appropriate hospital department
- Routes to correct specialist
- Provides department information

**Examples:**
```
Heart Attack → Cardiology
Diabetes → Endocrinology
Broken Bone → Orthopedics
Anxiety → Psychiatry
Pregnancy → Obstetrics/Gynecology
```

**Data Source:** `config/department_map.json`

**When to modify:**
- Adding new specialties
- Updating department mappings

---

#### `voice_processor.py` 🟢 LOW (Optional)
**Purpose:** Voice input/output features

**What it does:**
- Speech-to-text for symptom input
- Text-to-speech for results
- Voice commands

**Status:** ⚠️ Requires additional setup
- Web Speech API for browser
- Or server-side speech recognition

**When to modify:**
- Adding voice features
- Improving recognition accuracy

---

#### `report_scanner.py` 🟢 LOW (Optional)
**Purpose:** Medical report OCR scanning

**What it does:**
- Extracts text from report images
- Parses medical data
- Identifies key values (blood test results, diagnoses)

**Status:** ⚠️ Requires OCR library (Tesseract, Google Vision API)

**When to modify:**
- Adding OCR functionality
- Improving data extraction

---

## ⚙️ CONFIG DIRECTORY (`config/`)

### `disease_knowledge_base.json` 🔴 CRITICAL
**Purpose:** Detailed disease information

**Structure:**
```json
{
  "Common Cold": {
    "description": "Viral infection of upper respiratory tract",
    "symptoms": ["runny nose", "sore throat", "cough", "sneezing"],
    "severity": "mild",
    "treatment": ["Rest", "Fluids", "OTC pain relievers"],
    "when_to_see_doctor": "If symptoms persist > 10 days",
    "complications": ["Sinusitis", "Ear infection"],
    "prevention": ["Hand washing", "Avoid sick people"],
    "prevalence": "Very Common"
  }
}
```

**Contains:**
- 15+ detailed diseases
- Symptoms, treatments, prevention
- When to seek care
- Severity classifications

**When to update:**
- Adding new diseases
- Updating medical information
- Adding treatment options

---

### `symptom_lexicon.json` 🔴 CRITICAL
**Purpose:** Symptom synonyms and variations

**Structure:**
```json
{
  "symptom_lexicon": {
    "Fever": ["high temperature", "feeling hot", "pyrexia", "raised temp"],
    "Headache": ["head pain", "head hurts", "migraine", "head ache"],
    "Nausea": ["feeling sick", "queasy", "upset stomach", "sick feeling"],
    "Abdominal pain": ["stomach ache", "tummy pain", "belly pain", "stomach hurts"]
  }
}
```

**Purpose:**
- Matches casual language to medical terms
- Improves symptom recognition
- Handles spelling variations

**When to update:**
- Adding new symptom terms
- Including regional variations
- Supporting multiple languages

---

### `enhanced_symptom_lexicon.json` 🟠 HIGH
**Purpose:** Extended symptom vocabulary

**Differences from basic lexicon:**
- More detailed mappings
- Context-specific terms
- Regional variations
- Medical jargon

**When to update:** Along with main symptom_lexicon.json

---

### `red_flags.json` 🔴 CRITICAL
**Purpose:** Emergency symptom detection

**Structure:**
```json
{
  "red_flags": [
    {
      "name": "Cardiac Emergency",
      "trigger_symptoms": ["chest pain", "severe chest pressure"],
      "department": "Emergency/Cardiology",
      "notes": "Call ambulance immediately. Possible heart attack.",
      "severity": "emergency"
    },
    {
      "name": "Respiratory Distress",
      "trigger_symptoms": ["difficulty breathing", "can't breathe"],
      "department": "Emergency",
      "notes": "Seek immediate emergency care.",
      "severity": "emergency"
    }
  ]
}
```

**Red Flags Include:**
- Chest pain
- Difficulty breathing
- Severe bleeding
- Loss of consciousness
- Stroke symptoms (FAST)
- Severe allergic reactions

**When to update:**
- Adding emergency conditions
- Updating medical protocols

---

### `conditions_list.json` 🟠 HIGH
**Purpose:** List of all diagnosable conditions

**Structure:**
```json
{
  "conditions": [
    {
      "name": "Common Cold",
      "symptoms": ["runny nose", "sore throat", "cough"],
      "severity": "mild",
      "department": "General Medicine"
    }
  ]
}
```

**When to update:**
- Adding new conditions
- Updating symptom lists

---

### `department_map.json` 🟡 MEDIUM
**Purpose:** Condition-to-department routing

**Structure:**
```json
{
  "Heart Attack": "Cardiology",
  "Diabetes": "Endocrinology",
  "Broken Bone": "Orthopedics",
  "Depression": "Psychiatry",
  "Pregnancy": "Obstetrics/Gynecology"
}
```

**When to update:**
- Adding specialties
- Updating mappings

---

### `medicine_database.json` 🟡 MEDIUM
**Purpose:** Comprehensive medicine information

**Structure:**
```json
{
  "Paracetamol": {
    "generic_name": "Acetaminophen",
    "brand_names": ["Tylenol", "Panadol"],
    "indications": ["fever", "pain", "headache"],
    "dosage": {
      "adults": "500-1000mg every 4-6 hours",
      "children": "10-15mg/kg every 4-6 hours",
      "max_daily": "4000mg"
    },
    "side_effects": ["nausea", "rash"],
    "contraindications": ["liver disease"],
    "interactions": ["alcohol", "warfarin"],
    "pregnancy_category": "B",
    "prescription_required": false
  }
}
```

**When to update:**
- Adding new medicines
- Updating dosages
- Adding interactions

---

## 📊 DATA DIRECTORY (`data/`)

### `comprehensive_symptom_disease_mapping.csv` 🔴 CRITICAL
**Purpose:** Core prediction dataset

**Structure:**
```csv
Disease,Symptom,Weight,Prevalence,Critical
Common Cold,Runny Nose,0.9,Very Common,No
Common Cold,Sore Throat,0.85,Very Common,No
Heart Attack,Chest Pain,0.95,Uncommon,Yes
Heart Attack,Shortness of Breath,0.9,Uncommon,Yes
```

**Contains:**
- 92 medical conditions
- 290 unique symptoms
- Symptom-disease relationships
- Probability weights
- Prevalence data
- Critical symptom flags

**Used by:** `disease_predictor.py`

**When to update:**
- Adding diseases
- Adjusting weights
- Including new research

---

### `symptom_dataset.csv` 🟠 HIGH
**Purpose:** Training data for ML models

**Structure:**
```csv
Symptoms,Disease,Urgency
"fever,headache,body aches",Influenza,Urgent
"chest pain,shortness of breath",Heart Attack,Emergency
"runny nose,sneezing",Common Cold,Self-Care
```

**Used by:** `triage_engine.py` for ML training

**When to update:**
- Retraining triage model
- Adding new training examples

---

### `hospitals_india.csv` 🟠 HIGH
**Purpose:** Hospital database

**Structure:**
```csv
hospital_name,city,state,location_lat,location_lon,departments_available,contact_number
"AIIMS Delhi","New Delhi","Delhi",28.5672,77.2100,"Cardiology,Neurology,Emergency","011-2658-8500"
```

**Contains:**
- Hospital names
- GPS coordinates
- Available departments
- Contact information
- City/state

**Used by:** `hospital_finder.py`

**When to update:**
- Adding new hospitals
- Updating contact info
- Correcting locations

---

### `hospitals.csv` 🟡 MEDIUM
**Purpose:** Alternative hospital database

**Similar to:** `hospitals_india.csv`
**Usage:** Backup or different region

---

## 🎨 FRONTEND DIRECTORY (`frontend/`)

### `index.html` (2850 lines) 🔴 CRITICAL
**Purpose:** Main web application

**Sections:**

1. **Header**
   - Logo, title
   - Theme toggle (dark/light)
   - Ask AI button

2. **Symptom Input Form**
   - Text area for symptoms
   - Location input
   - Patient information:
     - Age
     - Gender
     - Chronic conditions
   - Analyze button

3. **Results Display**
   - Professional analysis section
   - Primary diagnosis
   - Probability percentages
   - Differential diagnosis (top 5)
   - Treatment recommendations
   - When to see doctor

4. **AI Chat Interface**
   - Chat messages
   - Input field
   - Suggestion buttons
   - Diet recommendations
   - Voice input button

5. **Hospital Finder**
   - Location search
   - Department filter
   - Results list with distances

6. **Medicine Recommendations**
   - Medicine cards
   - Dosage information
   - Side effects
   - Safety warnings

**JavaScript Functions:**
```javascript
// Main analysis
analyzeSymptoms()
  - Collects form data
  - Sends to /api/query
  - Displays results

// Chat
sendChatMessageDirect()
  - Sends message to /api/conversation
  - Maintains chat history
  - Updates UI

// Diet
updateChatSuggestions()
  - Updates suggestion buttons
  - Shows diet recommendations

// Location
getCurrentLocation()
  - Gets user's GPS coordinates
  - Updates location field
```

**Global Variables:**
```javascript
currentDiagnosis = {
  condition: "Common Cold",
  probability: 85.2,
  department: "General Medicine",
  patient_context: { age: 30, gender: "male" }
}

chatHistory = [
  { role: "system", content: "Patient diagnosed with..." },
  { role: "user", content: "What should I eat?" },
  { role: "assistant", content: "For Common Cold..." }
]
```

**When to modify:**
- Adding UI features
- Changing layout
- Adding form fields

---

### `styles.css` (3700+ lines) 🔴 CRITICAL
**Purpose:** All visual styling

**Sections:**

1. **CSS Variables**
```css
:root {
  --primary-color: #3b82f6;
  --secondary-color: #10b981;
  --text-primary: #1f2937;
  --bg-primary: #ffffff;
}

.dark-theme {
  --text-primary: #f9fafb;
  --bg-primary: #111827;
}
```

2. **Base Styles**
   - Reset CSS
   - Typography
   - Color schemes

3. **Layout**
   - Grid system
   - Flexbox
   - Responsive breakpoints

4. **Components**
   - Buttons
   - Cards
   - Forms
   - Chat bubbles
   - Badges
   - Modals

5. **Professional Analysis**
   - Diagnosis cards
   - Probability badges
   - Differential diagnosis
   - Treatment info

6. **Diet Recommendations**
```css
.diet-main-header
.diet-section-header
.diet-list
.diet-note
.diet-disclaimer
```

7. **Dark Theme**
   - All dark mode overrides
   - Color adjustments
   - Contrast fixes

8. **Animations**
   - Fade in
   - Slide up
   - Typing indicator
   - Loading spinners

9. **Responsive Design**
   - Mobile breakpoints
   - Tablet layouts
   - Desktop optimizations

**When to modify:**
- Changing colors
- Adjusting layouts
- Adding animations
- Responsive fixes

---

### `client-enhancements.js` (22KB) 🟠 HIGH
**Purpose:** Additional frontend functionality

**Features:**
- Form validation
- API error handling
- Loading states
- Animations
- Utility functions

**When to modify:**
- Adding client-side features
- Improving UX
- Error handling

---

## 🤖 MACHINE LEARNING FILES (Not in Git)

### `triage_model.pkl`
**Type:** Scikit-learn classification model
**Size:** ~1-5 MB
**Purpose:** Predicts urgency from symptoms
**Training:** `symptom_dataset.csv`
**Why not in Git:** Large binary file

### `triage_vectorizer.pkl`
**Type:** TF-IDF or CountVectorizer
**Size:** ~500KB-2MB
**Purpose:** Converts text to features
**Why not in Git:** Large binary file

**To regenerate:**
```python
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
import pandas as pd
import pickle

# Load data
df = pd.read_csv('data/symptom_dataset.csv')

# Vectorize
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(df['Symptoms'])
y = df['Urgency']

# Train
model = MultinomialNB()
model.fit(X, y)

# Save
pickle.dump(model, open('triage_model.pkl', 'wb'))
pickle.dump(vectorizer, open('triage_vectorizer.pkl', 'wb'))
```

---

## 🔄 FILE DEPENDENCIES

### Dependency Graph:
```
api.py (Main Hub)
  ├── disease_predictor.py
  │   ├── disease_knowledge_base.json
  │   ├── symptom_lexicon.json
  │   └── comprehensive_symptom_disease_mapping.csv
  │
  ├── mistral_client.py
  │   └── .env (API keys)
  │
  ├── parser.py
  │   └── symptom_lexicon.json
  │
  ├── triage_engine.py
  │   ├── triage_model.pkl
  │   └── triage_vectorizer.pkl
  │
  ├── hospital_finder.py
  │   └── hospitals_india.csv
  │
  └── medicine_recommender.py
      └── medicine_database.json

index.html
  ├── styles.css
  ├── client-enhancements.js
  └── api.py (via HTTP)
```

---

## 📊 FILE SIZE REFERENCE

**Large Files (>50KB):**
- `frontend/index.html` - 119KB
- `frontend/styles.css` - 71KB
- `data/comprehensive_symptom_disease_mapping.csv` - varies
- `backend/app/disease_predictor.py` - ~30KB
- `backend/app/mistral_client.py` - ~25KB

**Medium Files (10-50KB):**
- `backend/app/api.py` - ~45KB
- `config/disease_knowledge_base.json` - varies
- `config/medicine_database.json` - varies

**Small Files (<10KB):**
- Most Python files
- Most config JSONs

---

## 🎯 MODIFICATION CHECKLIST

### Adding a New Disease:
✅ Update `disease_knowledge_base.json`
✅ Add to `comprehensive_symptom_disease_mapping.csv`
✅ Update `conditions_list.json`
✅ Add department to `department_map.json`
✅ Test with `disease_predictor.py`

### Adding a New Feature:
✅ Backend: Add function to appropriate module
✅ API: Add endpoint to `api.py`
✅ Frontend: Add UI in `index.html`
✅ Styling: Add CSS in `styles.css`
✅ Documentation: Update `README.md`

### Updating Medicine Database:
✅ Edit `medicine_database.json`
✅ Follow JSON structure
✅ Include all required fields
✅ Test with `medicine_recommender.py`

---

## 🚀 QUICK REFERENCE

### Files You'll Edit Most Often:
1. `backend/app/api.py` - Adding endpoints
2. `frontend/index.html` - UI changes
3. `frontend/styles.css` - Styling
4. `config/disease_knowledge_base.json` - Medical data
5. `.env` - API keys

### Files You Rarely Touch:
1. `.gitignore` - Set once
2. `requirements.txt` - Only when adding packages
3. `parser.py` - Works well as-is
4. `triage_engine.py` - Unless retraining

### Configuration Files Priority:
1. 🔴 `disease_knowledge_base.json`
2. 🔴 `symptom_lexicon.json`
3. 🟠 `red_flags.json`
4. 🟡 `medicine_database.json`
5. 🟡 `department_map.json`

---

## 📝 NOTES

**Security:**
- Never commit `.env` file
- Keep API keys secret
- Sanitize user inputs in production

**Performance:**
- Large CSV files load on startup
- Consider caching for production
- Optimize API calls

**Scalability:**
- Database for production (vs JSON files)
- Redis for caching
- Load balancing for high traffic

**Medical Disclaimer:**
- All files include disclaimers
- Not a replacement for doctors
- For educational purposes

---

**Last Updated:** November 3, 2025
**Version:** 1.0
**Total Files:** 30
**Total Lines of Code:** ~13,000+
