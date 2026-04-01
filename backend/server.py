from fastapi import FastAPI, APIRouter
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.cors import CORSMiddleware
from pathlib import Path
import os
import logging

from database import db, client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="ANDREPAU POS API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Import route modules
from routes.auth import router as auth_router
from routes.products import router as products_router
from routes.suppliers import router as suppliers_router
from routes.sales import router as sales_router
from routes.nir import router as nir_router
from routes.reports import router as reports_router
from routes.cash import router as cash_router
from routes.bridge import router as bridge_router
from routes.held_orders import router as held_orders_router
from routes.exports import router as exports_router
from routes.anaf import router as anaf_router
from routes.seed import router as seed_router
from routes.sync import router as sync_router

# Include all routers
api_router.include_router(auth_router)
api_router.include_router(products_router)
api_router.include_router(suppliers_router)
api_router.include_router(sales_router)
api_router.include_router(nir_router)
api_router.include_router(reports_router)
api_router.include_router(cash_router)
api_router.include_router(bridge_router)
api_router.include_router(held_orders_router)
api_router.include_router(exports_router)
api_router.include_router(anaf_router)
api_router.include_router(seed_router)
api_router.include_router(sync_router)


@api_router.get("/")
async def root():
    return {"message": "ANDREPAU POS API", "version": "2.0.0"}


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- LOCAL MODE: Serve React build if it exists ---
_build_dir = Path(__file__).parent.parent / "frontend" / "build"
if _build_dir.exists():
    # Serve static assets (JS, CSS, images)
    _static_dir = _build_dir / "static"
    if _static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(_static_dir)), name="react_static")

    @app.get("/{full_path:path}")
    async def serve_react_app(full_path: str):
        """Serve React SPA - catch-all for non-API routes (local mode only)"""
        file_path = _build_dir / full_path
        if full_path and file_path.exists() and file_path.is_file():
            return FileResponse(str(file_path))
        return FileResponse(str(_build_dir / "index.html"))


@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
