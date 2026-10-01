import os
import random
import uuid
import re
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel
from supabase import create_client, client

# Safely load local .env if it exists, otherwise skip on cloud platforms like Render
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

app = FastAPI(title="QuickDrop API")

# --- Initialize Supabase ---
supabase_url = os.environ.get("SUPABASE_URL")
supabase_key = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(supabase_url, supabase_key)

BUCKET_NAME = "payloads"

class FetchPayload(BaseModel):
    pin: str

# --- API Endpoints ---

@app.post("/api/generate-upload")
async def generate_upload(
    file: UploadFile = File(...),
    time_limit_sec: int = Form(...),
    max_downloads: int = Form(...)
):
    """Uploads file securely through the backend using admin keys."""
    pin = str(random.randint(100000, 999999))
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', file.filename)
    object_key = f"{uuid.uuid4()}_{safe_filename}"
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=time_limit_sec)
    
    # Read file data
    file_bytes = await file.read()
    
    # 1. Upload directly to Supabase Storage as Admin
    try:
        res = supabase.storage.from_(BUCKET_NAME).upload(
            path=object_key,
            file=file_bytes,
            file_options={"content-type": file.content_type or "application/octet-stream"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage Upload Exception: {str(e)}")

    # 2. Insert tracking metadata into the quickdrop_files table
    try:
        supabase.table("quickdrop_files").insert({
            "pin": pin,
            "object_key": object_key,
            "filename": file.filename,
            "expires_at": expires_at.isoformat(),
            "max_downloads": max_downloads,
            "current_downloads": 0
        }).execute()
    except Exception as e:
        # Rollback storage upload if DB insert fails
        try:
            supabase.storage.from_(BUCKET_NAME).remove([object_key])
        except:
            pass
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    return {
        "pin": pin,
        "object_key": object_key
    }

@app.post("/api/fetch-payload")
def fetch_payload(data: FetchPayload):
    """Validates PIN, streams file bytes directly from backend, and burns it."""
    try:
        # 1. Query Database
        response = supabase.table("quickdrop_files").select("*").eq("pin", data.pin).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Invalid Key or payload was destroyed.")
        
        record = response.data[0]
        
        # 2. Check Expiration Timer
        expires_at = datetime.fromisoformat(record["expires_at"])
        if datetime.now(timezone.utc) > expires_at:
            delete_payload(record["pin"], record["object_key"])
            raise HTTPException(status_code=410, detail="Payload timed out and was permanently deleted.")

        # 3. Download file bytes directly from Supabase Storage as Admin
        file_res = supabase.storage.from_(BUCKET_NAME).download(record["object_key"])
        
        if not file_res:
            raise HTTPException(status_code=404, detail="File payload missing from storage bucket.")

        # 4. Handle Download Limits & Burn logic
        new_downloads = record["current_downloads"] + 1
        if new_downloads >= record["max_downloads"]:
            delete_payload(record["pin"], record["object_key"])
        else:
            supabase.table("quickdrop_files").update({"current_downloads": new_downloads}).eq("pin", data.pin).execute()

        # 5. Detect if it's a text snippet or a file
        is_text = record["filename"].startswith("snippet_") and record["filename"].endswith(".txt")
        payload_type = "text" if is_text else "file"
        
        if is_text:
            text_content = file_res.decode("utf-8", errors="ignore")
            return Response(
                content=text_content,
                media_type="text/plain",
                headers={
                    "X-Payload-Type": "text",
                    "X-Filename": record["filename"],
                    "X-Downloads-Remaining": str(record["max_downloads"] - new_downloads)
                }
            )
        else:
            return Response(
                content=file_res,
                media_type="application/octet-stream",
                headers={
                    "X-Payload-Type": "file",
                    "Content-Disposition": f'attachment; filename="{record["filename"]}"',
                    "X-Downloads-Remaining": str(record["max_downloads"] - new_downloads)
                }
            )
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
def delete_payload(pin: str, object_key: str):
    """Helper function to permanently destroy files and database records."""
    try:
        supabase.storage.from_(BUCKET_NAME).remove([object_key])
        supabase.table("quickdrop_files").delete().eq("pin", pin).execute()
    except Exception:
        pass

# --- Serve the Frontend UI ---
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("static/index.html")