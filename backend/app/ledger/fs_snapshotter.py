import os
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from app.ledger.blake3_hasher import hash_bytes, hash_file, hash_json
from app.config import settings

EXCLUDE_PATTERNS = {".git", "__pycache__", ".pytest_cache", "node_modules", ".venv", ".DS_Store"}

class FSSnapshotter:
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = Path(storage_dir or settings.BLOB_STORAGE_PATH)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_index_dir = self.storage_dir / "snapshots"
        self.snapshots_index_dir.mkdir(parents=True, exist_ok=True)
        self.blobs_dir = self.storage_dir / "blobs"
        self.blobs_dir.mkdir(parents=True, exist_ok=True)

    def _should_exclude(self, path: Path) -> bool:
        for part in path.parts:
            if part in EXCLUDE_PATTERNS or part.endswith(".pyc"):
                return True
        return False

    def store_blob(self, data: bytes) -> str:
        digest = hash_bytes(data)
        blob_path = self.blobs_dir / digest
        if not blob_path.exists():
            with open(blob_path, "wb") as f:
                f.write(data)
        return digest

    def get_blob(self, digest: str) -> Optional[bytes]:
        blob_path = self.blobs_dir / digest
        if blob_path.exists():
            with open(blob_path, "rb") as f:
                return f.read()
        return None

    def take_snapshot(self, root_dir: Path | str) -> Tuple[str, Dict[str, str]]:
        """
        Takes a content-addressed snapshot of a directory.
        Returns: (merkle_root_hash, manifest_dict)
        where manifest_dict maps relative_path -> blake3_digest
        """
        root = Path(root_dir).resolve()
        if not root.exists():
            return "empty", {}

        manifest: Dict[str, str] = {}
        for file_path in sorted(root.rglob("*")):
            if file_path.is_file() and not self._should_exclude(file_path):
                rel_path = str(file_path.relative_to(root))
                digest = hash_file(file_path)
                manifest[rel_path] = digest
                # Store blob in content-addressed store
                blob_dest = self.blobs_dir / digest
                if not blob_dest.exists():
                    shutil.copyfile(file_path, blob_dest)

        root_hash = hash_json(manifest)
        # Save manifest
        manifest_file = self.snapshots_index_dir / f"{root_hash}.json"
        with open(manifest_file, "w") as f:
            import json
            json.dump(manifest, f, indent=2, sort_keys=True)

        return root_hash, manifest

    def load_manifest(self, root_hash: str) -> Optional[Dict[str, str]]:
        if root_hash == "empty":
            return {}
        manifest_file = self.snapshots_index_dir / f"{root_hash}.json"
        if manifest_file.exists():
            import json
            with open(manifest_file, "r") as f:
                return json.load(f)
        return None

    def restore_snapshot(self, root_hash: str, target_dir: Path | str) -> bool:
        manifest = self.load_manifest(root_hash)
        if manifest is None:
            return False

        target = Path(target_dir).resolve()
        target.mkdir(parents=True, exist_ok=True)

        for rel_path, digest in manifest.items():
            dest = target / rel_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            blob = self.get_blob(digest)
            if blob is not None:
                with open(dest, "wb") as f:
                    f.write(blob)
        return True

    def diff_snapshots(self, hash_a: str, hash_b: str) -> Dict[str, List[str]]:
        manifest_a = self.load_manifest(hash_a) or {}
        manifest_b = self.load_manifest(hash_b) or {}

        added = [p for p in manifest_b if p not in manifest_a]
        deleted = [p for p in manifest_a if p not in manifest_b]
        modified = [p for p in manifest_b if p in manifest_a and manifest_b[p] != manifest_a[p]]

        return {
            "added": sorted(added),
            "deleted": sorted(deleted),
            "modified": sorted(modified)
        }
