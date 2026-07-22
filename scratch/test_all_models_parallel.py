import requests
import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

url = "http://localhost:8045/v1/chat/completions"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer sk-5ec70bf9fa324084b7a7326babf52c45"
}

# The user requested models mapped to likely API IDs
models_to_test = {
    "Gemini 3.6 Flash (High)": "gemini-3.6-flash-high",
    "Gemini 3.6 Flash (Medium)": "gemini-3.6-flash-medium",
    "Gemini 3.6 Flash (Low)": "gemini-3.6-flash-low",
    "Gemini 3.5 Flash (High)": "gemini-3.5-flash-high",
    "Gemini 3.5 Flash (Medium)": "gemini-3.5-flash-medium",
    "Gemini 3.5 Flash (Low)": "gemini-3.5-flash-low",
    "Gemini 3.1 Pro (High)": "gemini-3.1-pro-high",
    "Gemini 3.1 Pro (Low)": "gemini-3.1-pro-low",
    "Claude Sonnet 4.6 (Thinking)": "claude-sonnet-4-6-thinking",
    "Claude Opus 4.6 (Thinking)": "claude-opus-4-6-thinking",
    "GPT-OSS 120B (Medium)": "gpt-oss-120b-medium",
}

# Additional models that were found in the /v1/models list
additional_models = {
    "Gemini 3.6 Flash Tiered": "gemini-3.6-flash-tiered",
    "Gemini 3.5 Flash Extra Low": "gemini-3.5-flash-extra-low",
    "Gemini 3.1 Flash Lite": "gemini-3.1-flash-lite",
    "Gemini 3 Flash": "gemini-3-flash",
    "Gemini 3 Flash Agent": "gemini-3-flash-agent",
    "Claude Sonnet 4.6 (Standard)": "claude-sonnet-4-6",
}

def test_single_model(display_name, model_id):
    print(f"[START] Testing model: {display_name} ({model_id})...", flush=True)
    data = {
        "model": model_id,
        "messages": [{"role": "user", "content": "Hello! Reply with exactly 'Hello World' and nothing else."}]
    }
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=data, timeout=45)
        elapsed = time.time() - start_time
        status_code = response.status_code
        
        try:
            resp_data = response.json()
        except Exception:
            resp_data = response.text
            
        print(f"[DONE] Model: {display_name} | Status: {status_code} | Time: {elapsed:.2f}s", flush=True)
        if status_code == 200:
            content = resp_data.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"       Response from {display_name}: {content.strip()}", flush=True)
        else:
            print(f"       Response from {display_name}: {resp_data}", flush=True)
            
        return {
            "display_name": display_name,
            "model_id": model_id,
            "status_code": status_code,
            "latency": elapsed,
            "response": resp_data
        }
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"[ERROR] Model: {display_name} | Error: {e} | Time: {elapsed:.2f}s", flush=True)
        return {
            "display_name": display_name,
            "model_id": model_id,
            "status_code": "TIMEOUT" if "timeout" in str(e).lower() else "CONNECTION_ERROR",
            "latency": elapsed,
            "response": str(e)
        }

def main():
    all_tasks = []
    # Combine both dictionaries
    combined_models = {**models_to_test, **additional_models}
    
    print(f"Starting parallel testing of {len(combined_models)} models...", flush=True)
    results = []
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {
            executor.submit(test_single_model, name, m_id): (name, m_id)
            for name, m_id in combined_models.items()
        }
        
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            
    # Write results to JSON file
    with open("scratch/test_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, indent=4)
        
    print("\nAll tests complete. Results written to scratch/test_results.json", flush=True)

if __name__ == "__main__":
    main()
