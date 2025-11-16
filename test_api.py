import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key found: {bool(api_key)}")
print(f"API Key starts with: {api_key[:10]}..." if api_key else "No API key")

# Test the API
try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Say 'Hello World'"}],
        max_tokens=10
    )
    print("API test successful!")
    print(response.choices[0].message.content)
except Exception as e:
    print(f"API test failed: {e}")