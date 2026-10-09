from pathlib import Path
from fastapi import APIRouter, HTTPException, Response
from pydantic import BaseModel
from app.ledger.fs_snapshotter import FSSnapshotter

router = APIRouter(prefix="/snapshots", tags=["Snapshots"])
snapshotter = FSSnapshotter()

class SnapshotRequest(BaseModel):
    directory_path: str

@router.post("", response_model=dict)
async def take_snapshot(req: SnapshotRequest):
    p = Path(req.directory_path)
    if not p.exists():
        raise HTTPException(status_code=400, detail=f"Directory does not exist: {req.directory_path}")
    root_hash, manifest = snapshotter.take_snapshot(p)
    return {
        "root_hash": root_hash,
        "file_count": len(manifest),
        "manifest": manifest
    }

@router.get("/{root_hash}", response_model=dict)
async def get_manifest(root_hash: str):
    manifest = snapshotter.load_manifest(root_hash)
    if manifest is None:
        raise HTTPException(status_code=404, detail="Snapshot manifest not found.")
    return {"root_hash": root_hash, "manifest": manifest}

@router.get("/blobs/{digest}")
async def get_blob(digest: str):
    blob = snapshotter.get_blob(digest)
    if blob is None:
        raise HTTPException(status_code=404, detail="Blob not found.")
    return Response(content=blob, media_type="application/octet-stream")
