# voice_processor.py - Voice Input/Output Processing
import speech_recognition as sr
import pyttsx3
import io
import wave
import tempfile
import os
from threading import Thread
import time

class VoiceProcessor:
    def __init__(self):
        """Initialize voice processor with speech recognition and TTS"""
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize text-to-speech engine
        try:
            self.tts_engine = pyttsx3.init()
            self.tts_engine.setProperty('rate', 150)  # Speed of speech
            self.tts_engine.setProperty('volume', 0.8)  # Volume level
            
            # Try to set a more natural voice
            voices = self.tts_engine.getProperty('voices')
            if voices:
                # Prefer female voice for medical applications
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
                        break
                    elif 'david' in voice.name.lower() or 'male' in voice.name.lower():
                        self.tts_engine.setProperty('voice', voice.id)
            
            self.tts_available = True
        except Exception as e:
            print(f"TTS initialization failed: {e}")
            self.tts_available = False
        
        # Adjust for ambient noise
        try:
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"Microphone calibration failed: {e}")
    
    def transcribe_audio_file(self, audio_data):
        """Transcribe audio data to text"""
        try:
            # Create a temporary WAV file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file_path = temp_file.name
            
            try:
                # Load audio file
                with sr.AudioFile(temp_file_path) as source:
                    audio = self.recognizer.record(source)
                
                # Transcribe using Google Web Speech API (free tier)
                text = self.recognizer.recognize_google(audio, language='en-US')
                return {
                    'success': True,
                    'text': text,
                    'confidence': 1.0  # Google API doesn't return confidence
                }
                
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Could not understand the audio'
                }
            except sr.RequestError as e:
                # Fallback to offline recognition if available
                try:
                    text = self.recognizer.recognize_sphinx(audio)
                    return {
                        'success': True,
                        'text': text,
                        'confidence': 0.7
                    }
                except:
                    return {
                        'success': False,
                        'error': f'Speech recognition service error: {e}'
                    }
            finally:
                # Clean up temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                    
        except Exception as e:
            return {
                'success': False,
                'error': f'Audio processing failed: {str(e)}'
            }
    
    def transcribe_microphone(self, timeout=5, phrase_time_limit=None):
        """Listen to microphone and transcribe speech"""
        try:
            with self.microphone as source:
                print("Listening for speech...")
                # Listen for audio with timeout
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout, 
                    phrase_time_limit=phrase_time_limit
                )
            
            # Transcribe the audio
            try:
                text = self.recognizer.recognize_google(audio, language='en-US')
                return {
                    'success': True,
                    'text': text,
                    'confidence': 1.0
                }
            except sr.UnknownValueError:
                return {
                    'success': False,
                    'error': 'Could not understand the speech'
                }
            except sr.RequestError as e:
                return {
                    'success': False,
                    'error': f'Speech recognition error: {e}'
                }
                
        except sr.WaitTimeoutError:
            return {
                'success': False,
                'error': 'Listening timeout - no speech detected'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Microphone error: {str(e)}'
            }
    
    def text_to_speech(self, text, output_file=None):
        """Convert text to speech"""
        if not self.tts_available:
            return {
                'success': False,
                'error': 'Text-to-speech not available'
            }
        
        try:
            # Clean and prepare text for speech
            speech_text = self.prepare_text_for_speech(text)
            
            if output_file:
                # Save to file
                self.tts_engine.save_to_file(speech_text, output_file)
                self.tts_engine.runAndWait()
                return {
                    'success': True,
                    'file_path': output_file
                }
            else:
                # Speak directly
                self.tts_engine.say(speech_text)
                self.tts_engine.runAndWait()
                return {
                    'success': True,
                    'message': 'Speech completed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'TTS failed: {str(e)}'
            }
    
    def prepare_text_for_speech(self, text):
        """Prepare text for natural speech synthesis"""
        # Replace medical abbreviations with full words
        replacements = {
            'bp': 'blood pressure',
            'hr': 'heart rate',
            'bpm': 'beats per minute',
            'mg/dl': 'milligrams per deciliter',
            'kg': 'kilograms',
            'cm': 'centimeters',
            'mm': 'millimeters',
            'hb': 'hemoglobin',
            'wbc': 'white blood cell count',
            'rbc': 'red blood cell count',
            'ecg': 'electrocardiogram',
            'mri': 'magnetic resonance imaging',
            'ct': 'computed tomography',
            'xray': 'x-ray',
            'dr.': 'doctor',
            'vs': 'versus',
            '&': 'and',
            '%': 'percent'
        }
        
        speech_text = text.lower()
        for abbrev, full_word in replacements.items():
            speech_text = speech_text.replace(abbrev, full_word)
        
        # Add pauses for better speech flow
        speech_text = speech_text.replace('.', '. ')
        speech_text = speech_text.replace(',', ', ')
        speech_text = speech_text.replace(';', '; ')
        
        # Remove extra whitespace
        speech_text = ' '.join(speech_text.split())
        
        return speech_text
    
    def generate_medical_audio_response(self, diagnosis_result):
        """Generate a natural audio response for medical diagnosis"""
        try:
            response_parts = []
            
            # Greeting
            response_parts.append("Based on your symptoms, here is my assessment.")
            
            # Main diagnosis
            if diagnosis_result.get('condition'):
                condition = diagnosis_result['condition']
                status = diagnosis_result.get('status', '')
                
                if status == 'emergency':
                    response_parts.append(f"This appears to be a medical emergency related to {condition}.")
                    response_parts.append("You should seek immediate medical attention.")
                else:
                    response_parts.append(f"The possible condition is {condition}.")
                    
                    if status == 'GP':
                        response_parts.append("I recommend scheduling an appointment with your general practitioner.")
                    elif status in ['urgent', 'high']:
                        response_parts.append("This requires prompt medical attention.")
            
            # Department recommendation
            if diagnosis_result.get('department'):
                dept = diagnosis_result['department']
                response_parts.append(f"The recommended medical department is {dept}.")
            
            # Hospital information
            if diagnosis_result.get('hospitals') and len(diagnosis_result['hospitals']) > 0:
                nearest = diagnosis_result['hospitals'][0]
                response_parts.append(f"The nearest hospital is {nearest['hospital']}")
                response_parts.append(f"located {nearest['distance_km']} kilometers away.")
                
                if nearest.get('contact'):
                    response_parts.append(f"Their contact number is {nearest['contact']}.")
            
            # AI recommendations if available
            if diagnosis_result.get('ai_recommendations'):
                response_parts.append("Additional recommendations include:")
                for rec in diagnosis_result['ai_recommendations'][:3]:  # Limit to 3 recommendations
                    response_parts.append(rec)
            
            # Medical disclaimer
            response_parts.append("Please remember that this is an AI assessment and should not replace professional medical advice.")
            response_parts.append("Always consult with healthcare professionals for proper diagnosis and treatment.")
            
            # Combine all parts
            full_response = " ".join(response_parts)
            
            return self.text_to_speech(full_response)
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Audio response generation failed: {str(e)}'
            }

# Helper functions for API
def process_voice_input(audio_data):
    """Process voice input and return transcribed text"""
    processor = VoiceProcessor()
    return processor.transcribe_audio_file(audio_data)

def generate_voice_response(diagnosis_result):
    """Generate voice response for diagnosis result"""
    processor = VoiceProcessor()
    return processor.generate_medical_audio_response(diagnosis_result)