# 🏥 HealthAI - Medical Assistant with Live Location Hospital Finder

## 📁 Project Structure (Clean & Organized)

```
Project 4th Year/
├── backend/                          # Backend API
│   ├── app/
│   │   ├── api.py                    # ⭐ MAIN API (All routes here!)
│   │   ├── hospital_finder.py        # Hospital finder class
│   │   ├── medicine_recommender.py   # Medicine recommendations
│   │   ├── parser.py                 # AI symptom parser (optional)
│   │   ├── triage_engine.py          # AI triage (optional)
│   │   ├── mistral_client.py         # AI client (optional)
│   │   ├── voice_processor.py        # Voice features (optional)
│   │   ├── report_scanner.py         # Report scanning (optional)
│   │   └── department_mapper.py      # Department mapping
│   ├── run.py                        # 🚀 START SERVER (python run.py)
│   └── requirements.txt              # Python dependencies
│
├── frontend/                         # Frontend Web App
│   ├── index.html                    # ⭐ Main web page
│   ├── styles.css                    # Styling
│   └── client-enhancements.js        # JavaScript enhancements
│
├── config/                           # Configuration files
│   ├── symptom_lexicon.json         # Symptom mappings
│   ├── red_flags.json               # Emergency symptoms
│   ├── conditions_list.json         # Medical conditions
│   ├── department_map.json          # Hospital departments
│   └── medicine_database.json       # Medicine data
│
├── data/                             # Database files
│   ├── hospitals_india.csv          # ⭐ 40 hospitals (MAIN DATA)
│   ├── hospitals.csv                # Legacy hospital data
│   ├── comprehensive_symptom_disease_mapping.csv  # 95 diseases
│   └── symptom_dataset.csv          # Symptom patterns
│
└── docs/                             # Documentation (essential only)
    ├── README.md                     # This file
    ├── FEATURE_COMPLETE.md           # Feature summary
    ├── LIVE_LOCATION_HOSPITAL_FINDER.md  # Main feature docs
    ├── QUICK_TEST_GUIDE.md           # Testing guide
    ├── SINGLE_API_ARCHITECTURE.md    # Architecture guide
    └── MEDICAL_DATASETS_DOCUMENTATION.md  # Data docs
```

## 🚀 Quick Start

### **Step 1: Activate Virtual Environment**
```bash
& "F:/Project 4th Year/.venv/Scripts/Activate.ps1"
```

### **Step 2: Start Backend Server**
```bash
cd "f:\Project 4th Year"
python -m backend.app.api
```
**Wait for**: `Running on http://127.0.0.1:5000`

### **Step 3: Start Frontend Server** (New Terminal)
```bash
cd "f:\Project 4th Year\frontend"
python -m http.server 8000
```

### **Step 4: Open Browser**
```
http://localhost:8000
```

### **Step 5: Test Main Feature**
1. Click "Find Nearby Hospitals" (green button)
2. Allow location access
3. See hospitals sorted by distance!

📖 **For detailed instructions**, see [EXECUTION_GUIDE.md](EXECUTION_GUIDE.md)

## 🎯 Main Feature

**Live Location Hospital Finder**
- Click "Find Nearby Hospitals" button
- Allow location access
- See 40+ hospitals sorted by distance
- Get directions and call hospitals directly

## 📊 What's Included

### Backend (api.py)
- ✅ 14 API routes
- ✅ Hospital Finder (main feature)
- ✅ Medicine Recommendations
- ✅ Symptom Analysis
- ✅ AI Features (optional)
- ✅ Voice Features (optional)

### Frontend
- ✅ Beautiful UI with split-view
- ✅ AI Chat Interface
- ✅ Voice Input/Output
- ✅ Hospital Finder Button
- ✅ Mobile Responsive

### Data
- ✅ 40 real hospitals across 16 cities
- ✅ 95 diseases with symptoms
- ✅ 100+ symptom variations
- ✅ Medicine database

## 🗑️ Cleaned Up Files

**Deleted (were duplicates/unnecessary):**
- ❌ 15+ redundant documentation files
- ❌ Test files (test_*.py)
- ❌ Old API files (main_api.py, simple_api.py)
- ❌ Debug HTML files
- ❌ Workflow txt files
- ❌ Duplicate guides

**Kept (essential only):**
- ✅ Working code files
- ✅ Main documentation (6 files)
- ✅ Configuration & data files

## 📝 Essential Documentation

1. **README.md** - This file (overview)
2. **FEATURE_COMPLETE.md** - Feature summary
3. **LIVE_LOCATION_HOSPITAL_FINDER.md** - Main feature docs
4. **QUICK_TEST_GUIDE.md** - Testing guide
5. **SINGLE_API_ARCHITECTURE.md** - Architecture
6. **MEDICAL_DATASETS_DOCUMENTATION.md** - Data documentation

## 🎓 Technologies Used

- **Backend**: Python, Flask, Pandas
- **Frontend**: HTML5, CSS3, JavaScript
- **APIs**: Geolocation API, Google Maps
- **Data**: CSV, JSON
- **Algorithm**: Haversine formula

## ✅ Project Status

**Status**: 🟢 Production Ready

**Working Features:**
- ✅ Live location hospital finder
- ✅ Symptom analysis
- ✅ Medicine recommendations
- ✅ AI chat interface
- ✅ Voice input/output
- ✅ Mobile responsive

## 📞 Support

Check the documentation files for:
- Testing instructions
- API documentation
- Feature details
- Troubleshooting

---

**Version**: 1.0.0  
**Last Updated**: 2025  
**Status**: ✅ Complete & Clean
