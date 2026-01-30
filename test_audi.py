import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=api_key)

try:
    models = genai.list_models()
    print("✅ API OK - modèles disponibles :")
    for m in models:
        print(f"  - {m.name}")
except Exception as e:
    print("❌ Erreur API :", e)
