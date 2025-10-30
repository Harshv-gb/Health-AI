# report_scanner.py - Medical Report OCR and Analysis
import os
import io
import cv2
import numpy as np
import pytesseract
from PIL import Image
import PyPDF2
import docx
import re
import json

class MedicalReportScanner:
    def __init__(self):
        """Initialize the medical report scanner"""
        # Try to configure Tesseract path for Windows
        try:
            import pytesseract
            # Common Tesseract installation paths on Windows
            tesseract_paths = [
                r'C:\Program Files\Tesseract-OCR\tesseract.exe',
                r'C:\Program Files (x86)\Tesseract-OCR\tesseract.exe',
                r'C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe'.format(os.environ.get('USERNAME', '')),
                'tesseract'  # If in PATH
            ]
            
            for path in tesseract_paths:
                if os.path.exists(path) or path == 'tesseract':
                    pytesseract.pytesseract.tesseract_cmd = path
                    # Test if Tesseract works
                    try:
                        pytesseract.get_tesseract_version()
                        self.ocr_available = True
                        print(f"✅ Tesseract OCR found at: {path}")
                        break
                    except:
                        continue
            else:
                self.ocr_available = False
                print("⚠️ Tesseract OCR not found. Install from: https://github.com/UB-Mannheim/tesseract/wiki")
                
        except ImportError:
            self.ocr_available = False
            print("⚠️ pytesseract not installed. Run: pip install pytesseract")
        
        # Common medical terms and patterns to look for
        self.medical_keywords = [
            'blood pressure', 'bp', 'heart rate', 'pulse', 'temperature', 'fever',
            'hemoglobin', 'hb', 'glucose', 'sugar', 'cholesterol', 'triglycerides',
            'white blood cells', 'wbc', 'red blood cells', 'rbc', 'platelets',
            'creatinine', 'urea', 'bilirubin', 'protein', 'albumin',
            'diagnosis', 'symptoms', 'treatment', 'medication', 'prescription',
            'normal', 'abnormal', 'high', 'low', 'elevated', 'decreased'
        ]
        
        self.vital_patterns = {
            'blood_pressure': r'(?:bp|blood pressure)[:\s]*(\d{2,3}[/\\]\d{2,3})',
            'heart_rate': r'(?:heart rate|pulse)[:\s]*(\d{2,3})\s*(?:bpm|beats)',
            'temperature': r'(?:temp|temperature)[:\s]*(\d{2,3}(?:\.\d)?)\s*(?:°f|°c|f|c)',
            'glucose': r'(?:glucose|sugar)[:\s]*(\d{2,3})\s*(?:mg/dl|mmol)',
            'hemoglobin': r'(?:hemoglobin|hb)[:\s]*(\d{1,2}(?:\.\d)?)\s*(?:g/dl|g%)'
        }
    
    def extract_text_from_image(self, image_data):
        """Extract text from image using OCR"""
        try:
            if not self.ocr_available:
                return "OCR not available. Please install Tesseract OCR. See TESSERACT_SETUP.md for instructions."
            
            # Convert bytes to PIL Image
            image = Image.open(io.BytesIO(image_data))
            
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
            
            # Preprocess image for better OCR
            processed_image = self.preprocess_image(opencv_image)
            
            # Extract text using Tesseract
            custom_config = r'--oem 3 --psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789.,:/\-+()[]{}%°'
            text = pytesseract.image_to_string(processed_image, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"OCR extraction failed: {str(e)}")
    
    def preprocess_image(self, image):
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            blurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2
        )
        
        # Morphological operations to clean up
        kernel = np.ones((1, 1), np.uint8)
        cleaned = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return cleaned
    
    def extract_text_from_pdf(self, pdf_data):
        """Extract text from PDF file"""
        try:
            pdf_file = io.BytesIO(pdf_data)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"PDF extraction failed: {str(e)}")
    
    def extract_text_from_docx(self, docx_data):
        """Extract text from DOCX file"""
        try:
            docx_file = io.BytesIO(docx_data)
            doc = docx.Document(docx_file)
            
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"DOCX extraction failed: {str(e)}")
    
    def extract_text_from_file(self, file_data, filename):
        """Extract text from various file types"""
        filename_lower = filename.lower()
        
        if filename_lower.endswith(('.jpg', '.jpeg', '.png', '.bmp', '.tiff')):
            return self.extract_text_from_image(file_data)
        elif filename_lower.endswith('.pdf'):
            return self.extract_text_from_pdf(file_data)
        elif filename_lower.endswith('.docx'):
            return self.extract_text_from_docx(file_data)
        else:
            raise Exception(f"Unsupported file type: {filename}")
    
    def extract_medical_info(self, text):
        """Extract structured medical information from text"""
        medical_info = {
            'vitals': {},
            'lab_values': {},
            'symptoms': [],
            'medications': [],
            'diagnosis': [],
            'recommendations': []
        }
        
        text_lower = text.lower()
        
        # Extract vital signs
        for vital, pattern in self.vital_patterns.items():
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            if matches:
                medical_info['vitals'][vital] = matches[0]
        
        # Extract symptoms (look for common symptom words)
        symptom_keywords = [
            'pain', 'ache', 'fever', 'cough', 'headache', 'nausea', 'vomiting',
            'diarrhea', 'constipation', 'fatigue', 'weakness', 'dizziness',
            'shortness of breath', 'chest pain', 'abdominal pain'
        ]
        
        for keyword in symptom_keywords:
            if keyword in text_lower:
                medical_info['symptoms'].append(keyword)
        
        # Look for medication mentions
        med_pattern = r'(?:medication|medicine|drug|tablet|capsule|syrup)[:\s]*([a-zA-Z\s]+?)(?:\n|$|,)'
        medications = re.findall(med_pattern, text_lower, re.IGNORECASE)
        medical_info['medications'] = [med.strip() for med in medications if med.strip()]
        
        # Look for diagnosis
        diag_pattern = r'(?:diagnosis|diagnosed with|condition)[:\s]*([a-zA-Z\s]+?)(?:\n|$|,)'
        diagnoses = re.findall(diag_pattern, text_lower, re.IGNORECASE)
        medical_info['diagnosis'] = [diag.strip() for diag in diagnoses if diag.strip()]
        
        return medical_info
    
    def analyze_medical_report(self, text):
        """Provide AI-enhanced analysis of medical report"""
        medical_info = self.extract_medical_info(text)
        
        analysis = {
            'summary': '',
            'key_findings': [],
            'abnormal_values': [],
            'recommendations': [],
            'urgency_indicators': []
        }
        
        # Check for abnormal vital signs
        vitals = medical_info.get('vitals', {})
        
        if 'blood_pressure' in vitals:
            bp = vitals['blood_pressure']
            try:
                systolic, diastolic = map(int, bp.replace('\\', '/').split('/'))
                if systolic > 140 or diastolic > 90:
                    analysis['abnormal_values'].append(f"High blood pressure: {bp}")
                    analysis['urgency_indicators'].append("Hypertension detected")
                elif systolic < 90 or diastolic < 60:
                    analysis['abnormal_values'].append(f"Low blood pressure: {bp}")
            except:
                pass
        
        if 'heart_rate' in vitals:
            try:
                hr = int(vitals['heart_rate'])
                if hr > 100:
                    analysis['abnormal_values'].append(f"High heart rate: {hr}")
                elif hr < 60:
                    analysis['abnormal_values'].append(f"Low heart rate: {hr}")
            except:
                pass
        
        if 'temperature' in vitals:
            try:
                temp = float(vitals['temperature'])
                if temp > 100.4:  # Assuming Fahrenheit
                    analysis['abnormal_values'].append(f"Fever detected: {temp}°")
                    analysis['urgency_indicators'].append("Fever present")
            except:
                pass
        
        # Generate summary
        if analysis['abnormal_values']:
            analysis['summary'] = f"Medical report shows {len(analysis['abnormal_values'])} abnormal findings requiring attention."
        else:
            analysis['summary'] = "Medical report appears to show values within normal ranges."
        
        # Add key findings
        if medical_info['symptoms']:
            analysis['key_findings'].extend([f"Symptom: {symptom}" for symptom in medical_info['symptoms']])
        
        if medical_info['diagnosis']:
            analysis['key_findings'].extend([f"Diagnosis: {diag}" for diag in medical_info['diagnosis']])
        
        # Generate recommendations
        if analysis['urgency_indicators']:
            analysis['recommendations'].append("Consult with healthcare provider about abnormal findings")
        
        if medical_info['medications']:
            analysis['recommendations'].append("Review current medications with doctor")
        
        return analysis

# Helper functions for the API
def scan_medical_report(file_data, filename):
    """Main function to scan and analyze medical reports"""
    scanner = MedicalReportScanner()
    
    try:
        # Extract text from file
        extracted_text = scanner.extract_text_from_file(file_data, filename)
        
        if not extracted_text or len(extracted_text.strip()) < 10:
            return {
                'success': False,
                'error': 'No readable text found in the file'
            }
        
        # Analyze the extracted text
        medical_info = scanner.extract_medical_info(extracted_text)
        analysis = scanner.analyze_medical_report(extracted_text)
        
        return {
            'success': True,
            'extracted_text': extracted_text,
            'medical_info': medical_info,
            'analysis': analysis,
            'medical_analysis': analysis['summary']
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }