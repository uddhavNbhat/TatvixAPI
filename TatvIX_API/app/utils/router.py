from typing import Dict
from io import BytesIO
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from app.utils.logger import logger

def is_allowed_mime(mime_type: str):
    """ Checks if the mime type uploaded is allowed """
    try:
        mime_type_map = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpeg": "image/jpeg",
        }

        mime_type = mime_type.split('/')[-1]

        if mime_type not in mime_type_map.keys():
            raise Exception("Mime type not supported! ")

        return mime_type_map[mime_type]
    except Exception as e:
        raise e

def read_file_content(data: bytes) -> Dict[int, str] | bool:
    """ Reads raw file content if readable, else returns false """
    try:
        texts = {}
        is_text = False
        pdf_data = BytesIO(data)
        reader = PdfReader(stream=pdf_data)
        for index, page in enumerate(reader.pages):
            text = page.extract_text()
            if text and len(text.strip()) > 0:
                is_text = True
                texts[index] = text

        if is_text:
            return texts
        else:
            return False
    except PdfReadError:
        logger.error("Error: Cannot read file. It might be corrupted or encrypted.")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        return False