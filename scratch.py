import asyncio
from google import genai
import dotenv
import os
from pathlib import Path

# Load .env from project directory first, then fallback to current working directory.
_here = Path(__file__).resolve().parent
dotenv.load_dotenv(_here / '.env')
dotenv.load_dotenv('.env', override=False)

# Prefer GEMINI_API_KEY but accept GOOGLE_API_KEY for backward compatibility
api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
if not api_key:
    raise SystemExit("Missing API key: set GEMINI_API_KEY in your .env (or GOOGLE_API_KEY)")

client = genai.Client(api_key=api_key, http_options={'api_version': 'v1beta'})
model_name = os.getenv('JARVIS_MODEL_GEMINI', 'gemini-2.5-flash')
live_model_name = os.getenv('JARVIS_MODEL_VOICE_LIVE', 'models/gemini-2.5-flash-native-audio-preview-12-2025')


def test_text_api() -> bool:
    try:
        response = client.models.generate_content(
            model=model_name,
            contents='Reply with exactly: OK',
        )
        text = (response.text or '').strip()
        print('TEXT API SUCCESS:', text or '<empty response>')
        return True
    except Exception as e:
        print('TEXT API ERROR:', repr(e))
        return False

async def test():
    try:
        async with client.aio.live.connect(model=live_model_name) as session:
            print('LIVE API SUCCESS')
    except Exception as e:
        print('LIVE API ERROR:', repr(e))

if __name__ == '__main__':
    ok = test_text_api()
    if os.getenv('JARVIS_TEST_LIVE', '0') == '1':
        asyncio.run(test())
    raise SystemExit(0 if ok else 1)
