# config_example.py
import google.generativeai as genai

# RENAME THIS FILE TO config.py AND ADD YOUR KEY
API_KEY = "PASTE_YOUR_KEY_HERE" 
MODEL_NAME = "gemini-2.5-flash"
DB_PATH = "./cst_db"

def get_model():
    genai.configure(api_key=API_KEY)
    return genai.GenerativeModel(MODEL_NAME)