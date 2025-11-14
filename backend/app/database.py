"""
Database configuration and SQLAlchemy models for Health AI
"""
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DECIMAL, Boolean, TIMESTAMP, ForeignKey, ARRAY, text
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.sql import func
from dotenv import load_dotenv

load_dotenv()

# Database connection string
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/healthai')

# Create engine
engine = create_engine(DATABASE_URL, echo=False)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


# ==================== MODELS ====================

class Disease(Base):
    """Disease information table"""
    __tablename__ = 'diseases'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text)
    severity = Column(String(20))
    prevalence = Column(String(20))
    treatment = Column(Text)
    when_to_see_doctor = Column(Text)
    complications = Column(Text)
    prevention = Column(Text)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    symptoms = relationship('DiseaseSymptom', back_populates='disease', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Disease(name='{self.name}', severity='{self.severity}')>"


class Symptom(Base):
    """Symptoms table with synonyms"""
    __tablename__ = 'symptoms'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    synonyms = Column(Text)  # Stored as comma-separated string
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    diseases = relationship('DiseaseSymptom', back_populates='symptom', cascade='all, delete-orphan')
    
    def get_synonyms_list(self):
        """Return synonyms as list"""
        if self.synonyms:
            return [s.strip() for s in self.synonyms.split(',')]
        return []
    
    def set_synonyms_list(self, synonym_list):
        """Set synonyms from list"""
        self.synonyms = ', '.join(synonym_list)
    
    def __repr__(self):
        return f"<Symptom(name='{self.name}')>"


class DiseaseSymptom(Base):
    """Many-to-many relationship between diseases and symptoms with weights"""
    __tablename__ = 'disease_symptoms'
    
    id = Column(Integer, primary_key=True, index=True)
    disease_id = Column(Integer, ForeignKey('diseases.id', ondelete='CASCADE'), nullable=False)
    symptom_id = Column(Integer, ForeignKey('symptoms.id', ondelete='CASCADE'), nullable=False)
    weight = Column(DECIMAL(3, 2), default=0.5)  # 0.00 to 1.00
    is_critical = Column(Boolean, default=False)
    
    # Relationships
    disease = relationship('Disease', back_populates='symptoms')
    symptom = relationship('Symptom', back_populates='diseases')
    
    def __repr__(self):
        return f"<DiseaseSymptom(disease_id={self.disease_id}, symptom_id={self.symptom_id}, weight={self.weight})>"


class Hospital(Base):
    """Hospital information with location"""
    __tablename__ = 'hospitals'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100))
    state = Column(String(100))
    latitude = Column(DECIMAL(10, 8))
    longitude = Column(DECIMAL(11, 8))
    contact_number = Column(String(20))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    departments = relationship('HospitalDepartment', back_populates='hospital', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<Hospital(name='{self.name}', city='{self.city}')>"


class HospitalDepartment(Base):
    """Hospital departments/specialties"""
    __tablename__ = 'hospital_departments'
    
    id = Column(Integer, primary_key=True, index=True)
    hospital_id = Column(Integer, ForeignKey('hospitals.id', ondelete='CASCADE'), nullable=False)
    department_name = Column(String(100), nullable=False)
    
    # Relationships
    hospital = relationship('Hospital', back_populates='departments')
    
    def __repr__(self):
        return f"<HospitalDepartment(hospital_id={self.hospital_id}, dept='{self.department_name}')>"


class Medicine(Base):
    """Medicine information and recommendations"""
    __tablename__ = 'medicines'
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    generic_name = Column(String(200))
    indications = Column(Text)  # Stored as comma-separated
    dosage = Column(Text)
    side_effects = Column(Text)  # Stored as comma-separated
    contraindications = Column(Text)  # Stored as comma-separated
    interactions = Column(Text)  # Stored as comma-separated
    prescription_required = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    def get_indications_list(self):
        """Return indications as list"""
        if self.indications:
            return [s.strip() for s in self.indications.split(',')]
        return []
    
    def get_side_effects_list(self):
        """Return side effects as list"""
        if self.side_effects:
            return [s.strip() for s in self.side_effects.split(',')]
        return []
    
    def __repr__(self):
        return f"<Medicine(name='{self.name}', generic='{self.generic_name}')>"


class UserSession(Base):
    """Track user sessions and diagnoses (optional)"""
    __tablename__ = 'user_sessions'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, nullable=False, index=True)
    symptoms_input = Column(Text)
    predicted_disease = Column(String(100))
    probability = Column(DECIMAL(5, 2))
    patient_age = Column(Integer)
    patient_gender = Column(String(20))
    location_lat = Column(DECIMAL(10, 8))
    location_lon = Column(DECIMAL(11, 8))
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    chat_messages = relationship('ChatHistory', back_populates='session', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f"<UserSession(session_id='{self.session_id}', disease='{self.predicted_disease}')>"


class ChatHistory(Base):
    """Store chat conversation history (optional)"""
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), ForeignKey('user_sessions.session_id', ondelete='CASCADE'), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant' or 'system'
    message = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    session = relationship('UserSession', back_populates='chat_messages')
    
    def __repr__(self):
        return f"<ChatHistory(session_id='{self.session_id}', role='{self.role}')>"


# ==================== DATABASE FUNCTIONS ====================

def init_db():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def drop_all_tables():
    """Drop all tables (use with caution!)"""
    Base.metadata.drop_all(bind=engine)
    print("⚠️  All tables dropped!")


def get_db():
    """Get database session (use with context manager or try/finally)"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_db_session():
    """Get database session directly (remember to close!)"""
    return SessionLocal()


# ==================== UTILITY FUNCTIONS ====================

def test_connection():
    """Test database connection"""
    try:
        db = SessionLocal()
        # Try a simple query
        result = db.execute(text("SELECT 1"))
        db.close()
        print("✅ Database connection successful!")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


if __name__ == "__main__":
    print("🔧 Health AI Database Setup")
    print("=" * 50)
    
    # Test connection
    print("\n1. Testing database connection...")
    if test_connection():
        
        # Initialize database
        print("\n2. Creating database tables...")
        init_db()
        
        print("\n✅ Database setup complete!")
        print("\nTables created:")
        print("  - diseases")
        print("  - symptoms")
        print("  - disease_symptoms")
        print("  - hospitals")
        print("  - hospital_departments")
        print("  - medicines")
        print("  - user_sessions (optional)")
        print("  - chat_history (optional)")
    else:
        print("\n❌ Please check your DATABASE_URL in .env file")
        print("Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/healthai")
