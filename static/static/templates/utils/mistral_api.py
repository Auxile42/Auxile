import requests
import config

def mistral_ai_request(prompt):
    headers = {
        "Authorization": f"Bearer {config.MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "prompt": prompt,
        "max_tokens": 150
    }
    response = requests.post(config.MISTRAL_API_URL, headers=headers, json=data)
    return response.json()
