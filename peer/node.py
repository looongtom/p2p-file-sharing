import os
import re
import json
import time
import socket
import threading
import base64
import hashlib
import shutil
from typing import Dict, Any, Tuple, Optional
from functools import wraps
from flask import Flask, request, jsonify, Response
from flask_cors import CORS

from common.constants import (
    TRACKER_HOST,
    TRACKER_PORT,
    ADVERTISE_HOST,
    NODE_PORT,
    BUFFER_SIZE,
    PIECE_SIZE,
    BLOCK_SIZE,
    HEARTBEAT_SEC,
    SEED_DIR,
    DOWNLOAD_DIR,
    MODE_OWN,
    MODE_NEED,
    MODE_LIST,
    MODE_FIND_BY_NAME,
    MODE_REGISTER,
    MODE_EXIT,
    T_GET_PIECE,
    T_PIECE_BLOCK,
)
from common.utils import jencode, jdecode, sha256_hex, b64e, b64d


class Node:
    def __init__(self, node_id: int):
        self.node_id = node_id
        self.seed_dir = SEED_DIR
        self.download_dir = DOWNLOAD_DIR

        self.tracker = (TRACKER_HOST, TRACKER_PORT)

        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(("0.0.0.0", NODE_PORT))
        self.sock.settimeout(0.5)

        # download sessions: infohash -> state dict
        self.dl_lock = threading.Lock()
        self.downloads: Dict[str, Dict[str, Any]] = {}

        # keep track of seeded torrents so tracker TTL won't drop them (optional but useful)
        self.seeding = set()

        # User authentication storage
        self.users_file = os.path.join("/app", "users.json")
        self.users_lock = threading.Lock()
        self._ensure_users_file()

        self._log(f"bind=0.0.0.0:{NODE_PORT} advertise={ADVERTISE_HOST}:{NODE_PORT}")
        self._log(f"tracker={TRACKER_HOST}:{TRACKER_PORT} piece_size={PIECE_SIZE} block_size={BLOCK_SIZE}")

        threading.Thread(target=self._recv_loop, daemon=True).start()
        threading.Thread(target=self._heartbeat_loop, daemon=True).start()
        threading.Thread(target=self._sync_node_files_loop, daemon=True).start()

    def _log(self, msg: str) -> None:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S")
        print(f"{ts} [NODE {self.node_id}] {msg}", flush=True)

    # ---------------- User Authentication ----------------
    def _ensure_users_file(self) -> None:
        """Create users.json file if it doesn't exist"""
        if not os.path.exists(self.users_file):
            with open(self.users_file, "w", encoding="utf-8") as fp:
                json.dump({}, fp, indent=2)

    def _load_users(self) -> Dict[str, str]:
        """Load users from file"""
        with self.users_lock:
            if not os.path.exists(self.users_file):
                return {}
            try:
                with open(self.users_file, "r", encoding="utf-8") as fp:
                    return json.load(fp)
            except Exception:
                return {}

    def _save_users(self, users: Dict[str, str]) -> None:
        """Save users to file"""
        with self.users_lock:
            tmp = self.users_file + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fp:
                json.dump(users, fp, indent=2, ensure_ascii=False)
            os.replace(tmp, self.users_file)

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA256"""
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

    def _register_user(self, username: str, password: str) -> bool:
        """Register a new user"""
        if not username or not password:
            return False
        users = self._load_users()
        if username in users:
            return False  # User already exists
        users[username] = self._hash_password(password)
        self._save_users(users)
        return True

    def _verify_user(self, username: str, password: str) -> bool:
        """Verify user credentials"""
        users = self._load_users()
        if username not in users:
            return False
        return users[username] == self._hash_password(password)

    # ---------------- Tracker calls ----------------
    def _send_tracker(self, msg: Dict[str, Any]) -> None:
        encoded = jencode(msg)
        msg_size = len(encoded)
        if msg_size > BUFFER_SIZE:
            self._log(f"WARNING: Message size {msg_size} exceeds BUFFER_SIZE {BUFFER_SIZE}, may fail")
        try:
            self.sock.sendto(encoded, self.tracker)
        except OSError as e:
            if e.errno == 90:  # Message too long
                self._log(f"ERROR: Message too long ({msg_size} bytes) to send to tracker. File metadata too large.")
                raise
            raise

    def _tracker_call(self, req: Dict[str, Any]) -> Dict[str, Any]:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.settimeout(3.0)
        s.sendto(jencode(req), self.tracker)
        data, _ = s.recvfrom(BUFFER_SIZE)
        s.close()
        return jdecode(data)

    def _tracker_need(self, infohash: str) -> Dict[str, Any]:
        return self._tracker_call({"mode": MODE_NEED, "node_id": self.node_id, "infohash": infohash})

    def _tracker_list(self) -> Dict[str, Any]:
        return self._tracker_call({"mode": MODE_LIST, "node_id": self.node_id})

    def _tracker_find_by_name(self, filename: str) -> Dict[str, Any]:
        return self._tracker_call({"mode": MODE_FIND_BY_NAME, "node_id": self.node_id, "filename": filename})

    def _heartbeat_loop(self) -> None:
        """
        Heartbeat/REGISTER for both:
        - active downloads
        - active seeding torrents
        This prevents tracker TTL from dropping owners.
        """
        while True:
            time.sleep(HEARTBEAT_SEC)
            with self.dl_lock:
                active = set(self.downloads.keys()) | set(self.seeding)
            for ih in active:
                self._send_tracker({"mode": MODE_REGISTER, "node_id": self.node_id, "infohash": ih})

    # ---------------- Meta / Own ----------------
    def _build_meta(self, filepath: str) -> Tuple[str, Dict[str, Any]]:
        size = os.path.getsize(filepath)
        piece_hashes = []
        with open(filepath, "rb") as fp:
            while True:
                piece = fp.read(PIECE_SIZE)
                if not piece:
                    break
                piece_hashes.append(sha256_hex(piece))
        meta = {
            "filename": os.path.basename(filepath),
            "size": size,
            "piece_size": PIECE_SIZE,
            "piece_hashes": piece_hashes,
        }
        infohash = sha256_hex(json.dumps(meta, sort_keys=True).encode("utf-8"))
        return infohash, meta

    def own_file(self, filename: str) -> bool:
        path = os.path.join("/app", self.seed_dir, filename)
        if not os.path.exists(path):
            self._log(f"File not found (seed): {path}")
            return False

        try:
            ih, meta = self._build_meta(path)
            msg = {
                "mode": MODE_OWN,
                "node_id": self.node_id,
                "host": ADVERTISE_HOST,
                "port": NODE_PORT,
                "infohash": ih,
                "meta": meta,
            }
            # Check message size before sending
            encoded = jencode(msg)
            if len(encoded) > BUFFER_SIZE:
                self._log(f"OWN skipped: {filename} metadata too large ({len(encoded)} bytes, max {BUFFER_SIZE}). File has {len(meta['piece_hashes'])} pieces.")
                return False
            
            self._send_tracker(msg)
            self.seeding.add(ih)
            self._log(f"OWN announced: {filename} ih={ih[:10]}.. size={meta['size']} pieces={len(meta['piece_hashes'])}")
            return True
        except OSError as e:
            if e.errno == 90:  # Message too long
                self._log(f"OWN failed: {filename} - Message too long. File metadata exceeds UDP limit.")
                return False
            raise

    # ---------------- Resume helpers ----------------
    def _resume_paths(self, filename: str, target_dir: Optional[str] = None) -> Tuple[str, str]:
        if target_dir is None:
            target_dir = self.download_dir
        rp = os.path.join("/app", target_dir, f"{filename}.resume.json")
        pp = os.path.join("/app", target_dir, f"{filename}.part")
        return rp, pp

    def _save_resume(self, st: Dict[str, Any]) -> None:
        """
        Persist only JSON-serializable fields.
        DO NOT include st['buffers'] (contains bytes).
        """
        rp = st["resume_path"]
        tmp = rp + ".tmp"
        safe = {
            "infohash": st.get("infohash"),
            "filename": st.get("filename"),
            "size": st.get("size"),
            "piece_size": st.get("piece_size"),
            "piece_hashes": st.get("piece_hashes"),
            "completed": st.get("completed"),
            "done": st.get("done"),
            "total_pieces": st.get("total_pieces"),
        }
        with open(tmp, "w", encoding="utf-8") as fp:
            json.dump(safe, fp, ensure_ascii=False, indent=2)
        os.replace(tmp, rp)

    def _load_resume(self, filename: str, target_dir: Optional[str] = None) -> Optional[Dict[str, Any]]:
        rp, pp = self._resume_paths(filename, target_dir)
        if not os.path.exists(rp):
            return None
        with open(rp, "r", encoding="utf-8") as fp:
            st = json.load(fp)
        st["resume_path"] = rp
        st["part_path"] = pp
        st["buffers"] = {}
        if target_dir:
            st["target_dir"] = target_dir
        return st

    def _ensure_partfile(self, part_path: str, total_size: int) -> None:
        os.makedirs(os.path.dirname(part_path), exist_ok=True)
        if not os.path.exists(part_path):
            with open(part_path, "wb") as fp:
                fp.truncate(total_size)

    def _write_piece(self, st: Dict[str, Any], idx: int, data: bytes) -> None:
        with open(st["part_path"], "r+b") as fp:
            fp.seek(idx * st["piece_size"])
            fp.write(data)

    def _finalize(self, st: Dict[str, Any], target_dir: Optional[str] = None) -> None:
        if target_dir is None:
            target_dir = self.download_dir
        out = os.path.join("/app", target_dir, st["filename"])
        with open(st["part_path"], "rb+") as fp:
            fp.truncate(st["size"])
        os.replace(st["part_path"], out)
        try:
            os.remove(st["resume_path"])
        except Exception:
            pass
        self._log(f"DOWNLOAD COMPLETE: {st['filename']} saved to {out}")

    # ---------------- Peer transfer (UDP blocks) ----------------
    def _send_peer(self, msg: Dict[str, Any], addr: Tuple[str, int]) -> None:
        self.sock.sendto(jencode(msg), addr)

    def _find_seed_file_by_infohash(self, ih: str) -> Optional[Tuple[str, Dict[str, Any]]]:
        """
        Demo implementation: scan seed_dir to find file whose meta infohash matches.
        """
        seed_root = os.path.join("/app", self.seed_dir)
        if not os.path.exists(seed_root):
            return None

        for fn in os.listdir(seed_root):
            fp = os.path.join(seed_root, fn)
            if not os.path.isfile(fp):
                continue
            try:
                ih2, meta = self._build_meta(fp)
            except Exception:
                continue
            if ih2 == ih:
                return fp, meta
        return None

    def _serve_piece(self, ih: str, idx: int, addr: Tuple[str, int]) -> None:
        found = self._find_seed_file_by_infohash(ih)
        if not found:
            return
        fp, meta = found

        # optional server-side log
        # self._log(f"serve piece {idx} to {addr[0]}:{addr[1]}")

        with open(fp, "rb") as f:
            f.seek(idx * meta["piece_size"])
            piece = f.read(meta["piece_size"])

        total_blocks = (len(piece) + BLOCK_SIZE - 1) // BLOCK_SIZE if piece else 0
        for b in range(total_blocks):
            blk = piece[b * BLOCK_SIZE : (b + 1) * BLOCK_SIZE]
            self._send_peer(
                {
                    "type": T_PIECE_BLOCK,
                    "ih": ih,
                    "piece": idx,
                    "block": b,
                    "total_blocks": total_blocks,
                    "data": b64e(blk),
                },
                addr,
            )

    def _recv_loop(self) -> None:
        while True:
            try:
                data, addr = self.sock.recvfrom(BUFFER_SIZE)
            except socket.timeout:
                continue
            except Exception:
                continue

            try:
                msg = jdecode(data)
            except Exception:
                continue

            t = msg.get("type")
            if t == T_GET_PIECE:
                ih = msg.get("ih")
                idx = int(msg.get("piece", -1))
                if not ih or idx < 0:
                    continue
                threading.Thread(target=self._serve_piece, args=(ih, idx, addr), daemon=True).start()
                continue

            if t == T_PIECE_BLOCK:
                ih = msg.get("ih")
                if not ih:
                    continue
                p = int(msg.get("piece", -1))
                b = int(msg.get("block", -1))
                tb = int(msg.get("total_blocks", 0))
                if p < 0 or b < 0 or tb <= 0:
                    continue
                try:
                    chunk = b64d(msg.get("data", ""))
                except Exception:
                    continue

                with self.dl_lock:
                    st = self.downloads.get(ih)
                    if not st:
                        continue
                    buf = st["buffers"].setdefault(p, {"total": tb, "blocks": {}})
                    buf["total"] = tb
                    buf["blocks"][b] = chunk

    def _piece_worker(self, ih: str, peer: Dict[str, Any], q) -> None:
        """
        Worker pinned to a single peer.
        Critical fix:
        - if a piece times out or hash mismatch -> re-queue the piece (do not lose it)
        """
        import queue as _q

        addr = (peer["host"], int(peer["port"]))

        while True:
            try:
                idx = q.get_nowait()
            except _q.Empty:
                return

            success = False

            with self.dl_lock:
                st = self.downloads[ih]
                if st["completed"][idx] == 1:
                    q.task_done()
                    continue
                st["buffers"].pop(idx, None)

            # log request
            self._log(
                f"request piece {idx} from node {peer.get('node_id','?')} @ {peer['host']}:{peer['port']}"
            )

            # request piece
            self._send_peer({"type": T_GET_PIECE, "ih": ih, "piece": idx}, addr)

            deadline = time.time() + 5.0
            while time.time() < deadline:
                time.sleep(0.05)

                with self.dl_lock:
                    st = self.downloads[ih]
                    buf = st["buffers"].get(idx)
                    if not buf:
                        continue
                    if len(buf["blocks"]) != buf["total"]:
                        continue

                    blocks = buf["blocks"]
                    try:
                        data = b"".join(blocks[i] for i in range(buf["total"]))
                    except KeyError:
                        continue

                    if sha256_hex(data) != st["piece_hashes"][idx]:
                        self._log(f"piece {idx} hash mismatch -> requeue")
                        st["buffers"].pop(idx, None)
                        break

                    # write piece
                    self._write_piece(st, idx, data)
                    st["completed"][idx] = 1
                    st["done"] += 1
                    self._save_resume(st)

                    # log completed
                    self._log(
                        f"completed piece {idx} from node {peer.get('node_id','?')} @ {peer['host']}:{peer['port']}"
                    )

                    if st["done"] % 5 == 0 or st["done"] == st["total_pieces"]:
                        self._log(f"progress {st['done']}/{st['total_pieces']} pieces")

                    st["buffers"].pop(idx, None)
                    success = True
                    break

            if not success:
                # timed out (or mismatch) -> re-queue so another worker/another round can fetch it
                q.put(idx)

            q.task_done()

    # ---------------- Download ----------------
    def download_by_infohash(self, ih: str, target_dir: Optional[str] = None) -> None:
        resp = self._tracker_need(ih)
        if not resp.get("ok"):
            self._log(f"tracker says NOT_FOUND ih={ih[:10]}..")
            return

        meta = resp["meta"]
        peers = resp.get("peers", [])
        if not peers:
            self._log("no peers available")
            return

        filename = meta["filename"]
        size = int(meta["size"])
        piece_hashes = meta["piece_hashes"]
        total_pieces = len(piece_hashes)

        if target_dir is None:
            target_dir = self.download_dir

        st = self._load_resume(filename, target_dir)
        if st and st.get("infohash") == ih and st.get("piece_size") == PIECE_SIZE:
            st["piece_hashes"] = piece_hashes
            st["total_pieces"] = total_pieces
            st["done"] = int(sum(st["completed"]))
            st["target_dir"] = target_dir  # Ensure target_dir is set
            # Update peers from tracker to get current active peers
            st["active_peers"] = peers
            self._log(f"resume found: {filename} done={st['done']}/{total_pieces}")
        else:
            rp, pp = self._resume_paths(filename, target_dir)
            st = {
                "infohash": ih,
                "filename": filename,
                "size": size,
                "piece_size": PIECE_SIZE,
                "piece_hashes": piece_hashes,
                "completed": [0] * total_pieces,
                "done": 0,
                "total_pieces": total_pieces,
                "resume_path": rp,
                "part_path": pp,
                "buffers": {},
                "target_dir": target_dir,
            }
            self._ensure_partfile(pp, size)
            self._save_resume(st)

        self._ensure_partfile(st["part_path"], size)

        with self.dl_lock:
            self.downloads[ih] = st
            st["active_peers"] = peers

        self._log(f"META ok: {filename} size={size} pieces={total_pieces} peers={len(peers)} ih={ih[:10]}..")

        if st["done"] >= total_pieces:
            self._finalize(st, target_dir)
            if target_dir == self.seed_dir:
                # Auto-register with tracker after downloading to seed_dir
                self.own_file(filename)
            return

        import queue

        q = queue.Queue()
        for i in range(total_pieces):
            if st["completed"][i] == 0:
                q.put(i)

        # one worker per peer
        for peer in peers:
            threading.Thread(target=self._piece_worker, args=(ih, peer, q), daemon=True).start()

        q.join()

        with self.dl_lock:
            st2 = self.downloads.get(ih)
            if st2 and int(sum(st2["completed"])) == total_pieces:
                final_target_dir = st2.get("target_dir", target_dir)
                self._finalize(st2, final_target_dir)
                if final_target_dir == self.seed_dir:
                    # Auto-register with tracker after downloading to seed_dir
                    self.own_file(filename)
            else:
                missing = 0
                if st2:
                    missing = st2["total_pieces"] - int(sum(st2["completed"]))
                self._log(f"download finished but missing {missing} pieces (will resume on next run)")

    def download_by_filename(self, filename: str, target_dir: Optional[str] = None) -> None:
        resp = self._tracker_find_by_name(filename)
        if not resp.get("ok"):
            err = resp.get("error")
            if err == "AMBIGUOUS":
                self._log(f"AMBIGUOUS filename '{filename}'. Use infohash instead. Matches:")
                for m in resp.get("matches", []):
                    self._log(f"  {m.get('infohash','')[:10]}.. size={m.get('size')} peers={m.get('peers')}")
            else:
                self._log(f"File not found on tracker: {filename}")
            return
        ih = resp["match"]["infohash"]
        self.download_by_infohash(ih, target_dir)

    # ---------------- File Synchronization ----------------
    def _sync_file_to_dir(self, filename: str, target_dir: str) -> bool:
        """
        General function to sync a file to a specified directory.
        Downloads the file if it doesn't exist in the target directory.
        Starts download in a separate thread to avoid blocking.
        Returns True if file exists or download started, False otherwise.
        """
        target_path = os.path.join("/app", target_dir, filename)
        
        # Check if file already exists and is complete
        if os.path.exists(target_path):
            try:
                # Verify file is complete by checking size matches tracker
                resp = self._tracker_find_by_name(filename)
                if resp.get("ok"):
                    expected_size = resp["match"].get("size")
                    actual_size = os.path.getsize(target_path)
                    if expected_size == actual_size:
                        return True
            except Exception:
                pass
        
        # Check if already downloading this file to this directory
        with self.dl_lock:
            already_downloading = False
            for ih, st in self.downloads.items():
                if st.get("filename") == filename and st.get("target_dir") == target_dir:
                    already_downloading = True
                    break
        
        if already_downloading:
            return True  # Download in progress
        
        # File doesn't exist or size mismatch, start download in background
        try:
            self._log(f"SYNC: Starting download of {filename} to {target_dir}")
            threading.Thread(
                target=self.download_by_filename,
                args=(filename, target_dir),
                daemon=True
            ).start()
            return True
        except Exception as e:
            self._log(f"SYNC: Error starting sync of {filename} to {target_dir}: {e}")
            return False

    def _sync_node_files_loop(self) -> None:
        """
        Background thread that syncs node_files directory every 5 seconds.
        Implements bidirectional sync:
        - Pull: Download files from other nodes if missing
        - Push: Register local files with tracker
        """
        SYNC_INTERVAL = 5  # seconds
        
        while True:
            try:
                time.sleep(SYNC_INTERVAL)
                
                # Get list of files from tracker
                resp = self._tracker_list()
                if not resp.get("ok"):
                    continue
                
                tracker_files = {}
                for item in resp.get("items", []):
                    filename = item.get("filename")
                    if filename:
                        tracker_files[filename] = item
                
                # PULL: Download missing files from other nodes
                seed_dir_path = os.path.join("/app", self.seed_dir)
                os.makedirs(seed_dir_path, exist_ok=True)
                
                local_files = set()
                if os.path.exists(seed_dir_path):
                    for fn in os.listdir(seed_dir_path):
                        fp = os.path.join(seed_dir_path, fn)
                        if os.path.isfile(fp) and not fn.endswith(('.part', '.resume.json')):
                            local_files.add(fn)
                
                # Download files that exist on tracker but not locally
                for filename in tracker_files:
                    if filename not in local_files:
                        self._sync_file_to_dir(filename, self.seed_dir)
                
                # PUSH: Register local files with tracker
                for filename in local_files:
                    file_path = os.path.join(seed_dir_path, filename)
                    if not os.path.isfile(file_path):
                        continue
                    
                    # Check if file is already registered
                    try:
                        ih, meta = self._build_meta(file_path)
                        if ih not in self.seeding:
                            # File exists locally but not registered, register it
                            self.own_file(filename)
                    except Exception as e:
                        self._log(f"SYNC: Error registering {filename}: {e}")
                        continue
                
            except Exception as e:
                self._log(f"SYNC: Error in sync loop: {e}")
                continue

    # ---------------- API Server ----------------
    def start_api(self, api_port: int = 5000) -> None:
        """
        Start Flask API server to replace interactive CLI.
        API endpoints:
        - POST /api/register - Register a new user
        - POST /api/login - Login using Basic Auth
        - POST /api/torrent/send - Share a file (requires Basic Auth)
        - GET /api/torrent/list - List files on tracker (requires Basic Auth)
        - POST /api/torrent/download - Download a file by filename or infohash (requires Basic Auth)
        - POST /api/exit - Gracefully exit (requires Basic Auth)
        """
        app = Flask(__name__)
        CORS(app)  # Enable CORS for all routes

        def check_auth(username: str, password: str) -> bool:
            """Check if username and password are valid"""
            return self._verify_user(username, password)

        def authenticate() -> Response:
            """Send 401 response with Basic Auth challenge"""
            return Response(
                'Authentication required', 401,
                {'WWW-Authenticate': 'Basic realm="Login Required"'}
            )

        def requires_auth(f):
            """Decorator to require Basic Auth"""
            @wraps(f)
            def decorated(*args, **kwargs):
                auth = request.authorization
                if not auth or not check_auth(auth.username, auth.password):
                    return authenticate()
                return f(*args, **kwargs)
            return decorated

        @app.route('/api/register', methods=['POST'])
        def api_register():
            """Register a new user (first-time registration)"""
            data = request.get_json() or {}
            username = data.get('username')
            password = data.get('password')
            
            if not username or not password:
                return jsonify({"ok": False, "error": "username and password are required"}), 400
            
            if len(username) < 3:
                return jsonify({"ok": False, "error": "username must be at least 3 characters"}), 400
            
            # if len(password) < 6:
            #     return jsonify({"ok": False, "error": "password must be at least 6 characters"}), 400
            
            success = self._register_user(username, password)
            if success:
                return jsonify({"ok": True, "message": f"User {username} registered successfully"})
            else:
                return jsonify({"ok": False, "error": f"Username {username} already exists"}), 409

        @app.route('/api/login', methods=['POST'])
        def api_login():
            """Login using Basic Auth"""
            auth = request.authorization
            if not auth:
                return authenticate()
            
            if check_auth(auth.username, auth.password):
                return jsonify({
                    "ok": True,
                    "message": f"Login successful for user {auth.username}",
                    "username": auth.username
                })
            else:
                return jsonify({"ok": False, "error": "Invalid username or password"}), 401

        @app.route('/api/torrent/send', methods=['POST'])
        @requires_auth
        def api_send():
            """Share a file (seed) - requires Basic Auth
            Accepts either:
            - File upload via multipart/form-data with 'file' field
            - JSON with 'filename' field (for existing files in seed directory)
            """
            # Check if file was uploaded
            if 'file' in request.files:
                uploaded_file = request.files['file']
                if uploaded_file.filename == '':
                    return jsonify({"ok": False, "error": "No file selected"}), 400
                
                filename = uploaded_file.filename
                
                # Save uploaded file to download_dir first
                download_path = os.path.join("/app", self.download_dir, filename)
                os.makedirs(os.path.dirname(download_path), exist_ok=True)
                
                try:
                    uploaded_file.save(download_path)
                    self._log(f"File uploaded to download_dir: {filename}")
                except Exception as e:
                    self._log(f"Failed to save uploaded file: {e}")
                    return jsonify({"ok": False, "error": f"Failed to save uploaded file: {str(e)}"}), 500
                
                # Copy file from download_dir to seed_dir for seeding
                seed_path = os.path.join("/app", self.seed_dir, filename)
                os.makedirs(os.path.dirname(seed_path), exist_ok=True)
                
                try:
                    shutil.copy2(download_path, seed_path)
                    self._log(f"File copied to seed_dir: {filename}")
                except Exception as e:
                    self._log(f"Failed to copy file to seed_dir: {e}")
                    return jsonify({"ok": False, "error": f"Failed to copy file to seed directory: {str(e)}"}), 500
                
                # Use existing logic to share the file
                success = self.own_file(filename)
                if success:
                    return jsonify({
                        "ok": True, 
                        "message": f"File {filename} uploaded and is now being shared",
                        "filename": filename,
                        "size": os.path.getsize(seed_path)
                    })
                else:
                    return jsonify({"ok": False, "error": f"Failed to share file {filename}"}), 500
            
            # Fallback to original behavior: use filename from JSON
            data = request.get_json() or {}
            filename = data.get('filename')
            if not filename:
                return jsonify({"ok": False, "error": "Either 'file' upload or 'filename' in JSON is required"}), 400
            
            success = self.own_file(filename)
            if success:
                return jsonify({"ok": True, "message": f"File {filename} is now being shared"})
            else:
                return jsonify({"ok": False, "error": f"File {filename} not found in seed directory"}), 404

        @app.route('/api/torrent/list', methods=['GET'])
        @requires_auth
        def api_list():
            """List all files available on tracker - requires Basic Auth"""
            resp = self._tracker_list()
            if not resp.get("ok"):
                return jsonify({"ok": False, "error": "tracker list failed"}), 500
            
            items = resp.get("items", [])
            formatted_items = []
            for it in items:
                formatted_items.append({
                    "filename": it.get('filename'),
                    "size": it.get('size'),
                    "peers": it.get('peers'),
                    "infohash": str(it.get('infohash', ''))[:10] + ".."
                })
            
            return jsonify({
                "ok": True,
                "items": formatted_items,
                "count": len(formatted_items)
            })

        @app.route('/api/torrent/download', methods=['POST'])
        @requires_auth
        def api_download():
            """Download a file by filename or infohash - requires Basic Auth"""
            data = request.get_json() or {}
            arg = data.get('filename') or data.get('infohash')
            if not arg:
                return jsonify({"ok": False, "error": "filename or infohash is required"}), 400
            
            # Check if it's an infohash (hex string) or filename
            if re.fullmatch(r"[0-9a-fA-F]{16,}", arg or ""):
                threading.Thread(target=self.download_by_infohash, args=(arg.lower(),), daemon=True).start()
                return jsonify({"ok": True, "message": f"Download started for infohash {arg[:10]}.."})
            else:
                threading.Thread(target=self.download_by_filename, args=(arg,), daemon=True).start()
                return jsonify({"ok": True, "message": f"Download started for filename {arg}"})

        @app.route('/api/exit', methods=['POST'])
        @requires_auth
        def api_exit():
            """Gracefully exit - notify tracker about all downloads - requires Basic Auth"""
            with self.dl_lock:
                for ih in list(self.downloads.keys()):
                    self._send_tracker({"mode": MODE_EXIT, "node_id": self.node_id, "infohash": ih})
            self._log("API exit requested")
            # Note: Flask will continue running, but downloads are cleaned up
            return jsonify({"ok": True, "message": "Exit signal sent to tracker"})

        @app.route('/api/status', methods=['GET'])
        @requires_auth
        def api_status():
            """Get node status and active downloads - requires Basic Auth"""
            with self.dl_lock:
                active_downloads = []
                for ih, st in self.downloads.items():
                    active_downloads.append({
                        "infohash": ih[:10] + "..",
                        "filename": st.get("filename"),
                        "progress": f"{st.get('done', 0)}/{st.get('total_pieces', 0)}",
                        "size": st.get("size")
                    })
            
            return jsonify({
                "ok": True,
                "node_id": self.node_id,
                "seeding_count": len(self.seeding),
                "active_downloads": active_downloads,
                "downloads_count": len(self.downloads)
            })

        @app.route('/api/nodes/connected', methods=['GET'])
        @requires_auth
        def api_connected_nodes():
            """Get list of currently active connected peer nodes - requires Basic Auth
            Only returns nodes that are currently active (within tracker TTL).
            Nodes that have gone offline will be automatically filtered out.
            """
            connected_nodes = {}  # Use dict to deduplicate by (node_id, host, port)
            
            # Get all swarms this node is part of (downloads + seeding)
            with self.dl_lock:
                active_swarms = set(self.downloads.keys()) | set(self.seeding)
            
            # Query tracker for each swarm to get current active peers
            # The tracker automatically filters out inactive nodes (outside TTL)
            for ih in active_swarms:
                try:
                    resp = self._tracker_need(ih)
                    if resp.get("ok"):
                        peers = resp.get("peers", [])
                        for peer in peers:
                            # Exclude self
                            if peer.get("node_id") == self.node_id:
                                continue
                            
                            # Create unique key for deduplication
                            node_id = peer.get("node_id")
                            host = peer.get("host")
                            port = peer.get("port")
                            key = (node_id, host, port)
                            
                            # Only add if not already seen or update with latest info
                            if key not in connected_nodes:
                                connected_nodes[key] = {
                                    "node_id": node_id,
                                    "host": host,
                                    "port": port,
                                    "swarms": []
                                }
                            
                            # Track which swarms this node is in
                            swarm_info = {
                                "infohash": ih[:10] + "..",
                                "filename": resp.get("meta", {}).get("filename", "unknown")
                            }
                            if swarm_info not in connected_nodes[key]["swarms"]:
                                connected_nodes[key]["swarms"].append(swarm_info)
                except Exception as e:
                    self._log(f"Error querying tracker for swarm {ih[:10]}..: {e}")
                    continue
            
            # Convert to list format
            nodes_list = list(connected_nodes.values())
            
            return jsonify({
                "ok": True,
                "connected_nodes": nodes_list,
                "count": len(nodes_list)
            })

        @app.route('/health', methods=['GET'])
        def health():
            """Health check endpoint"""
            return jsonify({"ok": True, "status": "healthy"})

        self._log(f"Starting Flask API server on port {api_port}")
        app.run(host='0.0.0.0', port=api_port, debug=False, threaded=True)


def main() -> None:
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("-node_id", type=int, required=True)
    p.add_argument("-api_port", type=int, default=5000, help="Flask API server port (default: 5000)")
    args = p.parse_args()
    Node(args.node_id).start_api(api_port=args.api_port)


if __name__ == "__main__":
    main()
