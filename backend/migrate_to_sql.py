"""
Migration script to transfer data from JSON/CSV files to SQL database
Run this once after setting up the database
"""
import json
import pandas as pd
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent / 'app'))

from database import (
    init_db, get_db_session, test_connection,
    Disease, Symptom, DiseaseSymptom, Hospital, HospitalDepartment, Medicine
)


def migrate_diseases():
    """Migrate disease_knowledge_base.json to SQL"""
    print("\n📊 Migrating diseases...")
    db = get_db_session()
    
    try:
        # Load JSON file
        json_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'disease_knowledge_base.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        for disease_name, info in data.items():
            # Check if disease already exists
            existing = db.query(Disease).filter(Disease.name == disease_name).first()
            if existing:
                print(f"  ⚠️  Skipping {disease_name} (already exists)")
                continue
            
            disease = Disease(
                name=disease_name,
                description=info.get('description', ''),
                severity=info.get('severity', 'unknown'),
                prevalence=info.get('prevalence', 'unknown'),
                treatment=', '.join(info.get('treatment', [])),
                when_to_see_doctor=info.get('when_to_see_doctor', ''),
                complications=', '.join(info.get('complications', [])),
                prevention=', '.join(info.get('prevention', []))
            )
            db.add(disease)
            count += 1
        
        db.commit()
        print(f"✅ Migrated {count} diseases")
        
    except FileNotFoundError:
        print(f"❌ Could not find disease_knowledge_base.json at {json_path}")
    except Exception as e:
        print(f"❌ Error migrating diseases: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_symptoms():
    """Migrate symptom_lexicon.json to SQL"""
    print("\n📊 Migrating symptoms...")
    db = get_db_session()
    
    try:
        # Load JSON file
        json_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'symptom_lexicon.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        symptom_lexicon = data.get('symptom_lexicon', {})
        
        for symptom_name, synonyms in symptom_lexicon.items():
            # Check if symptom already exists
            existing = db.query(Symptom).filter(Symptom.name == symptom_name).first()
            if existing:
                print(f"  ⚠️  Skipping {symptom_name} (already exists)")
                continue
            
            symptom = Symptom(
                name=symptom_name,
                synonyms=', '.join(synonyms) if isinstance(synonyms, list) else ''
            )
            db.add(symptom)
            count += 1
        
        db.commit()
        print(f"✅ Migrated {count} symptoms")
        
    except FileNotFoundError:
        print(f"❌ Could not find symptom_lexicon.json at {json_path}")
    except Exception as e:
        print(f"❌ Error migrating symptoms: {e}")
        db.rollback()
    finally:
        db.close()


def migrate_disease_symptom_mapping():
    """Migrate comprehensive_symptom_disease_mapping.csv to SQL"""
    print("\n📊 Migrating disease-symptom mappings...")
    db = get_db_session()
    
    try:
        # Load CSV file
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'comprehensive_symptom_disease_mapping.csv')
        df = pd.read_csv(csv_path)
        
        count = 0
        skipped = 0
        diseases_added = 0
        symptoms_added = 0
        
        for _, row in df.iterrows():
            condition = row['condition']
            primary_symptoms = str(row['primary_symptoms']).split(',')
            secondary_symptoms = str(row.get('secondary_symptoms', '')).split(',')
            all_symptoms = primary_symptoms + secondary_symptoms
            
            # Get or create disease
            disease = db.query(Disease).filter(Disease.name == condition).first()
            if not disease:
                disease = Disease(
                    name=condition,
                    description=row.get('description', ''),
                    severity=row.get('severity', 'unknown'),
                    prevalence=row.get('prevalence', 'unknown'),
                    treatment='See doctor for treatment recommendations',
                    when_to_see_doctor='Consult a healthcare provider if symptoms persist or worsen'
                )
                db.add(disease)
                db.flush()
                diseases_added += 1
            
            # Process each symptom
            for symptom_text in all_symptoms:
                symptom_text = symptom_text.strip()
                if not symptom_text or symptom_text == 'nan':
                    continue
                
                # Get or create symptom
                symptom = db.query(Symptom).filter(Symptom.name == symptom_text).first()
                if not symptom:
                    symptom = Symptom(name=symptom_text, synonyms='')
                    db.add(symptom)
                    db.flush()
                    symptoms_added += 1
                
                # Check if mapping already exists
                existing = db.query(DiseaseSymptom).filter(
                    DiseaseSymptom.disease_id == disease.id,
                    DiseaseSymptom.symptom_id == symptom.id
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                # Create mapping with higher weight for primary symptoms
                is_primary = symptom_text in primary_symptoms
                weight = 0.9 if is_primary else 0.6
                is_critical = row.get('severity', '') in ['emergency', 'urgent']
                
                mapping = DiseaseSymptom(
                    disease_id=disease.id,
                    symptom_id=symptom.id,
                    weight=weight,
                    is_critical=is_critical
                )
                db.add(mapping)
                count += 1
        
        db.commit()
        print(f"✅ Migrated {count} disease-symptom mappings")
        print(f"   Added {diseases_added} new diseases, {symptoms_added} new symptoms (skipped {skipped} duplicates)")
        
    except FileNotFoundError:
        print(f"❌ Could not find comprehensive_symptom_disease_mapping.csv at {csv_path}")
    except Exception as e:
        print(f"❌ Error migrating mappings: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def migrate_hospitals():
    """Migrate hospitals_india.csv to SQL"""
    print("\n📊 Migrating hospitals...")
    db = get_db_session()
    
    try:
        # Load CSV file
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'hospitals_india.csv')
        df = pd.read_csv(csv_path)
        
        count = 0
        dept_count = 0
        
        # Common coordinates for cities (approximate)
        city_coords = {
            'Hyderabad': (17.3850, 78.4867),
            'New Delhi': (28.6139, 77.2090),
            'Noida': (28.5355, 77.3910),
            'Mumbai': (19.0760, 72.8777),
            'Bangalore': (12.9716, 77.5946),
            'Chennai': (13.0827, 80.2707),
            'Kolkata': (22.5726, 88.3639),
            'Pune': (18.5204, 73.8567),
            'Ahmedabad': (23.0225, 72.5714),
            'Jaipur': (26.9124, 75.7873)
        }
        
        for _, row in df.iterrows():
            # Check if hospital already exists
            existing = db.query(Hospital).filter(
                Hospital.name == row['hospital_name'],
                Hospital.city == row['city']
            ).first()
            
            if existing:
                continue
            
            # Get coordinates for the city
            city = row.get('city', '')
            lat, lon = city_coords.get(city, (None, None))
            
            hospital = Hospital(
                name=row['hospital_name'],
                city=city,
                state=row.get('state', ''),
                latitude=lat,
                longitude=lon,
                contact_number=str(row.get('phone', ''))
            )
            db.add(hospital)
            db.flush()  # Get hospital.id
            
            # Add department
            if pd.notna(row.get('department')):
                dept_name = str(row['department']).strip()
                if dept_name:
                    dept_obj = HospitalDepartment(
                        hospital_id=hospital.id,
                        department_name=dept_name
                    )
                    db.add(dept_obj)
                    dept_count += 1
            
            count += 1
        
        db.commit()
        print(f"✅ Migrated {count} hospitals with {dept_count} departments")
        
    except FileNotFoundError:
        print(f"❌ Could not find hospitals_india.csv at {csv_path}")
    except Exception as e:
        print(f"❌ Error migrating hospitals: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


def migrate_medicines():
    """Migrate medicine_database.json to SQL"""
    print("\n📊 Migrating medicines...")
    db = get_db_session()
    
    try:
        # Load JSON file
        json_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'medicine_database.json')
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        count = 0
        
        for medicine_name, info in data.items():
            # Check if medicine already exists
            existing = db.query(Medicine).filter(Medicine.name == medicine_name).first()
            if existing:
                print(f"  ⚠️  Skipping {medicine_name} (already exists)")
                continue
            
            # Convert lists to comma-separated strings
            indications = info.get('indications', [])
            if isinstance(indications, list):
                indications = ', '.join(indications)
            
            side_effects = info.get('side_effects', [])
            if isinstance(side_effects, list):
                side_effects = ', '.join(side_effects)
            
            contraindications = info.get('contraindications', [])
            if isinstance(contraindications, list):
                contraindications = ', '.join(contraindications)
            
            interactions = info.get('interactions', [])
            if isinstance(interactions, list):
                interactions = ', '.join(interactions)
            
            medicine = Medicine(
                name=medicine_name,
                generic_name=info.get('generic_name', ''),
                indications=indications,
                dosage=str(info.get('dosage', '')),
                side_effects=side_effects,
                contraindications=contraindications,
                interactions=interactions,
                prescription_required=info.get('prescription_required', False)
            )
            db.add(medicine)
            count += 1
        
        db.commit()
        print(f"✅ Migrated {count} medicines")
        
    except FileNotFoundError:
        print(f"❌ Could not find medicine_database.json at {json_path}")
    except Exception as e:
        print(f"❌ Error migrating medicines: {e}")
        db.rollback()
    finally:
        db.close()


def verify_migration():
    """Verify that data was migrated successfully"""
    print("\n🔍 Verifying migration...")
    db = get_db_session()
    
    try:
        disease_count = db.query(Disease).count()
        symptom_count = db.query(Symptom).count()
        mapping_count = db.query(DiseaseSymptom).count()
        hospital_count = db.query(Hospital).count()
        dept_count = db.query(HospitalDepartment).count()
        medicine_count = db.query(Medicine).count()
        
        print(f"\n📊 Database Statistics:")
        print(f"  • Diseases: {disease_count}")
        print(f"  • Symptoms: {symptom_count}")
        print(f"  • Disease-Symptom Mappings: {mapping_count}")
        print(f"  • Hospitals: {hospital_count}")
        print(f"  • Hospital Departments: {dept_count}")
        print(f"  • Medicines: {medicine_count}")
        
        if disease_count > 0 and symptom_count > 0:
            print("\n✅ Migration verification passed!")
            return True
        else:
            print("\n⚠️  Warning: Some tables appear empty")
            return False
            
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        return False
    finally:
        db.close()


def main():
    """Main migration process"""
    print("=" * 70)
    print("🏥 HEALTH AI - DATA MIGRATION TOOL")
    print("=" * 70)
    
    # Test database connection
    print("\n1️⃣  Testing database connection...")
    if not test_connection():
        print("\n❌ Cannot connect to database!")
        print("Please check:")
        print("  1. PostgreSQL is installed and running")
        print("  2. Database 'healthai' exists")
        print("  3. DATABASE_URL in .env is correct")
        print("\nExample: DATABASE_URL=postgresql://postgres:password@localhost:5432/healthai")
        return
    
    # Initialize database (create tables)
    print("\n2️⃣  Initializing database tables...")
    init_db()
    
    # Migrate data
    print("\n3️⃣  Migrating data from JSON/CSV files...")
    
    migrate_diseases()
    migrate_symptoms()
    migrate_disease_symptom_mapping()
    migrate_hospitals()
    migrate_medicines()
    
    # Verify migration
    print("\n4️⃣  Verifying migration...")
    if verify_migration():
        print("\n" + "=" * 70)
        print("✅ MIGRATION COMPLETED SUCCESSFULLY!")
        print("=" * 70)
        print("\nYou can now:")
        print("  1. Update backend code to use SQL database")
        print("  2. Run the Flask API server")
        print("  3. Test the application with real database")
    else:
        print("\n⚠️  Migration completed with warnings")


if __name__ == "__main__":
    main()
