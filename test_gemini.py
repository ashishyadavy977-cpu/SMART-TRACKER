from google import genai
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)

response = client.models.generate_content(
    model=os.getenv("GEMINI_MODEL", "gemini-3.8-flash"),
    contents="Hello Gemini! Explain what Python is in simple Hinglish.",
)

print(response.text)
