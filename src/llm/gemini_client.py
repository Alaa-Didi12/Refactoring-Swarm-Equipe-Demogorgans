# src/llm/gemini_client.py - VERSION CORRECTE
import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

def get_working_model():
    """Trouve un modèle qui fonctionne."""
    api_key = os.getenv("GOOGLE_API_KEY", "").strip().strip('"').strip("'")
    
    if not api_key or not api_key.startswith("AIza"):
        return None
    
    # Modèles à essayer (les plus courants)
    models_to_try = [
        'gemini-1.5-pro-latest',  # Nouveau nom
        'gemini-1.5-pro',         # Ancien nom
        'gemini-1.0-pro-latest',  # Alternative
        'gemini-1.0-pro',
        'gemini-pro',             # Le plus basique
        'models/gemini-1.5-pro-001',  # Format complet
        'models/gemini-1.0-pro-001',
    ]
    
    genai.configure(api_key=api_key)
    
    for model_name in models_to_try:
        try:
            print(f"   🔍 Test du modèle: {model_name}")
            model = genai.GenerativeModel(model_name)
            # Test rapide
            response = model.generate_content("test", generation_config={"max_output_tokens": 1})
            print(f"   ✅ Modèle fonctionnel: {model_name}")
            return model_name
        except Exception as e:
            continue
    
    return None

# Cache le modèle fonctionnel
WORKING_MODEL = get_working_model()

def call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Utilise le VRAI Gemini avec le bon modèle."""
    
    api_key = os.getenv("GOOGLE_API_KEY", "").strip().strip('"').strip("'")
    
    if not api_key or not api_key.startswith("AIza"):
        print("   ❌ Clé API invalide")
        return _fallback_response(system_prompt, user_prompt)
    
    if not WORKING_MODEL:
        print("   ❌ Aucun modèle Gemini fonctionnel trouvé")
        return _fallback_response(system_prompt, user_prompt)
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(WORKING_MODEL)
        
        print(f"   🤖 Appel Gemini avec {WORKING_MODEL}")
        
        # Prépare le prompt
        full_prompt = f"""{system_prompt}

{user_prompt}

Réponds en français."""
        
        # Appel API
        response = model.generate_content(
            full_prompt,
            generation_config={
                "temperature": 0.1,
                "max_output_tokens": 2000,
            }
        )
        
        print(f"   ✅ Réponse Gemini reçue ({len(response.text)} caractères)")
        return response.text
        
    except Exception as e:
        print(f"   ❌ Erreur Gemini: {e}")
        return _fallback_response(system_prompt, user_prompt)

def _fallback_response(system_prompt: str, user_prompt: str) -> str:
    """Fallback si Gemini échoue."""
    print("   🔄 Fallback simulation")
    
    # Simulation basique
    return json.dumps({
        "message": "Gemini API non disponible - mode simulation",
        "test": "ok"
    })

# Test au démarrage
if __name__ == "__main__":
    print("🧪 Test Gemini...")
    if WORKING_MODEL:
        print(f"✅ Modèle trouvé: {WORKING_MODEL}")
        # Test réel
        test = call_gemini("Tu es un test", "Dis bonjour")
        print(f"Réponse: {test[:100]}...")
    else:
        print("❌ Aucun modèle fonctionnel")