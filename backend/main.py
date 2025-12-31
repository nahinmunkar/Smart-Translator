import os
import json
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

class TranslationRequest(BaseModel):
    text: str
    target_lang: str

# --- 1. SMALLER CHUNKS FOR SAFETY ---
# Reduced to 600 to ensure AI has enough memory to map every single word
def chunk_text(text, max_chars=600):
    # Split by sentence endings (. ? ! or newlines)
    sentences = re.split(r'(?<=[.!?\n])\s+', text)
    
    chunks = []
    current_chunk = []
    current_length = 0
    
    for sentence in sentences:
        # Check if adding this sentence keeps us under the limit
        if current_length + len(sentence) > max_chars and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_length = 0
        
        current_chunk.append(sentence)
        current_length += len(sentence)
    
    if current_chunk:
        chunks.append(" ".join(current_chunk))
        
    return chunks

@app.post("/translate")
async def translate_text(request: TranslationRequest):
    print(f"--- New Request: {len(request.text)} chars ---")
    
    chunks = chunk_text(request.text, max_chars=600)
    print(f"Split into {len(chunks)} smaller chunks.")
    
    final_full_translation = []
    final_word_mapping = []

    for i, chunk in enumerate(chunks):
        if not chunk.strip():
            continue
            
        print(f"Processing Chunk {i+1}/{len(chunks)}...")
        
        # --- 2. STRICTER PROMPT ---
        # Explicitly telling it NOT to summarize and to be complete.
        system_prompt = f"""
        You are a strict translator. Translate the text into {request.target_lang}.
        
        CRITICAL RULES:
        1. You must return valid JSON.
        2. "word_mapping": You MUST create a mapping object for EVERY SINGLE WORD in the source text. Do not skip words. Do not summarize.
        3. "full_translation": The natural translation of the sentence.
        
        JSON Structure:
        {{
          "full_translation": "string",
          "word_mapping": [
             {{"original": "Word1", "translated": "Trans1"}},
             {{"original": "Word2", "translated": "Trans2"}}
          ]
        }}
        """

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chunk}
                ],
                # Using the largest model to ensure it follows instructions
                model="llama-3.3-70b-versatile", 
                temperature=0.3, # Lower temperature = more precise/less creative
                response_format={"type": "json_object"}
            )
            
            response_content = chat_completion.choices[0].message.content
            chunk_data = json.loads(response_content)
            
            # 3. VERIFY DATA BEFORE ADDING
            chunk_trans = chunk_data.get("full_translation", "")
            chunk_map = chunk_data.get("word_mapping", [])
            
            # Add to our final list
            final_full_translation.append(chunk_trans)
            final_word_mapping.extend(chunk_map)
            
            print(f"   -> Success: Got {len(chunk_map)} words mapped.")

        except Exception as e:
            print(f"   -> ERROR on chunk {i+1}: {e}")
            # Fallback so the text doesn't disappear completely
            final_full_translation.append(f"[{chunk}]") 

    print(f"--- Done. Total words mapped: {len(final_word_mapping)} ---")

    return {
        "full_translation": " ".join(final_full_translation),
        "word_mapping": final_word_mapping
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)