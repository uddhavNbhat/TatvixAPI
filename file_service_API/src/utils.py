import mimetypes
from pathlib import Path
import logging

def is_allowed_mime(path: Path):
    """ Checks if the mime type uploaded is allowed """
    try:
        mime_type_map = {
            "pdf": "application/pdf",
            "png": "image/png",
            "jpeg": "image/jpeg",
        }
        
        mime_type, _ = mimetypes.guess_type(path) # Dervies mime type dynamically based on file format stored
        
        mime_type = mime_type.split('/')[-1]
        
        logging.info(mime_type)
        
        if mime_type not in mime_type_map.keys():
            raise Exception("Mime type not supported! ")
        
        return mime_type_map[mime_type]
    except Exception as e:
        raise e