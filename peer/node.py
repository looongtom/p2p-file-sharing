# peer/node.py
from __future__ import annotations

import os
import json
import time
import socket
import argparse
import base64
import hashlib
from threading import Thread, Event, Lock
from typing import Dict, Any, Tuple, Optional

from common.constants import (
    MODE_REGISTER, MODE_OWN, MODE_NEED, MODE_UPDATE, MODE_EXIT,
    DEFAULT_BUFFER_SIZE, DEFAULT_NODE_HEARTBEAT_INTERVAL,
    DEFAULT_CHUNK_SIZE, DEFAULT_ACK_TIMEOUT, DEFAULT_MAX_RETRIES
)
from common.protocol import encode_message, decode_message


class Node:
    def __init__(self, node_id: int):
        self.node_id = node_id

        # Tracker
        self.tracker_host = os.getenv("TRACKER_HOST", "tracker")
        self.tracker_port = int(os.getenv("TRACKER_PORT", "12345"))
        self.tracker_addr: Tuple[str, int] = (self.tracker_host, self.tracker_port)

        # Peer endpoint
        self.bind_host = os.getenv("BIND_HOST", "0.0.0.0")
        self.node_port = int(os.getenv("NODE_PORT", "20001"))

        self.advertise_host = os.getenv("ADVERTISE_HOST", os.getenv("HOSTNAME", "peer1"))
        self.advertise_port = self.node_port

        # Sizes and timeouts
        self.buffer_size = int(os.getenv("BUFFER_SIZE", str(DEFAULT_BUFFER_SIZE)))
        self.heartbeat_interval = int(os.getenv("NODE_TIME_INTERVAL", str(DEFAULT_NODE_HEARTBEAT_INTERVAL)))
        self.chunk_size = int(os.getenv("CHUNK_SIZE", str(DEFAULT_CHUNK_SIZE)))
        self.ack_timeout = float(os.getenv("ACK_TIMEOUT", str(DEFAULT_ACK_TIMEOUT)))
        self.max_retries = int(os.getenv("MAX_RETRIES", str(DEFAULT_MAX_RETRIES)))

        # File dirs (in container)
        self.seed_dir = os.getenv("SEED_DIR", "node_files")
        self.download_dir = os.getenv("DOWNLOAD_DIR", "downloads")
        os.makedirs(self.seed_dir, exist_ok=True)
        os.makedirs(self.download_dir, exist_ok=True)

        self.running = True

        # UDP socket (single port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.bind_host, self.node_port))

        # Tracker response sync
        self._tracker_resp_lock = Lock()
        self._tracker_response: Optional[Dict[str, Any]] = None
        self._tracker_event = Event()

        # Ack handling
        self._ack_events: Dict[Tuple[str, int, Tuple[str, int]], Event] = {}
        self._ack_lock = Lock()

        # Download sessions
        self._dl_lock = Lock()
        self._downloads: Dict[str, Dict[str, Any]] = {}

        print(f"[NODE {self.node_id}] bind={self.bind_host}:{self.node_port} advertise={self.advertise_host}:{self.advertise_port}")
        print(f"[NODE {self.node_id}] tracker={self.tracker_host}:{self.tracker_port}")
        print(f"[NODE {self.node_id}] seed_dir=/app/{self.seed_dir} download_dir=/app/{self.download_dir}")

        Thread(target=self._recv_loop, daemon=True).start()
        Thread(target=self._heartbeat_loop, daemon=True).start()

    # -------- send helpers --------
    def _send(self, payload: Dict[str, Any], addr: Tuple[str, int]):
        self.sock.sendto(encode_message(payload), addr)

    def _send_to_tracker(self, payload: Dict[str, Any]):
        payload.setdefault("node_id", self.node_id)
        payload.setdefault("host", self.advertise_host)
        payload.setdefault("port", self.advertise_port)
        self._send(payload, self.tracker_addr)

    # -------- tracker ops --------
    def register(self):
        self._send_to_tracker({"mode": MODE_REGISTER})

    def own_file(self, filename: str):
        path = os.path.join(self.seed_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"Seed file not found: /app/{self.seed_dir}/{filename}")
        self._send_to_tracker({"mode": MODE_OWN, "filename": filename})

    def need_file(self, filename: str) -> Dict[str, Any]:
        with self._tracker_resp_lock:
            self._tracker_response = None
            self._tracker_event.clear()

        self._send_to_tracker({"mode": MODE_NEED, "filename": filename})

        ok = self._tracker_event.wait(timeout=5)
        if not ok:
            raise TimeoutError("Tracker did not respond in time.")
        with self._tracker_resp_lock:
            return self._tracker_response or {}

    def update_db(self):
        self._send_to_tracker({"mode": MODE_UPDATE})

    def exit(self):
        self._send_to_tracker({"mode": MODE_EXIT})

    # -------- heartbeat --------
    def _heartbeat_loop(self):
        while self.running:
            try:
                self.register()
            except Exception:
                pass
            time.sleep(self.heartbeat_interval)

    # -------- file helpers --------
    def _file_sha256(self, path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        return h.hexdigest()

    # -------- peer protocol handlers --------
    def _handle_peer_req(self, msg: Dict[str, Any], addr: Tuple[str, int]):
        filename = msg.get("filename")
        if not filename:
            return
        path = os.path.join(self.seed_dir, filename)
        if not os.path.exists(path):
            self._send({"type": "PEER_META", "ok": False, "filename": filename, "error": "NOT_FOUND"}, addr)
            return

        size = os.path.getsize(path)
        sha256 = self._file_sha256(path)
        total_chunks = (size + self.chunk_size - 1) // self.chunk_size

        self._send({
            "type": "PEER_META",
            "ok": True,
            "filename": filename,
            "size": size,
            "sha256": sha256,
            "chunk_size": self.chunk_size,
            "total_chunks": total_chunks
        }, addr)

        Thread(target=self._send_file_chunks, args=(filename, path, total_chunks, addr), daemon=True).start()

    def _send_file_chunks(self, filename: str, path: str, total_chunks: int, peer_addr: Tuple[str, int]):
        with open(path, "rb") as f:
            for seq in range(total_chunks):
                data = f.read(self.chunk_size)
                payload = {
                    "type": "PEER_CHUNK",
                    "filename": filename,
                    "seq": seq,
                    "data": base64.b64encode(data).decode("ascii"),
                }

                ack_key = (filename, seq, peer_addr)
                ev = Event()
                with self._ack_lock:
                    self._ack_events[ack_key] = ev

                sent_ok = False
                for _ in range(self.max_retries):
                    self._send(payload, peer_addr)
                    if ev.wait(timeout=self.ack_timeout):
                        sent_ok = True
                        break

                with self._ack_lock:
                    self._ack_events.pop(ack_key, None)

                if not sent_ok:
                    print(f"[NODE {self.node_id}] transfer to {peer_addr} failed at seq={seq}")
                    return

        try:
            self.update_db()
        except Exception:
            pass
        print(f"[NODE {self.node_id}] finished sending {filename} to {peer_addr}")

    def _handle_peer_meta(self, msg: Dict[str, Any], addr: Tuple[str, int]):
        filename = msg.get("filename")
        if not filename:
            return
        if not msg.get("ok", False):
            print(f"[NODE {self.node_id}] META not ok for {filename} from {addr}: {msg.get('error')}")
            return

        with self._dl_lock:
            self._downloads[filename] = {
                "from": addr,
                "size": int(msg["size"]),
                "sha256": msg["sha256"],
                "chunk_size": int(msg["chunk_size"]),
                "total_chunks": int(msg["total_chunks"]),
                "received": {},
                "received_count": 0
            }

        print(f"[NODE {self.node_id}] META ok: {filename} size={msg['size']} chunks={msg['total_chunks']} from {addr}")

    def _handle_peer_chunk(self, msg: Dict[str, Any], addr: Tuple[str, int]):
        filename = msg.get("filename")
        seq = msg.get("seq")
        data_b64 = msg.get("data")
        if filename is None or seq is None or data_b64 is None:
            return

        try:
            chunk = base64.b64decode(data_b64.encode("ascii"))
        except Exception:
            return

        completed = False
        with self._dl_lock:
            sess = self._downloads.get(filename)
            if not sess:
                return
            if int(seq) not in sess["received"]:
                sess["received"][int(seq)] = chunk
                sess["received_count"] += 1
            if sess["received_count"] >= sess["total_chunks"]:
                completed = True

        # ack
        self._send({"type": "PEER_ACK", "filename": filename, "seq": int(seq)}, addr)

        if completed:
            self._finalize_download(filename)

    def _finalize_download(self, filename: str):
        with self._dl_lock:
            sess = self._downloads.get(filename)
            if not sess:
                return
            total = sess["total_chunks"]
            chunks = sess["received"]
            expected_sha = sess["sha256"]
            size = sess["size"]

        out_path = os.path.join(self.download_dir, filename)
        tmp_path = out_path + ".part"

        with open(tmp_path, "wb") as f:
            for i in range(total):
                f.write(chunks.get(i, b""))

        with open(tmp_path, "rb+") as f:
            f.truncate(size)

        h = hashlib.sha256()
        with open(tmp_path, "rb") as f:
            for block in iter(lambda: f.read(1024 * 1024), b""):
                h.update(block)
        got_sha = h.hexdigest()

        if got_sha != expected_sha:
            print(f"[NODE {self.node_id}] hash mismatch for {filename}: expected={expected_sha} got={got_sha}")
            return

        os.replace(tmp_path, out_path)
        print(f"[NODE {self.node_id}] DOWNLOAD COMPLETE: {filename} saved to /app/{self.download_dir}/{filename}")

        with self._dl_lock:
            self._downloads.pop(filename, None)

    def _handle_peer_ack(self, msg: Dict[str, Any], addr: Tuple[str, int]):
        filename = msg.get("filename")
        seq = msg.get("seq")
        if filename is None or seq is None:
            return
        key = (filename, int(seq), addr)
        with self._ack_lock:
            ev = self._ack_events.get(key)
        if ev:
            ev.set()

    # -------- receive loop --------
    def _recv_loop(self):
        while True:
            try:
                data, addr = self.sock.recvfrom(self.buffer_size)
            except Exception:
                continue

            try:
                msg = decode_message(data)
            except Exception:
                continue

            if msg.get("mode") == "SEARCH_RESULT":
                with self._tracker_resp_lock:
                    self._tracker_response = msg
                    self._tracker_event.set()
                continue

            mtype = msg.get("type")
            if mtype == "PEER_REQ":
                self._handle_peer_req(msg, addr)
            elif mtype == "PEER_META":
                self._handle_peer_meta(msg, addr)
            elif mtype == "PEER_CHUNK":
                self._handle_peer_chunk(msg, addr)
            elif mtype == "PEER_ACK":
                self._handle_peer_ack(msg, addr)

    # -------- high level transfer --------
    def download_file(self, filename: str):
        resp = self.need_file(filename)
        results = resp.get("search_result", [])
        if not results:
            print(f"[NODE {self.node_id}] No peers found for {filename}")
            return

        entry = results[0][0]
        addr_list = entry.get("addr")
        if not addr_list or len(addr_list) != 2:
            print(f"[NODE {self.node_id}] Invalid peer addr: {entry}")
            return
        peer_addr = (addr_list[0], int(addr_list[1]))

        self._send({"type": "PEER_REQ", "filename": filename, "from_node": self.node_id}, peer_addr)
        print(f"[NODE {self.node_id}] requested {filename} from {peer_addr}")

    # -------- interactive --------
    def start_interactive(self):
        print("\nCommands:")
        print("  torrent -setMode send <filename>      (announce OWN; file must exist in /app/node_files)")
        print("  torrent -setMode download <filename>  (download real file to /app/downloads)")
        print("  exit\n")

        while True:
            try:
                cmd = input(f"[NODE {self.node_id}]> ").strip()
                if not cmd:
                    continue
                if cmd == "exit":
                    self.running = False
                    self.exit()
                    break

                parts = cmd.split()
                if len(parts) >= 4 and parts[0] == "torrent" and parts[1] == "-setMode":
                    mode = parts[2]
                    filename = " ".join(parts[3:])

                    if mode == "send":
                        self.own_file(filename)
                        print(f"[NODE {self.node_id}] OWN announced: {filename}")

                    elif mode == "download":
                        self.download_file(filename)

                    else:
                        print("Unknown mode. Use send|download.")
                else:
                    print("Unknown command.")
            except EOFError:
                # no TTY -> keep container alive
                while True:
                    time.sleep(3600)
            except KeyboardInterrupt:
                self.running = False
                try:
                    self.exit()
                except Exception:
                    pass
                break


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-node_id", type=int, required=True)
    args = ap.parse_args()
    Node(node_id=args.node_id).start_interactive()


if __name__ == "__main__":
    main()
