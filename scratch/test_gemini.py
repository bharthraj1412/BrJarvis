import os
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = os.environ.get("GOOGLE_API_KEY")
print("API Key:", api_key)
client = genai.Client(api_key=api_key)

try:
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Hello",
    )
    print("Response gemini-2.5-flash:", response.text)
except Exception as e:
    print("Error gemini-2.5-flash:", e)

try:
    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents="Hello",
    )
    print("Response gemini-1.5-flash:", response.text)
except Exception as e:
    print("Error gemini-1.5-flash:", e)
