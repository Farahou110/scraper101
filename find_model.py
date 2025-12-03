import google.generativeai as genai
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
env_path = Path('.') / '.env'
load_dotenv(dotenv_path=env_path)

api_key = os.environ.get("GEMINI_API_KEY")

if not api_key:
    print("❌ Error: API Key not found in .env file")
    exit()

print(f"🔑 Checking models for API Key: {api_key[:5]}...")

try:
    genai.configure(api_key=api_key)
    
    print("\n✅ AVAILABLE MODELS:")
    print("-" * 30)
    found_any = False
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"• {m.name}")
            found_any = True
            
    if not found_any:
        print("⚠️ No generative models found. Check your API key permissions.")
    print("-" * 30)

except Exception as e:
    print(f"\n❌ CONNECTION ERROR:\n{e}")