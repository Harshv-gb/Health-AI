# mistral_client.py - Integration with Mistral AI for conversational medical advice
import os
import json
import requests
from typing import Dict, List, Optional
from dotenv import load_dotenv
import openai  # Using OpenAI client as fallback

# Load environment variables
load_dotenv()

class MistralAIClient:
    def __init__(self):
        """Initialize Mistral AI client"""
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        
        # Mistral API endpoint
        self.mistral_url = "https://api.mistral.ai/v1/chat/completions"
        
        # Initialize OpenAI as fallback
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        
        # Medical context and guidelines
        self.medical_context = self._load_medical_context()
        
    def _load_medical_context(self) -> str:
        """Load medical context for AI responses"""
        return """
        You are a medical AI assistant helping with symptom assessment. Your role is to:
        
        1. ALWAYS emphasize that you're not a replacement for professional medical advice
        2. Provide educational information about symptoms and conditions
        3. Suggest appropriate care levels (self-care, GP, urgent, emergency)
        4. Ask relevant follow-up questions to better understand symptoms
        5. Be empathetic and supportive
        6. Never provide specific medication dosages or diagnoses
        7. Always recommend consulting healthcare professionals for concerning symptoms
        
        Guidelines:
        - Use simple, non-technical language
        - Be concise but thorough
        - Focus on safety and appropriate care seeking
        - Consider cultural sensitivity and accessibility
        """

    def get_conversational_advice(self, user_message: str, symptom_context: Dict, 
                                chat_history: List[Dict] = None) -> Dict:
        """
        Get conversational medical advice using Mistral AI
        """
        if not chat_history:
            chat_history = []
        
        # Prepare the prompt with medical context
        system_prompt = self._build_system_prompt(symptom_context)
        
        # Prepare messages for the AI
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history
        for msg in chat_history[-5:]:  # Keep last 5 messages for context
            messages.append(msg)
        
        # Add current user message
        messages.append({"role": "user", "content": user_message})
        
        # Try Mistral AI first, fallback to OpenAI
        if self.mistral_api_key:
            response = self._query_mistral(messages)
        elif self.openai_api_key:
            response = self._query_openai(messages)
        else:
            response = self._generate_fallback_response(user_message, symptom_context)
        
        return {
            "ai_response": response,
            "follow_up_suggestions": self._generate_follow_up_suggestions(symptom_context),
            "safety_disclaimer": self._get_safety_disclaimer(),
            "conversation_context": messages
        }

    def _build_system_prompt(self, symptom_context: Dict) -> str:
        """Build system prompt with current symptom context"""
        base_prompt = self.medical_context
        
        if symptom_context:
            symptoms = symptom_context.get("symptoms", [])
            urgency = symptom_context.get("urgency_level", "unknown")
            assessment = symptom_context.get("assessment", "")
            
            context_addition = f"""
            
            Current Patient Context:
            - Reported symptoms: {', '.join(symptoms) if symptoms else 'None provided'}
            - Assessed urgency level: {urgency}
            - System assessment: {assessment}
            
            Please provide helpful, contextual advice based on this information while following all medical guidelines.
            """
            
            base_prompt += context_addition
        
        return base_prompt

    def _query_mistral(self, messages: List[Dict]) -> str:
        """Query Mistral AI API"""
        try:
            headers = {
                "Authorization": f"Bearer {self.mistral_api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "mistral-medium",
                "messages": messages,
                "max_tokens": 500,
                "temperature": 0.3,  # Lower temperature for medical advice
                "top_p": 0.9
            }
            
            response = requests.post(self.mistral_url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                print(f"Mistral API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"Error querying Mistral: {e}")
            return None

    def _query_openai(self, messages: List[Dict]) -> str:
        """Query OpenAI API as fallback"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            print(f"Error querying OpenAI: {e}")
            return None

    def _generate_fallback_response(self, user_message: str, symptom_context: Dict) -> str:
        """Generate fallback response when no AI service is available"""
        urgency = symptom_context.get("urgency_level", "unknown")
        symptoms = symptom_context.get("symptoms", [])
        
        # Basic template responses based on urgency
        if urgency == "emergency":
            return """🚨 Based on your symptoms, this appears to be a medical emergency. 
            Please seek immediate medical attention by calling emergency services or going to the nearest emergency room. 
            Do not delay seeking care."""
            
        elif urgency == "urgent":
            return f"""Your symptoms ({', '.join(symptoms)}) suggest you should seek medical attention promptly. 
            Please contact your doctor or visit an urgent care facility within the next few hours. 
            Monitor your symptoms closely and seek emergency care if they worsen."""
            
        elif urgency == "GP":
            return f"""Your symptoms ({', '.join(symptoms)}) would benefit from medical evaluation. 
            Please schedule an appointment with your general practitioner or family doctor. 
            In the meantime, monitor your symptoms and seek urgent care if they worsen significantly."""
            
        else:
            return f"""Your symptoms ({', '.join(symptoms)}) may be manageable with self-care measures. 
            However, please monitor them closely and seek medical advice if they persist, worsen, or if you develop new concerning symptoms. 
            When in doubt, it's always best to consult with a healthcare professional."""

    def _generate_follow_up_suggestions(self, symptom_context: Dict) -> List[str]:
        """Generate follow-up conversation suggestions"""
        base_suggestions = [
            "Tell me more about when these symptoms started",
            "Have you experienced anything like this before?",
            "Are there any other symptoms you'd like to discuss?",
            "Do you have any specific concerns about your symptoms?"
        ]
        
        symptoms = symptom_context.get("symptoms", [])
        
        # Add symptom-specific suggestions
        if any("pain" in symptom.lower() for symptom in symptoms):
            base_suggestions.append("Can you describe the pain in more detail?")
        
        if any("fever" in symptom.lower() for symptom in symptoms):
            base_suggestions.append("Have you taken your temperature recently?")
        
        if any("headache" in symptom.lower() for symptom in symptoms):
            base_suggestions.append("Is this headache different from ones you usually get?")
        
        return base_suggestions

    def _get_safety_disclaimer(self) -> str:
        """Get safety disclaimer for AI responses"""
        return """
        ⚠️ Important: This AI assistant provides educational information only and is not a substitute for professional medical advice, diagnosis, or treatment. Always consult with qualified healthcare providers for medical concerns. In case of emergency, call emergency services immediately.
        """

    def generate_health_education(self, condition: str, symptoms: List[str]) -> Dict:
        """Generate educational content about a condition"""
        prompt = f"""
        Provide brief, easy-to-understand educational information about {condition} for someone experiencing these symptoms: {', '.join(symptoms)}.
        
        Include:
        1. What is {condition}?
        2. Common symptoms
        3. When to seek medical care
        4. General self-care tips (if appropriate)
        
        Keep it concise and emphasize the importance of professional medical advice.
        """
        
        messages = [
            {"role": "system", "content": self.medical_context},
            {"role": "user", "content": prompt}
        ]
        
        if self.mistral_api_key:
            content = self._query_mistral(messages)
        elif self.openai_api_key:
            content = self._query_openai(messages)
        else:
            content = self._generate_fallback_education(condition)
        
        return {
            "educational_content": content,
            "disclaimer": self._get_safety_disclaimer(),
            "condition": condition,
            "related_symptoms": symptoms
        }

    def _generate_fallback_education(self, condition: str) -> str:
        """Generate basic educational content without AI"""
        return f"""
        {condition} Information:
        
        This is a general educational overview. For accurate information about {condition}, please consult with healthcare professionals who can provide personalized advice based on your specific situation.
        
        Key points to remember:
        - Always seek professional medical advice for health concerns
        - Monitor your symptoms and note any changes
        - Follow up with healthcare providers as recommended
        - Seek urgent care if symptoms worsen or new concerning symptoms develop
        
        For detailed, personalized information about {condition}, please consult with your doctor or healthcare provider.
        """

    def assess_mental_health_context(self, user_message: str) -> Dict:
        """Assess if mental health support might be helpful"""
        mental_health_keywords = [
            "anxious", "anxiety", "depressed", "depression", "stress", "worried", 
            "panic", "scared", "overwhelmed", "hopeless", "sad", "crying"
        ]
        
        message_lower = user_message.lower()
        mental_health_indicators = [kw for kw in mental_health_keywords if kw in message_lower]
        
        if mental_health_indicators:
            return {
                "mental_health_support_suggested": True,
                "detected_indicators": mental_health_indicators,
                "support_message": """
                It sounds like you might be experiencing some emotional distress along with your physical symptoms. 
                This is completely normal and seeking support for both physical and mental health is important. 
                Consider speaking with a healthcare provider about both your physical symptoms and how you're feeling emotionally.
                """,
                "resources": [
                    "National Mental Health Crisis Line: 988 (US)",
                    "Crisis Text Line: Text HOME to 741741",
                    "Your local emergency services for immediate crisis support"
                ]
            }
        
        return {"mental_health_support_suggested": False}

    def generate_diet_recommendations(self, condition: str, patient_context: Dict = None) -> Dict:
        """Generate personalized diet recommendations for a given condition"""
        age = patient_context.get("age") if patient_context else None
        gender = patient_context.get("gender") if patient_context else None
        chronic_conditions = patient_context.get("chronic_conditions", []) if patient_context else []
        
        # Build context-aware prompt
        context_info = ""
        if age:
            context_info += f"\n- Patient age: {age} years"
        if gender:
            context_info += f"\n- Gender: {gender}"
        if chronic_conditions:
            context_info += f"\n- Existing conditions: {', '.join(chronic_conditions)}"
        
        prompt = f"""
        Provide a comprehensive dietary recommendation plan for a patient diagnosed with {condition}.
        {context_info if context_info else ""}
        
        Please structure your response in a CLEAN, EASY-TO-READ format:
        
        ## 1. Foods to Include
        List 5-7 specific foods with brief explanations:
        - **Food name**: Why it helps (one line explanation)
        
        ## 2. Foods to Avoid
        List 3-5 foods to avoid:
        - **Food name**: Why to avoid (brief reason)
        
        ## 3. Hydration Guidelines
        - Daily fluid recommendations
        - Best beverages
        - Timing suggestions
        
        ## 4. Meal Timing & Frequency
        - How often to eat
        - Portion guidance
        - Best times for meals
        
        ## 5. Additional Tips
        - 2-3 practical, actionable tips
        
        IMPORTANT FORMATTING RULES:
        - Use simple bullet points (•, -, or ✅/❌)
        - NO TABLES - they don't display well
        - Keep each point concise (1-2 lines max)
        - Use bold (**text**) for emphasis only
        - Write in clear, simple language
        
        Keep recommendations:
        - Practical and easy to follow
        - Culturally sensitive and accessible
        - Evidence-based for {condition}
        - Safe for general population
        
        End with: ⚠️ Important: These are general guidelines. Individual nutritional needs vary. Please consult with a healthcare provider or registered dietitian for personalized dietary advice.
        """
        
        messages = [
            {"role": "system", "content": self.medical_context + "\n\nYou are providing dietary guidance for medical conditions. Focus on evidence-based nutrition advice while emphasizing the importance of professional nutritional consultation."},
            {"role": "user", "content": prompt}
        ]
        
        if self.mistral_api_key:
            diet_content = self._query_mistral(messages)
        elif self.openai_api_key:
            diet_content = self._query_openai(messages)
        else:
            diet_content = self._generate_fallback_diet(condition)
        
        return {
            "condition": condition,
            "diet_recommendations": diet_content,
            "patient_context": patient_context or {},
            "disclaimer": "⚠️ These dietary recommendations are general guidelines only. Individual nutritional needs vary. Please consult with a healthcare provider or registered dietitian for personalized dietary advice, especially if you have allergies, other medical conditions, or take medications.",
            "consultation_note": "For personalized meal plans and specific dietary restrictions, please consult with a registered dietitian or nutritionist."
        }

    def _generate_fallback_diet(self, condition: str) -> str:
        """Generate basic dietary advice without AI"""
        common_diets = {
            "Common Cold": """
            **Foods to Include:**
            - Warm soups and broths (chicken soup, vegetable broth)
            - Citrus fruits (oranges, lemons for vitamin C)
            - Ginger tea and honey
            - Garlic and onions (immune-boosting)
            - Leafy greens (spinach, kale)
            - Yogurt with probiotics
            
            **Foods to Avoid:**
            - Dairy products if mucus is excessive
            - Processed and sugary foods
            - Alcohol and caffeine
            
            **Hydration:**
            - Drink 8-10 glasses of water daily
            - Warm herbal teas
            - Warm water with honey and lemon
            
            **Meal Timing:**
            - Eat small, frequent meals
            - Don't skip meals even if appetite is low
            
            **Additional Tips:**
            - Vitamin C rich foods help recovery
            - Stay well-hydrated to loosen mucus
            - Warm liquids soothe throat
            """,
            
            "Influenza": """
            **Foods to Include:**
            - Clear broths and soups
            - Bananas, rice, applesauce, toast (BRAT diet)
            - Eggs (easy protein)
            - Berries rich in antioxidants
            - Sweet potatoes
            - Green tea
            
            **Foods to Avoid:**
            - Heavy, greasy foods
            - Dairy if nausea present
            - Spicy foods
            - Alcohol
            
            **Hydration:**
            - 10-12 glasses of fluids daily
            - Electrolyte drinks if fever present
            - Warm liquids preferred
            
            **Meal Timing:**
            - Small portions every 2-3 hours
            - Light foods to avoid nausea
            
            **Additional Tips:**
            - Protein helps immune function
            - Vitamin D and zinc support recovery
            - Rest and nutrition go hand in hand
            """,
            
            "Diabetes": """
            **Foods to Include:**
            - Non-starchy vegetables (broccoli, spinach, peppers)
            - Whole grains (brown rice, quinoa, oats)
            - Lean proteins (fish, chicken, legumes)
            - Healthy fats (avocado, nuts, olive oil)
            - Fiber-rich foods
            
            **Foods to Avoid:**
            - Sugary drinks and sweets
            - White bread, pasta, rice
            - Fried foods
            - Processed snacks
            
            **Hydration:**
            - 8-10 glasses of water daily
            - Avoid sugary beverages
            - Unsweetened tea is acceptable
            
            **Meal Timing:**
            - Regular meal times (3 meals + 2 snacks)
            - Don't skip meals
            - Monitor carbohydrate intake
            
            **Additional Tips:**
            - Control portion sizes
            - Monitor blood sugar regularly
            - Consult dietitian for meal planning
            """
        }
        
        # Return specific diet if available, otherwise generic advice
        if condition in common_diets:
            return common_diets[condition]
        else:
            return f"""
            **General Dietary Guidelines for {condition}:**
            
            **Foods to Include:**
            - Fresh fruits and vegetables
            - Whole grains
            - Lean proteins
            - Adequate hydration
            
            **Foods to Avoid:**
            - Processed foods
            - Excessive sugar and salt
            - Alcohol
            
            **Important:** Specific dietary recommendations for {condition} should be obtained from a registered dietitian or healthcare provider who can provide personalized advice based on your complete medical history.
            
            Please consult with healthcare professionals for a detailed meal plan tailored to your condition.
            """

# Global instance
mistral_client = MistralAIClient()

def get_ai_medical_advice(user_message: str, symptom_context: Dict, 
                         chat_history: List[Dict] = None) -> Dict:
    """Convenience function for getting AI medical advice"""
    return mistral_client.get_conversational_advice(user_message, symptom_context, chat_history)

def get_health_education(condition: str, symptoms: List[str]) -> Dict:
    """Convenience function for health education"""
    return mistral_client.generate_health_education(condition, symptoms)

def get_diet_recommendations(condition: str, patient_context: Dict = None) -> Dict:
    """Convenience function for getting diet recommendations"""
    return mistral_client.generate_diet_recommendations(condition, patient_context)

if __name__ == "__main__":
    # Test the Mistral client
    test_context = {
        "symptoms": ["headache", "nausea"],
        "urgency_level": "GP",
        "assessment": "Mild symptoms suggesting need for GP consultation"
    }
    
    test_message = "I'm worried about these symptoms. What should I do?"
    
    result = get_ai_medical_advice(test_message, test_context)
    print("AI Response:", result["ai_response"])
    print("Follow-up Suggestions:", result["follow_up_suggestions"])
