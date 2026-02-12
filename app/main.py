from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
import os

# Import routers
from app.controllers.manufacturer_controller import router as manufacturer_router
from app.controllers.distributor_controller import router as distributor_router
from app.controllers.seller_controller import router as seller_router
from app.controllers.auth_controller import router as auth_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    debug=settings.DEBUG,
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change to specific domains in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files for image serving
uploads_dir = "uploads"
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Include routers
app.include_router(auth_router)
app.include_router(manufacturer_router)
app.include_router(distributor_router)
app.include_router(seller_router)

# Health check endpoint
@app.get("/", tags=["Health"])
def read_root():
    return {"message": f"{settings.PROJECT_NAME} is running!"}