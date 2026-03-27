from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from src.utils import is_allowed_mime
from pathlib import Path
import uuid
import logging

app = FastAPI()

logging.basicConfig(level=logging.DEBUG)

# Base storage path
STORAGE_PATH = Path("/storage")

origins = ["http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/upload", status_code=201)
async def upload(file: UploadFile = File()):
    try:
        fid = str(uuid.uuid4())  # Unique file id generated per file upload
        ext = Path(file.filename).suffix
        path = STORAGE_PATH / f"{fid}{ext}"

        logging.info(path)

        mime_type = is_allowed_mime(path=path)

        with open(path, "wb") as f:
            f.write(await file.read())

        logging.info(path)

        return {"ok": True, "file_id": f"/storage/{fid}", "mime_type": mime_type}

    except Exception as e:
        logging.info(f"Error at upload: {e}")
        return HTTPException(500, {"ok": False, "error": "Internal Server Error!"})


@app.get("/api/download/{fid}", status_code=200)
async def download(fid: str, mime_type: str):
    try:
        path = STORAGE_PATH / f"{fid}.{mime_type}"
        mime_type = is_allowed_mime(path=path)

        return FileResponse(path, media_type=mime_type, filename=fid)

    except Exception as e:
        logging.info(f"Error at download: {e}")
        return HTTPException(500, {"ok": False, "error": "Internal Server Error!"})


@app.delete("/api/invalidate/{fid}", status_code=204)
async def delete(fid: str, mime_type: str):
    try:
        path = STORAGE_PATH / f"{fid}.{mime_type}"

        is_allowed_mime(path=path)

        if path.exists():
            path.unlink()
            return

        raise HTTPException(404, {"ok": False, "error": "No such file exists!"})

    # If http execption, catch and raise it
    except HTTPException:
        raise

    except Exception as e:
        logging.info(f"Error at delete: {e}")
        raise HTTPException(500, {"ok": False, "error": "Internal Server Error!"})
