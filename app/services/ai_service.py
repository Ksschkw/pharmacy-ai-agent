import requests
import json
import logging
import urllib3
from dotenv import load_dotenv
from pathlib import Path
from typing import Dict, List, Optional

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

def parse_prescription(ocr_text: str, api_key: str) -> Dict:
    """Parse prescription text using LLM"""
    models = {
        "deepseek-chat": "deepseek/deepseek-chat-v3-0324:free",
        "deepseek-r1": "deepseek/deepseek-r1-0528:free",
        "mistralai": "mistralai/mistral-7b-instruct"
    }

    for model_name, model_id in models.items():
        try:
            logging.info(f"Trying model: {model_name} ({model_id})")
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}"},
                json={
                    "model": model_id,
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a medical prescription parsing assistant. Your sole task is to extract specific, structured information from prescription text and return it as a JSON object. You must adhere strictly to the provided JSON schema. If a field's value cannot be found in the text, it should be set to null. Do not include any fields not explicitly defined in the schema below. **Prioritize understanding the intent despite common OCR errors like swapped characters (e.g., 'O' for '0', 'l' for '1', 'S' for '5'), missing letters, or extra spaces. Correct these errors internally before extraction.**\n\nJSON Schema:\n{\n  \"medications\": [\n    {\n      \"name\": \"string\",\n      \"dosage\": \"string\",\n      \"frequency\": \"string\"\n    }\n  ],\n  \"doctor\": \"string\",\n  \"date_issued\": \"string\" (YYYY-MM-DD format),\n  \"patient_name\": \"string\"\n}"
                        },
                        {
                            "role": "user",
                            "content": f"Prescription text: {ocr_text}"
                        }
                    ]
                },
                timeout=30,
                verify=False
            )
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            json_start = content.find("{")
            json_end = content.rfind("}") + 1
            if json_start != -1:
                json_string = content[json_start:json_end]
                parsed_data = json.loads(json_string)
                # Ensure medications list is valid
                if "medications" in parsed_data:
                    for med in parsed_data["medications"]:
                        if "frequency" not in med or med["frequency"] is None:
                            med["frequency"] = "Not specified"  # Fallback value
                return parsed_data
        except requests.exceptions.HTTPError as http_err:
            logging.error(f"HTTP Error with {model_name}: {http_err}")
            if 'response' in locals():
                logging.error(f"API response: {response.text}")
        except Exception as e:
            logging.error(f"Error with {model_name}: {e}")
    
    logging.error("All API calls failed.")
    return {
        "error": "Failed to parse prescription",
        "raw_text": ocr_text
    }