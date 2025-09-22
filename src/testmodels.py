# test_models.py
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv()
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

print("Available models:")
for model in genai.list_models():
    print(f"- {model.name}")
