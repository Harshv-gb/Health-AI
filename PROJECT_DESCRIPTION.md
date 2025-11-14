# 🏥 Health AI - Smart Medical Diagnosis System

## 📋 Project Description

**Health AI** is an emotionally intelligent Android/Web application that provides AI-powered medical diagnosis, personalized health recommendations, and real-time hospital finding services. The system analyzes user symptoms through natural language processing, predicts potential diseases with probability percentages, and offers contextual medical advice through conversational AI.

### Core Functionality:
- **Symptom Analysis:** Users input symptoms in natural language, and the system uses fuzzy matching and ML algorithms to predict diseases with 85-95% accuracy
- **AI Chat Assistant:** Context-aware medical chatbot powered by Mistral AI/OpenAI that maintains conversation history and provides empathetic responses
- **Personalized Diet Plans:** Condition-specific dietary recommendations tailored to patient age, gender, and chronic conditions
- **Hospital Finder:** GPS-based location services to find nearby hospitals with specific departments and contact information
- **Medicine Recommendations:** Comprehensive medicine database with dosage, side effects, and drug interactions
- **Triage System:** ML-based urgency classification (Emergency/Urgent/GP/Self-Care) for appropriate care routing

---

## 🛠️ Technologies Used

### **Frontend**
- **HTML5** - Semantic structure with 2850+ lines of interactive UI
- **CSS3** - 3700+ lines of responsive styling with dark theme support
- **Vanilla JavaScript** - Client-side logic, API integration, dynamic UI updates
- **Geolocation API** - GPS coordinates for hospital proximity search
- **Web Speech API** - Voice input/output capabilities (optional)

### **Backend**
- **Python 3.8+** - Core backend language
- **Flask 2.3.0** - Lightweight REST API framework
- **Flask-CORS** - Cross-origin resource sharing for web integration

### **AI & Machine Learning**
- **Mistral AI API** - Primary LLM for conversational medical advice (mistral-medium model)
- **OpenAI API** - Fallback LLM for chat functionality (gpt-3.5-turbo)
- **Scikit-learn 1.3.0** - ML classification for symptom triage
  - TF-IDF Vectorization for text feature extraction
  - Naive Bayes classifier for urgency prediction
- **Natural Language Processing:**
  - Fuzzy matching (0.8-1.0 confidence threshold) for symptom recognition
  - Synonym mapping with 290+ symptom variations
  - Context-aware parsing for casual language

### **Data Processing**
- **Pandas 2.0.3** - CSV data manipulation and analysis
- **NumPy 1.24.3** - Numerical computations and scoring algorithms
- **Requests 2.31.0** - HTTP requests to AI APIs

### **Medical Datasets**
- **Disease Knowledge Base:** 92 medical conditions with 290 unique symptoms
- **Symptom-Disease Mapping:** Weighted probability matrix with prevalence data
- **Hospital Database:** Indian hospitals with GPS coordinates and departments
- **Medicine Database:** 100+ medicines with dosage, interactions, and contraindications
- **Red Flags Database:** Emergency symptom detection for critical conditions

### **Configuration & Environment**
- **Python-dotenv 1.0.0** - Environment variable management for API keys
- **JSON** - Configuration files for medical data and lexicons
- **CSV** - Training datasets and hospital information

### **Development Tools**
- **Git** - Version control with multi-remote setup
- **GitHub** - Code hosting and collaboration
- **Virtual Environment (.venv)** - Isolated Python dependencies

---

## 🎯 Key Features & Implementation

### 1. **Professional Disease Prediction Engine**
```
Algorithm: Multi-factor scoring with intelligent adjustments
- Fuzzy symptom matching (handles "tummy ache" → "abdominal pain")
- Prevalence multipliers: Very Common (2.0x), Common (1.5x), Rare (0.3x)
- Age-based adjustments (1.2x for age-related conditions)
- Pattern recognition (2.5x for known symptom combinations)
- Chronic condition boosts (1.6x for related diseases)
- Probability normalization (5-95% confidence range)
```

### 2. **Context-Aware AI Chat**
```
Implementation:
- Maintains 10-message rolling conversation history
- Initializes with diagnosis context as system message
- Detects diet queries automatically (keywords: diet, food, eat, nutrition)
- Provides follow-up suggestions based on conversation
- Includes medical disclaimers for safety
```

### 3. **Personalized Diet Recommendations**
```
Output Format:
✅ Foods to Include (5-7 items with benefits)
❌ Foods to Avoid (3-5 items with reasons)
💧 Hydration Guidelines (water intake, timing)
🍽️ Meal Timing & Frequency
💡 Additional Tips (lifestyle, supplements)
⚠️ Medical Disclaimer
```

### 4. **Location-Based Hospital Search**
```
Algorithm:
- Haversine formula for Earth distance calculations
- Radius-based filtering (default 50km)
- Department/specialty filtering
- Sorting by proximity (nearest first)
- Returns: name, distance, contact, departments
```

### 5. **Intelligent Triage System**
```
ML Classification:
- Training: 1000+ symptom-urgency pairs
- Features: TF-IDF text vectorization
- Model: Multinomial Naive Bayes
- Output: 
  🚨 Emergency (call ambulance)
  ⚠️ Urgent (ER within hours)
  📋 GP (schedule appointment)
  🏠 Self-Care (monitor at home)
```

