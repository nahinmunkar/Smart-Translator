import requests
import json

# Test the backend API
try:
    response = requests.post(
        'http://127.0.0.1:8000/translate',
        json={'text': 'Hello world', 'target_lang': 'French'},
        headers={'Content-Type': 'application/json'}
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")
