from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pathlib import Path
from datetime import datetime, timezone
import io
import uuid
import logging
import jwt

from database import db
from auth import get_current_user, JWT_SECRET, JWT_ALGORITHM

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/bridge/download")
async def download_bridge_zip(user: dict = Depends(get_current_user)):
    return _create_bridge_zip()


@router.get("/bridge/download-direct")
async def download_bridge_direct(token: str = None):
    if not token:
        raise HTTPException(status_code=401, detail="Token necesar")
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except Exception:
        raise HTTPException(status_code=401, detail="Token invalid")
    return _create_bridge_zip()


def _create_bridge_zip():
    import zipfile
    bridge_dir = Path(__file__).parent.parent
    files_to_zip = {
        "fiscal_bridge.py": bridge_dir / "fiscal_bridge.py",
        "install_bridge.bat": bridge_dir / "install_bridge.bat",
        "start_bridge.bat": bridge_dir / "start_bridge.bat",
        "ACTUALIZEAZA_BRIDGE.bat": bridge_dir / "actualizeaza_bridge.bat",
    }
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
        for name, path in files_to_zip.items():
            if path.exists():
                zf.write(path, name)
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=ANDREPAU_Bridge_Service.zip"}
    )


@router.post("/fiscal/queue")
async def queue_fiscal_job(data: dict, user: dict = Depends(get_current_user)):
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "type": data.get("type", "receipt"),
        "data": data.get("data", {}),
        "status": "pending",
        "result": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": user.get("username", "unknown"),
        "completed_at": None
    }
    await db.fiscal_jobs.insert_one(job)
    logger.info(f"[FISCAL] Job queued: {job['type']} | ID: {job_id} | By: {user.get('username')}")
    return {"job_id": job_id, "status": "pending"}


@router.get("/fiscal/pending")
async def get_pending_jobs(bridge_key: str = None):
    jobs = await db.fiscal_jobs.find(
        {"status": "pending"},
        {"_id": 0}
    ).sort("created_at", 1).limit(1).to_list(1)

    if jobs:
        job = jobs[0]
        await db.fiscal_jobs.update_one(
            {"job_id": job["job_id"], "status": "pending"},
            {"$set": {"status": "processing"}}
        )
        return {"job": job}
    return {"job": None}


@router.post("/fiscal/result/{job_id}")
async def report_fiscal_result(job_id: str, data: dict):
    status = "completed" if data.get("success") else "failed"
    result = await db.fiscal_jobs.update_one(
        {"job_id": job_id},
        {"$set": {
            "status": status,
            "result": data,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Job negasit")
    logger.info(f"[FISCAL] Job result: {job_id} | Status: {status} | Error: {data.get('error', 'none')}")
    return {"ok": True}


@router.get("/fiscal/status/{job_id}")
async def get_fiscal_job_status(job_id: str):
    job = await db.fiscal_jobs.find_one(
        {"job_id": job_id},
        {"_id": 0}
    )
    if not job:
        raise HTTPException(status_code=404, detail="Job negasit")
    return job


@router.get("/fiscal/bridge-status")
async def get_bridge_status():
    last_poll = await db.fiscal_bridge_status.find_one(
        {"key": "last_poll"},
        {"_id": 0}
    )
    if last_poll:
        last_time = datetime.fromisoformat(last_poll["timestamp"])
        now = datetime.now(timezone.utc)
        connected = (now - last_time).total_seconds() < 30
        return {"connected": connected, "last_poll": last_poll["timestamp"]}
    return {"connected": False, "last_poll": None}


@router.post("/fiscal/bridge-ping")
async def bridge_ping():
    await db.fiscal_bridge_status.update_one(
        {"key": "last_poll"},
        {"$set": {"key": "last_poll", "timestamp": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    return {"ok": True}
