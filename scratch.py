import asyncio
from google import genai
import dotenv
import os

dotenv.load_dotenv('.env')

# Prefer GEMINI_API_KEY but accept GOOGLE_API_KEY for backward compatibility
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise SystemExit("Missing API key: set GEMINI_API_KEY in your .env (or GOOGLE_API_KEY)")

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})

async def test():
    try:
        async with client.aio.live.connect(model='gemini-2.0-flash-exp') as session:
            print('SUCCESS')
    except Exception as e:
        print('ERROR:', repr(e))

if __name__ == '__main__':
    asyncio.run(test())
