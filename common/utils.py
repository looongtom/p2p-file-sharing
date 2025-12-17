import json, hashlib, base64

def jencode(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

def jdecode(b: bytes) -> dict:
    return json.loads(b.decode("utf-8", errors="ignore"))

def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def b64e(b: bytes) -> str:
    return base64.b64encode(b).decode("ascii")

def b64d(s: str) -> bytes:
    return base64.b64decode(s.encode("ascii"))
