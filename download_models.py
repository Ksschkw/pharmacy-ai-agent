# download_models.py
from paddleocr import PaddleOCR
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_models():
    try:
        logger.info("Downloading PaddleOCR models...")
        ocr = PaddleOCR(
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            show_log=True
        )
        # Test with a simple image to force model download
        ocr.predict(input="https://paddleocr.bj.bcebos.com/ppstructure/docs/table/table.jpg")
        logger.info("Models downloaded successfully!")
    except Exception as e:
        logger.error(f"Model download failed: {e}")

if __name__ == "__main__":
    download_models()