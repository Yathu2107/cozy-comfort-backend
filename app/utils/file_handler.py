import os
import uuid
from typing import Optional
from fastapi import UploadFile, HTTPException
import aiofiles

# Allowed image extensions
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create uploads directory if it doesn't exist
UPLOAD_DIR = "uploads/blanket_images"
os.makedirs(UPLOAD_DIR, exist_ok=True)

async def save_image(file: UploadFile) -> str:
    """
    Save uploaded image file and return the file path
    """
    # Check file extension
    file_extension = os.path.splitext(file.filename)[1].lower()
    if file_extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_extension}"
    file_path = os.path.join(UPLOAD_DIR, unique_filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        await f.write(contents)
    
    # Return relative path for URL
    return f"/uploads/blanket_images/{unique_filename}"

def delete_image(image_url: str) -> bool:
    """
    Delete image file from filesystem
    """
    try:
        if image_url and image_url.startswith("/uploads/"):
            file_path = image_url[1:]  # Remove leading slash
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
    except Exception:
        pass
    return False

def validate_image_file(file: UploadFile) -> bool:
    """
    Validate if uploaded file is a valid image
    """
    if not file.filename:
        return False
    
    file_extension = os.path.splitext(file.filename)[1].lower()
    return file_extension in ALLOWED_EXTENSIONS
