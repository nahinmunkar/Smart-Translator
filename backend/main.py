import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

# Load the API key from .env file
load_dotenv()

app = FastAPI()

# Allow the frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Groq Client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class TranslationRequest(BaseModel):
    text: str
    target_lang: str

@app.post("/translate")
async def translate_text(request: TranslationRequest):
    # This prompt forces the AI to reply in strict JSON format
    system_prompt = f"""
    You are a translator. Translate the user's text into {request.target_lang}.
    You must return a strictly valid JSON object with exactly two keys:
    1. "full_translation": The complete, fluent translation of the sentence.
    2. "word_mapping": A list of objects, where each object has "original" (the word in source text) and "translated" (the literal translation of that word).
    """

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": request.text}
            ],
            model="llama-3.3-70b-versatile", # Fast and free model and upgraded
            response_format={"type": "json_object"} # Force JSON mode
        )
        
        # Parse the JSON string back into a Python dictionary
        result = json.loads(chat_completion.choices[0].message.content)
        return result

    except Exception as e:
        print(f"Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    

    # ... (all your previous code is above here)

if __name__ == "__main__":
    import uvicorn
    # This starts the server programmatically
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)