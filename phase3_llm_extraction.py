# phase3_llm_extraction.py
import json
from groq import Groq

client = Groq(api_key="")  # get this from https://console.groq.com/keys

def call_llm(prompt):
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",   # fast, free-tier model
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

def extract_and_clean_address(address_text, landmark_text=""):
    """Takes raw address (+ optional landmark) text, returns a cleaned, geocodable address string."""
    combined_text = f"{address_text}, {landmark_text}" if landmark_text else address_text

    prompt = f"""
Extract and reconstruct a complete, standard physical address from this text in a way that my geocoder can understand.
Always include city, province, and country if they can be reasonably inferred 
(assume Karachi, Sindh, Pakistan if no other city is mentioned and context suggests Pakistan).
Ignore floor/flat/unit numbers and informal building descriptions — focus on road, area, and landmark names.
Return the address as a SINGLE LINE, comma-separated (e.g. "Road, City, Province, Country"). 
Do not use line breaks. Return ONLY the address, nothing else, no explanation.


Text: "{combined_text}"
"""
    # --- Call your chosen LLM API here (Gemini/Groq) ---
    response = call_llm(prompt)
    print(f"[DEBUG] LLM returned: {repr(response)}")   # placeholder — plug in your actual API call
    cleaned_address = response.strip()

    return cleaned_address