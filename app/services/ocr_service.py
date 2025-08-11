import cv2
from paddleocr import PaddleOCR
import os
import logging
from .ai_service import parse_prescription
from dotenv import load_dotenv
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.ERROR)

# Load environment variables
env_path = Path(__file__).resolve().parent.parent.parent / '.env'
load_dotenv(env_path)

class OCRService:
    def __init__(self):
        det_model_dir = str(Path(__file__).parent.parent.parent / 'paddle_models' / 'models' / 'ppocrv5_server_det')
        rec_model_dir = str(Path(__file__).parent.parent.parent / 'paddle_models' / 'models' / 'ppocrv5_server_rec')
        self.ocr = PaddleOCR(
            det_model_dir=det_model_dir,
            rec_model_dir=rec_model_dir,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False
        )
        self.api_key = os.getenv("API_KEY")
    
    def process_image(self, image_path: str):
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image at {image_path}")
            
            result = self.ocr.predict(input=img)
            rec_texts = []
            for res in result:
                rec_texts.extend(res.get('rec_texts', []))
            
            ocr_text = " ".join(rec_texts)
            parsed_data = parse_prescription(ocr_text, self.api_key)
            
            return {
                "image_path": image_path,
                "ocr_raw": ocr_text,
                "parsed_data": parsed_data
            }
        except Exception as e:
            logging.error(f"OCR Processing Error: {e}")
            return {
                "image_path": image_path,
                "ocr_raw": "",
                "parsed_data": {"error": str(e)}
            }