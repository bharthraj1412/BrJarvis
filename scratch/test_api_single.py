import requests
import json

url = "http://localhost:8045/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-5ec70bf9fa324084b7a7326babf52c45"
}
data = {
    "model": "gemini-3.1-pro-high",
    "messages": [{"role": "user", "content": "Hello"}]
}

try:
    response = requests.post(url, headers=headers, json=data, timeout=15)
    print("Status Code:", response.status_code)
    print("Headers:", response.headers)
    print("Content:")
    try:
        print(json.dumps(response.json(), indent=2))
    except Exception:
        print(response.text)
except Exception as e:
    print("Error connecting to server:", e)
