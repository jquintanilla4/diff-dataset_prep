import google.generativeai as genai
import os
from dotenv import load_dotenv

load_dotenv()

genai.configure(api_key=os.environ["GEMINI_API_KEY"])

model = genai.GenerativeModel('gemini-1.5-flash')  # Or try 'gemini-pro-vision'

try:
    response = model.generate_content("Please describe a sunset.")
    print(response.text)
except Exception as e:
    print(f"Error: {e}")