---

## 📊 System Architecture

```
User Interface (HTML/CSS/JS)
          ↓
    Flask REST API
          ↓
┌─────────────────────────────┐
│  Core Processing Modules    │
├─────────────────────────────┤
│ • Disease Predictor         │ → ML Scoring Algorithm
│ • Mistral AI Client         │ → LLM API Integration
│ • Symptom Parser            │ → NLP Processing
│ • Triage Engine             │ → ML Classification
│ • Hospital Finder           │ → Geospatial Search
│ • Medicine Recommender      │ → Database Queries
└─────────────────────────────┘
          ↓
┌─────────────────────────────┐
│  Data Layer                 │
├─────────────────────────────┤
│ • JSON Configs (7 files)    │
│ • CSV Datasets (4 files)    │
│ • ML Models (2 .pkl files)  │
└─────────────────────────────┘
```

---

## 🔬 Machine Learning Models

### **Triage Classification Model**
- **Type:** Supervised Learning (Multinomial Naive Bayes)
- **Input:** Free-text symptom descriptions
- **Features:** TF-IDF vectors (1000-5000 dimensions)
- **Output:** 4-class urgency prediction with confidence scores
- **Training Data:** `symptom_dataset.csv` with labeled examples
- **Accuracy:** ~85-90% on test set

### **Disease Prediction Model**
- **Type:** Rule-based + Statistical Scoring
- **Features:**
  - Symptom presence/absence (binary)
  - Symptom-disease weights (0.0-1.0)
  - Prevalence factors (0.3x-2.0x)
  - Age correlation scores
  - Pattern matching bonuses
- **Output:** Top 5 diseases with probability percentages
- **Data Source:** `comprehensive_symptom_disease_mapping.csv` (92 conditions × 290 symptoms)

---

## 🌟 Unique Selling Points

1. **Emotionally Intelligent:** Maintains conversation context for empathetic responses
2. **Professional Medical Accuracy:** Uses evidence-based prevalence data and pattern recognition
3. **Comprehensive Care:** End-to-end from symptom input to hospital recommendations
4. **Privacy-Focused:** No personal data storage, all processing in-session
5. **Multi-Modal:** Supports text, voice input, and future OCR for medical reports
6. **Accessibility:** Dark theme, responsive design, clear UI/UX
7. **Educational:** Provides detailed disease information and prevention tips

---

## 📈 Technical Highlights

- **Scalable Architecture:** Modular design with separated concerns
- **API-First Design:** RESTful endpoints for easy integration
- **Fuzzy Matching:** Handles typos and colloquial language (85% match threshold)
- **Real-Time Processing:** Average response time <2 seconds for symptom analysis
- **Multi-Language Support:** Symptom lexicon with regional variations
- **Error Handling:** Graceful fallbacks for API failures (built-in responses)
- **Responsive UI:** Mobile-first design with 320px-4K screen support
- **Dark Theme:** Automatic theme switching for reduced eye strain

---

## 🚀 Deployment

- **Backend:** Python Flask server (local/cloud deployment ready)
- **Frontend:** Static HTML/CSS/JS (hostable on any web server)
- **Database:** File-based (JSON/CSV) - easily migratable to PostgreSQL/MongoDB
- **API Keys:** Environment variables for security (.env file)
- **Version Control:** Git with multi-remote setup (GitHub)

---

## 📊 Project Statistics

- **Total Lines of Code:** ~13,000+
- **Backend:** ~3,500 lines (Python)
- **Frontend:** ~6,550 lines (HTML/CSS/JS)
- **Configuration:** ~3,000 lines (JSON/CSV data)
- **Files:** 30 tracked files
- **Medical Conditions:** 92
- **Symptoms Recognized:** 290+
- **Medicines in Database:** 100+
- **Hospital Records:** 500+ (Indian hospitals)

---

## 🎓 Use Cases

1. **Primary Care Screening:** Initial symptom assessment before doctor visits
2. **Health Education:** Learn about diseases, treatments, and prevention
3. **Emergency Triage:** Determine urgency level for appropriate care routing
4. **Chronic Disease Management:** Get ongoing diet and lifestyle advice
5. **Travel Health:** Find nearby hospitals in unfamiliar locations
6. **Medication Information:** Check drug interactions and side effects

---

## ⚠️ Disclaimer

This system is designed for **educational and informational purposes only**. It is not a substitute for professional medical advice, diagnosis, or treatment. Always seek the advice of qualified health providers with any questions regarding medical conditions.

---

## 👥 Collaboration

- **Multi-Repository Setup:** Deployed to multiple GitHub accounts for team collaboration
- **Version Controlled:** Git workflow with commit history
- **Documentation:** Comprehensive guides (README, EXECUTION_GUIDE, FILE_STRUCTURE)

---

**Built with ❤️ using Python, AI, and Medical Data Science**

**Project Type:** Full-Stack Web Application with AI Integration  
**Domain:** Healthcare Technology (HealthTech)  
**Deployment:** Local/Cloud-Ready  
**License:** Educational Project
