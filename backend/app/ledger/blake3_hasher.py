import json
from pathlib import Path
from typing import Any, Union

try:
    import blake3
    def hash_bytes(data: bytes) -> str:
        return blake3.blake3(data).hexdigest()
except ImportError:
    import hashlib
    def hash_bytes(data: bytes) -> str:
        return hashlib.blake2b(data).hexdigest()

def hash_str(text: str) -> str:
    return hash_bytes(text.encode("utf-8"))

def hash_json(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return hash_bytes(serialized.encode("utf-8"))

def hash_file(path: Union[str, Path]) -> str:
    p = Path(path)
    if not p.exists() or not p.is_file():
        raise FileNotFoundError(f"File not found: {path}")
    
    try:
        import blake3
        hasher = blake3.blake3()
    except ImportError:
        import hashlib
        hasher = hashlib.blake2b()

    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()
